#!/usr/bin/env python3
"""Exercise orchestration with fake stage commands; never modify the installed OS."""
import contextlib
import importlib.machinery
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO/'scripts'))

def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module

installer = load('installer', REPO/'install')
yay = load('yay_bootstrap', REPO/'scripts/yay')

class Orchestration(unittest.TestCase):
    def invoke(self, stage, replies=(), status=0):
        stream = io.StringIO()
        result = ({'side_effect': [subprocess.CompletedProcess([], code) for code in status]}
                  if isinstance(status, tuple) else {'return_value': subprocess.CompletedProcess([], status)})
        with patch.object(installer.Installer, 'preflight'), patch('builtins.input', side_effect=replies), \
                patch.object(installer.subprocess, 'run', **result) as run, \
                contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            code = installer.main(['--profile', 'framework', '--from', stage])
        return code, run.call_args_list, stream.getvalue()

    def test_dry_run_executes_nothing_and_shows_order(self):
        stream = io.StringIO()
        with patch.object(installer.subprocess, 'run') as run, \
                patch.object(installer.subprocess, 'check_output') as query, \
                patch('builtins.input') as prompt, contextlib.redirect_stdout(stream):
            self.assertEqual(installer.main(['--profile', 'framework', '--dry-run']), 0)
        run.assert_not_called(); query.assert_not_called(); prompt.assert_not_called()
        stages = [line.removeprefix('Stage: ') for line in stream.getvalue().splitlines() if line.startswith('Stage: ')]
        self.assertEqual(stages, list(installer.STAGES))
        self.assertIn('MANUAL STEP', stream.getvalue())

    def test_noninteractive_install_stops_before_commands(self):
        with patch.object(sys.stdin, 'isatty', return_value=False), patch.object(installer.subprocess, 'run') as run, \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(installer.main(['--profile', 'framework']), 1)
        run.assert_not_called()

    def test_package_failure_stops_and_names_resume_stage(self):
        code, calls, output = self.invoke('packages', ['install'], status=(0, 17))
        self.assertEqual(code, 1)
        self.assertEqual(len(calls), 2)
        self.assertNotIn('--apply', calls[0].args[0])
        self.assertEqual(calls[1].args[0][0], 'doas')
        self.assertIn('--apply', calls[1].args[0])
        self.assertIn('--from packages', output)
        self.assertNotIn('Stage: aur', output)

    def test_configuration_review_cannot_be_skipped(self):
        code, calls, output = self.invoke('configuration', ['install', ''])
        self.assertEqual(code, 3)
        commands = [call.args[0] for call in calls]
        self.assertEqual(len(commands), 2)
        self.assertTrue(all('--apply' not in command for command in commands))
        self.assertNotEqual(commands[0][0], 'doas')
        self.assertEqual(commands[1][0], 'doas')
        self.assertIn('--from configuration', output)

    def test_apply_keeps_user_and_root_scopes_separate(self):
        install = installer.Installer('framework')
        with patch('builtins.input', return_value='replace'), patch.object(installer.subprocess, 'run',
                return_value=subprocess.CompletedProcess([], 0)) as run, contextlib.redirect_stdout(io.StringIO()):
            install.configuration()
        commands = [call.args[0] for call in run.call_args_list]
        file_applies = [command for command in commands if '--apply' in command and '--scope' in command]
        self.assertEqual(len(file_applies), 2)
        self.assertNotEqual(file_applies[0][0], 'doas')
        self.assertIn('home', file_applies[0])
        self.assertEqual(file_applies[1][0], 'doas')
        self.assertIn('system', file_applies[1])
        self.assertTrue(all('--replace' in command for command in file_applies))

    def test_group_activation_pauses_before_service_enablement(self):
        with patch.object(installer.os, 'getgroups', return_value=[]), patch.object(installer.os, 'getgid', return_value=-1):
            code, calls, output = self.invoke('services', ['install'])
        self.assertEqual(code, 3)
        self.assertEqual(calls, [])
        self.assertIn('Log out', output)
        self.assertIn('--from services', output)

    def test_private_input_pause_precedes_service_commands(self):
        with patch.object(installer.os, 'getgroups', return_value=[42]), \
                patch.object(installer.grp, 'getgrnam', return_value=SimpleNamespace(gr_gid=42)):
            code, calls, output = self.invoke('services', ['install', ''])
        self.assertEqual(code, 3)
        self.assertEqual(calls, [])
        self.assertIn('home.conf', output)
        self.assertIn('--from services', output)

    def test_repository_review_and_first_backup_survive_reruns(self):
        with tempfile.TemporaryDirectory(prefix='bootstrap-repositories-test-') as temporary:
            root = Path(temporary)
            (root/'templates').mkdir()
            (root/'templates/pacman.conf').write_text('reviewed policy\n')
            target, backup = root/'pacman.conf', root/'pacman.conf.before-bootstrap'
            target.write_text('original policy\n')
            real_run = subprocess.run
            def fake_command(command, **kwargs):
                if '/usr/bin/cp' in command or '/usr/bin/install' in command:
                    # Exercise the actual file commands, without doas and only
                    # against the explicitly substituted temporary paths.
                    self.assertTrue(all(Path(arg).is_relative_to(root) for arg in command[-2:]))
                    return real_run(command[1:], **kwargs)
                return subprocess.CompletedProcess(command, 0)
            paths = {'/etc/pacman.conf': target, '/etc/pacman.conf.before-bootstrap': backup}
            with patch.object(installer, 'REPO', root), patch.object(installer, 'Path', side_effect=lambda p: paths[p]), \
                    patch.object(installer.subprocess, 'run', side_effect=fake_command), contextlib.redirect_stdout(io.StringIO()):
                install = installer.Installer('framework')
                with patch('builtins.input', return_value=''), self.assertRaises(installer.Paused):
                    install.repositories()
                self.assertEqual(target.read_text(), 'original policy\n')
                self.assertFalse(backup.exists())
                with patch('builtins.input', return_value='replace'):
                    install.repositories()
                    self.assertEqual(target.read_text(), 'reviewed policy\n')
                    target.write_text('later edit\n')
                    install.repositories()
                self.assertEqual(backup.read_text(), 'original policy\n')
                with patch('builtins.input', side_effect=AssertionError('Identical policy needs no replacement')):
                    install.repositories()

    def test_boot_review_blocks_writes_and_efi_stays_manual(self):
        install = installer.Installer('framework')
        with patch('builtins.input', return_value=''), patch.object(installer.subprocess, 'run') as run, \
                contextlib.redirect_stdout(io.StringIO()), self.assertRaises(installer.Paused):
            install.boot()
        run.assert_not_called()
        with patch('builtins.input', return_value='continue'), patch.object(installer.subprocess, 'run',
                return_value=subprocess.CompletedProcess([], 0)) as run, contextlib.redirect_stdout(io.StringIO()):
            install.boot()
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(len(commands), 2)
        self.assertTrue(all(any(str(arg).endswith('/scripts/initramfs') for arg in command) for command in commands))
        with patch('builtins.input', return_value='continue'), patch.object(installer.subprocess, 'run') as run, \
                contextlib.redirect_stdout(io.StringIO()):
            installer.Installer('portable').boot()
        run.assert_not_called()

    def test_verify_resume_only_verifies_and_preserves_failures(self):
        for status in (0, 1, 2):
            with self.subTest(status=status):
                code, calls, output = self.invoke('verify', status=status)
                self.assertEqual(code, status)
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0].args[0][0], 'doas')
                self.assertTrue(str(calls[0].args[0][1]).endswith('/scripts/verify'))
                self.assertIn('physical', output)

    def test_yay_decline_does_not_run_aur_packages(self):
        code, calls, output = self.invoke('aur', ['install'], status=(0, 3))
        self.assertEqual(code, 3)
        self.assertEqual(len(calls), 2)
        self.assertIn('--from aur', output)

