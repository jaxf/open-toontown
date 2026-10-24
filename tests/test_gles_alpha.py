"""Render the patched fallback fragment shader using Mesa's ES2 context.

Run on Linux with TT_TEST_ENGINE pointing to a prepared engine checkout.
No iOS simulator is used. Device compilation remains a separate CI gate.
"""
import ast
import ctypes as C
import os
from pathlib import Path
import re
import subprocess
import unittest


@unittest.skipUnless(os.environ.get('TT_TEST_ENGINE'), 'requires prepared engine and Mesa EGL')
class GLESAlphaTests(unittest.TestCase):
    def test_actual_fallback_shader_cutouts_and_state_changes(self):
        egl = C.CDLL('libEGL.so.1')
        def api(lib, name, result, *args):
            f = getattr(lib, name)
            f.restype, f.argtypes = result, args
            return f
        ptr, integer, uint = C.c_void_p, C.c_int, C.c_uint
        getproc = api(egl, 'eglGetProcAddress', ptr, C.c_char_p)
        platform = C.CFUNCTYPE(ptr, uint, ptr, C.POINTER(integer))(
            getproc(b'eglGetPlatformDisplayEXT'))
        display = platform(0x31DD, None, None)  # surfaceless Mesa
        self.assertTrue(api(egl, 'eglInitialize', uint, ptr, ptr, ptr)(display, None, None))
        api(egl, 'eglBindAPI', uint, uint)(0x30A0)
        attrs = (integer * 13)(0x3033, 1, 0x3040, 4, 0x3024, 8, 0x3023, 8,
                               0x3022, 8, 0x3021, 8, 0x3038)
        config, count = ptr(), integer()
        self.assertTrue(api(egl, 'eglChooseConfig', uint, ptr, ptr, ptr, integer, ptr)(
            display, attrs, C.byref(config), 1, C.byref(count)))
        self.assertGreater(count.value, 0)
        context = api(egl, 'eglCreateContext', ptr, ptr, ptr, ptr, ptr)(
            display, config, None, (integer * 3)(0x3098, 2, 0x3038))
        surface = api(egl, 'eglCreatePbufferSurface', ptr, ptr, ptr, ptr)(
            display, config, (integer * 5)(0x3057, 1, 0x3056, 1, 0x3038))
        self.assertTrue(api(egl, 'eglMakeCurrent', uint, ptr, ptr, ptr, ptr)(
            display, surface, surface, context))
        def gl(name, result, *args):
            return C.CFUNCTYPE(result, *args)(getproc(name.encode()))
        def shader(kind, source):
            handle = gl('glCreateShader', uint, uint)(kind)
            string = C.c_char_p(source.encode())
            gl('glShaderSource', None, uint, integer, ptr, ptr)(handle, 1, C.byref(string), None)
            gl('glCompileShader', None, uint)(handle)
            ok = integer()
            gl('glGetShaderiv', None, uint, uint, ptr)(handle, 0x8B81, C.byref(ok))
            log = C.create_string_buffer(8192)
            gl('glGetShaderInfoLog', None, uint, integer, ptr, ptr)(handle, 8192, None, log)
            self.assertTrue(ok.value, log.value.decode())
            return handle
        source = (Path(os.environ['TT_TEST_ENGINE']) /
                  'panda/src/glstuff/glGraphicsStateGuardian_src.cxx').read_text()
        fragment = source.split('static const string default_fshader =', 1)[1].split('\n#endif\n\n', 1)[0]
        processed = subprocess.check_output(['cpp', '-P', '-DOPENGLES'],
                                            input=fragment, text=True)
        fragment = ''.join(ast.literal_eval(s) for s in re.findall(r'"(?:[^"\\]|\\.)*"', processed))
        vertex = '''#version 100
attribute vec2 vertex;
varying lowp vec4 color;
varying highp vec3 texcoord;
uniform float testAlpha;
void main() { gl_Position=vec4(vertex,0.0,1.0);
color=vec4(1.0,0.0,0.0,testAlpha); texcoord=vec3(0.5,0.5,1.0); }
'''
        program = gl('glCreateProgram', uint)()
        for kind, text in [(0x8B31, vertex), (0x8B30, fragment)]:
            gl('glAttachShader', None, uint, uint)(program, shader(kind, text))
        gl('glLinkProgram', None, uint)(program)
        ok = integer()
        gl('glGetProgramiv', None, uint, uint, ptr)(program, 0x8B82, C.byref(ok))
        self.assertTrue(ok.value, 'shader link failed')
        gl('glUseProgram', None, uint)(program)
        location = gl('glGetUniformLocation', integer, uint, C.c_char_p)
        alpha_loc = location(program, b'testAlpha')
        test_loc = location(program, b'p3d_TTAlphaTest')
        self.assertGreaterEqual(test_loc, 0)
        texture = uint()
        gl('glGenTextures', None, integer, ptr)(1, C.byref(texture))
        gl('glBindTexture', None, uint, uint)(0x0DE1, texture)
        for parameter in (0x2800, 0x2801):
            gl('glTexParameteri', None, uint, uint, integer)(0x0DE1, parameter, 0x2600)
        gl('glTexImage2D', None, uint, integer, integer, integer, integer, integer, uint, uint, ptr)(
            0x0DE1, 0, 0x1908, 1, 1, 0, 0x1908, 0x1401, (C.c_ubyte * 4)(255,255,255,255))
        vertices = (C.c_float * 6)(-1,-1,3,-1,-1,3)
        attribute = gl('glGetAttribLocation', integer, uint, C.c_char_p)(program, b'vertex')
        gl('glVertexAttribPointer', None, uint, integer, uint, uint, integer, ptr)(attribute, 2, 0x1406, 0, 0, vertices)
        gl('glEnableVertexAttribArray', None, uint)(attribute)
        gl('glViewport', None, integer, integer, integer, integer)(0,0,1,1)
        # Alternate opaque, binary and dual-pass comparisons on the same program.
        for mode in (0,7,2,5,4,3,6,1,8,7,0):
            for alpha in (0.0,0.25,0.5,0.75,1.0):
                expected = [True,False,alpha<0.5,alpha==0.5,alpha<=0.5,
                            alpha>0.5,alpha!=0.5,alpha>=0.5,True][mode]
                gl('glClearColor', None, C.c_float,C.c_float,C.c_float,C.c_float)(0,0,1,1)
                gl('glClear', None, uint)(0x4000)
                gl('glUniform1f', None, integer,C.c_float)(alpha_loc,alpha)
                gl('glUniform2f', None, integer,C.c_float,C.c_float)(test_loc,mode,0.5)
                gl('glDrawArrays', None, uint,integer,integer)(4,0,3)
                pixel = (C.c_ubyte * 4)()
                gl('glReadPixels', None, integer,integer,integer,integer,uint,uint,ptr)(0,0,1,1,0x1908,0x1401,pixel)
                self.assertEqual(tuple(pixel[:3]), (255,0,0) if expected else (0,0,255), (mode,alpha))
        self.assertEqual(gl('glGetError', uint)(), 0)
        api(egl, 'eglMakeCurrent', uint, ptr,ptr,ptr,ptr)(display,None,None,None)
        api(egl, 'eglTerminate', uint, ptr)(display)
