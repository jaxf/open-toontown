"""Use the saved movement bindings without leaving the old keys active."""
from direct.controls.ControlManager import ControlManager as PandaControlManager
from direct.showbase.InputStateGlobal import inputState
from toontown.expansion.ControlSettings import keys


class ControlManager(PandaControlManager):
    def enable(self):
        if self.isEnabled:return
        self.isEnabled=1
        # passMessagesThrough can leave tokens when controls were disabled.
        for token in self.inputStateTokens:token.release()
        self.inputStateTokens=[]
        mapping=keys()
        for action in ('forward','reverse','turnLeft','turnRight','jump'):
            self.inputStateTokens.append(inputState.watchWithModifiers(action,mapping[action],inputSource=inputState.ArrowKeys))
        for action,start,end in [('run','running-on','running-off'),
                ('forward','force-forward','force-forward-stop'),
                ('turnLeft','force-turnLeft','force-turnLeft-stop'),
                ('turnRight','force-turnRight','force-turnRight-stop'),
                ('turnLeft','mouse-look_left','mouse-look_left-done'),
                ('turnRight','mouse-look_right','mouse-look_right-done')]:
            self.inputStateTokens.append(inputState.watch(action,start,end))
        if self.currentControls:self.currentControls.enableAvatarControls()

    def disable(self):
        # The old pass-through implementation installs hardcoded arrow watches.
        through=self.passMessagesThrough
        self.passMessagesThrough=False
        try:PandaControlManager.disable(self)
        finally:self.passMessagesThrough=through
