"""Key bindings and field of view in the Shticker Book options."""
from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton, DirectScrolledFrame, DirectSlider, DGG
from direct.showbase.ShowBaseGlobal import base
from direct.showbase.MessengerGlobal import messenger
from panda3d.core import TextNode
from toontown.expansion.ControlSettings import BINDINGS, DEFAULTS, keys, field_of_view


class ControlsTabPage(DirectFrame):
    def __init__(self,parent):
        DirectFrame.__init__(self,parent=parent,relief=None)
        self.capture=None
        self.buttons={}
        self.info=DirectLabel(parent=self,text='Click a key to change it. Choose an unused key.',
            text_scale=.037,pos=(0,0,.43),relief=None)
        self.scroll=DirectScrolledFrame(parent=self,frameSize=(-.72,.72,-.36,.36),
            canvasSize=(-.69,.66,-len(BINDINGS)*.085,0),frameColor=(.95,.91,.78,1),scrollBarWidth=.035)
        for i,(action,label,key) in enumerate(BINDINGS):
            z=-.055-i*.085
            DirectLabel(parent=self.scroll.getCanvas(),text=label,text_align=TextNode.ALeft,
                text_scale=.037,pos=(-.64,0,z),relief=None)
            self.buttons[action]=DirectButton(parent=self.scroll.getCanvas(),text=keys()[action],
                text_scale=.034,pos=(.43,0,z),frameSize=(-.19,.19,-.025,.04),
                command=self.begin_capture,extraArgs=[action])
        self.fovLabel=DirectLabel(parent=self,text='',text_scale=.04,pos=(-.36,0,-.44),relief=None)
        self.slider=DirectSlider(parent=self,range=(50,100),value=field_of_view(),pageSize=1,
            scale=.35,pos=(.31,0,-.43),command=self.set_fov)
        self.set_fov()
        DirectLabel(parent=self,text='Activity controls (fishing, racing, minigames) appear in their instructions.',
            text_scale=.028,pos=(0,0,-.55),relief=None)
        DirectButton(parent=self,text='Restore defaults',text_scale=.035,pos=(0,0,-.65),command=self.reset)
        self.accept('wheel_up',self.wheel,[-.08]);self.accept('wheel_down',self.wheel,[.08])

    def wheel(self,amount):
        if not self.isHidden():
            bar=self.scroll.verticalScroll;bar['value']=max(0,min(1,bar['value']+amount))

    def begin_capture(self,action):
        self.cancel_capture()
        self.capture=action;base.capturingControl=True
        self.info['text']='Press a key for '+dict((a,l) for a,l,k in BINDINGS)[action]+'. Click outside to cancel.'
        thrower=base.buttonThrowers[0].node()
        self.oldDownEvent=thrower.getButtonDownEvent()
        thrower.setButtonDownEvent('control-binding-capture')
        self.accept('control-binding-capture',self.finish_capture)

    def cancel_capture(self):
        if self.capture is not None:
            base.buttonThrowers[0].node().setButtonDownEvent(self.oldDownEvent)
        self.capture=None;base.capturingControl=False
        self.ignore('control-binding-capture')

    def finish_capture(self,key):
        action=self.capture
        if key.startswith(('mouse','wheel')):
            self.cancel_capture();return
        # Accept concrete keyboard buttons. A modifier can itself be a binding.
        mapping=keys()
        for other,value in mapping.items():
            if other!=action and value==key:
                self.info['text']='That key is already in use. Press another key.'
                return
        mapping[action]=key
        self.cancel_capture()
        self.save(mapping)
        self.info['text']='Saved. Click another key to change it.'

    def save(self,mapping):
        base.settings.updateSetting('key-bindings',mapping);base.settings.writeSettings()
        for action,button in self.buttons.items():button['text']=mapping[action]
        messenger.send('controls-changed')

    def set_fov(self):
        if not hasattr(self,'slider'):return
        value=round(self.slider['value'])
        self.fovLabel['text']='Field of view: %s°'%value
        base.settings.updateSetting('camera-fov',value)
        avatar=getattr(base,'localAvatar',None)
        if avatar:avatar.setCameraFov(value)

    def reset(self):
        self.cancel_capture();self.save(dict(DEFAULTS));self.slider['value']=70;self.set_fov()

    def enter(self):self.show()

    def exit(self):
        self.cancel_capture();base.settings.writeSettings();self.hide()

    def destroy(self):
        self.cancel_capture();DirectFrame.destroy(self)
