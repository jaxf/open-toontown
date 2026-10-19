"""Add missing custom CMake targets to the pinned engine's disposable checkout.

This first gate compiles native C++ and the ES2 renderer for iPhone. Navigation
depends on Python and is intentionally not counted as compiled by this gate.
The desktop makepanda build is unchanged.
"""
import argparse
from pathlib import Path
import subprocess

PIN = '06615744481946654610833679a0893589114504'


def replace_once(root, name, old, new):
    path = root / name
    text = path.read_text()
    if new in text:
        return
    if text.count(old) != 1:
        raise ValueError('Unexpected engine source: ' + name)
    path.write_text(text.replace(old, new, 1))


def prepare(root):
    root = Path(root).resolve()
    revision = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != PIN:
        raise ValueError('Only the audited engine revision may be patched')
    # Upstream's set() stores its help text as a truthy value, ignoring OFF.
    # Make this a real boolean option so the C++-only gate needs no bindings.
    replace_once(root, 'dtool/Config.cmake',
                 'set(INTERROGATE_C_INTERFACE\n', 'option(INTERROGATE_C_INTERFACE\n')
    # ES renderers share these headers even when desktop OpenGL is disabled.
    replace_once(root, 'panda/src/glstuff/CMakeLists.txt',
                 'if(NOT HAVE_GL)\n',
                 'if(NOT HAVE_GL AND NOT HAVE_GLES1 AND NOT HAVE_GLES2)\n')
    # Apple is not synonymous with macOS. iOS has neither AppKit nor the
    # public desktop IOKit HID API. Keep the original paths for macOS.
    replace_once(root, 'panda/src/device/CMakeLists.txt',
                 'elseif(APPLE)', 'elseif(CMAKE_SYSTEM_NAME STREQUAL "Darwin")')
    for name in ('ioKitInputDevice.h', 'ioKitInputDevice.cxx',
                 'ioKitInputDeviceManager.h', 'ioKitInputDeviceManager.cxx'):
        replace_once(root, 'panda/src/device/' + name,
                     '#if defined(__APPLE__) && !defined(CPPPARSER)',
                     '#if defined(__APPLE__) && !defined(BUILD_IPHONE) && !defined(CPPPARSER)')
    replace_once(root, 'panda/src/device/inputDeviceManager.cxx',
                 '#elif defined(__APPLE__)',
                 '#elif defined(__APPLE__) && !defined(BUILD_IPHONE)')
    replace_once(root, 'dtool/src/dtoolutil/CMakeLists.txt',
                 '  find_library(APPKIT_LIBRARY AppKit)\n'
                 '  target_link_libraries(p3dtoolutil ${FOUNDATION_LIBRARY} ${APPKIT_LIBRARY})',
                 '  target_link_libraries(p3dtoolutil ${FOUNDATION_LIBRARY})\n'
                 '  if(CMAKE_SYSTEM_NAME STREQUAL "Darwin")\n'
                 '    find_library(APPKIT_LIBRARY AppKit)\n'
                 '    target_link_libraries(p3dtoolutil ${APPKIT_LIBRARY})\n'
                 '  endif()')
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
