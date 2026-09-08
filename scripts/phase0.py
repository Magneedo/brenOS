#!/usr/bin/env python3
"""Finish privilege setup, then hand off to the existing unprivileged installer."""
import argparse
import grp
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parent.parent

# Only this fixed stdlib program runs elevated, with policy text as data. It
# never imports code from the checkout or reads a user-writable temporary file.
CREATE_POLICY = '''import os, pathlib, subprocess, sys, tempfile
target = pathlib.Path('/etc/doas.conf')
if os.geteuid() != 0 or target.exists() or target.is_symlink():
    sys.exit('Refusing to replace existing doas policy; inspect it manually.')
with tempfile.TemporaryDirectory(prefix='.artix-phase0-', dir='/etc') as directory:
    candidate = pathlib.Path(directory) / 'doas.conf'
    candidate.write_text(sys.argv[1])
    candidate.chmod(0o600)
    subprocess.run(['/usr/bin/doas', '-C', str(candidate)], check=True)
    os.link(candidate, target)  # Atomic creation; cannot overwrite even a dangling symlink.
print('Installed the reviewed final doas policy, root-owned mode 0600.')
'''


def trusted_path(path):
    for item in (path, *path.parents):
        info = item.lstat()
        if item.is_symlink() or info.st_uid not in (0, 1000) or info.st_mode & 0o022:
            raise ValueError(f'Unsafe checkout input or parent: {item}')


def pinned_policy():
    manifest = REPO / 'manifests/repositories.tsv'
    trusted_path(manifest)
    rows = [line.split('\t') for line in manifest.read_text().splitlines()
            if line.startswith('dotfiles\t')]
    if (len(rows) != 1 or len(rows[0]) != 3
            or rows[0][1] != 'https://github.com/Magneedo/dotfiles.git'
            or not re.fullmatch('[0-9a-f]{40}', rows[0][2])):
        raise ValueError('Expected one exact dotfiles commit pin and its reviewed HTTPS origin.')
    _, url, revision = rows[0]
    patch = REPO / 'patches/dotfiles.patch'
    if patch.exists() and '+++ b/etc/doas.conf' in patch.read_text():
        raise ValueError('A local patch changes doas policy; review that policy manually before phase 0.')
    print(f'Reading final doas policy from dotfiles at {revision}; no floating branch.', flush=True)
    with tempfile.TemporaryDirectory(prefix='artix-policy-') as directory:
        # Read one Git blob as data, never run a source script or copy a whole tree.
        subprocess.run(['/usr/bin/git', 'init', '--bare', '-q', directory], check=True)
        subprocess.run(['/usr/bin/git', '-C', directory, '-c', 'core.hooksPath=/dev/null',
                        'fetch', '-q', '--depth=1', url, revision], check=True)
        policy = subprocess.check_output(['/usr/bin/git', '-C', directory, 'show',
                                          revision + ':etc/doas.conf'], text=True)
    if not policy.strip() or len(policy) > 16384 or '\0' in policy:
        raise ValueError('Invalid pinned policy text.')
    return policy


def ensure_policy():
    target = Path('/etc/doas.conf')
    if target.exists() or target.is_symlink():
        info = target.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
            raise ValueError('Existing doas policy must be a root-owned, non-writable regular file; repair it manually.')
        print('Keeping existing doas policy. The normal configuration stage reviews/restores final policy.')
    else:
        if grp.getgrnam('wheel').gr_gid not in os.getgroups():
            raise ValueError('Log in again after adding bren to wheel; no groups are changed here.')
        policy = pinned_policy()
        print('\nFinal pinned doas policy (not a temporary bootstrap rule):\n' + policy)
        print('This grants the intended wheel administration and the listed power commands.')
        if input('Type policy to install it using the root password, or Enter to stop: ').strip() != 'policy':
            return 3
        command = shlex.join(['/usr/bin/python3', '-I', '-c', CREATE_POLICY, policy])
        print('Root access required now to validate and create /etc/doas.conf; enter the root password at su.', flush=True)
        subprocess.run(['/usr/bin/su', '--login', '--shell', '/bin/bash', '--command',
                        'cd / && exec ' + command, 'root'], check=True)
    print('Checking doas access interactively; enter bren\'s password if requested.', flush=True)
    subprocess.run(['/usr/bin/doas', '/usr/bin/true'], check=True)
    return 0


def installer_preflight(profile):
    # Prerequisites now exist: reuse the main installer's safeguards, including
    # its exact account/home and findmnt checks, before creating any policy.
    loader = importlib.machinery.SourceFileLoader('artix_installer', str(REPO / 'install'))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    module.Installer(profile).preflight()


def main(argv=None):
    parser = argparse.ArgumentParser(description='Internal phase-0 handoff; start with ./bootstrap.')
    parser.add_argument('--profile', choices=('framework', 'portable'), required=True)
    parser.add_argument('--from', dest='stage', required=True,
                        choices=('repositories', 'packages', 'aur', 'desktop', 'configuration', 'services', 'boot', 'verify'))
    args = parser.parse_args(argv)
    try:
        if os.getuid() != 1000 or os.geteuid() != 1000 or os.getgid() != 1000:
            raise ValueError('Use ./bootstrap as bren, never as root.')
        if not sys.stdin.isatty():
            raise ValueError('Use ./bootstrap from a local interactive console.')
        if not REPO.is_relative_to('/home/bren'):
            raise ValueError('Keep the trusted checkout under /home/bren.')
        for path in (REPO / 'bootstrap', Path(__file__).absolute(), REPO / 'install'):
            trusted_path(path)
        installer_preflight(args.profile)
        status = ensure_policy()
        if status:
            print(f'Paused. Resume: ./bootstrap --profile {args.profile} --from {args.stage}')
            return status
        print('Phase 0 complete. Continuing the existing installer as bren.', flush=True)
        # Absolute interpreter/path and isolated Python avoid CWD/PYTHONPATH imports.
        return subprocess.run(['/usr/bin/python3', '-I', str(REPO / 'install'),
                               '--profile', args.profile, '--from', args.stage], cwd=REPO).returncode
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(f'Phase 0 stopped: {error}\nResolve the error, then rerun ./bootstrap '
              f'--profile {args.profile} --from {args.stage}', file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print(f'Paused. Resume: ./bootstrap --profile {args.profile} --from {args.stage}', file=sys.stderr)
        return 3


if __name__ == '__main__':
    sys.exit(main())
