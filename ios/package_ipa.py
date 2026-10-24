"""Assemble a complete device payload, then make an IPA for AltStore re-signing.

Runs on the build Mac, using the exact device framework/engine just compiled.
Never executes iOS binaries on the host and never claims a device startup test.
"""
import argparse
import hashlib
import json
import plistlib
import re
import shutil
import subprocess
import sys
from pathlib import Path
import zipfile

from ios.stage_game import game_files

PYTHON_VERSION = '3.13'
BUNDLE_ID = 'com.jaxf.opentoontown'


def run(*args):
    return subprocess.check_output([str(a) for a in args], text=True)


def copy_file(source, target):
    if not source.is_file() or source.is_symlink():
        raise ValueError('Missing or symlinked input: ' + str(source))
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_python(source, target):
    for path in sorted(source.rglob('*')):
        if path.is_file() and path.suffix == '.py' and '__pycache__' not in path.parts:
            copy_file(path, target / path.relative_to(source))
    target.mkdir(parents=True, exist_ok=True)
    (target / '__init__.py').touch(exist_ok=True)


def framework_metadata(name):
    return {
        'CFBundleExecutable': name, 'CFBundleName': name,
        'CFBundleIdentifier': BUNDLE_ID + '.' + name.replace('_', '-'),
        'CFBundlePackageType': 'FMWK', 'CFBundleVersion': '1',
        'CFBundleShortVersionString': '0.1', 'MinimumOSVersion': '15.0',
        'CFBundleSupportedPlatforms': ['iPhoneOS'],
    }


def relocate_extension(app, extension, import_root):
    """CPython AppleFrameworkLoader contract: .fwork and reverse .origin."""
    relative = extension.relative_to(import_root)
    module = '.'.join((*relative.parts[:-1], relative.name.split('.')[0]))
    name = 'py.' + module
    framework = app / 'Frameworks' / (name + '.framework')
    framework.mkdir()  # Duplicate/colliding module names are errors.
    binary = framework / name
    extension.rename(binary)
    with (framework / 'Info.plist').open('wb') as output:
        plistlib.dump(framework_metadata(name), output)
    marker = extension.with_suffix('.fwork')
    marker.write_text(binary.relative_to(app).as_posix() + '\n')
    (framework / (name + '.origin')).write_text(marker.relative_to(app).as_posix() + '\n')
    return binary


def check_device(binary):
    run('xcrun', 'lipo', binary, '-verify_arch', 'arm64')
    output = run('xcrun', 'vtool', '-show-build', binary)
    if not re.search(r'platform\s+IOS\s*$', output, re.M):
        raise ValueError('Not an iPhoneOS binary: ' + str(binary))


def relocate_binary(app, binary, framework=False):
    check_device(binary)
    # Only the embedded Python framework may come from the build directory.
    # Reject accidental host libraries rather than shipping an unlaunchable app.
    for line in run('xcrun', 'otool', '-L', binary).splitlines()[1:]:
        dependency = line.strip().split(' (compatibility version', 1)[0]
        if binary.name != 'OpenToontown' and dependency == str(binary):
            continue
        if 'Python.framework/' in dependency:
            run('xcrun', 'install_name_tool', '-change', dependency,
                '@rpath/Python.framework/Python', binary)
        elif dependency.startswith(('/System/Library/', '/usr/lib/')):
            continue
        elif dependency.startswith('@rpath/'):
            if not (app / 'Frameworks' / dependency[len('@rpath/'):]).is_file():
                # A dylib's old install ID will be replaced below.
                if not framework or dependency.split('/')[-1] != binary.name:
                    raise ValueError('Unbundled dependency: ' + dependency)
        elif framework and line == run('xcrun', 'otool', '-L', binary).splitlines()[1]:
            continue  # First entry is the library's own old install ID.
        else:
            raise ValueError('Unexpected native dependency: ' + dependency)
    commands = run('xcrun', 'otool', '-l', binary)
    for path in re.findall(r'cmd LC_RPATH\s+cmdsize \d+\s+path (.*?) \(offset', commands):
        run('xcrun', 'install_name_tool', '-delete_rpath', path, binary)
    if framework:
        run('xcrun', 'install_name_tool', '-id',
            '@rpath/' + binary.relative_to(app / 'Frameworks').as_posix(), binary)
    else:
        run('xcrun', 'install_name_tool', '-add_rpath', '@executable_path/Frameworks', binary)


def audit_payload(app):
    required = [
        'OpenToontown', 'Info.plist', 'Device.prc', 'Frameworks/Python.framework/Python',
        'python/lib/python3.13/encodings/__init__.py',
        'python/site-packages/direct/showbase/ShowBase.py',
        'python/site-packages/panda3d/__init__.py',
        'python/site-packages/pytz/__init__.py', 'python/site-packages/certifi/cacert.pem',
        'Game/etc/toon.dc', 'Game/etc/otp.dc', 'Game/toontown/toonbase/ToontownStart.py',
        'Game/resources/phase_3/models/gui/loading-background.bam',
        'Game/resources/phase_3/models/gui/progress-background.bam',
        'Game/resources/phase_3/models/gui/toon_council.bam',
    ]
    for name in required:
        if not (app / name).is_file():
            raise ValueError('Incomplete app: ' + name)
    dynamic = app / 'python/lib/python3.13/lib-dynload'
    for module in ('_ssl', '_hashlib', '_socket', 'select', 'math', '_struct', 'zlib'):
        if len(list(dynamic.glob(module + '.*.fwork'))) != 1:
            raise ValueError('Missing packaged Python extension: ' + module)
    for marker in app.rglob('*.fwork'):
        binary = app / marker.read_text().strip()
        if not binary.is_file() or app not in binary.resolve().parents:
            raise ValueError('Invalid framework marker: ' + str(marker))
        origin = binary.with_name(binary.name + '.origin')
        if origin.read_text().strip() != marker.relative_to(app).as_posix():
            raise ValueError('Invalid framework reverse marker')
    for path in app.rglob('*'):
        if path.is_symlink():
            raise ValueError('Unexpected bundle symlink: ' + str(path))
        if path.suffix in ('.so', '.a', '.dylib'):
            raise ValueError('Unprocessed native payload: ' + str(path))
        if path.suffix == '.py':
            compile(path.read_bytes(), str(path.relative_to(app)), 'exec')


