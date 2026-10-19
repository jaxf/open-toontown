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


if __name__=='__main__':
    unittest.main()
