"""Stage full-game content, NOT an IPA. Requires the complete resources checkout.

Copies only explicit game roots, never databases, logs, invitation tokens,
virtualenvs, repository internals or developer configuration. Includes all
client gameplay Python and native art, not just a Ministry Plaza demo.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

PHASES = ('3', '3.5', '4', '5', '5.5', '6', '7', '8', '9', '10', '11', '12', '13')


def game_files(root):
    root = Path(root).resolve()
    for folder in ('otp', 'toontown', 'assets', 'resources', 'etc'):
        if not (root / folder).is_dir() or (root / folder).is_symlink():
            raise ValueError('Missing or symlinked content root: ' + folder)
    for phase in PHASES:
        directory = root / 'resources' / ('phase_' + phase)
        if not directory.is_dir() or not any(p.is_file() for p in directory.rglob('*')):
            raise ValueError('Missing/empty resource phase ' + phase)
    files = [root / 'etc' / name for name in ('Configrc.prc', 'otp.dc', 'toon.dc')]
    for folder in ('otp', 'toontown', 'assets', 'resources'):
        for path in sorted((root / folder).rglob('*')):
            relative = path.relative_to(root)
            if any(part.startswith('.') or part == '__pycache__' for part in relative.parts):
                continue
            if path.is_symlink():
                raise ValueError('Bundle content must not contain symlinks: ' + str(relative))
            if not path.is_file():
                continue
            if folder in ('otp', 'toontown') and path.suffix != '.py':
                continue
            files.append(path)
    if any(not p.is_file() or p.is_symlink() for p in files):
        raise ValueError('Missing or symlinked game configuration')
    return files


def stage(root, destination):
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if root == destination or root in destination.parents:
        raise ValueError('Stage content outside the source tree')
    files = game_files(root)
    manifest = {'format': 1, 'kind': 'full-game-content-not-ipa', 'files': {}}
    # Exclusive mode: never overwrite an existing archive.
    with zipfile.ZipFile(destination, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            name = path.relative_to(root).as_posix()
            digest = hashlib.sha256()
            with path.open('rb') as source, archive.open('game/' + name, 'w', force_zip64=True) as target:
                for chunk in iter(lambda: source.read(1024 * 1024), b''):
                    target.write(chunk)
                    digest.update(chunk)
            manifest['files'][name] = digest.hexdigest()
        archive.writestr('content-manifest.json', json.dumps(manifest, indent=2))
    return len(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    count = stage(args.root, args.output)
    print('Staged %s game files. This archive is not installable and contains no iOS engine.' % count)


if __name__ == '__main__':
    main()
