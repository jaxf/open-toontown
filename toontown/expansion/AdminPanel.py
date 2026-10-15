from direct.gui.DirectGui import DirectButton, DirectFrame, DirectLabel, DirectScrolledFrame, DGG
from direct.task.TaskManagerGlobal import taskMgr
from toontown.toonbase.ToonBaseGlobal import base
from . import ExpansionGlobals as E
from .AdminPolicy import ADMIN_LEVEL


class AdminPanel:
    """Self-only testing controls; every action is checked again on the AI."""
    def __init__(self):
        self.button = DirectButton(parent=base.a2dTopRight, text='Admin',
            text_scale=.044, relief=DGG.FLAT, frameSize=(-.14,.14,-.045,.045),
            frameColor=(.18,.24,.31,1), text_fg=(1,.90,.65,1),
            pos=(-.53,0,-.13), command=self.toggle)
        self.button.hide()
        self.panel = DirectFrame(parent=base.aspect2d, frameSize=(-.58,.58,-.77,.77),
            frameColor=(.10,.14,.19,.98), sortOrder=100)
        DirectLabel(parent=self.panel, text='ADMIN • WORLD TESTING', text_scale=.048,
                    text_fg=(1,.90,.65,1), pos=(0,0,.68), relief=None)
        DirectButton(parent=self.panel, text='Close', text_scale=.035,
                     pos=(.47,0,.69), frameSize=(-.08,.08,-.03,.035),
                     relief=DGG.FLAT,frameColor=(.25,.32,.40,1),text_fg=(1,1,1,1),command=self.close)
        DirectButton(parent=self.panel, text='Max my Toon + unlock travel', text_scale=.043,
                     frameSize=(-.49,.49,-.055,.055), pos=(0,0,.55),relief=DGG.FLAT,
                     frameColor=(.93,.75,.38,1),text_fg=(.12,.16,.20,1),command=self.max_toon)
        DirectLabel(parent=self.panel,
                    text='Permanent: max Laff, all gags, jellybeans, Cog suits.\nClears active tasks. Applies only to your Toon.',
                    text_scale=.029, text_fg=(.82,.85,.90,1), pos=(0,0,.43), relief=None)
        self.status=DirectLabel(parent=self.panel, text='Choose a destination below.',
                    text_scale=.031, text_wordwrap=32, text_fg=(1,.90,.65,1),
                    pos=(0,0,-.69), relief=None)
        self.scroll=DirectScrolledFrame(parent=self.panel,
                    frameSize=(-.52,.52,-.60,.34), canvasSize=(-.50,.46,-2.5,0),
                    frameColor=(.15,.19,.25,1), scrollBarWidth=.035)
        choices=sorted(E.destinations().items(), key=lambda item:(item[0] not in E.ALL_ZONES,item[1]))
        self.scroll['canvasSize']=(-.50,.46,-len(choices)*.09,0)
        for index,(zone,name) in enumerate(choices):
            DirectButton(parent=self.scroll.getCanvas(), text=name, text_scale=.034,
                text_fg=(1,1,1,1), frameColor=(.21,.29,.35,1),
                relief=DGG.FLAT,frameSize=(-.47,.47,-.036,.036), pos=(-.015,0,-.05-index*.09),
                command=self.teleport, extraArgs=[zone])
        self.panel.setX(-.20)
        self.panel.accept('wheel_up',self.scroll_by,[-.065])
        self.panel.accept('wheel_down',self.scroll_by,[.065])
        self.panel.hide()
        self.taskName='admin-panel-%s' % id(self)
        taskMgr.doMethodLater(.25,self.update,self.taskName)

    def scroll_by(self, amount):
        if not self.panel.isHidden():
            bar=self.scroll.verticalScroll
            bar['value']=max(0,min(1,bar['value']+amount))

    def available(self):
        avatar=getattr(base,'localAvatar',None)
        play=getattr(base.cr,'playGame',None)
        place=play.getPlace() if play else None
        fsm=getattr(place,'fsm',None)
        state=fsm.getCurrentState() if fsm else None
        return (avatar is not None and avatar.getAccessLevel() >= ADMIN_LEVEL
                and state is not None and state.getName() == 'walk'
                and not avatar.getTransitioning()
                and not avatar.hasActiveBoardingGroup())

    def update(self, task):
        if self.available():
            self.button.show()
        else:
            self.button.hide()
            self.panel.hide()
        return task.again

    def toggle(self):
        if not self.available():
            return
        if self.panel.isHidden():
            self.panel.show()
        else:
            self.close()

    def close(self):
        self.panel.hide()

    def send(self, action, zone=0):
        manager=getattr(base.cr,'magicWordManager',None)
        if not self.available() or manager is None:
            self.status['text']='Wait until your Toon is walking in the world.'
            return False
        manager.sendUpdate('requestAdminAction',[action,zone])
        return True

    def max_toon(self):
        if self.send('max'):
            self.status['text']='Max request sent. Watch system chat for confirmation.'

    def teleport(self, zone):
        if self.send('teleport',zone):
            self.close()

    def destroy(self):
        taskMgr.remove(self.taskName)
        self.button.destroy()
        self.panel.destroy()
