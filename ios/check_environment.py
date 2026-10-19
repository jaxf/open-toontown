"""Read-only iOS toolchain/dependency audit. Does NOT claim a successful port."""
import argparse
import ast
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def native_imports(root):
    modules = {}
    for directory in ('otp', 'toontown'):
        for source in (root / directory).rglob('*.py'):
            tree = ast.parse(source.read_text(encoding='utf-8-sig'), filename=str(source))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and (node.module or '').startswith('panda3d.'):
                    modules.setdefault(node.module, set()).update(a.name for a in node.names)
    return {name: sorted(symbols) for name, symbols in sorted(modules.items())}


def audit(root=ROOT):
    checks = {'macOS': sys.platform == 'darwin',
              'xcodebuild': bool(shutil.which('xcodebuild')),
              'iphoneos_sdk': False,
              'resources_present': (root / 'resources/phase_3').is_dir()}
    if checks['macOS'] and checks['xcodebuild'] and shutil.which('xcrun'):
        result = subprocess.run(['xcrun', '--sdk', 'iphoneos', '--show-sdk-path'],
                                capture_output=True, text=True, timeout=30)
        checks['iphoneos_sdk'] = result.returncode == 0 and Path(result.stdout.strip()).is_dir()
    return {'checks': checks, 'native_imports': native_imports(root), 'ipa_ready': False,
            'unresolved': ['iOS arm64 Python and Panda3D/OTP/Toontown build',
                           'modern iOS renderer and audio backend',
                           'UIKit touch/pointer/keyboard and lifecycle integration',
                           'device signing, packaging and full-game device tests']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    report = audit()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for name, ok in report['checks'].items():
            print(('%-8s' % ('PRESENT' if ok else 'MISSING')) + name)
        print('Native Python modules: ' + ', '.join(report['native_imports']))
        print('NOT IPA-READY: ' + '; '.join(report['unresolved']))
    return 1  # Deliberately cannot be mistaken for a passing native build.


if __name__ == '__main__':
    sys.exit(main())
