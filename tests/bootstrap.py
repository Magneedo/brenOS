#!/usr/bin/env python3
"""Phase-0 tests: fake package/privilege commands, local Git, temporary files only."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import pty
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('phase0', REPO / 'scripts/phase0.py')
phase0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phase0)


def shell(code, *args, terminal=False, reply=''):
    command = ['/bin/bash', '-p', '-c', 'source ' + shlex.quote(str(REPO / 'bootstrap')) + '\n' + code, 'test', *args]
    if not terminal:
        return subprocess.run(command, capture_output=True, text=True, timeout=5)
    master, slave = pty.openpty()
    try:
        with subprocess.Popen(command, stdin=slave, stdout=slave, stderr=slave) as process:
            os.close(slave)
            slave = None
            os.write(master, reply.encode())
            process.wait(timeout=5)
            chunks = []
            while True:
                try:
                    block = os.read(master, 8192)
                except OSError:
                    break
                if not block:
                    break
                chunks.append(block)
            return subprocess.CompletedProcess(command, process.returncode, b''.join(chunks).decode(), '')
    finally:
        os.close(master)
        if slave is not None:
            os.close(slave)


class Launcher(unittest.TestCase):
    def test_wrong_distro_and_init(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('etc', 'sbin', 'proc/1', 'bin'):
                (root / name).mkdir(parents=True, exist_ok=True)
            for name in ('runit', 'runit-init'):
                (root / 'bin' / name).touch()
            (root / 'sbin/init').symlink_to(root / 'bin/runit-init')
            (root / 'proc/1/comm').write_text('runit\n')
            for distro, expected in [('arch', 1), ('artix', 0)]:
                (root / 'etc/os-release').write_text('ID=' + distro + '\n')
                self.assertEqual(shell('check_platform "$1"', directory).returncode, expected)
            (root / 'proc/1/comm').write_text('systemd\n')
            self.assertNotEqual(shell('check_platform "$1"', directory).returncode, 0)

    def test_user_root_and_group_identity(self):
        fixture = '''getent() { printf '%s\\n' "$fixture_passwd"; }
id() { printf 'bren wheel\\n'; }
fixture_passwd=$1
check_account "$2" "$3" "$4"
'''
        good = 'bren:x:1000:1000::/home/bren:/bin/bash'
        for uid, euid, gid in [('1000','1000','1000'), ('0','0','0'), ('1001','1001','1000'), ('1000','0','1000'), ('1000','1000','1001')]:
            result = shell(fixture, good, uid, euid, gid)
            self.assertEqual(result.returncode == 0, uid == euid == gid == '1000')
        for account in [good.replace('bren:', 'alice:', 1), good.replace('/bin/bash', '/bin/zsh'), good.replace('/home/bren', '/home/alice')]:
            self.assertNotEqual(shell(fixture, account, '1000', '1000', '1000').returncode, 0)

    def test_esp_absent_readonly_wrong_type_and_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'proc').mkdir()
            for mount, valid in [('', False), ('/dev/test /boot vfat ro 0 0\n', False),
                                 ('/dev/test /boot ext4 rw 0 0\n', False),
                                 ('/dev/test /boot vfat rw,relatime 0 0\n', True)]:
                (root / 'proc/mounts').write_text(mount)
                self.assertEqual(shell('check_boot "$1"', directory).returncode == 0, valid)

    def test_prerequisite_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            cert = Path(directory) / 'etc/ssl/certs/ca-certificates.crt'
            cert.parent.mkdir(parents=True)
            cert.write_text('test trust bundle\n')
            self.assertEqual(shell('command() { return 0; }; missing_packages "$1"', directory).stdout, '')
            result = shell('command() { return 1; }; missing_packages "$1"', directory)
            self.assertEqual(result.stdout.splitlines(), ['python', 'git', 'opendoas', 'util-linux'])
            cert.unlink()
            self.assertEqual(shell('command() { return 0; }; missing_packages "$1"', directory).stdout, 'ca-certificates\n')

    def test_dry_run_never_calls_privileged_or_installer_commands(self):
        result = shell('su() { exit 99; }; exec() { exit 98; }; main --dry-run --from services')
        self.assertEqual(result.returncode, 0)
        self.assertIn('./install --profile framework --from services', result.stdout)
        self.assertNotEqual(shell('main --profile "framework; bad" --dry-run').returncode, 0)
        self.assertNotEqual(shell('main --from "../../bad" --dry-run').returncode, 0)

    def test_noninteractive_stops(self):
        result = shell('su() { exit 99; }; main')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('interactive', result.stderr)

    def test_first_run_prerequisites_retry_and_handoff(self):
        # Stub every host check/mutation and exec. The real host cannot be changed.
        fixture = '''unset DISPLAY WAYLAND_DISPLAY SSH_CONNECTION SSH_TTY
check_platform() { :; }; check_account() { :; }; check_checkout() { :; }
check_boot() { printf 'CHECK_BOOT\\n'; }
pacman() { printf 'UNEXPECTED_PACMAN\\n'; exit 99; }
ready=no
missing_packages() { if [[ $ready == no ]]; then printf 'python\\nopendoas\\n'; fi; }
su() { printf 'ROOT %s\\n' "$*"; ready=yes; }
exec() { printf 'HANDOFF %s\\n' "$*"; }
main --from packages
main --from packages
'''
        result = shell(fixture, terminal=True, reply='prepare\n')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout.count('ROOT --login'), 1)
        self.assertEqual(result.stdout.count('HANDOFF /usr/bin/python3 -I'), 2)
        self.assertLess(result.stdout.index('CHECK_BOOT'), result.stdout.index('ROOT --login'))
        self.assertIn('/usr/bin/pacman -Syu --needed python opendoas', result.stdout)
        self.assertIn('no phase-0 package transaction', result.stdout)
        declined = shell(fixture, terminal=True, reply='\n')
        self.assertEqual(declined.returncode, 3)
        self.assertNotIn('ROOT --login', declined.stdout)
        failed = shell(fixture.replace('ready=yes;', 'return 1;'), terminal=True, reply='prepare\n')
        self.assertNotEqual(failed.returncode, 0)
        self.assertNotIn('HANDOFF', failed.stdout)


class Policy(unittest.TestCase):
    def test_exact_pin_read_without_executing_source_and_bad_pin_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            upstream = root / 'upstream'
            upstream.mkdir()
            (upstream / 'etc').mkdir()
            content = 'permit persist :wheel\n'
            (upstream / 'etc/doas.conf').write_text(content)
            subprocess.run(['git','init','-q',str(upstream)], check=True)
            subprocess.run(['git','-C',str(upstream),'add','.'], check=True)
            subprocess.run(['git','-C',str(upstream),'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture'], check=True)
            revision = subprocess.check_output(['git','-C',str(upstream),'rev-parse','HEAD'],text=True).strip()
            (upstream / 'etc/doas.conf').write_text('uncommitted content must not be used\n')
            (root / 'manifests').mkdir()
            manifest = root / 'manifests/repositories.tsv'
            manifest.write_text(f'dotfiles\thttps://github.com/Magneedo/dotfiles.git\t{revision}\n')
            real_run = subprocess.run
            def local_git(command, **kwargs):
                command = list(command)
                if 'fetch' in command:
                    self.assertEqual(command[-2:], ['https://github.com/Magneedo/dotfiles.git',revision])
                    command[-2] = str(upstream)
                return real_run(command, **kwargs)
            with patch.object(phase0,'REPO',root), patch.object(phase0,'trusted_path'), \
                    patch.object(phase0.subprocess,'run',side_effect=local_git), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(phase0.pinned_policy(), content)
            manifest.write_text('dotfiles\thttps://github.com/Magneedo/dotfiles.git\tmain\n')
            with patch.object(phase0,'REPO',root), patch.object(phase0,'trusted_path'), \
                    patch.object(phase0.subprocess,'run') as run, self.assertRaises(ValueError):
                phase0.pinned_policy()
            run.assert_not_called()

    def test_untrusted_or_symlink_input_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input'
            path.write_text('test\n')
            path.chmod(0o666)
            with self.assertRaises(ValueError):
                phase0.trusted_path(path)
            path.unlink()
            path.symlink_to(Path(directory)/'absent')
            with self.assertRaises(ValueError):
                phase0.trusted_path(path)

    def test_policy_creation_is_atomic_private_and_refuses_existing_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / 'doas.conf'
            # Exercise the exact elevated program, replacing only root/filesystem
            # locations and the doas syntax checker. No real privileged command.
            program = phase0.CREATE_POLICY.replace("pathlib.Path('/etc/doas.conf')", 'pathlib.Path(' + repr(str(target)) + ')')
            program = program.replace('os.geteuid() != 0', 'False').replace("dir='/etc'", 'dir=' + repr(directory))
            policy = 'permit bren as root cmd /usr/bin/true\n'
            with patch.object(sys, 'argv', ['test', policy]), patch('subprocess.run') as checker:
                exec(program, {})
            self.assertEqual(target.read_text(), policy)
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            self.assertEqual(target.stat().st_nlink, 1)
            checker.assert_called_once()
            for symbolic in (False, True):
                if symbolic:
                    target.unlink()
                    target.symlink_to(root / 'absent')
                with patch.object(sys, 'argv', ['test', policy]), patch('subprocess.run') as checker, self.assertRaises(SystemExit):
                    exec(program, {})
                checker.assert_not_called()
            target.unlink()
            with patch.object(sys, 'argv', ['test', policy]), patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'doas')), self.assertRaises(subprocess.CalledProcessError):
                exec(program, {})
            self.assertFalse(target.exists())
            # Another process creates policy after the initial existence check.
            # Atomic publication must preserve its file, not replace it.
            def race(*args, **kwargs):
                target.write_text('concurrent policy\n')
            with patch.object(sys, 'argv', ['test', policy]), patch('subprocess.run', side_effect=race), self.assertRaises(FileExistsError):
                exec(program, {})
            self.assertEqual(target.read_text(), 'concurrent policy\n')

    def test_review_decline_and_quoted_policy_data(self):
        policy = 'permit bren as root cmd /usr/bin/true # quote \' ; $(not-executed)\n'
        absent = unittest.mock.Mock()
        absent.exists.return_value = absent.is_symlink.return_value = False
        with patch.object(phase0, 'Path', return_value=absent), patch.object(phase0, 'pinned_policy', return_value=policy), \
                patch.object(phase0.grp, 'getgrnam', return_value=type('Group', (), {'gr_gid': 42})()), \
                patch.object(phase0.os, 'getgroups', return_value=[42]), contextlib.redirect_stdout(io.StringIO()):
            with patch('builtins.input', return_value=''), patch.object(phase0.subprocess, 'run') as run:
                self.assertEqual(phase0.ensure_policy(), 3)
                run.assert_not_called()
            with patch('builtins.input', return_value='policy'), patch.object(phase0.subprocess, 'run') as run:
                self.assertEqual(phase0.ensure_policy(), 0)
                invocation = run.call_args_list[0].args[0]
                self.assertEqual(invocation[0], '/usr/bin/su')
                parsed = shlex.split(invocation[5].removeprefix('cd / && exec '))
                self.assertEqual(parsed, ['/usr/bin/python3', '-I', '-c', phase0.CREATE_POLICY, policy])
                self.assertEqual(run.call_args_list[1].args[0], ['/usr/bin/doas', '/usr/bin/true'])

    def test_existing_policy_is_kept_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'doas.conf'
            target.write_text('existing policy\n')
            real_stat = target.lstat()
            safe = type('Stat', (), {'st_mode': real_stat.st_mode, 'st_uid': 0})()
            with patch.object(phase0, 'Path', return_value=target), patch.object(Path, 'lstat', return_value=safe), \
                    patch.object(phase0, 'pinned_policy') as fetch, patch.object(phase0.subprocess, 'run') as run, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(phase0.ensure_policy(), 0)
                fetch.assert_not_called()
                run.assert_called_once_with(['/usr/bin/doas', '/usr/bin/true'], check=True)
            target.unlink()
            target.symlink_to(Path(directory) / 'absent')
            with patch.object(phase0, 'Path', return_value=target), self.assertRaises(ValueError):
                phase0.ensure_policy()

    def test_wrong_user_root_and_unprivileged_handoff_status(self):
        for uid in (0, 1001):
            with patch.object(phase0.os, 'getuid', return_value=uid), patch.object(phase0, 'ensure_policy') as policy, \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(phase0.main(['--profile','framework','--from','repositories']), 1)
                policy.assert_not_called()
        with patch.object(phase0.os, 'getuid', return_value=1000), patch.object(phase0.os, 'geteuid', return_value=1000), \
                patch.object(phase0.os, 'getgid', return_value=1000), patch.object(sys.stdin, 'isatty', return_value=True), \
                patch.object(phase0, 'trusted_path'), patch.object(phase0, 'installer_preflight') as check, \
                patch.object(phase0, 'ensure_policy', return_value=0), patch.object(phase0.subprocess, 'run', return_value=subprocess.CompletedProcess([],3)) as run, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(phase0.main(['--profile','framework','--from','services']), 3)
            check.assert_called_once_with('framework')
            self.assertEqual(run.call_args.args[0], ['/usr/bin/python3','-I',str(REPO/'install'),'--profile','framework','--from','services'])
            self.assertEqual(run.call_args.kwargs['cwd'], REPO)


if __name__ == '__main__':
    if os.geteuid() == 0:
        sys.exit('Run tests as an ordinary user.')
    unittest.main()
