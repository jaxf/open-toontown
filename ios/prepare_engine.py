"""Add missing custom CMake targets to the pinned engine's disposable checkout.

This first gate compiles native C++ and the ES2 renderer for iPhone. Navigation
depends on Python and is intentionally not counted as compiled by this gate.
The desktop makepanda build is unchanged.
"""
import argparse
from pathlib import Path
import subprocess

PIN = '06615744481946654610833679a0893589114504'

# CullResult relies on alpha testing for binary and dual transparency.
# The legacy GLES fallback shader lacks the fixed-function alpha test.
ALPHA_TEST_GLSL = '''uniform vec2 p3d_TTAlphaTest;
bool tt_alpha_pass(float a) {
  float m = p3d_TTAlphaTest.x;
  float r = p3d_TTAlphaTest.y;
  if (m == 1.0) return false;
  if (m == 2.0) return a < r;
  if (m == 3.0) return a == r;
  if (m == 4.0) return a <= r;
  if (m == 5.0) return a > r;
  if (m == 6.0) return a != r;
  if (m == 7.0) return a >= r;
  return true;
}
'''


def replace_once(root, name, old, new):
    path = root / name
    text = path.read_text()
    if new in text:
        return
    if text.count(old) != 1:
        raise ValueError('Unexpected engine source: ' + name)
    path.write_text(text.replace(old, new, 1))


def defer_dna_loader(root):
    # Static iOS linking runs this parser's globals before Panda's config
    # globals. Construct the dedicated loader only when DNA first needs it.
    # Patch both Bison input and the fallback parser, without changing desktop
    # engine sources outside this disposable iOS checkout.
    for name in ('dnaParser.yxx', 'dnaParser.cxx.prebuilt'):
        path = 'panda/src/dna/' + name
        replace_once(root, path, 'static Loader loader;',
                     'static Loader &dna_model_loader() {\n'
                     '  static Loader loader;\n'
                     '  return loader;\n'
                     '}')
        text = (root / path).read_text()
        old = 'loader.load_sync('
        new = 'dna_model_loader().load_sync('
        if old in text:
            if text.count(old) != 3 or new in text:
                raise ValueError('Unexpected DNA model loading sites: ' + name)
            (root / path).write_text(text.replace(old, new))
        elif text.count(new) != 3:
            raise ValueError('Missing DNA model loading sites: ' + name)


def restore_gles_alpha_test(root):
    import json
    shader = 'panda/src/glstuff/glGraphicsStateGuardian_src.cxx'
    declaration = '  "uniform lowp vec4 p3d_TexAlphaOnly;\\n"\n'
    code = ''.join('  ' + json.dumps(line + '\n') + '\n'
                   for line in ALPHA_TEST_GLSL.splitlines())
    replace_once(root, shader, declaration, declaration + code)
    ending = '  "  gl_FragColor *= color;\\n"\n'
    replace_once(root, shader, ending, ending +
                 '  "  if (!tt_alpha_pass(gl_FragColor.a)) discard;\\n"\n')
    header = 'panda/src/glstuff/glShaderContext_src.h'
    replace_once(root, header, '  GLuint _glsl_program;\n',
                 '  GLuint _glsl_program;\n  GLint _tt_alpha_test_index = -1;\n')
    context = 'panda/src/glstuff/glShaderContext_src.cxx'
    replace_once(root, context, '#include "colorAttrib.h"',
                 '#include "alphaTestAttrib.h"\n#include "colorAttrib.h"')
    location = '  GLint p = _glgsg->_glGetUniformLocation(_glsl_program, name_buffer);\n'
    replace_once(root, context, location, location + '''
  if (strcmp(name_buffer, "p3d_TTAlphaTest") == 0) {
    _tt_alpha_test_index = p;
    return;
  }
''')
    # Alpha-only changes are absent from the legacy parameter dependency mask.
    start = '  // Find out which state properties have changed.\n'
    replace_once(root, context, start, '''  if (_tt_alpha_test_index >= 0) {
    const AlphaTestAttrib *alpha;
    target_rs->get_attrib_def(alpha);
    const GLfloat test[2] = {(GLfloat)alpha->get_mode(),
                             (GLfloat)alpha->get_reference_alpha()};
    _glgsg->_glUniform2fv(_tt_alpha_test_index, 1, test);
  }

''' + start)


