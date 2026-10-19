"""Clipboard-shaped Bureaubot architecture using the original Cog materials."""
from panda3d.core import (GeomVertexFormat, GeomVertexWriter, GeomVertexReader, GeomVertexData,
                         GeomNode, CollisionBox, Point3)
from toontown.suit.BureaubotModels import build_logo, _box, _prism, _disc


def decorate_building(building):
    """Replace the copied Bossbot shell; retain the game's attachment contract."""
    shell = building.find('**/*_building')
    # Reuse the painted, riveted atlas, not the Bossbot geometry or its UVs.
    texture=next(t for t in shell.findAllTextures() if t.getName()=='phase_4_palette_3cmla_7')
    shell.removeNode()
    front = building.find('**/*_front')
    for child in front.getChildren():child.removeNode()
    front.attachNewNode(GeomNode('bureau-sign-decal-surface'))
    shell=building.attachNewNode('bureaubot_building')
    def metal(mesh,uv=(.01,.51,.24,.74)):
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
    bronze=(.76,.59,.40,1)
    # Tall clipped-corner clipboard, with an actual open, raised binder-clip roof.
    metal(_prism(shell,'clipboard-upper-shell',[(0,9),(30,9),(30,37),(27,41),(3,41),(0,37)],12,bronze,y=3))
    for x in (5,25):metal(_box(shell,'clipboard-foot',(x,3,4.5),(10,12,9),bronze))
    for x in (1,29):metal(_box(shell,'edge-binding',(x,-3.1,20),(2,1.1,39),steel))
    # Stacked sheet cornices and inset horizontal office windows replace tie/eyes.
    for z in (19,25,31,37):
        metal(_box(shell,'paper-course',(15,-3.3,z),(25,1.2,1.05),steel),(.55,.76,.79,.98))
    for z in (21.8,27.8,33.8):
        _box(shell,'recessed-window-band',(15,-3.65,z),(23,.25,3.8),(.12,.22,.25,1))
        for x in (5,10,15,20,25):
            _box(shell,'window-glass',(x,-3.85,z),(3.6,.12,2.7),(.36,.48,.49,1))
            _box(shell,'window-glint',(x-.65,-3.94,z+.3),(.28,.08,2),(.65,.73,.68,1))
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
    collisions=building.find('**/+CollisionNode').node()
    collisions.clearSolids()
    for lo,hi in (((0,-3,9),(30,9,41)),((0,-3,0),(10,9,9)),
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
