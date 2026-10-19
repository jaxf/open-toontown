"""Encounter rules, native battle adapter, wire schema and real collision art."""
import ast
import math
import random
import unittest
from pathlib import Path
from types import SimpleNamespace, MethodType
from unittest.mock import Mock
from direct.fsm.FSM import FSM
from panda3d.core import (loadPrcFileData,Point3,CollisionNode,CollisionSphere,
    CollisionHandlerQueue,CollisionTraverser,BitMask32)
from panda3d.direct import DCFile
from toontown.expansion import BureauBossGlobals as G

ROOT=Path(__file__).resolve().parents[1]


def method(file,cls,name,namespace):
    tree=ast.parse((ROOT/file).read_text())
    c=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls)
    m=next(n for n in c.body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module(body=[m],type_ignores=[]),file,'exec'),namespace)
    return namespace[name]


class PaperworkTests(unittest.TestCase):
    def fill(self,game,now):
        for side in range(2):
            for i in range(3):
                self.assertTrue(game.use(1,side,G.STATIONS[side],now));now+=1
                self.assertTrue(game.use(1,2+side,G.STATIONS[2+side],now));now+=1
        return now

    def test_four_consistent_cycles_win_and_cannot_replay(self):
        p=G.PaperworkCycle();now=0
        for cycle in range(4):
            now=self.fill(p,now)
            self.assertTrue(p.use(1,4,G.STATIONS[4],now));now+=1
            self.assertEqual(p.damage,25*(cycle+1))
            self.assertFalse(p.use(2,4,G.STATIONS[4],now))
        self.assertFalse(p.use(2,0,G.STATIONS[0],now))

    def test_cannot_feed_without_form_or_use_from_distance(self):
        p=G.PaperworkCycle()
        for station in range(5):self.assertFalse(p.use(1,station,(0,-500,0),0))
        self.assertFalse(p.use(1,0,(math.nan,0,0),0))
        self.assertFalse(p.use(1,2,G.STATIONS[2],0))
        self.assertTrue(p.use(1,0,G.STATIONS[0],0))
        self.assertFalse(p.use(1,1,G.STATIONS[1],1))
        self.assertFalse(p.use(1,2,G.STATIONS[2],.9))
        self.assertTrue(p.use(1,2,G.STATIONS[2],1))

    def test_expiry_and_disconnect_release_state(self):
        p=G.PaperworkCycle();now=self.fill(p,0)
        self.assertFalse(p.use(1,4,G.STATIONS[4],now+G.EXPOSE_SECONDS))
        self.assertEqual(p.loads,[0,0]);self.assertEqual(p.damage,0)
        self.assertTrue(p.use(9,0,G.STATIONS[0],100))
        p.remove(9);self.assertNotIn(9,p.carrying);self.assertNotIn(9,p.last_use)

    def test_rosters_vary_within_native_level_ranges(self):
        rosters=set()
        for seed in range(30):
            for wave in (1,2):
                roster=G.wave_roster(random.Random(seed),wave,4)
                rosters.add(tuple(roster))
                for rank,level,skel in roster:
                    self.assertTrue(8<=level<=11)
                    self.assertTrue(rank-1<=level<=rank+3)
                    self.assertEqual(skel,wave==2)
        self.assertGreater(len(rosters),30)


