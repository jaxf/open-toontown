#import "TTGameInputBridge.h"
#include <Python.h>

static NSError *TTInputError(void) {
    // Do not expose Python tracebacks or session credentials in native UI.
    return [NSError errorWithDomain:@"OpenToontown.Input" code:1 userInfo:@{
        NSLocalizedDescriptionKey: @"The game input connection failed. Reopen the client."
    }];
}

@implementation TTGameInputBridge {
    __weak TTControlsView *_view;
    PyObject *_input;
    BOOL _invalid;
    BOOL _handlingFailure;
}

- (nullable instancetype)initWithControlsView:(TTControlsView *)view
                                       error:(NSError * _Nullable * _Nullable)error {
    NSAssert(NSThread.isMainThread, @"Game input must run on the main engine thread");
    self = [super init];
    if (!self) return nil;
    if (!Py_IsInitialized()) {
        if (error) *error = TTInputError();
        return nil;
    }
    PyGILState_STATE gil = PyGILState_Ensure();
    PyObject *module = PyImport_ImportModule("toontown.mobile.NativeControls");
    if (module) {
        _input = PyObject_CallMethod(module, "create", NULL);
        Py_DECREF(module);
    }
    if (!_input) PyErr_Clear();
    PyGILState_Release(gil);
    if (!_input) {
        if (error) *error = TTInputError();
        return nil;
    }
    _view = view;
    view.gameplayEnabled = NO;
    view.delegate = self;
    [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(appInactive:)
        name:UIApplicationWillResignActiveNotification object:nil];
    return self;
}

- (void)finishCall:(PyObject *)result {
    if (result) {
        Py_DECREF(result);
        return;
    }
    PyErr_Clear();
    // Mark closed before cancelling UIKit touches: cancellation sends callbacks.
    _invalid = YES;
    if (_handlingFailure) return;
    _handlingFailure = YES;
    _view.gameplayEnabled = NO;
    PyObject *closed = PyObject_CallMethod(_input, "close", NULL);
    Py_XDECREF(closed);
    PyErr_Clear();
    if (self.inputFailed) self.inputFailed(TTInputError());
    _handlingFailure = NO;
}

- (void)controlsView:(TTControlsView *)view movedStickX:(CGFloat)x y:(CGFloat)y {
    NSAssert(NSThread.isMainThread, @"Game input must run on the main engine thread");
    if (_invalid || !_input) return;
    PyGILState_STATE gil = PyGILState_Ensure();
    [self finishCall:PyObject_CallMethod(_input, "move_stick", "dd", (double)x, (double)y)];
    PyGILState_Release(gil);
}

- (void)controlsView:(TTControlsView *)view jumpPressed:(BOOL)pressed {
    NSAssert(NSThread.isMainThread, @"Game input must run on the main engine thread");
    if (_invalid || !_input) return;
    PyGILState_STATE gil = PyGILState_Ensure();
    [self finishCall:PyObject_CallMethod(_input, "jump", "O", pressed ? Py_True : Py_False)];
    PyGILState_Release(gil);
}

- (void)setActive:(BOOL)active {
    NSAssert(NSThread.isMainThread, @"Game input must run on the main engine thread");
    if (_invalid || !_input) return;
    _view.gameplayEnabled = NO; // Cancel contacts before changing router state.
    PyGILState_STATE gil = PyGILState_Ensure();
    [self finishCall:PyObject_CallMethod(_input, "set_enabled", "O", active ? Py_True : Py_False)];
    PyGILState_Release(gil);
    if (!_invalid) _view.gameplayEnabled = active;
}

- (void)appInactive:(NSNotification *)notification {
    [self setActive:NO];
}

- (void)invalidate {
    NSAssert(NSThread.isMainThread, @"Game input must run on the main engine thread");
    _invalid = YES;
    _view.gameplayEnabled = NO;
    if (_view.delegate == self) _view.delegate = nil;
    [[NSNotificationCenter defaultCenter] removeObserver:self];
    if (_input && Py_IsInitialized()) {
        PyGILState_STATE gil = PyGILState_Ensure();
        PyObject *closed = PyObject_CallMethod(_input, "close", NULL);
        Py_XDECREF(closed);
        PyErr_Clear();
        Py_CLEAR(_input);
        PyGILState_Release(gil);
    }
    _input = NULL;
}

- (void)dealloc {
    [self invalidate];
}
@end
