"""Real Panda3D geometry/collision checks; requires the resources checkout."""
import unittest
from pathlib import Path
from panda3d.core import (loadPrcFileData, CollisionNode, CollisionRay,
                          CollisionTraverser, CollisionHandlerQueue, BitMask32, CollisionSphere)
loadPrcFileData('', 'window-type none\naudio-library-name null\nmodel-path resources\ndefault-model-extension .bam')
from direct.showbase.ShowBase import ShowBase
from toontown.expansion import ExpansionGlobals as E
from toontown.expansion.ExpansionScene import build_scene


@unittest.skipUnless(Path('resources/phase_4').exists(), 'resources checkout required')
class GeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=ShowBase()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def test_every_zone_builds_with_aligned_tunnels_and_spawn_floor(self):
        for zone in sorted(E.ALL_ZONES):
            with self.subTest(zone=zone):
                scene=build_scene(zone)
                scene.reparentTo(self.app.render)
                gates=scene.findAllMatches('**/linktunnel*')
                self.assertEqual(len(gates),len(E.connections(zone)))
                for gate in gates:
                    origin=gate.find('**/tunnel_origin')
                    trigger=gate.find('**/tunnel_trigger')
                    self.assertFalse(origin.isEmpty())
                    self.assertFalse(trigger.isEmpty())
                    self.assertLess(origin.getPos(gate).length(),.001)
                    self.assertLess(origin.getHpr(gate).length(),.001)
                for target,transform in zip(E.connections(zone),E.gate_transforms(zone)):
                    gate=scene.find('**/linktunnel*_%s'%target)
                    self.assertFalse(gate.isEmpty())
                    self.assertLess((gate.getPos(scene)-type(gate.getPos())(*transform[:3])).length(),.001)
                ray=CollisionNode('spawn-floor-probe')
                ray.setFromCollideMask(BitMask32.bit(1))
                ray.setIntoCollideMask(BitMask32.allOff())
                x,y,z = E.spawn_point(zone)[:3]
                ray.addSolid(CollisionRay(x,y,50,0,0,-1))
                probe=scene.attachNewNode(ray)
                queue=CollisionHandlerQueue()
                traverser=CollisionTraverser()
                traverser.addCollider(probe,queue)
                traverser.traverse(scene)
                self.assertGreater(queue.getNumEntries(),0)
                queue.sortEntries()
                floor_z = queue.getEntry(0).getSurfacePoint(scene).z
                self.assertLessEqual(abs(floor_z),.12)
                self.assertGreater(z,floor_z)
                scene.removeNode()

    def test_authored_walking_routes_and_oak_passage_are_clear(self):
        from tools.build_acorn_models import ROOT_ROUTE, catmull
        samples={19000: [(0,y) for y in range(-100,56,4)]+
                        [(x,20) for x in range(-108,-40,4)],
                 19100: catmull(ROOT_ROUTE,steps=6)}
        for zone,points in samples.items():
            scene=build_scene(zone)
            for x,y in points:
                with self.subTest(zone=zone,x=x,y=y):
                    for mask,solid in ((1,CollisionSphere(x,y,3,1.2)),
                                       (2,CollisionRay(x,y,20,0,0,-1))):
                        node=CollisionNode('walking-probe')
                        node.setFromCollideMask(BitMask32(mask))
                        node.setIntoCollideMask(BitMask32.allOff())
                        node.addSolid(solid)
                        probe=scene.attachNewNode(node)
                        queue=CollisionHandlerQueue()
                        traverser=CollisionTraverser()
                        traverser.addCollider(probe,queue)
                        traverser.traverse(scene)
                        if mask==1:
                            self.assertEqual(queue.getNumEntries(),0,
                                [queue.getEntry(i).getIntoNodePath().getName()
                                 for i in range(queue.getNumEntries())])
                        else:
                            self.assertGreater(queue.getNumEntries(),0)
                        probe.removeNode()
            scene.removeNode()

    def test_both_authored_tunnel_arrivals_have_clear_ground(self):
        from panda3d.core import Point3
        for zone in (19000,19100):
            scene=build_scene(zone)
            for gate in scene.findAllMatches('**/linktunnel*'):
                point=scene.getRelativePoint(gate,Point3(0,5,0))
                for mask,solid in ((1,CollisionSphere(point.x,point.y,point.z+3,1.2)),
                                   (2,CollisionRay(point.x,point.y,point.z+15,0,0,-1))):
                    node=CollisionNode('arrival-check')
                    node.setFromCollideMask(BitMask32(mask))
                    node.setIntoCollideMask(BitMask32.allOff())
                    node.addSolid(solid)
                    probe=scene.attachNewNode(node)
                    queue=CollisionHandlerQueue()
                    traverser=CollisionTraverser()
                    traverser.addCollider(probe,queue)
                    traverser.traverse(scene)
                    if mask==1:
                        self.assertEqual(queue.getNumEntries(),0,gate.getName())
                    else:
                        self.assertGreater(queue.getNumEntries(),0)
                        queue.sortEntries()
                        self.assertLess(abs(queue.getEntry(0).getSurfacePoint(scene).z-point.z),.12)
                    probe.removeNode()
            scene.removeNode()

    def test_custom_models_use_portable_existing_textures(self):
        import zlib
        for filename in Path('assets/acorn/models').glob('*.bam.pz'):
            raw=zlib.decompress(filename.read_bytes())
            self.assertNotIn(b'/workspace/',raw,filename.name)
            self.assertNotIn(b'/root/',raw,filename.name)
            model=self.app.loader.loadModel(str(filename.resolve()))
            for texture in model.findAllTextures():
                self.assertTrue(texture.hasRamImage(),texture.getName())
                for path in (texture.getFilename(),texture.getAlphaFilename()):
                    if not path.empty():
                        self.assertTrue((Path('resources')/path.toOsSpecific()).exists(),str(path))
            model.removeNode()

    def test_original_playground_arrivals_have_ground_and_no_wall(self):
        from math import radians, sin, cos
        models={5000:'phase_8/models/neighborhoods/daisys_garden',
                1000:'phase_6/models/neighborhoods/donalds_dock',
                9000:'phase_8/models/neighborhoods/donalds_dreamland',
                4000:'phase_6/models/neighborhoods/minnies_melody_land',
                8000:'phase_6/models/karting/GasolineAlley_TT'}
        for zone,path in models.items():
            with self.subTest(zone=zone):
                scene=self.app.loader.loadModel(path)
                x,y,z,h=E.SOURCE_GATES[zone]
                x-=sin(radians(h))*5
                y+=cos(radians(h))*5
                for mask,solid in ((2,CollisionRay(x,y,z+50,0,0,-1)),
                                   (1,CollisionSphere(x,y,z+3,1.5))):
                    node=CollisionNode('arrival-probe')
                    node.setFromCollideMask(BitMask32(mask))
                    node.setIntoCollideMask(BitMask32.allOff())
                    node.addSolid(solid)
                    probe=scene.attachNewNode(node)
                    queue=CollisionHandlerQueue()
                    traverser=CollisionTraverser()
                    traverser.addCollider(probe,queue)
                    traverser.traverse(scene)
                    if mask == 2:
                        self.assertGreater(queue.getNumEntries(),0)
                        queue.sortEntries()
                        self.assertLess(abs(queue.getEntry(0).getSurfacePoint(scene).z-z),.1)
                    else:
                        self.assertEqual(queue.getNumEntries(),0)
                    probe.removeNode()
                scene.removeNode()

    def test_declared_audio_and_tunnel_assets_exist(self):
        for spec in E.NEIGHBORHOODS.values():
            self.assertTrue((Path('resources')/spec['music']).is_file())
        self.assertTrue(Path('resources/phase_4/models/modules/safe_zone_tunnel_TT.bam').is_file())


if __name__ == '__main__':
    unittest.main()
