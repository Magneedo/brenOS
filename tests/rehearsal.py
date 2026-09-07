#!/usr/bin/env python3
"""Exercise deployment failure/retry behavior using temporary roots only."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parent.parent

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

if __name__ == '__main__':
    if os.geteuid() == 0:
        raise SystemExit('Run rehearsals as an ordinary user.')
    unittest.main()
