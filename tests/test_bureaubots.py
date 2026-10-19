"""Model regressions runnable without the OTP-enabled game runtime."""
import math
import unittest
from panda3d.core import GeomVertexReader, loadPrcFileData

loadPrcFileData('', 'window-type none\naudio-library-name null\n'
    'model-path resources\ndefault-model-extension .bam')
from direct.showbase.ShowBase import ShowBase
from toontown.suit import BureaubotModels as B


class BureaubotModelsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ShowBase()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def test_heads_have_valid_geometry(self):
        self.assertEqual(len({entry[0] for entry in B.CATALOG}),8)
        for key,_,_,_ in B.CATALOG:
            with self.subTest(key=key):
                head = B.build_head(key)
                low,high = head.getTightBounds()
                self.assertGreater(high.z-low.z,1)
                self.assertGreater(high.y-low.y,.5)
                for mesh in head.findAllMatches('**/+GeomNode'):
                    for i in range(mesh.node().getNumGeoms()):
                        geom = mesh.node().getGeom(i)
                        vertices = GeomVertexReader(geom.getVertexData(),'vertex')
                        while not vertices.isAtEnd():
                            self.assertTrue(all(math.isfinite(v) for v in vertices.getData3()))
                        self.assertGreater(geom.getPrimitive(0).getNumPrimitives(),0)
                head.removeNode()

    def test_original_rigs_bind_both_animations_and_move_heads(self):
        for key,name,_,_ in B.CATALOG:
            with self.subTest(key=key):
                actor = B.make_actor(key,self.app.loader)
                try:
                    self.assertEqual(actor.getName(),name)
                    self.assertTrue(actor.getAnimControl('neutral'))
                    self.assertTrue(actor.getAnimControl('walk'))
                    self.assertFalse(actor.find('**/'+key+'-head').isEmpty())
                    self.assertFalse(actor.find('**/bureaubot-emblem').isEmpty())
                    actor.stop()
                    for anim in ('neutral','walk'):
                        actor.pose(anim,0)
                        actor.update(force=True)
                        head = actor.find('**/'+key+'-head')
                        first = head.getMat(actor)
                        actor.pose(anim,actor.getNumFrames(anim)//2)
                        actor.update(force=True)
                        self.assertFalse(first.almostEqual(head.getMat(actor),.00001))
                        low,high = actor.getTightBounds()
                        self.assertGreater(high.z-low.z,4)
                finally:
                    actor.cleanup()
                    actor.removeNode()

    def test_unknown_models_fail_clearly(self):
        with self.assertRaises(ValueError):
            B.build_head('missing')
        with self.assertRaises(ValueError):
            B.make_actor('missing',self.app.loader)



class LiveSuitMethodsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import ast
        from types import SimpleNamespace
        from direct.actor import Actor
        from panda3d.core import ConfigVariableBool, VBase4
        from test_bureaubot_integration import ROOT, production_methods, battle_catalog
        from toontown.suit import SuitDNA, BureaubotGlobals as BG
        cls.app=ShowBase()
        ns={'BureaubotGlobals':BG,'BureaubotModels':B,'SuitDNA':SuitDNA,
            'SuitBattleGlobals':battle_catalog(),'VBase4':VBase4,'Actor':Actor,
            'ConfigVariableBool':ConfigVariableBool,'loader':cls.app.loader}
        tree=ast.parse((ROOT/'toontown/suit/Suit.py').read_text())
        for node in tree.body:
            if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name):
                name=node.targets[0].id
                if name.startswith('AllSuits') or name=='SuitsCEOBattle':
                    ns[name]=ast.literal_eval(node.value)
        ns['TutorialModelDict']={b:('/models/char/suit'+b.upper()+'-',3.5 if b=='c' else 4) for b in 'abc'}
        methods=production_methods('toontown/suit/Suit.py','Suit',
            ['generateSuit','generateBody','generateAnimDict','setSuitClothes',
             'generateCorporateMedallion','getLoseActor','generateCorporateTie'],ns)
        methods['setHeight']=lambda self,height:setattr(self,'height',height)
        methods['generateHealthBar']=lambda self:None  # OTP-dependent meter is unchanged.
        cls.SuitHarness=type('SuitHarness',(Actor.Actor,),methods)
        cls.BG=BG;cls.SuitDNA=SuitDNA

    @classmethod
    def tearDownClass(cls):cls.app.destroy()

    def test_live_heads_chests_attacks_and_defeat_rigs(self):
        from panda3d.core import ConfigVariableBool
        config=ConfigVariableBool('want-new-cogs',False)
        original=config.value
        try:
            for newCogs in (False,True):
                config.setValue(newCogs)
                for code in self.BG.CODES:
                    with self.subTest(code=code,newCogs=newCogs):
                        suit=self.SuitHarness()
                        suit.style=self.SuitDNA.SuitDNA();suit.style.newSuit(code)
                        suit.isWaiter=False
                        try:
                            suit.generateSuit()
                            self.assertGreater(suit.height,4)
                            self.assertEqual(suit.corpMedallion.getParent().getName(),'joint_attachMeter')
                            for name,_,_ in self.BG.ANIMATIONS[suit.style.body]:
                                self.assertIsNotNone(suit.getAnimControl(name),name)
                                suit.pose(name,1);suit.update(force=True)
                            defeated=suit.getLoseActor()
                            self.assertIsNotNone(defeated.getAnimControl('lose'))
                            self.assertFalse(defeated.find('**/'+self.BG.BY_CODE[code][0]+'-head').isEmpty())
                            defeated.cleanup();defeated.removeNode()
                        finally:suit.cleanup();suit.removeNode()
        finally:config.setValue(original)

    def test_takeovers_load_standalone_building_for_every_floor_count(self):
        import ast
        from pathlib import Path
        from types import SimpleNamespace as NS
        from panda3d.core import TextNode,DepthOffsetAttrib,DecalEffect,NodePath
        from toontown.building import BureaubotBuilding
        source=Path('toontown/building/DistributedBuilding.py').read_text()
        cls=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef))
        method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='setupSuitBuilding')
        parent=NodePath('street-zone');original=parent.attachNewNode('toon-shop')
        # A Bureaubot takeover must never request any legacy department model.
        def forbidden_model(name):raise AssertionError('Legacy landmark requested: '+name)
        store=NS(findNode=forbidden_model,getZoneFromBlockNumber=lambda b:2100,
                 getTitleFromBlockNumber=lambda b:'Pending Approval')
        cr=NS(playGame=NS(dnaStore=store,hood=NS(loader=NS(zoneDict={2100:parent}))))
        scope=dict(BureaubotBuilding=BureaubotBuilding,loader=self.app.loader,base=NS(cr=cr),
            ZoneUtil=NS(getTrueZoneId=lambda z,i:z),TextNode=TextNode,
            DepthOffsetAttrib=DepthOffsetAttrib,DecalEffect=DecalEffect,
            TTLocalizer=NS(CogsInc='Cogs, Inc.',CogsIncExt=', Inc.'),
            SuitDNA=NS(getDeptFullname=lambda t:'Bureaubots'),
            ToontownGlobals=NS(getSuitFont=lambda:self.app.loader.loadFont('phase_3/models/fonts/vtRemingtonPortable.ttf')))
        exec(compile(ast.Module(body=[method],type_ignores=[]),'takeover-test','exec'),scope)
        try:
            for difficulty in range(10):
                obj=NS(cr=cr,track=ord('u'),difficulty=difficulty,block=1,interiorZoneId=2101,
                       loadElevator=lambda n:None)
                model=scope['setupSuitBuilding'](obj,original)
                self.assertEqual(model.getTag('department'),'u')
                self.assertFalse(model.find('**/*_door_origin').isEmpty())
                self.assertTrue(model.find('**/*corp*').isEmpty())
                model.removeNode()
        finally:parent.removeNode()

    def test_building_keeps_collision_door_sign_and_elevator(self):
        from toontown.building.BureaubotBuilding import MODEL_PATH,add_elevator_badge
        building=self.app.loader.loadModel(MODEL_PATH)
        try:
            self.assertEqual(1,building.findAllMatches('**/+CollisionNode').getNumPaths())
            self.assertTrue(building.find('**/*corp*').isEmpty())
            self.assertFalse(building.find('**/*_door_origin').isEmpty())
            self.assertFalse(building.find('**/sign_origin').isEmpty())
            self.assertEqual(building.getTag('department'),'u')
            self.assertFalse(building.find('**/bureaubot-facade-crest').isEmpty())
            self.assertTrue(building.find('**/drawer-panel').isEmpty())
            self.assertTrue(building.find('**/suit_landmark_new_corp_building').isEmpty())
            self.assertFalse(building.find('**/clip-crown').isEmpty())
            self.assertEqual(building.findAllMatches('**/clip-upright').getNumPaths(),2)
            self.assertEqual(building.find('**/+CollisionNode').node().getNumSolids(),7)
            self.assertEqual(building.find('**/+CollisionNode').node().getIntoCollideMask().getWord(),5)
            self.assertGreater(building.find('**/*_building').findAllTextures().getNumTextures(),0)
            elevator=self.app.loader.loadModel('phase_4/models/modules/elevator')
            elevator.reparentTo(building.find('**/*_door_origin'))
            self.assertFalse(add_elevator_badge(elevator).isEmpty())
            self.assertFalse(elevator.find('**/left-door').isEmpty())
            self.assertFalse(elevator.find('**/right-door').isEmpty())
        finally:building.removeNode()


if __name__=='__main__':
    unittest.main()
