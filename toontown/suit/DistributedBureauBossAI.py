"""Eight-player native battles followed by an authoritative paperwork fight."""
import random
from direct.fsm.FSM import FSM
from direct.task.TaskManagerGlobal import taskMgr
from direct.showbase.MessengerGlobal import messenger
from panda3d.core import ClockObject
from .DistributedBossCogAI import DistributedBossCogAI
from .DistributedSuitAI import DistributedSuitAI
from .SuitDNA import SuitDNA
from .BureaubotGlobals import CODES, DEPT
from toontown.expansion import BureauBossGlobals as G
from toontown.battle import BattleExperienceAI


class DistributedBureauBossAI(DistributedBossCogAI, FSM):
    def __init__(self, air):
        DistributedBossCogAI.__init__(self, air, DEPT)
        FSM.__init__(self, 'DistributedBureauBossAI')
        self.paperwork = G.PaperworkCycle()
        self.roster = set()
        self.joined = set()
        self.rng = random.Random()
        self.rewarded = False
        self.stamp_index = 0
        self.pending_stamp = None
        self.next_stamp = 0

    def getHoodId(self):
        return G.HOOD

    def countDisguises(self):
        # Test entrance is available before the separate suit progression ships.
        return 0, len(self.looseToons) + len(self.involvedToons)

    def setRoster(self, ids):
        self.roster = set(ids)
        for avatar in ids:
            self.addToon(avatar)

    def avatarEnter(self):
        avatar = self.air.getAvatarIdFromSender()
        if avatar in self.roster and avatar in self.involvedToons:
            self.joined.add(avatar)

    def removeToon(self, avatar):
        self.roster.discard(avatar)
        self.joined.discard(avatar)
        self.paperwork.remove(avatar)
        DistributedBossCogAI.removeToon(self, avatar)
        self.sendToonIds()

    def divideToons(self):
        # Keep small testing parties together; larger parties use two teams.
        ids = self.involvedToons[:G.MAX_PLAYERS]
        self.rng.shuffle(ids)
        cut = len(ids) if len(ids) <= 4 else (len(ids)+1)//2
        self.toonsA, self.toonsB = ids[:cut], ids[cut:]
        self.sendToonIds()

    def enterWaitForToons(self):
        self.acceptNewToons()
        self.barrier = self.beginBarrier('WaitForToons', self.involvedToons, 45, self.ready)

    def ready(self, ids):
        # Only clients that actually entered the instance may start it.
        for avatar in self.involvedToons[:]:
            if avatar not in self.joined:
                self.removeToon(avatar)
        if self.involvedToons:
            self.divideToons()
            self.b_setState('Elevator')

    def makeBattleOneBattles(self):
        self.postBattleState = 'PrepareBattleTwo'
        self.initializeBattles(1, G.BATTLE_ORIGIN)

    def generateSuits(self, battleNumber):
        # initializeBattles calls this once per side, including empty sides.
        side = self.toonsA if not getattr(self,'_generating_second',False) else self.toonsB
        self._generating_second = not getattr(self,'_generating_second',False)
        if not side:
            return {'activeSuits': [], 'reserveSuits': []}
        suits=[]
        for rank,level,skeleton in G.wave_roster(self.rng,battleNumber,len(side)):
            suit=DistributedSuitAI(self.air,None)
            suit.dna=SuitDNA();suit.dna.newSuit(CODES[rank-1])
            suit.setLevel(level+1)
            suit.setSkelecog(int(skeleton))
            suit.generateWithRequired(self.zoneId)
            suits.append(suit)
        return {'activeSuits':suits[:4], 'reserveSuits':[(s,0) for s in suits[4:]]}

    def initializeBattles(self, number, origin):
        self._generating_second=False
        DistributedBossCogAI.initializeBattles(self,number,origin)

    def enterPrepareBattleTwo(self):
        self.postBattleState='PrepareBattleThree'
        self.initializeBattles(2,G.BATTLE_ORIGIN)
        self.barrier=self.beginBarrier('PrepareBattleTwo',self.involvedToons,12,
                                        lambda ids:self.b_setState('BattleTwo'))

    def exitPrepareBattleTwo(self):
        self.ignoreBarrier(self.barrier)

    enterBattleTwo = DistributedBossCogAI.enterBattleOne
    exitBattleTwo = DistributedBossCogAI.exitBattleOne

    def enterPrepareBattleThree(self):
        self.resetBattles()
        self.barrier=self.beginBarrier('PrepareBattleThree',self.involvedToons,18,
                                        lambda ids:self.b_setState('BattleThree'))

    def exitPrepareBattleThree(self):
        self.ignoreBarrier(self.barrier)

    def enterBattleThree(self):
        self.next_stamp=self.now()+G.STAMP_INTERVAL
        self.publishPaperwork()
        taskMgr.doMethodLater(.2,self.tick,self.uniqueName('paperwork-tick'))

    def exitBattleThree(self):
        taskMgr.remove(self.uniqueName('paperwork-tick'))
        self.pending_stamp=None
        self.sendUpdate('setStamp',[0,0,0])

    @staticmethod
    def now():
        return ClockObject.getGlobalClock().getFrameTime()

    def validToon(self, avatar):
        toon=self.air.doId2do.get(avatar)
        if (avatar not in self.involvedToons or avatar not in self.joined or
                not toon or toon.getHp()<=0 or toon.zoneId!=self.zoneId):
            return None
        return toon

    def requestUseStation(self, station):
        if self.state!='BattleThree': return
        avatar=self.air.getAvatarIdFromSender()
        toon=self.validToon(avatar)
        if not toon: return
        now=self.now()
        # A late click can arrive before the periodic tick. Broadcast expiry
        # even when that click is rejected, so all clients unlock their sorters.
        if self.paperwork.expire(now):self.publishPaperwork()
        if self.paperwork.use(avatar,station,tuple(toon.getPos()),now):
            self.publishPaperwork()
            self.sendUpdate('stationUsed',[avatar,station])
            if self.paperwork.damage>=G.MAX_DAMAGE:
                self.b_setState('Victory')

    def publishPaperwork(self):
        p=self.paperwork
        self.sendUpdate('setPaperwork',[*p.loads, max(0,int(p.exposed_until-self.now()+.999))
            if p.exposed_until else 0,p.damage,sorted(p.carrying)])

    def tick(self, task):
        now=self.now()
        if self.paperwork.expire(now):self.publishPaperwork()
        if self.pending_stamp and now>=self.pending_stamp[2]:
            x,y,_=self.pending_stamp
            for avatar in self.involvedToons[:]:
                toon=self.validToon(avatar)
                if toon and (toon.getX()-x)**2+(toon.getY()-y)**2<=G.STAMP_RADIUS**2 and toon.getZ()<6:
                    self.damageToon(toon,G.STAMP_DAMAGE)
            self.pending_stamp=None
            self.sendUpdate('setStamp',[2,x,y])
        if now>=self.next_stamp and not self.paperwork.exposed_until:
            x,y=G.STAMP_TARGETS[self.stamp_index%len(G.STAMP_TARGETS)]
            self.stamp_index+=1
            self.pending_stamp=(x,y,now+G.STAMP_WARNING)
            self.next_stamp=now+G.STAMP_INTERVAL
            self.sendUpdate('setStamp',[1,x,y])
        return task.again

    def zapToon(self, *args):
        # This encounter's damage is computed by the server, never the client.
        pass

    def enterVictory(self):
        if not self.rewarded:
            self.rewarded=True
            BattleExperienceAI.assignRewards(self.involvedToons,self.toonSkillPtsGained,
                self.suitsKilled,G.HOOD,self.helpfulToons)
        self.barrier=self.beginBarrier('Victory',self.involvedToons,15,
                                        lambda ids:self.b_setState('Epilogue'))

    def exitVictory(self):
        self.ignoreBarrier(self.barrier)

    def enterEpilogue(self):
        self.sendUpdate('returnToPlaza',[])
        taskMgr.doMethodLater(12,self.finishEncounter,self.uniqueName('bureau-finish'))

    def finishEncounter(self, task):
        messenger.send(self.uniqueName('BossDone'))
        return task.done

    def delete(self):
        for name in ('paperwork-tick','bureau-finish','BossDone'):
            taskMgr.remove(self.uniqueName(name))
        if self.barrier is not None:self.ignoreBarrier(self.barrier)
        self.resetBattles()
        DistributedBossCogAI.delete(self)
