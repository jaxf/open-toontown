"""Normal walking with held-Shift sprint and modifier-independent air steering."""
from panda3d.core import KeyboardButton
from direct.controls.GravityWalker import GravityWalker
from direct.showbase.InputStateGlobal import inputState
from direct.showbase import ShowBaseGlobal


class ToonWalker(GravityWalker):
    sprintMultiplier = 1.65
    keySource = 'toon-walker-physical-arrows'

    def handleAvatarControls(self, task):
        watcher = ShowBaseGlobal.base.mouseWatcherNode
        active = watcher is not None
        # Poll physical buttons while controls are active. Pressing Ctrl to jump
        # must not swallow arrow presses as modified keyboard events. The native
        # walker turns the Toon in the air and the attached smart camera follows.
        for action,button in (('turnLeft',KeyboardButton.left()),
                              ('turnRight',KeyboardButton.right())):
            inputState.set(action, bool(active and watcher.isButtonDown(button)), self.keySource)
        # Also recognize Shift+Ctrl when sprinting before starting a jump.
        avatar = getattr(ShowBaseGlobal.base, 'localAvatar', None)
        useControlJump = avatar is not None and not avatar.controlManager.wantWASD
        inputState.set('jump', bool(active and useControlJump and
                       watcher.isButtonDown(KeyboardButton.control())), self.keySource)
        sprint = active and watcher.isButtonDown(KeyboardButton.shift())
        forward,reverse = self.avatarControlForwardSpeed,self.avatarControlReverseSpeed
        if sprint:
            self.avatarControlForwardSpeed *= self.sprintMultiplier
            self.avatarControlReverseSpeed *= self.sprintMultiplier
        try:
            return GravityWalker.handleAvatarControls(self, task)
        finally:
            # Preserve the caller's walking/slow-walking settings, including
            # transitions to swimming, interiors, minigames and disabled controls.
            self.avatarControlForwardSpeed,self.avatarControlReverseSpeed = forward,reverse

    def disableAvatarControls(self):
        for action in ('turnLeft','turnRight','jump'):
            inputState.set(action, False, self.keySource)
        GravityWalker.disableAvatarControls(self)