class AdapterTests(unittest.TestCase):
    def test_server_rejects_nonparticipants_dead_wrong_zone_and_wrong_stage(self):
        use=method('toontown/suit/DistributedBureauBossAI.py','DistributedBureauBossAI',
                   'requestUseStation',{'G':G})
        valid=method('toontown/suit/DistributedBureauBossAI.py','DistributedBureauBossAI',
                     'validToon',{})
        toon=SimpleNamespace(zoneId=90001,getHp=lambda:100,getPos=lambda:Point3(*G.STATIONS[0]))
        boss=SimpleNamespace(state='BattleThree',zoneId=90001,involvedToons=[1],joined={1},
            paperwork=G.PaperworkCycle(),now=lambda:0,publishPaperwork=Mock(),sendUpdate=Mock(),b_setState=Mock())
        boss.air=SimpleNamespace(getAvatarIdFromSender=lambda:1,doId2do={1:toon})
        boss.validToon=MethodType(valid,boss)
        for change in ('state','joined','zone','dead'):
            boss.state='Introduction' if change=='state' else 'BattleThree'
            boss.joined=set() if change=='joined' else {1}
            toon.zoneId=90002 if change=='zone' else 90001
            toon.getHp=lambda:0 if change=='dead' else 100
            use(boss,0)
            self.assertFalse(boss.paperwork.carrying)
        boss.state='BattleThree';boss.joined={1};toon.zoneId=90001;toon.getHp=lambda:100
        use(boss,0);self.assertEqual(boss.paperwork.carrying,{1})

    def test_native_team_initializer_builds_two_battles_and_skeleton_second_wave(self):
        class Suit:
            def __init__(self,*a):pass
            def setLevel(self,v):self.level=v
            def setSkelecog(self,v):self.skeleton=v
            def generateWithRequired(self,z):self.zone=z
        class DNA:
            def newSuit(self,name):self.name=name
        from toontown.suit.BureaubotGlobals import CODES
        gen=method('toontown/suit/DistributedBureauBossAI.py','DistributedBureauBossAI','generateSuits',
                   {'G':G,'SuitDNA':DNA,'DistributedSuitAI':Suit,'CODES':CODES})
        globals_=SimpleNamespace(BossCogBattleAPosHpr=(0,-25,0,0,0,0),BossCogBattleBPosHpr=(0,25,0,180,0,0))
        init=method('toontown/suit/DistributedBossCogAI.py','DistributedBossCogAI','initializeBattles',
                    {'ToontownGlobals':globals_})
        for count in (1,4,8):
            ids=list(range(1,count+1))
            boss=SimpleNamespace(involvedToons=ids,toonsA=ids[:4],toonsB=ids[4:],
                zoneId=90001,air=None,rng=random.Random(1),resetBattles=lambda:None,
                handleRoundADone=None,handleRoundBDone=None,handleBattleADone=None,handleBattleBDone=None,
                sendBattleIds=Mock(),moveSuits=Mock(),b_setArenaSide=Mock(),arenaSide=None,
                makeBattle=Mock(return_value=SimpleNamespace(doId=42)))
            boss.generateSuits=MethodType(gen,boss)
            for wave in (1,2):
                boss._generating_second=False;init(boss,wave,G.BATTLE_ORIGIN)
                for suit in boss.suitsA+boss.suitsB+[s for s,_ in boss.reserveSuits]:
                    self.assertEqual(suit.skeleton,int(wave==2));self.assertTrue(9<=suit.level<=12)
                self.assertEqual(bool(boss.suitsB),count>4)

    def test_native_stage_callbacks_wait_for_both_teams(self):
        callback=method('toontown/suit/DistributedBossCogAI.py','DistributedBossCogAI',
                        'handleBattleADone',{})
        boss=SimpleNamespace(battleA=SimpleNamespace(requestDelete=Mock()),battleB=object(),
            arenaSide=0,sendBattleIds=Mock(),hasToons=lambda:True,hasToonsAlive=lambda:True,
            postBattleState='PrepareBattleTwo',b_setState=Mock())
        callback(boss,90001,[1,2,3,4]);boss.b_setState.assert_not_called()
        boss.battleB=None;callback(boss,90001,[1,2,3,4])
        boss.b_setState.assert_called_once_with('PrepareBattleTwo')

    def test_dynamic_instance_cleanup_is_idempotent(self):
        destroyed=[]
        parent=SimpleNamespace(destroyBossOffice=lambda owner,boss:destroyed.append(boss.zoneId))
        destroy=method('toontown/expansion/BureauBossLobbyAI.py','BureauBossLobbyAI',
                       'destroyBossOffice',{'LobbyManagerAI':parent})
        boss=SimpleNamespace(zoneId=90001,uniqueName=lambda n:n)
        lobby=SimpleNamespace(instances={90001:boss},ignore=Mock())
        destroy(lobby,boss);destroy(lobby,boss)
        self.assertEqual(destroyed,[90001]);self.assertFalse(lobby.instances)

    def test_wire_schema_and_elevator_routing(self):
        dc=DCFile();self.assertTrue(dc.read(str(ROOT/'etc/otp.dc')))
        self.assertTrue(dc.read(str(ROOT/'etc/toon.dc')))
        for name in ('BureauBossLobby','DistributedBureauBossElevator','DistributedBureauBoss'):
            self.assertIsNotNone(dc.getClassByName(name))
        sender=SimpleNamespace(send=Mock())
        handler=method('toontown/expansion/ExpansionHood.py','ExpansionStreet',
                       'handleElevatorDone',{'messenger':sender})
        place=SimpleNamespace(doneEvent='done')
        status={'where':'cogHQBossBattle','zoneId':90001,'hoodId':14000}
        handler(place,status)
        self.assertIsNone(place.doneStatus['shardId']);self.assertEqual(place.doneStatus['avId'],-1)
        sender.send.assert_called_once_with('done')


class GeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        loadPrcFileData('','window-type none\naudio-library-name null\nmodel-path resources\ndefault-model-extension .bam')
        from direct.showbase.ShowBase import ShowBase
        cls.app=ShowBase()

    @classmethod
    def tearDownClass(cls):cls.app.destroy()

    def test_station_approaches_and_native_elevator_exist(self):
        from toontown.expansion.BureauBossScene import build_room
        scene=build_room()
        self.assertEqual(len(scene.findAllMatches('**/=boss-station')),5)
        elevator=scene.find('**/bureau-arrival-elevator')
        self.assertFalse(elevator.find('**/left-door').isEmpty())
        for point in G.STATIONS:
            node=CollisionNode('avatar-test');node.setFromCollideMask(BitMask32.bit(0))
            node.setIntoCollideMask(BitMask32.allOff());node.addSolid(CollisionSphere(0,0,2,1))
            probe=scene.attachNewNode(node);probe.setPos(*point)
            queue=CollisionHandlerQueue();trav=CollisionTraverser();trav.addCollider(probe,queue);trav.traverse(scene)
            self.assertEqual(queue.getNumEntries(),0,(point,[str(queue.getEntry(i).getIntoNodePath()) for i in range(queue.getNumEntries())]))
            probe.removeNode()
        scene.removeNode()

    def test_native_animated_boss_has_head_badge_and_two_tracks(self):
        from toontown.suit.BureauBossModel import make_preview
        actor=make_preview(self.app.loader)
        head=actor.find('**/director-filing-head')
        lo,hi=head.getTightBounds(actor)
        self.assertGreater(lo.z,16);self.assertGreater(hi.z,25)
        for name in ('left_tread','right_tread','director-stamp-hand','bureaubot-emblem'):
            self.assertFalse(actor.find('**/'+name).isEmpty(),name)
        actor.pose('Fb_downHit',10);actor.update(force=True)
        self.assertFalse(head.isEmpty())
        actor.cleanup();actor.removeNode()

    def test_all_eight_arrival_seats_clear_cabin_walls(self):
        from toontown.expansion.BureauBossScene import build_room
        scene=build_room();elevator=scene.find('**/bureau-arrival-elevator')
        # The opening points into the room; all eight native seat coordinates
        # remain inside the cabin rather than behind a collision wall.
        self.assertAlmostEqual(elevator.getH(),180)
        for x,y in ((-2.5,9),(2.5,9),(-8,9),(8,9),(-2.5,4),(2.5,4),(-8,4),(8,4)):
            node=CollisionNode('seated-toon');node.setFromCollideMask(BitMask32.bit(0))
            node.setIntoCollideMask(BitMask32.allOff());node.addSolid(CollisionSphere(0,0,2,1))
            probe=elevator.attachNewNode(node);probe.setPos(x,y,.1)
            queue=CollisionHandlerQueue();trav=CollisionTraverser();trav.addCollider(probe,queue);trav.traverse(scene)
            self.assertEqual(queue.getNumEntries(),0,(x,y))
            probe.removeNode()
        scene.removeNode()


if __name__=='__main__':unittest.main()
