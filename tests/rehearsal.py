#!/usr/bin/env python3
"""Exercise deployment failure/retry behavior using temporary roots only."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO/'scripts'))
from common import equivalent, literal_assignments, policy_integrity_ok, service_running

class Rehearsal(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='bootstrap-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'root'

    def files(self, *args, success=True):
        result = subprocess.run([str(REPO/'scripts/files'), '--profile', 'framework',
                                 '--scope', 'all', '--root', str(self.root), *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def test_preview_is_read_only_and_apply_is_idempotent(self):
        self.files()
        self.assertFalse(self.root.exists())
        self.files('--apply')
        self.assertIn('Applied 0 changes.', self.files('--apply').stdout)
        result = subprocess.run([str(REPO/'scripts/verify'), '--profile', 'framework',
                                 '--root', str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_prepared_sources_include_reviewed_patches(self):
        env = dict(os.environ, GIT_CEILING_DIRECTORIES=str(REPO/'.work'))
        for patch in (REPO/'patches').glob('*.patch'):
            prepared = REPO/'.work/sources'/patch.stem
            result = subprocess.run(['git', 'apply', '--reverse', '--check', str(patch)],
                                    cwd=prepared, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, patch.name + ': ' + result.stderr)

    def test_conflict_preflight_and_backup(self):
        self.files('--apply')
        first = self.root/'home/bren/.bash_profile'
        changed = self.root/'home/bren/.bashrc'
        first.unlink()
        changed.write_text('preserve this local edit\n')
        self.files('--apply', success=False)
        self.assertFalse(first.exists(), 'Conflicts must be found before any file writes')
        self.assertEqual(changed.read_text(), 'preserve this local edit\n')
        self.files('--replace', '--apply')
        backups = list((self.root/'var/lib/artix-bootstrap/backups').glob('*/home/bren/.bashrc'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), 'preserve this local edit\n')
        self.assertNotEqual(changed.read_text(), backups[0].read_text())

    def test_symlink_parent_cannot_escape_root(self):
        outside = Path(self.tmp.name)/'outside'
        outside.mkdir()
        (self.root/'home/bren').mkdir(parents=True)
        (self.root/'home/bren/.config').symlink_to(outside, target_is_directory=True)
        self.files('--apply', '--replace', success=False)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.root/'home/bren/.bash_profile').exists())

    def test_boot_render_validates_inputs(self):
        out = Path(self.tmp.name)/'boot'
        args = [str(REPO/'scripts/boot-plan'), '--root-uuid', '11111111-1111-1111-1111-111111111111',
                '--swap-uuid', '22222222-2222-2222-2222-222222222222', '--esp-uuid', 'ABCD-1234',
                '--output', str(out)]
        result = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('subvol=/@snapshots', (out/'fstab').read_text())
        self.assertIn(r'initrd=\intel-ucode.img initrd=\booster-linux.img', (out/'cmdline').read_text())
        self.assertNotIn('resume_offset', (out/'cmdline').read_text())
        args[2] = 'unsafe;value'
        result = subprocess.run(args, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)

    def test_mutating_stages_default_to_preview(self):
        for script in ('packages', 'aur', 'services', 'permissions', 'initramfs'):
            with self.subTest(script=script):
                result = subprocess.run([str(REPO/'scripts'/script)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(result.stdout.strip())

    def test_directory_override_does_not_hide_changed_policy(self):
        observed = 'warning: polkit: /etc/polkit-1/rules.d (GID mismatch)\n'
        self.assertTrue(policy_integrity_ok('polkit', {'status': 1, 'stderr': observed}))
        changed_rule = 'warning: polkit: /etc/polkit-1/rules.d/99-artix.rules (SHA256 checksum mismatch)\n'
        self.assertFalse(policy_integrity_ok('polkit', {'status': 1, 'stderr': observed + changed_rule}))
        self.assertFalse(policy_integrity_ok('polkit', {'status': 1, 'stderr': changed_rule}))
        self.assertFalse(policy_integrity_ok('openssh', {'status': 1, 'stderr': observed}))
        self.assertFalse(policy_integrity_ok('polkit', {'status': 2, 'stderr': observed}))

    def test_only_literal_shell_representation_is_normalized(self):
        source, target = Path(self.tmp.name)/'source', Path(self.tmp.name)/'target'
        relative = 'etc/runit/sv/wpa_supplicant/conf'
        source.write_text("CONF_FILE=/etc/wpa_supplicant/home.conf\nWPA_INTERFACE=wlan0\nOPTS='-s'\n")
        target.write_text('CONF_FILE="/etc/wpa_supplicant/home.conf"\nWPA_INTERFACE=wlan0\nOPTS=-s\n')
        self.assertTrue(equivalent(source, target, relative))
        for text in ('OPTS=-dd\n', 'OPTS=$HOME\n', "OPTS='$(id)'\n", 'OPTS=-s; id\n', 'OPTS=-s\nexit 0\n'):
            target.write_text(text)
            self.assertFalse(equivalent(source, target, relative), text)
        self.assertIsNone(literal_assignments('OPTS="$HOME"\n'))

    def test_dhcpcd_trailing_blank_lines_only(self):
        source, target = Path(self.tmp.name)/'source', Path(self.tmp.name)/'target'
        relative = 'etc/runit/sv/dhcpcd/run'
        source.write_text('#!/bin/sh\nexec 2>&1\nexec dhcpcd -B -q -w\n')
        target.write_text(source.read_text() + '\n')
        self.assertTrue(equivalent(source, target, relative))
        self.assertFalse(equivalent(source, target, 'another/script'))
        target.write_text(source.read_text().replace('-w', '-b'))
        self.assertFalse(equivalent(source, target, relative))

    def test_inaccessible_files_are_not_mismatches(self):
        self.files('--apply')
        protected = self.root/'etc/doas.conf'
        protected.chmod(0)
        self.addCleanup(protected.chmod, 0o600)
        result = subprocess.run([str(REPO/'scripts/verify'), '--profile', 'framework',
                                 '--root', str(self.root), '--json'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('"UNKNOWN"', result.stdout)
        protected.chmod(0o600)
        protected.write_text('different policy\n')
        result = subprocess.run([str(REPO/'scripts/verify'), '--profile', 'framework',
                                 '--root', str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)

    def test_runit_status_distinguishes_down_and_unreadable(self):
        result = lambda status, out, err='': subprocess.CompletedProcess(['sv'], status, out, err)
        self.assertTrue(service_running(result(0, 'run: /service/dbus: (pid 123) 5s\n')))
        self.assertFalse(service_running(result(1, 'down: /service/dbus: 5s, normally up\n')))
        self.assertIsNone(service_running(result(1, 'warning: /service/dbus: unable to open supervise/ok: access denied\n')))
        self.assertIsNone(service_running(result(1, 'run: /service/dbus: (pid 123) 5s\n', 'status read failed')))

if __name__ == '__main__':
    if os.geteuid() == 0:
        raise SystemExit('Run rehearsals as an ordinary user.')
    unittest.main()
