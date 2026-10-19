"""Campus routing, native patrol assets and real geometry regression checks."""
import re,unittest,math,ast,sys,random
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from panda3d.core import (loadPrcFileData,CollisionNode,CollisionSphere,CollisionRay,CollisionSegment,
    CollisionHandlerQueue,CollisionTraverser,BitMask32,Point3)
loadPrcFileData('', 'window-type none\naudio-library-name null\nmodel-path resources\ndefault-model-extension .bam')
from direct.showbase.ShowBase import ShowBase
from toontown.expansion import BureauHQGlobals as H,ExpansionGlobals as E
from toontown.expansion.ExpansionScene import build_scene
from toontown.suit.BureaubotGlobals import street_weights
from tools.author_bureau_hq_patrols import generate


def production_method(path,class_name,name,namespace):
    tree=ast.parse(Path(path).read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==class_name)
    method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module(body=[method],type_ignores=[]),path,'exec'),namespace)
    return namespace[name]


class CampusManifestTests(unittest.TestCase):
    def test_links_and_static_reservations(self):
        self.assertEqual(E.connections(H.MINISTRY),(H.ENTRY,H.ARCHIVES,H.WORKS))
        for zone in H.ZONES:
            self.assertEqual(E.hood_id(zone),H.MINISTRY)
            self.assertIn(zone,E.BATTLE_ZONES)
            self.assertNotIn(zone,E.SERVICE_ZONES)
            self.assertNotIn(zone,E.SERVICE_INTERIORS)
            for target in E.connections(zone):self.assertIn(zone,E.connections(target))
            self.assertEqual(len(E.connections(zone)),len(E.gate_transforms(zone)))
        self.assertTrue(Path('resources',H.SPEC['music']).exists())

    def test_high_level_bureau_only_population(self):
        for row in H.planner_rows():
            self.assertEqual(street_weights(row[8]),(0,0,0,0,100))
            self.assertEqual(row[9],(8,9,10))
            self.assertEqual(row[1:3],[18,24])
            self.assertEqual(row[3:6],[0,0,0])

    def test_committed_patrol_graphs_are_reproducible_and_connected(self):
        for zone in H.ZONES:
            text=Path(H.dna_path(zone)).read_text()
            self.assertEqual(text,generate(zone))
            points={int(i) for i in re.findall(r'store_suit_point \[ (\d+)',text)}
            edges=[tuple(map(int,e)) for e in re.findall(r'suit_edge \[ (\d+) (\d+) \]',text)]
            reached={0}
            while True:
                new=reached|{b for a,b in edges if a in reached}
                if new==reached:break
                reached=new
            self.assertEqual(reached,points)
            self.assertEqual(text.count('battle_cell'),4)


class CampusIntegrationTests(unittest.TestCase):
    def test_server_registers_three_native_planners(self):
        class Planner:
            def __init__(self,air,zone):self.zoneId=zone;self.events=[]
            def generateWithRequired(self,zone):self.events.append(('generate',zone))
            def d_setZoneId(self,zone):self.events.append(('zone',zone))
            def initTasks(self):self.events.append(('tasks',))
        startup=production_method('toontown/expansion/BureauHQDataAI.py','BureauHQDataAI','startup',{'H':H})
        air=SimpleNamespace(dnaStoreMap={},dnaDataMap={},suitPlanners={},loadDNAFileAI=lambda store,path:path)
        entrance=[]
        hood=SimpleNamespace(air=air,suitPlanners=[],createBossEntrance=lambda:entrance.append(True))
        modules={'panda3d.toontown':SimpleNamespace(DNAStorage=object),
                 'toontown.suit.DistributedSuitPlannerAI':SimpleNamespace(DistributedSuitPlannerAI=Planner)}
        with patch.dict(sys.modules,modules):startup(hood)
        self.assertEqual(set(air.suitPlanners),H.ZONES)
        self.assertEqual(entrance,[True])
        self.assertEqual(set(air.dnaStoreMap),H.ZONES)
        for zone,planner in air.suitPlanners.items():
            self.assertEqual(air.dnaDataMap[zone],H.dna_path(zone))
            self.assertEqual(planner.events,[('generate',zone),('zone',zone),('tasks',)])

    def test_hq_ignores_global_invasion_and_default_suit(self):
        from toontown.suit import SuitDNA
        fromSky=SimpleNamespace(fromSky=1)
        chosen=[];invasions=[]
        class Suit:
            def __init__(self,*args):self.flyInSuit=0;self.buildingSuit=0
            def setupSuitDNA(self,*args):chosen.append(args)
            def delete(self):pass
        namespace={'random':random,'SuitTimings':fromSky,'SuitDNA':SuitDNA,
                   'DistributedSuitAI':SimpleNamespace(DistributedSuitAI=Suit),
                   'simbase':SimpleNamespace(air=None)}
        create=production_method('toontown/suit/DistributedSuitPlannerAI.py','DistributedSuitPlannerAI','createNewSuit',namespace)
        notify=SimpleNamespace(getDebug=lambda:False,debug=lambda *a:None)
        sp=SimpleNamespace(notify=notify,defaultSuitName='f',pointCollision=lambda *a:False,
            newSuitShouldAttemptTakeover=lambda:False,chooseDestination=lambda *a,**k:False,
            pickLevelTypeAndTrack=lambda level,kind,track:(level,kind,track),
            air=SimpleNamespace(suitInvasionManager=SimpleNamespace(
                getInvadingCog=lambda:(invasions.append(True) or ('f',False)))))
        for zone in sorted(H.ZONES):
            sp.zoneId=zone
            create(sp,[],[object()])
        self.assertEqual(invasions,[])
        self.assertEqual(chosen,[(None,None,None)]*3)  # Native picker gets HQ weights.
        sp.zoneId=2100;create(sp,[],[object()])
        self.assertEqual(len(invasions),1)
        self.assertEqual(chosen[-1][2],'c')

    def test_defeat_returns_to_safe_acorn_playground(self):
        from test_expansion import load_zone_functions
        ns={'ExpansionGlobals':E,'HQToSafezone':{}}
        tree=ast.parse(Path('toontown/toonbase/ToontownGlobals.py').read_text())
        statement=next(n for n in tree.body if isinstance(n,ast.Assign) and
            isinstance(n.targets[0],ast.Subscript) and isinstance(n.targets[0].value,ast.Name) and
            n.targets[0].value.id=='HQToSafezone')
        exec(compile(ast.Module(body=[statement],type_ignores=[]),'HQ-safezone','exec'),ns)
        functions=load_zone_functions();functions['HQToSafezone']=ns['HQToSafezone']
        for zone in H.ZONES:self.assertEqual(functions['getSafeZoneId'](zone),H.ENTRY)


class CampusGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=ShowBase()
    @classmethod
    def tearDownClass(cls):cls.app.destroy()

    def assert_walkable(self,scene,x,y,radius=1.2,allow_tunnel_trigger=False):
        for mask,solid in ((1,CollisionSphere(x,y,3,radius)),(2,CollisionRay(x,y,20,0,0,-1))):
            node=CollisionNode('campus-probe');node.setFromCollideMask(BitMask32(mask));node.setIntoCollideMask(BitMask32.allOff());node.addSolid(solid)
            probe=scene.attachNewNode(node);queue=CollisionHandlerQueue();trav=CollisionTraverser()
            trav.addCollider(probe,queue);trav.traverse(scene)
            hits=[queue.getEntry(i).getIntoNodePath().getName() for i in range(queue.getNumEntries())]
            if mask==1 and allow_tunnel_trigger:
                # A path terminating at a native Cog gateway should intersect
                # its travel event volume, while still clearing physical walls.
                hits=[hit for hit in hits if not hit.startswith('tunnel_trigger')]
            if mask==1:self.assertEqual(hits,[],(x,y,hits))
            else:
                self.assertGreater(len(hits),0,(x,y))
                queue.sortEntries();self.assertLess(abs(queue.getEntry(0).getSurfacePoint(scene).z),.2)
            probe.removeNode()

    def test_spawns_arrivals_and_native_tunnel_nodes(self):
        for zone in H.ZONES:
            scene=build_scene(zone)
            try:
                self.assert_walkable(scene,*E.spawn_point(zone)[:2])
                for target in H.LINKS[zone]:
                    gate=scene.find('**/linktunnel*_%s'%target)
                    self.assertFalse(gate.isEmpty())
                    self.assertFalse(gate.find('**/tunnel_trigger').isEmpty())
                    self.assertLess(gate.find('**/tunnel_origin').getPos(gate).length(),.001)
                    p=scene.getRelativePoint(gate,Point3(0,8,0))
                    self.assert_walkable(scene,p.x,p.y)
            finally:scene.removeNode()

    def test_patrol_and_battle_clearance(self):
        for zone in H.ZONES:
            scene=build_scene(zone)
            try:
                for route in H.patrol_paths(zone):
                    for a,b in zip(route,route[1:]+route[:1]):
                        count=max(1,math.ceil(math.dist(a,b)/8))
                        for i in range(count):self.assert_walkable(scene,a[0]+(b[0]-a[0])*i/count,a[1]+(b[1]-a[1])*i/count,3)
                for x,y in H.BATTLE_PADS[zone]:self.assert_walkable(scene,x,y,18)
                # Validate every generated edge, including any connecting paths.
                text=generate(zone)
                vertices={int(i):(float(x),float(y)) for i,x,y in re.findall(
                    r'store_suit_point \[ (\d+), STREET_POINT, ([\d.-]+) ([\d.-]+)',text)}
                for a,b in re.findall(r'suit_edge \[ (\d+) (\d+) \]',text):
                    p,q=vertices[int(a)],vertices[int(b)]
                    for t in (0,.5,1):self.assert_walkable(scene,p[0]+(q[0]-p[0])*t,p[1]+(q[1]-p[1])*t,3)
            finally:scene.removeNode()

    def test_native_hooks_register_travel_and_return_origins(self):
        from test_expansion import load_zone_functions
        routing=SimpleNamespace(**load_zone_functions())
        namespace={'render':self.app.render,'base':SimpleNamespace(localAvatar=SimpleNamespace(
            cr=SimpleNamespace(playGame=SimpleNamespace(hood=None)))),
            'ZoneUtil':routing,'ToontownGlobals':SimpleNamespace(WallBitmask=BitMask32(1),GhostBitmask=BitMask32(8))}
        hook=production_method('toontown/distributed/HoodMgr.py','HoodMgr','addLinkTunnelHooks',namespace)
        ids={s['short']:h for h,s in E.HOOD_SPECS.items()}
        manager=SimpleNamespace(getIdFromName=ids.__getitem__)
        for zone in H.ZONES|{H.ENTRY}:
            scene=build_scene(zone);scene.reparentTo(self.app.render);events=[]
            part=SimpleNamespace(accept=lambda event,callback,args:events.append((event,args[0])),handleEnterTunnel=None)
            origins=hook(manager,part,[scene],zone)
            try:
                self.assertEqual({status['zoneId'] for _,status in events},set(E.connections(zone)))
                for event,status in events:
                    target=status['zoneId']
                    self.assertTrue(event.startswith('entertunnel_trigger_'))
                    self.assertEqual(status['loader'],'safeZoneLoader')
                    self.assertEqual(status['where'],'playground')
                    self.assertEqual(status['hoodId'],E.hood_id(target))
                    self.assertEqual(status['how'],'tunnelIn')
                    self.assertFalse(status['tunnelOrigin'].isEmpty())
            finally:
                for origin in origins:origin.removeNode()
                scene.removeNode()

    def test_acorn_gateway_is_hooked_and_approach_is_clear(self):
        scene=build_scene(H.ENTRY)
        try:
            gate=scene.find('**/19000:woodland/**/linktunnel_bureau_14000')
            self.assertFalse(gate.isEmpty())
            # Check the usable doorway width through the native travel trigger,
            # not just the single line that missed the old fence/shop overlap.
            for x in range(50,129,3):
                for y in (15,20,25):
                    self.assert_walkable(scene,x,y,allow_tunnel_trigger=True)
            # Some decorative native models have incomplete collision meshes.
            # Their visible bounds must also clear the entire Cog gateway.
            world=gate.getParent();lo,hi=gate.getTightBounds(scene)
            scenery=list(world.getChildren())+[
                node for node in world.getParent().getChildren() if node!=world]
            for node in scenery:
                if node==gate or node.getName()=='sculpted-village-ground':continue
                bounds=node.getTightBounds(scene)
                if bounds is None:continue
                a,b=bounds
                overlaps=(a.x<hi.x and b.x>lo.x and a.y<hi.y and b.y>lo.y)
                self.assertFalse(overlaps,'Scenery overlaps Cog gateway: '+node.getName())
        finally:scene.removeNode()

    def test_exploration_routes_avoid_native_props(self):
        for zone in H.ZONES:
            scene=build_scene(zone)
            try:
                for sample in scene.findAllMatches('**/exploration-route/walk-sample-*'):
                    point=sample.getPos(scene)
                    with self.subTest(zone=zone,x=point.x,y=point.y):
                        self.assert_walkable(scene,point.x,point.y,allow_tunnel_trigger=True)
                sources={n.getTag('source-model') for n in scene.findAllMatches('**/=source-model')}
                self.assertGreaterEqual(len(sources),8)
            finally:scene.removeNode()

    def test_dark_paving_and_dressed_outskirts_in_every_zone(self):
        for zone in H.ZONES:
            scene=build_scene(zone)
            try:
                textures={texture.getFilename().getBasename() for texture in scene.findAllTextures()}
                self.assertIn('FootFactoryFloor.jpg',textures)
                self.assertNotIn('sidewalk_4cont_brown.jpg',textures)
                outskirts=scene.find('**/layered-industrial-outskirts')
                self.assertFalse(outskirts.isEmpty())
                native=list(outskirts.findAllMatches('**/=source-model'))
                # Background scenery exists on both sides and behind arrival.
                for sx,sy in ((-1,-1),(-1,1),(1,-1),(1,1)):
                    self.assertTrue(any(n.getX(scene)*sx>200 and n.getY(scene)*sy>100 for n in native))
            finally:scene.removeNode()

    def test_ministry_has_staggered_exits_and_real_court_dividers(self):
        scene=build_scene(H.MINISTRY)
        try:
            self.assertGreaterEqual(len(scene.findAllMatches('**/=layout-role=court-divider')),12)
            self.assertGreater(abs(H.GATES[H.MINISTRY][1][1]-H.GATES[H.MINISTRY][2][1]),90)
            self.assertFalse(scene.find('**/ministry-irregular-footprint').isEmpty())
            self.assertTrue(scene.find('**/continuous-courtyard-ground').isEmpty())
            self.assertGreaterEqual(len(H.PATROLS[H.MINISTRY]),15)
        finally:scene.removeNode()

    def test_landmarks_visible_from_arrival(self):
        # These view rays must reach the landmark without hitting foreground
        # buildings. Only the final 22 units may intersect the focal building.
        targets=((H.MINISTRY,(29,143,53)),(H.ARCHIVES,(-68,118,85)),(H.WORKS,(103,108,75)),
                 (H.MINISTRY,(28,139,12)),(H.ARCHIVES,(-66,124,12)),(H.WORKS,(95,83,12)))
        for zone,target in targets:
            scene=build_scene(zone)
            start=Point3(*H.SPAWNS[zone][:2],10);end=Point3(*target)
            node=CollisionNode('landmark-sightline');node.setFromCollideMask(BitMask32(1))
            node.setIntoCollideMask(BitMask32.allOff());node.addSolid(CollisionSegment(start,end))
            probe=scene.attachNewNode(node);queue=CollisionHandlerQueue();trav=CollisionTraverser()
            trav.addCollider(probe,queue);trav.traverse(scene)
            try:
                for i in range(queue.getNumEntries()):
                    hit=queue.getEntry(i)
                    self.assertLess((hit.getSurfacePoint(scene)-end).length(),22,
                                    (zone,str(hit.getIntoNodePath())))
            finally:scene.removeNode()

    def test_display_buildings_have_no_nameplates(self):
        for zone in H.ZONES:
            scene=build_scene(zone)
            try:
                for building in list(scene.findAllMatches('**/=architecture'))+list(scene.findAllMatches('**/inspection-station')):
                    self.assertTrue(building.find('**/+TextNode').isEmpty(),str(building))
                if zone==H.MINISTRY:
                    self.assertFalse(scene.find('**/bureau-boss-elevator-locator').isEmpty())
                    self.assertEqual(len(scene.findAllMatches('**/boss-group-pad')),8)
                else:
                    self.assertFalse(scene.find('**/closed-facility').isEmpty())
            finally:scene.removeNode()

    def test_machine_approaches_and_state_lifecycle(self):
        from toontown.expansion.BureauHQInteractions import BureauHQInteractions,SOUNDS
        for path in SOUNDS.values():self.assertTrue(Path('resources',path).exists())
        avatar=self.app.render.attachNewNode('interaction-test-toon')
        self.app.localAvatar=avatar
        state=SimpleNamespace(name='walk');state.getName=lambda:state.name
        place=SimpleNamespace(fsm=SimpleNamespace(getCurrentState=lambda:state))
        task=SimpleNamespace(cont='cont',done='done')
        try:
            for zone in H.ZONES:
                scene=build_scene(zone);scene.reparentTo(self.app.render)
                controller=BureauHQInteractions(self.app,place,scene)
                try:
                    self.assertEqual(len(controller.machines),2)
                    for machine in controller.machines:
                        point=machine.find('use-point').getPos(scene)
                        self.assert_walkable(scene,point.x,point.y,radius=2)
                        avatar.setPos(scene,point);state.name='walk';controller.readyAt=0
                        controller.update(task)
                        self.assertFalse(controller.button.isHidden())
                        self.assertTrue(controller.use())
                        self.assertFalse(controller.use())  # Prevent click spam.
                        motion=machine.getPythonTag('action-node')
                        controller.running.setT(.8)
                        self.assertNotEqual(motion.getTransform(),controller.originals[machine])
                        state.name='battle';controller.update(task)
                        self.assertTrue(controller.button.isHidden())
                        self.assertEqual(motion.getTransform(),controller.originals[machine])
                        self.assertFalse(controller.use())
                        state.name='walk';controller.readyAt=0
                        avatar.setPos(scene,point+Point3(50,0,0))
                        self.assertFalse(controller.use())
                    name=controller.taskName
                    controller.destroy();controller.destroy()
                    self.assertFalse(self.app.taskMgr.hasTaskNamed(name))
                    self.assertEqual(controller.ambient,[])
                finally:controller.destroy();scene.removeNode()
        finally:avatar.removeNode();del self.app.localAvatar


if __name__=='__main__':unittest.main()