class YayBootstrap(unittest.TestCase):
    def test_fresh_local_clone_review_build_and_retry(self):
        with tempfile.TemporaryDirectory(prefix='bootstrap-yay-test-') as temporary:
            root = Path(temporary)
            upstream, target = root/'upstream', root/'target'
            upstream.mkdir(); target.mkdir()
            subprocess.run(['git', 'init', '-q', str(upstream)], check=True)
            (upstream/'PKGBUILD').write_text('# Test recipe: never executed.\n')
            subprocess.run(['git', '-C', str(upstream), 'add', 'PKGBUILD'], check=True)
            subprocess.run(['git', '-C', str(upstream), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                            'commit', '-qm', 'fixture'], check=True)
            revision = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()
            with patch.object(yay, 'REPO', target), patch.object(yay, 'URL', str(upstream)), \
                    patch.object(yay, 'REVISION', revision), patch.object(yay.shutil, 'which', return_value=None), \
                    patch.object(sys.stdin, 'isatty', return_value=True), patch('builtins.input', return_value=''), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(yay.main(['--apply']), 3)
            self.assertFalse((target/'.work/makepkg.conf').exists(), 'Declining review must not prepare a build')
            recipe = target/'.work/aur/yay/PKGBUILD'
            original = recipe.read_text()
            recipe.write_text('preserve my recipe edit\n')
            with patch.object(yay, 'REPO', target), patch.object(yay, 'URL', str(upstream)), \
                    patch.object(yay, 'REVISION', revision), patch.object(yay.shutil, 'which', return_value=None), \
                    patch.object(sys.stdin, 'isatty', return_value=True), contextlib.redirect_stdout(io.StringIO()), \
                    self.assertRaises(subprocess.CalledProcessError):
                yay.main(['--apply'])
            self.assertEqual(recipe.read_text(), 'preserve my recipe edit\n')
            recipe.write_text(original)
            real_run = subprocess.run
            built = []
            def fake_makepkg(command, **kwargs):
                if command[0] == 'makepkg':
                    built.append((command, kwargs['cwd']))
                    return subprocess.CompletedProcess(command, 0)
                return real_run(command, **kwargs)
            with patch.object(yay, 'REPO', target), patch.object(yay, 'URL', str(upstream)), \
                    patch.object(yay, 'REVISION', revision), patch.object(yay.shutil, 'which', side_effect=[None, '/test/yay']), \
                    patch.object(sys.stdin, 'isatty', return_value=True), patch('builtins.input', return_value='build'), \
                    patch.object(yay.subprocess, 'run', side_effect=fake_makepkg), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(yay.main(['--apply']), 0)
            self.assertEqual(len(built), 1)
            self.assertEqual(built[0][1], target/'.work/aur/yay')
            self.assertIn('PACMAN_AUTH=(doas)', (target/'.work/makepkg.conf').read_text())
            with patch.object(yay.shutil, 'which', return_value='/test/yay'), patch.object(yay, 'run') as run, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(yay.main(['--apply']), 0)
            run.assert_not_called()

if __name__ == '__main__':
    if os.geteuid() == 0:
        sys.exit('Run tests as an ordinary user.')
    unittest.main()
