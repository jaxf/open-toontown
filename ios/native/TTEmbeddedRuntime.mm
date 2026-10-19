#import "TTEmbeddedRuntime.h"
#include "TTBuiltinModules.h"
#include <Python.h>

static NSError *TTRuntimeError(NSInteger code) {
    NSArray<NSString *> *messages = @[
        @"This build is missing game files or its packaged Python runtime.",
        @"The Python runtime could not start. Close and reopen the app.",
        @"Game setup failed. Check the private server address, player token and installed game dependencies.",
        @"The game stopped. Close and reopen the app before reconnecting."
    ];
    return [NSError errorWithDomain:@"OpenToontown.Runtime" code:code userInfo:@{
        NSLocalizedDescriptionKey: messages[MIN(MAX(code, 0), 3)]
    }];
}

static BOOL TTExists(NSURL *root, NSString *path) {
    return [[NSFileManager defaultManager] fileExistsAtPath:
        [root URLByAppendingPathComponent:path].path];
}

static PyStatus TTAppendPath(PyConfig *config, NSString *path) {
    wchar_t *value = Py_DecodeLocale(path.fileSystemRepresentation, NULL);
    if (!value) return PyStatus_NoMemory();
    PyStatus result = PyWideStringList_Append(&config->module_search_paths, value);
    PyMem_RawFree(value);
    return result;
}

@implementation TTEmbeddedRuntime {
    PyObject *_runtime;
}

- (BOOL)prepareWithBundle:(NSBundle *)bundle userData:(NSURL *)userData
                  server:(NSString *)server token:(NSString *)token
                   error:(NSError * _Nullable * _Nullable)error {
    static BOOL attempted = NO;
    if (!NSThread.isMainThread || attempted || Py_IsInitialized()) {
        if (error) *error = TTRuntimeError(1);
        return NO;
    }
    NSURL *root = bundle.resourceURL;
    NSURL *game = [root URLByAppendingPathComponent:@"Game" isDirectory:YES];
    NSURL *python = [root URLByAppendingPathComponent:@"python" isDirectory:YES];
    NSURL *platform = [root URLByAppendingPathComponent:@"Device.prc"];
    // This is an intentionally incomplete development bundle until packaging
    // supplies the full content/runtime. Do not launch a reduced game instead.
    if (!TTExists(game, @"etc/Configrc.prc") || !TTExists(game, @"resources/phase_3") ||
        !TTExists(game, @"toontown/mobile/EmbeddedRuntime.py") ||
        !TTExists(python, @"lib/python3.13/encodings/__init__.py") ||
        !TTExists(root, @"Device.prc")) {
        if (error) *error = TTRuntimeError(0);
        return NO;
    }
    if (![[NSFileManager defaultManager] createDirectoryAtURL:userData
            withIntermediateDirectories:YES attributes:@{NSFilePosixPermissions: @0700} error:nil] ||
        ![[NSFileManager defaultManager] changeCurrentDirectoryPath:game.path]) {
        if (error) *error = TTRuntimeError(0);
        return NO;
    }
    attempted = YES;
    PyPreConfig pre;
    PyPreConfig_InitIsolatedConfig(&pre);
    pre.utf8_mode = 1;
    PyStatus status = Py_PreInitialize(&pre);
    if (PyStatus_Exception(status) || TTRegisterBuiltinModules() != 0) {
        if (error) *error = TTRuntimeError(1);
        return NO;
    }
    PyConfig config;
    PyConfig_InitIsolatedConfig(&config);
    config.write_bytecode = 0;
    config.buffered_stdio = 0;
    config.install_signal_handlers = 0; // UIKit owns process lifecycle/signals.
    config.site_import = 0;
    config.parse_argv = 0;
    config.pathconfig_warnings = 0;
    config.module_search_paths_set = 1;
    status = PyConfig_SetBytesString(&config, &config.home, python.path.fileSystemRepresentation);
    if (!PyStatus_Exception(status))
        status = PyConfig_SetBytesString(&config, &config.executable, bundle.executablePath.fileSystemRepresentation);
    for (NSString *path in @[game.path, [python.path stringByAppendingPathComponent:@"lib/python3.13"],
                            [python.path stringByAppendingPathComponent:@"lib/python3.13/lib-dynload"],
                            [python.path stringByAppendingPathComponent:@"site-packages"]]) {
        if (!PyStatus_Exception(status)) status = TTAppendPath(&config, path);
    }
    char program[] = "OpenToontown";
    char *arguments[] = {program}; // No credential in argv, environment or PRC.
    if (!PyStatus_Exception(status)) status = PyConfig_SetBytesArgv(&config, 1, arguments);
    if (!PyStatus_Exception(status)) status = Py_InitializeFromConfig(&config);
    PyConfig_Clear(&config);
    if (PyStatus_Exception(status)) {
        if (Py_IsInitialized()) { PyErr_Clear(); PyEval_SaveThread(); }
        if (error) *error = TTRuntimeError(1);
        return NO;
    }
    PyObject *module = PyImport_ImportModule("toontown.mobile.EmbeddedRuntime");
    if (module) {
        _runtime = PyObject_CallMethod(module, "Runtime", "sssss",
            game.path.UTF8String, userData.path.UTF8String, platform.path.UTF8String,
            server.UTF8String, token.UTF8String);
        Py_DECREF(module);
    }
    if (!_runtime) PyErr_Clear(); // Never send token-bearing exception text to UI/logs.
    PyEval_SaveThread(); // Allow the game's Python workers between UI callbacks.
    if (!_runtime && error) *error = TTRuntimeError(2);
    return _runtime != NULL;
}

- (BOOL)call:(const char *)method truth:(BOOL * _Nullable)truth
        error:(NSError * _Nullable * _Nullable)error {
    if (!NSThread.isMainThread || !_runtime || !Py_IsInitialized()) {
        if (error) *error = TTRuntimeError(3);
        return NO;
    }
    PyGILState_STATE gil = PyGILState_Ensure();
    PyObject *result = PyObject_CallMethod(_runtime, method, NULL);
    int value = result && truth ? PyObject_IsTrue(result) : 0;
    BOOL success = result != NULL && value >= 0;
    if (truth) *truth = success && value == 1;
    Py_XDECREF(result);
    if (!success) PyErr_Clear();
    PyGILState_Release(gil);
    if (!success && error) *error = TTRuntimeError(3);
    return success;
}

- (BOOL)start:(NSError * _Nullable * _Nullable)error { return [self call:"start" truth:NULL error:error]; }
- (BOOL)frameAllowingMovement:(BOOL *)allowed error:(NSError * _Nullable * _Nullable)error {
    return [self call:"frame" truth:allowed error:error];
}
- (BOOL)pause:(NSError * _Nullable * _Nullable)error { return [self call:"pause" truth:NULL error:error]; }
- (BOOL)resume:(NSError * _Nullable * _Nullable)error { return [self call:"resume" truth:NULL error:error]; }

- (void)stop {
    NSAssert(NSThread.isMainThread, @"Stop the runtime on the main thread in the foreground");
    if (_runtime && Py_IsInitialized()) {
        [self call:"close" truth:NULL error:nil];
        PyGILState_STATE gil = PyGILState_Ensure();
        Py_CLEAR(_runtime);
        PyGILState_Release(gil);
    }
    // Do not Py_FinalizeEx/reinitialize Panda's process-wide native statics.
}
@end