def prepare(root):
    root = Path(root).resolve()
    revision = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != PIN:
        raise ValueError('Only the audited engine revision may be patched')
    defer_dna_loader(root)
    restore_gles_alpha_test(root)
    # Upstream's set() stores its help text as a truthy value, ignoring OFF.
    # Make this a real boolean option so the C++-only gate needs no bindings.
    replace_once(root, 'dtool/Config.cmake',
                 'set(INTERROGATE_C_INTERFACE\n', 'option(INTERROGATE_C_INTERFACE\n')
    # ES renderers share these headers even when desktop OpenGL is disabled.
    replace_once(root, 'panda/src/glstuff/CMakeLists.txt',
                 'if(NOT HAVE_GL)\n',
                 'if(NOT HAVE_GL AND NOT HAVE_GLES1 AND NOT HAVE_GLES2)\n')
    # aux-display is a list: an empty platform declaration does not erase the
    # desktop entries. The embedded app registers its pipe statically, so give
    # it an explicit mode that never dlopens those desktop renderer libraries.
    replace_once(root, 'panda/src/display/graphicsPipeSelection.cxx',
                 '  _default_module_loaded = false;\n',
                 '  _default_module_loaded = false;\n'
                 '#ifdef BUILD_IPHONE\n'
                 '  if (_default_display_module == "static") {\n'
                 '    _default_display_module.clear();\n'
                 '    _display_modules.clear();\n'
                 '    _default_module_loaded = true;\n'
                 '  }\n'
                 '#endif\n')
    # iOS exposes the same BSD socket API without enabling desktop Mac APIs.
    replace_once(root, 'panda/src/nativenet/socket_portable.h',
                 '#elif defined(IS_LINUX) || defined(IS_OSX) || defined(IS_FREEBSD) || defined(__EMSCRIPTEN__)',
                 '#elif defined(IS_LINUX) || defined(IS_OSX) || defined(BUILD_IPHONE) || defined(IS_FREEBSD) || defined(__EMSCRIPTEN__)')
    # This platform include precedes Panda's generated configuration header.
    replace_once(root, 'direct/src/showbase/showBase.cxx',
                 '#ifdef __APPLE__\n// We have to include this',
                 '#ifdef __APPLE__\n#include <TargetConditionals.h>\n#endif\n'
                 '#if defined(__APPLE__) && TARGET_OS_OSX\n// We have to include this')
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
    # The external binding generator runs on the build Mac, never the phone.
    replace_once(root, 'dtool/Config.cmake',
                 '      -DHAVE_PYTHON=OFF\n',
                 '      -DHAVE_PYTHON=OFF\n      -DCMAKE_POLICY_VERSION_MINIMUM=3.5\n')
    # Cross builds must never use macOS Python headers/libraries. Keep the host
    # executable separate; static modules link the device framework explicitly.
    replace_once(root, 'dtool/Package.cmake',
                 'find_package(Python ${WANT_PYTHON_VERSION} QUIET COMPONENTS Interpreter Development)',
                 'if(TT_IOS_PYTHON_FRAMEWORK)\n'
                 '  include("${PROJECT_SOURCE_DIR}/toontown-python.cmake")\n'
                 'else()\n'
                 '  find_package(Python ${WANT_PYTHON_VERSION} QUIET COMPONENTS Interpreter Development)\n'
                 'endif()')
    (root / 'toontown-python.cmake').write_text(
        Path(__file__).with_name('device-python.cmake').read_text())
    native = Path(__file__).with_name('native')
    for name in ('TTBuiltinModules.h', 'TTBuiltinModules.cxx', 'TTLinkCheck.cxx',
                 'TTPandaInputView.h', 'TTPandaInputView.mm', 'TTGraphicsHost.h',
                 'TTGLESView.h', 'TTGLESView.mm', 'TTGraphicsPipe.mm', 'TTGraphicsLinkCheck.mm',
                 'TTEmbeddedRuntime.h', 'TTEmbeddedRuntime.mm', 'TTGameViewController.h',
                 'TTGameViewController.mm', 'TTApplication.mm', 'TTControlsView.h',
                 'TTControlsView.mm', 'TTGameInputBridge.h', 'TTGameInputBridge.mm',
                 'Device.prc', 'Info.plist.in'):
        (root / name).write_text((native / name).read_text())
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
