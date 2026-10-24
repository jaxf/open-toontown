"""Multi-contact key ownership for native touch overlays and controller adapters.

No movement/network shortcuts: emit existing game key events so native game
states retain control. UIKit must still provide hit-testing, a pointer device
for DirectGUI and the software keyboard. This is not yet an on-device overlay.
"""
import math

KEYS = frozenset(('arrow_up', 'arrow_down', 'arrow_left', 'arrow_right', 'control',
                  'shift', 'space', 'insert', 'delete', 'tab', 'escape', 'enter',
                  'f7', 'f8', 'home', 'end', 'alt', 'page_up', 'page_down'))


def stick_keys(x, y, deadzone=0.25):
    if not all(math.isfinite(v) for v in (x, y, deadzone)) or not 0 <= deadzone < 1:
        raise ValueError('Invalid stick coordinates/deadzone')
    keys = set()
    if abs(x) > deadzone:
        keys.add('arrow_right' if x > 0 else 'arrow_left')
    if abs(y) > deadzone:
        keys.add('arrow_up' if y > 0 else 'arrow_down')
    return keys


class TouchInput:
    def __init__(self, emit, clock):
        self.emit, self.clock = emit, clock
        self.contacts = {}
        self.enabled = True

    def _held(self):
        return set().union(*self.contacts.values()) if self.contacts else set()

    def _event(self, key, down):
        event = key if down else key + '-up'
        self.emit(event, [])
        # Native pie/cannon controls also subscribe to timestamped events.
        self.emit('time-' + event, [self.clock()])

    def update(self, contact, keys):
        keys = frozenset(keys)
        if not keys <= KEYS:
            raise ValueError('Unknown mobile key')
        if not self.enabled:
            return
        before = self._held()
        if keys:
            self.contacts[contact] = keys
        else:
            self.contacts.pop(contact, None)
        after = self._held()
        for key in sorted(before - after):
            self._event(key, False)
        for key in sorted(after - before):
            self._event(key, True)

    def end(self, contact):
        self.update(contact, ())

    def cancel_all(self):
        held = self._held()
        self.contacts.clear()
        for key in sorted(held):
            self._event(key, False)

    def set_enabled(self, enabled):
        self.cancel_all()
        self.enabled = bool(enabled)


def engine_input():
    from direct.showbase.MessengerGlobal import messenger
    from panda3d.core import ClockObject
    return TouchInput(messenger.send, ClockObject.getGlobalClock().getFrameTime)
