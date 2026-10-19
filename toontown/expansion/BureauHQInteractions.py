"""Optional local scenery interactions; no keyboard bindings or game rewards."""
from panda3d.core import Vec3,ClockObject
from direct.interval.IntervalGlobal import Sequence,Wait,LerpPosInterval,LerpHprInterval
from direct.gui.DirectGui import DirectButton,DirectLabel

SOUNDS={
    'stamp':'phase_5/audio/sfx/SA_rubber_stamp.ogg',
    'drawer':'phase_9/audio/sfx/CHQ_FACT_switch_popup.ogg',
    'ticket':'phase_9/audio/sfx/CHQ_FACT_switch_pressed.ogg',
    'registry':'phase_9/audio/sfx/CHQ_FACT_switch_depressed.ogg'}


def action_interval(machine):
    """Always returns art to its original pose; collisions never animate."""
    node=machine.getPythonTag('action-node');kind=machine.getTag('bureau-action')
    if kind=='registry':
        start=node.getHpr()
        return Sequence(LerpHprInterval(node,1.2,start+Vec3(0,0,22.5),startHpr=start,
                                        blendType='easeInOut'),Wait(.8),
                        LerpHprInterval(node,1.2,start,blendType='easeInOut'))
    start=node.getPos()
    offset={'stamp':Vec3(0,0,-1.6),'drawer':Vec3(0,-3,0),'ticket':Vec3(0,-3.3,0)}[kind]
    return Sequence(LerpPosInterval(node,.3,start+offset,startPos=start,blendType='easeOut'),
                    Wait(1.4),LerpPosInterval(node,.7,start,blendType='easeInOut'))


class BureauHQInteractions:
    def __init__(self,app,place,scene):
        self.app=app;self.place=place;self.scene=scene
        self.clock=ClockObject.getGlobalClock()
        self.machines=list(scene.findAllMatches('**/=bureau-action'))
        self.current=None;self.running=None;self.runningMachine=None
        self.readyAt=0;self.messageUntil=0;self.destroyed=False
        self.taskName='bureau-scenery-%s'%id(self)
        self.sounds={kind:app.loader.loadSfx(path) for kind,path in SOUNDS.items()}
        self.originals={node:node.getPythonTag('action-node').getTransform() for node in self.machines}
        self.gui=app.loader.loadModel('phase_3/models/gui/quit_button')
        self.button=DirectButton(parent=app.aspect2d,relief=None,
            image=tuple(self.gui.find('**/QuitBtn_'+suffix) for suffix in ('UP','DN','RLVR')),
            image_scale=(2.6,1,1),scale=.75,pos=(0,0,-.77),
            text='',text_scale=.056,text_pos=(0,-.015),command=self.use)
        self.message=DirectLabel(parent=app.aspect2d,relief=None,text='',
            text_scale=.042,text_fg=(1,.94,.74,1),text_shadow=(0,0,0,1),
            pos=(0,0,-.65),text_wordwrap=43)
        self.button.hide();self.message.hide()
        self.ambient=[]
        for node in scene.findAllMatches('**/=bureau-ambient'):
            original=node.getTransform()
            if node.getTag('bureau-ambient')=='gear':
                start=node.getHpr()
                interval=LerpHprInterval(node,18,start+Vec3(360,0,0),startHpr=start)
            else:
                start=node.getPos()
                # Each packet travels one spacing, then is replaced at its start.
                interval=LerpPosInterval(node,5,start+Vec3(0,14,0),startPos=start)
            interval.loop();self.ambient.append((node,original,interval))
        app.taskMgr.add(self.update,self.taskName)

    def walking(self):
        state=self.place.fsm.getCurrentState()
        return state is not None and state.getName()=='walk'

    def nearest(self):
        if not self.walking():return None
        avatar=self.app.localAvatar
        candidates=[]
        for node in self.machines:
            local=avatar.getPos(node)
            distance=avatar.getDistance(node.find('use-point'))
            if distance<=10 and local.y < -3 and abs(local.z)<5:
                candidates.append((distance,node))
        return min(candidates,key=lambda item:item[0])[1] if candidates else None

    def reset_action(self):
        if self.running is not None:self.running.pause()
        if self.runningMachine is not None:
            machine=self.runningMachine
            machine.getPythonTag('action-node').setTransform(self.originals[machine])
            machine.getPythonTag('status-light').clearColorScale()
        self.running=None;self.runningMachine=None
        for sound in self.sounds.values():sound.stop()

    def use(self):
        if self.destroyed:return False
        now=self.clock.getFrameTime();machine=self.nearest()
        # Recheck on click: the user may have moved or entered battle since the
        # last task update. Local feedback can never claim progression rewards.
        if machine is None or now<self.readyAt:return False
        self.reset_action();self.runningMachine=machine
        self.running=action_interval(machine);self.running.start()
        machine.getPythonTag('status-light').setColorScale(.4,1,.45,1)
        self.sounds[machine.getTag('bureau-action')].play()
        self.readyAt=now+4;self.messageUntil=now+4
        self.message['text']=machine.getTag('action-response');self.message.show()
        self.button.hide()
        return True

    def update(self,task):
        if self.destroyed:return task.done
        now=self.clock.getFrameTime()
        self.current=self.nearest()
        if not self.walking():
            if self.running is not None:self.reset_action()
            self.message.hide()
        elif self.running is not None and not self.running.isPlaying():self.reset_action()
        if self.current is not None and now>=self.readyAt:
            self.button['text']=self.current.getTag('action-title');self.button.show()
        else:self.button.hide()
        if now>=self.messageUntil:self.message.hide()
        return task.cont

    def destroy(self):
        if self.destroyed:return
        self.destroyed=True;self.app.taskMgr.remove(self.taskName);self.reset_action()
        for node,original,interval in self.ambient:
            interval.pause();node.setTransform(original)
        self.ambient=[]
        self.button.destroy();self.message.destroy();self.gui.removeNode()
        self.machines=[];self.originals.clear();self.sounds.clear()
