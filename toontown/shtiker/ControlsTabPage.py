"""Key bindings and field of view in the Shticker Book options."""
from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton, DirectScrolledFrame, DirectSlider, DGG
from direct.showbase.ShowBaseGlobal import base
from direct.showbase.MessengerGlobal import messenger
from direct.task.TaskManagerGlobal import taskMgr
from panda3d.core import TextNode, Point3
from toontown.expansion.ControlSettings import BINDINGS, DEFAULTS, keys, field_of_view


class ControlsTabPage(DirectFrame):
    def __init__(self,parent):
        DirectFrame.__init__(self,parent=parent,relief=None)
        self.capture=None
        self.buttons={}
        self.dragTaskName='controls-fov-drag-'+self.guiId
        self.lastFov=None
        gui=base.loader.loadModel('phase_3/models/gui/quit_button')
        buttonImages=tuple(gui.find('**/'+name) for name in ('QuitBtn_UP','QuitBtn_DN','QuitBtn_RLVR'))
        self.info=DirectLabel(parent=self,text='Click a key to change it. Choose an unused key.',
            text_scale=.037,pos=(0,0,.43),relief=None)
        self.scroll=DirectScrolledFrame(parent=self,frameSize=(-.72,.72,-.36,.36),
            canvasSize=(-.69,.66,-len(BINDINGS)*.105,0),relief=None,
            frameColor=(1,1,1,0),scrollBarWidth=.035)
        for i,(action,label,key) in enumerate(BINDINGS):
            z=-.065-i*.105
            DirectLabel(parent=self.scroll.getCanvas(),text=label,text_align=TextNode.ALeft,
                text_scale=.037,pos=(-.64,0,z),relief=None)
            self.buttons[action]=DirectButton(parent=self.scroll.getCanvas(),text=self.key_label(keys()[action]),
                relief=None,image=buttonImages,image_scale=(.86,1,.72),
                text_scale=.034,text_pos=(0,-.012),pos=(.43,0,z+.01),
                command=self.begin_capture,extraArgs=[action])
        self.fovLabel=DirectLabel(parent=self,text='',text_scale=.04,pos=(-.36,0,-.44),relief=None)
        self.slider=DirectSlider(parent=self,range=(50,100),value=field_of_view(),pageSize=0,
            frameSize=(-.35,.35,-.035,.035),frameVisibleScale=(1,.25),
            thumb_frameSize=(-.025,.025,-.035,.035),thumb_relief=DGG.RAISED,
            thumb_borderWidth=(.006,.006),thumb_frameColor=(1,.85,.15,1),
            pos=(.31,0,-.43),command=self.set_fov)
        # A press anywhere on the track follows the pointer immediately instead
        # of advancing one page at a time. The larger thumb is easy to grab.
        self.slider.bind(DGG.B1PRESS,self.begin_fov_drag)
        self.slider.thumb.bind(DGG.B1PRESS,self.begin_fov_drag)
        self.accept('mouse1-up',self.end_fov_drag)
        self.set_fov()
        DirectLabel(parent=self,text='Activity controls (fishing, racing, minigames) appear in their instructions.',
            text_scale=.028,pos=(0,0,-.55),relief=None)
        DirectButton(parent=self,text='Restore defaults',relief=None,image=buttonImages,
            image_scale=(1.15,1,.85),text_scale=.04,text_pos=(0,-.015),
            pos=(0,0,-.65),command=self.reset)
        gui.removeNode()
        self.accept('wheel_up',self.wheel,[-.08]);self.accept('wheel_down',self.wheel,[.08])

    def wheel(self,amount):
        if not self.isHidden():
            bar=self.scroll.verticalScroll;bar['value']=max(0,min(1,bar['value']+amount))

    @staticmethod
    def key_label(key):
        return key.replace('arrow_','').replace('_',' ').replace('-',' + ').title()

    def begin_fov_drag(self,event):
        self.cancel_capture()
        self.end_fov_drag()
        self.update_fov_from_pointer()
        taskMgr.add(self.drag_fov,self.dragTaskName)

    def update_fov_from_pointer(self):
        mouse=base.mouseWatcherNode
        if mouse.hasMouse():
            point=self.slider.getRelativePoint(base.render2d,Point3(mouse.getMouseX(),0,mouse.getMouseY()))
            ratio=max(0,min(1,(point.x+.325)/.65))
            self.slider['value']=50+50*ratio
            self.set_fov()

    def drag_fov(self,task):
        if self.isHidden():return task.done
        self.update_fov_from_pointer()
        return task.cont

    def end_fov_drag(self):
        taskMgr.remove(self.dragTaskName)

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
        for action,button in self.buttons.items():button['text']=self.key_label(mapping[action])
        messenger.send('controls-changed')

    def set_fov(self):
        if not hasattr(self,'slider'):return
        value=self.slider['value']
        if value==self.lastFov:return
        self.lastFov=value
        self.fovLabel['text']='Field of view: %s°'%round(value)
        base.settings.updateSetting('camera-fov',value)
        avatar=getattr(base,'localAvatar',None)
        if avatar:avatar.setCameraFov(value)

    def reset(self):
        self.cancel_capture();self.save(dict(DEFAULTS));self.slider['value']=70;self.set_fov()

    def enter(self):self.show()

    def exit(self):
        self.end_fov_drag()
        self.cancel_capture();base.settings.writeSettings();self.hide()

    def destroy(self):
        self.end_fov_drag()
        self.ignoreAll()
        self.cancel_capture();DirectFrame.destroy(self)
