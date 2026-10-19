"""Native boss cinematics/battles with the Final Review interaction HUD."""
from direct.fsm.FSM import FSM
from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait
from direct.showbase.ShowBaseGlobal import base
from direct.gui.DirectGui import DirectLabel, DirectButton, DirectWaitBar
from panda3d.core import Point3, ClockObject, TransparencyAttrib
from .DistributedBossCog import DistributedBossCog
from toontown.expansion import BureauBossGlobals as G
from toontown.expansion.BureauHQScene import native
from toontown.expansion.Geometry import cylinder
from toontown.building import ElevatorConstants

OneBossCog=None


class DistributedBureauBoss(DistributedBossCog,FSM):
    def __init__(self,cr):
        DistributedBossCog.__init__(self,cr)
        FSM.__init__(self,'DistributedBureauBoss')
        self.ready=False
        self.pendingState=None
        self.loads=[0,0];self.damage=0;self.exposedUntil=0
        self.carrying=[];self.paperProps={}
        self.station=None;self.useAt=0
        self.hud=[];self.warning=None;self.stamp=None

    def announceGenerate(self):
        global OneBossCog
        self.reparentTo(base.render);self.setPosHpr(*G.BOSS_POS)
        self.setName(G.NAME);self.setDisplayName(G.NAME+'\nBureaubot')
        self.loadEnvironment()
        scene=base.cr.playGame.hood.loader.geom
        self.setupElevator(scene.find('**/bureau-arrival-elevator'))
        origin=scene.attachNewNode('bureau-battle-origin');origin.setPosHpr(*G.BATTLE_ORIGIN)
        self.battleANode.reparentTo(origin);self.battleBNode.reparentTo(origin)
        self.battleOrigin=origin
        self.createHud()
        OneBossCog=self
        DistributedBossCog.announceGenerate(self)
        self.ready=True
        self.loop('Ff_neutral')
        if self.pendingState:self.request(self.pendingState)

    def setState(self,state):
        if not self.ready:self.pendingState=state
        else:self.request(state)

    def createHud(self):
        self.banner=DirectLabel(relief=None,text='',text_scale=.045,pos=(0,0,.85),
            text_fg=(1,.93,.77,1),text_shadow=(0,0,0,1))
        self.progress=DirectWaitBar(range=G.MAX_DAMAGE,value=G.MAX_DAMAGE,
            scale=.55,pos=(0,0,.73),barColor=(.75,.35,.12,1),text=G.NAME,text_scale=.055)
        art=base.loader.loadModel('phase_3/models/gui/quit_button')
        self.button=DirectButton(relief=None,geom=(art.find('**/QuitBtn_UP'),
            art.find('**/QuitBtn_DN'),art.find('**/QuitBtn_RLVR')),scale=1.2,
            text='',text_scale=.04,pos=(0,0,-.8),command=self.useStation)
        self.buttonArt=art
        self.hud=[self.banner,self.progress,self.button]
        self.progress.hide();self.button.hide()
        self.paperSfx=base.loader.loadSfx('phase_3.5/audio/sfx/SA_shred.ogg')
        self.hitSfx=base.loader.loadSfx('phase_9/audio/sfx/CHQ_VP_collapse.ogg')

    def enterWaitForToons(self):
        self.banner['text']='Waiting for the review group...'
        base.taskMgr.add(self.waitForPlace,self.uniqueName('bureau-arrival-wait'))

    def waitForPlace(self,task):
        place=self.cr.playGame.getPlace()
        if self.gotAllToons and getattr(place,'bossCog',None)==self:
            self.d_avatarEnter()
            self.doneBarrier('WaitForToons')
            return task.done
        return task.cont

    def exitWaitForToons(self):
        base.taskMgr.remove(self.uniqueName('bureau-arrival-wait'))

    def placeToonInElevator(self,toon):
        # No rental-disguise dependency while the new progression is unfinished.
        toon.reparentTo(self.elevatorModel)
        toon.setPos(*ElevatorConstants.BigElevatorPoints[self.involvedToons.index(toon.doId)])
        toon.setHpr(180,0,0);toon.loop('neutral')

    def enterElevator(self):
        self.banner['text']='The Final Review Chamber'
        DistributedBossCog.enterElevator(self)
        # View through the doors, not through the newly enclosed cabin back.
        base.camera.setPosHpr(self.elevatorModel,0,-22,10,0,0,0)

    def makeIntroductionMovie(self,delayDeletes):
        self.banner['text']='Round 1: Senior staff review'
        walk=Parallel()
        for i,avatar in enumerate(self.involvedToons):
            toon=self.cr.doId2do.get(avatar)
            if toon:
                toon.wrtReparentTo(base.render)
                target=Point3(-56+(i%4-1.5)*3,-48-(i//4)*4,0)
                walk.append(Sequence(Func(toon.loop,'walk'),toon.posInterval(3,target),Func(toon.loop,'neutral')))
        return Sequence(Func(base.camera.wrtReparentTo,base.render),
            Func(base.camera.setPos,-43,-40,17),Func(base.camera.lookAt,12,65,23),
            Func(self.setChatAbsolute,'Your appointment has been denied.',0),walk,Wait(2))

    def enterPrepareBattleTwo(self):
        self.toMovieMode();self.banner['text']='Round 2: Permanent staff - Skelecogs'
        self.stagePause('PrepareBattleTwo',4)

    def stagePause(self,barrier,seconds):
        seq=Sequence(Wait(seconds),Func(self.doneBarrier,barrier))
        self.storeInterval(seq,'bureau-stage');seq.start()

    def exitPrepareBattleTwo(self):
        self.clearInterval('bureau-stage')

    def enterBattleTwo(self):
        DistributedBossCog.enterBattleOne(self)

    exitBattleTwo=DistributedBossCog.exitBattleOne

    def enterPrepareBattleThree(self):
        self.toMovieMode()
        self.banner['text']='Collect forms. Fill BOTH sorters. Stamp the rejection when exposed!'
        for i,avatar in enumerate(self.involvedToons):
            toon=self.cr.doId2do.get(avatar)
            if toon:
                toon.wrtReparentTo(base.render);toon.setPos((i%4-1.5)*7,-33-i//4*8,0)
        base.camera.reparentTo(base.render);base.camera.setPos(1,-74,27);base.camera.lookAt(12,35,12)
        self.stagePause('PrepareBattleThree',8)

    def exitPrepareBattleThree(self):
        self.clearInterval('bureau-stage')

    def enterBattleThree(self):
        self.releaseToons(finalBattle=1)
        self.progress.show()
        base.playMusic(self.battleThreeMusic,looping=1,volume=.8)
        base.taskMgr.add(self.updateHud,self.uniqueName('bureau-hud'))

    def exitBattleThree(self):
        base.taskMgr.remove(self.uniqueName('bureau-hud'))
        self.button.hide();self.battleThreeMusic.stop()
        self.clearWarning()

    def setPaperwork(self,left,right,seconds,damage,carrying):
        self.loads=[left,right];self.exposedUntil=self.now()+seconds if seconds else 0
        old=self.damage;self.damage=damage;self.carrying=carrying
        if self.ready:
            self.progress['value']=G.MAX_DAMAGE-damage
            if damage>old:
                self.hitSfx.play()
                self.play('Fb_downHit')
                self.stageAnimationReset()

    def stageAnimationReset(self):
        seq=Sequence(Wait(2),Func(self.loop,'Ff_neutral'))
        self.clearInterval('bureau-hit',finish=0)
        self.storeInterval(seq,'bureau-hit');seq.start()

    @staticmethod
    def now():
        return ClockObject.getGlobalClock().getFrameTime()

    def updateHud(self,task):
        if self.state!='BattleThree':return task.done
        local=base.localAvatar
        carrying=local.doId in self.carrying
        seconds=max(0,int(self.exposedUntil-self.now()+.999)) if self.exposedUntil else 0
        if seconds:
            self.banner['text']='OVERLOADED! Stamp the rejection!  %ss'%seconds
        else:
            self.banner['text']='Left sorter: %s/3   Right sorter: %s/3  |  %s'%(
                *self.loads,'Carrying a form' if carrying else 'Collect a form from a side table')
        pos=local.getPos(base.render)
        self.station=None
        for i,point in enumerate(G.STATIONS):
            valid=(i<2 and not carrying and not seconds or
                   2<=i<4 and carrying and not seconds and self.loads[i-2]<3 or i==4 and seconds)
            if valid and (pos-Point3(*point)).length()<=G.USE_RADIUS:
                self.station=i;break
        if self.station is None:self.button.hide()
        else:
            self.button['text']=G.STATION_NAMES[self.station]
            self.button.show()
        for avatar in list(self.paperProps):
            if avatar not in self.carrying:
                self.paperProps.pop(avatar).removeNode()
        for avatar in self.carrying:
            toon=self.cr.doId2do.get(avatar)
            if toon and avatar not in self.paperProps:
                self.paperProps[avatar]=native(toon,'phase_11/models/lawbotHQ/LB_paper_stacks',
                                              (1,-.8,2.2),size=(1.2,.8,.25))
        return task.cont

    def useStation(self):
        if self.state=='BattleThree' and self.station is not None and self.now()>=self.useAt:
            self.sendUpdate('requestUseStation',[self.station]);self.useAt=self.now()+1

    def stationUsed(self,avatar,station):
        if not self.ready:return
        self.paperSfx.play()
        group=base.cr.playGame.hood.loader.geom.find('**/=boss-station='+str(station))
        if not group.isEmpty():
            node=group.getPythonTag('action-node')
            if node:
                name='bureau-machine-%s'%station
                self.clearInterval(name)
                origin=node.getPos()
                seq=Sequence(node.posInterval(.2,origin+Point3(0,0,-.8)),node.posInterval(.3,origin))
                self.storeInterval(seq,name);seq.start()

    def clearWarning(self):
        for name in ('warning','stamp'):
            node=getattr(self,name,None)
            if node:node.removeNode()
            setattr(self,name,None)

    def setStamp(self,phase,x,y):
        if not self.ready:return
        self.clearInterval('bureau-stamp',finish=0)
        self.clearWarning()
        if phase==1:
            self.warning=cylinder(base.render,'stamp-warning',(x,y,.12),G.STAMP_RADIUS,.08,(.9,.18,.06,.55))
            self.warning.setTransparency(TransparencyAttrib.MAlpha)
            self.dizzyAlert.play()
        elif phase==2:
            self.stamp=native(base.render,'phase_5/models/props/rubber-stamp',(x,y,20),height=18,pitch=90)
            self.hitSfx.play()
            seq=Sequence(self.stamp.posInterval(.18,Point3(x,y,.2)),Wait(.35),Func(self.clearWarning))
            self.storeInterval(seq,'bureau-stamp');seq.start()

    def enterVictory(self):
        self.progress['value']=0
        self.banner['text']='REJECTED! The Director General has been overruled.'
        self.toMovieMode();self.play('Fb_fall');self.deathSfx.play()
        self.stagePause('Victory',7)

    def exitVictory(self):
        self.clearInterval('bureau-stage')

    def enterEpilogue(self):
        self.banner['text']='Review complete. Returning to Ministry Plaza...'

    def returnToPlaza(self):
        place=self.cr.playGame.getPlace()
        if not place or not self.hasLocalToon():return
        place.fsm.request('teleportOut',[{'loader':'safeZoneLoader','where':'playground',
            'how':'teleportIn','zoneId':G.HOOD,'hoodId':G.HOOD,'shardId':None,'avId':-1,'battle':1}])

    def disable(self):
        global OneBossCog
        self.ready=False
        # Pause before destroying nodes; finishing a cinematic here would fire
        # stale barrier/teleport callbacks while changing zones.
        for name in list(self.activeIntervals):self.clearInterval(name,finish=0)
        for name in ('bureau-arrival-wait','bureau-hud'):base.taskMgr.remove(self.uniqueName(name))
        self.clearWarning()
        for prop in self.paperProps.values():prop.removeNode()
        self.paperProps.clear()
        for item in self.hud:item.destroy()
        self.hud=[]
        if hasattr(self,'buttonArt'):self.buttonArt.removeNode()
        if hasattr(self,'battleOrigin'):self.battleOrigin.removeNode()
        for name in ('elevatorMusic','battleOneMusic','battleThreeMusic','epilogueMusic'):
            if hasattr(self,name):getattr(self,name).stop()
        if OneBossCog is self:OneBossCog=None
        DistributedBossCog.disable(self)
