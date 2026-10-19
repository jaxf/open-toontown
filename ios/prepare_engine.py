"""Add missing custom CMake targets to the pinned engine's disposable checkout.

This first gate compiles native C++ and the ES2 renderer for iPhone. Navigation
depends on Python and is intentionally not counted as compiled by this gate.
The desktop makepanda build is unchanged.
"""
import argparse
from pathlib import Path
import subprocess

PIN = '06615744481946654610833679a0893589114504'


def prepare(root):
    root = Path(root).resolve()
    revision = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != PIN:
        raise ValueError('Only the audited engine revision may be patched')
    overlay = Path(__file__).with_name('native-components.cmake').read_text()
    target = root / 'CMakeLists.txt'
    text = target.read_text()
    marker = '\n# Open Toontown iOS native compilation gate\n'
    if marker not in text:
        target.write_text(text + marker + 'include("${PROJECT_SOURCE_DIR}/toontown-ios.cmake")\n')
    (root / 'toontown-ios.cmake').write_text(overlay)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('engine', type=Path)
    prepare(parser.parse_args().engine)
