"""Main-thread entry points called by TTGameInputBridge after game startup.

This uses the existing key-event router; it never moves an avatar directly.
The native host controls availability across menus, chat and app suspension.
Pointer/tap delivery belongs to the graphics window, not this overlay.
"""
from toontown.mobile.TouchInput import engine_input, stick_keys


class NativeControls:
    def __init__(self, router):
        self.router = router
        self.router.set_enabled(False)

    def move_stick(self, x, y):
        self.router.update('uikit-stick', stick_keys(x, y))

    def jump(self, pressed):
        self.router.update('uikit-jump', {'control'} if pressed else ())

    def set_enabled(self, enabled):
        self.router.set_enabled(enabled)

    def close(self):
        self.router.set_enabled(False)


def create():
    from panda3d.core import ConfigVariableBool
    if not ConfigVariableBool('mobile-client', False).value:
        raise RuntimeError('Native controls require the embedded mobile client')
    return NativeControls(engine_input())
