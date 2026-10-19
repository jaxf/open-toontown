"""Clipboard-shaped Bureaubot architecture using the original Cog materials."""
from pathlib import Path
from panda3d.core import (GeomVertexFormat, GeomVertexWriter, GeomVertexReader, GeomVertexData,
                         GeomNode, CollisionBox, Point3, NodePath, CollisionNode, BitMask32)
from toontown.suit.BureaubotModels import build_logo, _box, _prism, _disc


MODEL_PATH=str(Path(__file__).resolve().parents[2]/'assets/bureaubots/models/bureaubot-building.bam')


def build_building(loader):
    """Author a standalone landmark. No other department's model is loaded."""
    building=NodePath('suit_landmark_bureau')
    texture=loader.loadTexture('phase_4/maps/phase_4_palette_3cmla_7.jpg')
    front=building.attachNewNode('bureau_front')
    front.attachNewNode(GeomNode('bureau-sign-decal-surface'))
    building.attachNewNode('bureau_door_origin').setPos(15,-3.09498,0)
    building.attachNewNode('sign_origin').setPos(15,-4.2,14)
    shell=building.attachNewNode('bureaubot_building')
    def metal(mesh,uv=(.60,.95,.66,.98)):
        node=mesh.node()
        low,high=mesh.getTightBounds()
        for i in range(node.getNumGeoms()):
            geom=node.modifyGeom(i)
            data=GeomVertexData(geom.getVertexData().convertTo(GeomVertexFormat.getV3n3c4t2()))
            reader=GeomVertexReader(data,'vertex');writer=GeomVertexWriter(data,'texcoord')
            while not reader.isAtEnd():
                p=reader.getData3()
                u=(p.x-low.x)/max(.001,high.x-low.x)
                v=(p.z-low.z)/max(.001,high.z-low.z)
                writer.addData2(uv[0]+u*(uv[2]-uv[0]),uv[1]+v*(uv[3]-uv[1]))
            geom.setVertexData(data)
        mesh.setTexture(texture,1)
        return mesh
    steel=(.94,.91,.85,1)
    bronze=(.94,.82,.65,1)
    # Tall clipped-corner clipboard, with an actual open, raised binder-clip roof.
    metal(_prism(shell,'clipboard-upper-shell',[(0,9),(30,9),(30,17),(26,20),
        (26,37),(22,41),(8,41),(4,37),(4,20),(0,17)],12,bronze,y=3))
    for x in (5,25):metal(_box(shell,'clipboard-foot',(x,3,4.5),(10,12,9),bronze))
    for x in (1,29):
        metal(_box(shell,'base-binding',(x,-3.2,8.5),(1.6,1.1,16),steel))
        for z in (2,7,12,16):_disc(shell,'binding-rivet',x,-3.82,z,.3,.3,(.36,.40,.39,1),.18)
    for x in (4.6,25.4):metal(_box(shell,'edge-binding',(x,-3.1,28.5),(1.5,1.1,20),steel))
    # Stacked sheet cornices and inset horizontal office windows replace tie/eyes.
    for z in (19,25,31):
        metal(_box(shell,'paper-course',(15,-3.3,z),(21,1.2,1.05),steel),(.55,.76,.79,.98))
    for z in (21.8,27.8):
        _box(shell,'recessed-window-band',(15,-3.65,z),(19,.25,3.8),(.12,.22,.25,1))
        for x in (7.5,12.5,17.5,22.5):
            _box(shell,'window-glass',(x,-3.85,z),(3.6,.12,2.7),(.36,.48,.49,1))
            _box(shell,'window-glint',(x-.65,-3.94,z+.3),(.28,.08,2),(.65,.73,.68,1))
    # A broad bureaucratic scowl below the clip echoes the other departments'
    # living-building faces, while the stepped paper shoulders remain unique.
    _prism(shell,'left-eye',[(6,36.5),(14.1,34.8),(12.8,33),(9,33.2)],.35,(.91,.94,.88,1),y=-3.65)
    _prism(shell,'right-eye',[(15.9,34.8),(24,36.5),(21,33.2),(17.2,33)],.35,(.91,.94,.88,1),y=-3.65)
    for x in (11.7,18.3):_disc(shell,'bureau-pupil',x,-3.93,34.6,.7,1,(.07,.09,.09,1),.12)
    metal(_prism(shell,'clipboard-brow',[(5,37.7),(15,35.5),(25,37.7),(24,39),(15,37),(6,39)],1.4,steel,y=-3.6),(.55,.76,.79,.98))
    for x in (10,20):metal(_box(shell,'clip-upright',(x,2,43.2),(2.5,5,9),steel))
    metal(_prism(shell,'clip-crown',[(8.75,46),(21.25,46),(19,49),(11,49)],5,steel,y=2))
    metal(_box(shell,'clip-jaw',(15,-3.5,39.3),(16,3,3.4),steel),(.55,.76,.79,.98))
    for x in (9,21):_disc(shell,'clip-rivet',x,-5.1,39.4,.48,.48,(.29,.32,.31,1),.22)
    # Department badge is cast into the roof clip, not pasted over the windows.
    crest=build_logo()
    crest.setName('bureaubot-facade-crest')
    crest.reparentTo(building)
    crest.find('**/cast-clipboard').setHpr(0,0,0)
    crest.setPos(15,-5.3,39.3)
    crest.setScale(4.4,1.5,4.4)
    building.find('**/sign_origin').setY(-4.2)
    # Camera collision follows the new silhouette and leaves the elevator clear.
    collisions=CollisionNode('bureau_camera_collisions')
    collisions.setFromCollideMask(BitMask32.allOff())
    # Match native landmark wall + camera masks (bits 0 and 2).
    collisions.setIntoCollideMask(BitMask32(5))
    building.attachNewNode(collisions)
    for lo,hi in (((0,-3,9),(30,9,18)),((4,-3,18),(26,9,41)),((0,-3,0),(10,9,9)),
                  ((20,-3,0),(30,9,9)),((8.75,-.5,41),(11.25,4.5,47)),
                  ((18.75,-.5,41),(21.25,4.5,47)),((9,-.5,46),(21,4.5,49))):
        collisions.addSolid(CollisionBox(Point3(*lo),Point3(*hi)))
    building.setTag('department', 'u')
    return building


def add_elevator_badge(elevator):
    badge=build_logo()
    badge.reparentTo(elevator.find('**/elevator'))
    badge.setPos(0,6.79,6.8)
    badge.setScale(3)
    return badge