def assemble(root, work, packages, destination):
    if sys.platform != 'darwin':
        raise RuntimeError('IPA assembly requires the macOS device build tools')
    destination.mkdir(parents=True, exist_ok=False)
    app = destination / 'Payload/OpenToontown.app'
    app.mkdir(parents=True)
    built = work / 'panda-bindings/bin/OpenToontown.app'
    for name in ('OpenToontown', 'Info.plist', 'Device.prc'):
        copy_file(built / name, app / name)
    with (app / 'Info.plist').open('rb') as source:
        info = plistlib.load(source)
    # Keep the explicit app build number. Shallow CI checkouts always report
    # a commit count of one, which made distinct IPAs indistinguishable in logs.
    info.update(CFBundleSupportedPlatforms=['iPhoneOS'])
    with (app / 'Info.plist').open('wb') as output:
        plistlib.dump(info, output)
    for source in game_files(root):
        copy_file(source, app / 'Game' / source.relative_to(root))
    stdlib = app / 'python/lib' / ('python' + PYTHON_VERSION)
    source_lib = work / 'python-install/lib' / ('python' + PYTHON_VERSION)
    shutil.copytree(source_lib, stdlib, ignore=shutil.ignore_patterns(
        '__pycache__', '*.pyc', '*.a', 'config-*', 'site-packages'))
    site = app / 'python/site-packages'
    shutil.copytree(packages, site, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'bin'))
    copy_python(work / 'panda/direct/src', site / 'direct')
    (site / 'panda3d').mkdir()
    (site / 'panda3d/__init__.py').write_text('# Native submodules are registered by the iOS host.\n')
    # ShowBase and DirectGUI use these engine-provided fallback models.
    shutil.copytree(work / 'panda/models', app / 'Game/engine-models',
                    ignore=shutil.ignore_patterns('CMakeLists.txt'))
    framework = app / 'Frameworks/Python.framework'
    framework.mkdir(parents=True)
    python_binary = framework / 'Python'
    copy_file(work / 'python-install/Python.framework/Python', python_binary)
    with (framework / 'Info.plist').open('wb') as output:
        plistlib.dump(framework_metadata('Python'), output)
    binaries = [python_binary]
    for extension in sorted(stdlib.rglob('*.so')):
        binaries.append(relocate_extension(app, extension, stdlib / 'lib-dynload'))
    for extension in sorted(site.rglob('*.so')):
        raise ValueError('Only pure-Python third-party wheels are allowed: ' + str(extension))
    licenses = app / 'Licenses'
    shutil.copytree(work / 'dependencies/share/licenses', licenses)
    for name, source in [('Python.txt', work / 'cpython/LICENSE'),
                         ('Panda3D.txt', work / 'panda/LICENSE')]:
        copy_file(source, licenses / name)
    for source in root.glob('LICENSE*'):
        copy_file(source, licenses / source.name)
    for binary in binaries:
        relocate_binary(app, binary, framework=True)
    relocate_binary(app, app / 'OpenToontown')
    audit_payload(app)
    manifest = {'format': 1, 'game_commit': run('git', '-C', root, 'rev-parse', 'HEAD').strip(),
                'resource_commit': run('git', '-C', root / 'resources', 'rev-parse', 'HEAD').strip(),
                'device_gameplay_tested': False, 'files': {}}
    for folder in ('Game', 'python', 'Licenses'):
        for path in sorted((app / folder).rglob('*')):
            if path.is_file():
                with path.open('rb') as stream:
                    manifest['files'][path.relative_to(app).as_posix()] = hashlib.file_digest(stream, 'sha256').hexdigest()
    (app / 'payload-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    # Ad-hoc signatures make nested-code structure verifiable. AltStore must
    # replace these with the user's device provisioning/signatures at install.
    for binary in binaries:
        run('codesign', '--force', '--sign', '-', '--timestamp=none', binary.parent)
    run('codesign', '--force', '--sign', '-', '--timestamp=none', app)
    run('codesign', '--verify', '--deep', '--strict', app)
    ipa = destination / 'OpenToontown.ipa'
    with zipfile.ZipFile(ipa, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(app.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(destination))
    report = {key: value for key, value in manifest.items() if key != 'files'}
    report.update(build_version=info['CFBundleVersion'],
                  file_count=len(manifest['files']), framework_count=len(binaries),
                  ipa_bytes=ipa.stat().st_size, signing='ad-hoc; requires AltStore re-signing')
    (destination / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    print('IPA ASSEMBLED. Device install, startup, login and gameplay remain untested.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'work', 'packages', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    assemble(args.root.resolve(), args.work.resolve(), args.packages.resolve(), args.output.resolve())


if __name__ == '__main__':
    main()
