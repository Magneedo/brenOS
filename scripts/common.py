"""Small shared manifest/path helpers; Python standard library only."""
from pathlib import Path
import configparser
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
        if part.is_symlink():
            raise ValueError(f'Refusing symlink destination/parent: {part}')
    return target

def equivalent(source, target, relative):
    if not target.is_file():
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
    return source.read_bytes() == target.read_bytes()

def run(*args):
    return subprocess.run(args, check=True)

def output(*args):
    return subprocess.check_output(args, text=True).strip()
