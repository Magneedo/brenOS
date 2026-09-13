"""Small shared manifest/path helpers; Python standard library only."""
from pathlib import Path
import configparser
import re
import stat
import subprocess

REPO = Path(__file__).resolve().parent.parent

def lines(name):
    return [line for line in (REPO / 'manifests' / name).read_text().splitlines()
            if line.strip() and not line.startswith('#')]

def selected(kind, profile):
    names = lines(f'{kind}-portable.txt')
    if profile == 'framework':
        names += lines(f'{kind}-framework.txt')
    return sorted(set(names))

def file_rows(profile):
    for line in lines('files.tsv'):
        row = line.split('\t')
        if len(row) != 5:
            raise ValueError(f'Invalid files.tsv row: {line}')
        if row[0] == 'portable' or profile == 'framework':
            yield row

def source_path(source, relative):
    base = (REPO if source == 'bootstrap' else REPO / '.work/desktop-stage'
            if source == 'desktop' else REPO / '.work/sources' / source)
    p = base / relative
    if not p.resolve().is_relative_to(base.resolve()) or not p.is_file():
        raise ValueError(f'Missing/unsafe source {p}; run scripts/sources first')
    return p

def target_path(root, relative):
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts or not p.parts:
        raise ValueError(f'Unsafe destination: {relative}')
    target = root / p
    for part in (target, *target.parents):
        if part == root:
            break
        try:
            mode = part.lstat().st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise ValueError(f'Refusing symlink destination/parent: {part}')
    return target

def equivalent(source, target, relative):
    try:
        mode = target.stat().st_mode
    except FileNotFoundError:
        return False
    if not stat.S_ISREG(mode):
        return False
    if relative.endswith('/obs-studio/basic/profiles/Untitled/basic.ini'):
        # Only intentional recording keys are managed; OBS owns other state.
        wanted, actual = configparser.ConfigParser(), configparser.ConfigParser()
        wanted.read(source); actual.read(target)
        return all(actual.has_option(s, k) and actual.get(s, k) == v
                   for s in wanted.sections() for k, v in wanted.items(s))
    if relative == 'etc/locale.gen':
        active = lambda p: [l.split() for l in p.read_text().splitlines()
                            if l.strip() and not l.lstrip().startswith('#')]
        return active(source) == active(target)
    if relative == 'etc/runit/sv/wpa_supplicant/conf':
        wanted = literal_assignments(source.read_text())
        if wanted is not None:
            return wanted == literal_assignments(target.read_text())
    if relative == 'etc/runit/sv/dhcpcd/run':
        return source.read_bytes().rstrip(b'\n') == target.read_bytes().rstrip(b'\n')
    return source.read_bytes() == target.read_bytes()

def literal_assignments(text):
    # Only literal assignments are normalized. Never execute shell configuration
    # or equate quoted expansions with executable shell syntax.
    result = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        match = re.fullmatch(r'''([A-Z_][A-Z0-9_]*)=(?:([-\w./:=]+)|'([-\w./:= ]*)'|"([-\w./:= ]*)")''',
                             line.strip(), re.ASCII)
        if match is None:
            return None
        result.append((match[1], next(v for v in match.groups()[1:] if v is not None)))
    return result

def service_running(result):
    if result.returncode in (0, 1) and not result.stderr.strip():
        if result.stdout.startswith('run:'):
            return True
        if result.stdout.startswith('down:'):
            return False
    return None

def run(*args):
    return subprocess.run(args, check=True)

def output(*args):
    return subprocess.check_output(args, text=True).strip()

def policy_integrity_ok(name, result):
    # The one captured package-metadata difference is also checked against
    # directories.tsv. Any additional warning or content change remains a failure.
    return result.get('status') == 0 or (
        name == 'polkit' and result.get('status') == 1
        and result.get('stderr', '').splitlines() ==
        ['warning: polkit: /etc/polkit-1/rules.d (GID mismatch)'])
