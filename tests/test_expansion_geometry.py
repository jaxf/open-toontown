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
                ray=CollisionNode('spawn-floor-probe')
                ray.setFromCollideMask(BitMask32.bit(1))
                ray.setIntoCollideMask(BitMask32.allOff())
                ray.addSolid(CollisionRay(0,-18,50,0,0,-1))
                probe=scene.attachNewNode(ray)
                queue=CollisionHandlerQueue()
                traverser=CollisionTraverser()
                traverser.addCollider(probe,queue)
                traverser.traverse(scene)
                self.assertGreater(queue.getNumEntries(),0)
                queue.sortEntries()
                self.assertAlmostEqual(queue.getEntry(0).getSurfacePoint(scene).z,.03,places=2)
                scene.removeNode()

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
