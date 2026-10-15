"""Rebuild the Acorn art assets with Panda3D; no Blender or game server needed.

Only custom meshes are baked. Original Toontown buildings/props remain external
resource references in the DNA. Deterministic UVs, vertex shading and collision
surfaces are stored in the models, so the game and editor see the same art.
"""
from math import sin, cos, pi, sqrt, exp
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from panda3d.core import (
    loadPrcFileData, NodePath, GeomVertexData, GeomVertexFormat, GeomVertexWriter,
    GeomTriangles, Geom, GeomNode, Vec3, Point3, CollisionNode, CollisionPolygon,
    CollisionCapsule, CollisionBox, BitMask32, Filename, Texture, TextNode,
    TransparencyAttrib, compressFile,
)
loadPrcFileData('', 'window-type none\naudio-library-name null\nmodel-path resources\n'
                    'default-model-extension .bam\nbam-texture-mode unchanged')
from direct.showbase.ShowBase import ShowBase

OUT = ROOT / 'assets/acorn/models'
GRASS = 'phase_3.5/maps/grassDG.jpg'
DIRT = 'phase_3.5/maps/dustroad.jpg'
STONE = 'phase_3.5/maps/cobblestone_brown.jpg'
BARK = 'phase_4/maps/treehouse_tree_trunk2.jpg'
WOOD = 'phase_6/maps/outdoor_zone_wood_boards.jpg'
CREAM = (.98, .89, .63, 1)


class Mesh:
    def __init__(self, name, texture=None):
        self.name, self.texture = name, texture
        self.data = GeomVertexData(name, GeomVertexFormat.getV3n3c4t2(), Geom.UHStatic)
        self.v = GeomVertexWriter(self.data, 'vertex')
        self.n = GeomVertexWriter(self.data, 'normal')
        self.c = GeomVertexWriter(self.data, 'color')
        self.uv = GeomVertexWriter(self.data, 'texcoord')
        self.tri = GeomTriangles(Geom.UHStatic)
        self.count = 0

    def face(self, points, uvs=None, color=(1, 1, 1, 1), shade=True):
        points = [Point3(*p) for p in points]
        normal = (points[1]-points[0]).cross(points[2]-points[0])
        if normal.lengthSquared() < 1e-10:
            return
        normal.normalize()
        light = .80 + .20 * max(0, normal.dot(Vec3(-.4, -.55, .73))) if shade else 1
        start = self.count
        for i, p in enumerate(points):
            self.v.addData3(p)
            self.n.addData3(normal)
            self.c.addData4(color[0]*light, color[1]*light, color[2]*light, color[3])
            self.uv.addData2(*(uvs[i] if uvs else (p.x/12, p.y/12)))
            self.count += 1
        for i in range(1, len(points)-1):
            self.tri.addVertices(start, start+i, start+i+1)

    def attach(self, parent, ground_layer=None):
        geom = Geom(self.data)
        geom.addPrimitive(self.tri)
        node = GeomNode(self.name)
        node.addGeom(geom)
        result = parent.attachNewNode(node)
        if self.texture:
            tex = app.loader.loadTexture(self.texture)
            tex.setMinfilter(Texture.FTLinearMipmapLinear)
            tex.setMagfilter(Texture.FTLinear)
            result.setTexture(tex)
        if ground_layer is not None:
            # Coplanar ground layers use the game's ground bin. Disabling depth
            # writes prevents distant z-fighting even with a 16-bit depth buffer.
            result.setBin('ground', ground_layer)
            result.setDepthWrite(False)
        return result


def collider(parent, name, mask):
    node = CollisionNode(name)
    node.setFromCollideMask(BitMask32.allOff())
    node.setIntoCollideMask(BitMask32(mask))
    parent.attachNewNode(node)
    return node


def collision_face(node, points):
    for i in range(1, len(points)-1):
        p = [Point3(*v) for v in (points[0], points[i], points[i+1])]
        if (p[1]-p[0]).cross(p[2]-p[0]).lengthSquared() > 1e-8:
            node.addSolid(CollisionPolygon(*p))


def tube(parent, name, rings, texture=BARK, color=(1, 1, 1, 1), sides=16,
         collide=False):
    """Sweep a textured polygonal tube along a hand-shaped branch/root."""
    mesh = Mesh(name, texture)
    walls = collider(parent, name+'-walls', 1) if collide else None
    vertices = []
    for j, (x, y, z, radius) in enumerate(rings):
        here = Vec3(x, y, z)
        before = Vec3(*rings[max(0, j-1)][:3])
        after = Vec3(*rings[min(len(rings)-1, j+1)][:3])
        axis = (after-before).normalized()
        ref = Vec3(0, 1, 0) if abs(axis.z) > .8 else Vec3(0, 0, 1)
        u = axis.cross(ref).normalized()
        v = axis.cross(u).normalized()
        vertices.append([here + (u*cos(i*2*pi/sides)+v*sin(i*2*pi/sides))*radius
                         for i in range(sides)])
    for j in range(len(rings)-1):
        for i in range(sides):
            k = (i+1) % sides
            points = [vertices[j][i], vertices[j][k], vertices[j+1][k], vertices[j+1][i]]
            mesh.face(points, [(i/sides*2,j/2),((i+1)/sides*2,j/2),
                               ((i+1)/sides*2,(j+1)/2),(i/sides*2,(j+1)/2)], color)
        if walls:
            walls.addSolid(CollisionCapsule(Point3(*rings[j][:3]),
                                            Point3(*rings[j+1][:3]),
                                            min(rings[j][3], rings[j+1][3])*.9))
    mesh.face(list(reversed(vertices[0])), color=color)
    mesh.face(vertices[-1], color=color)
    return mesh.attach(parent)


def leaf_cluster(parent, name, center, width, height, color):
    """Layered cutout foliage uses the same billboard convention as stock trees."""
    pivot=parent.attachNewNode(name)
    pivot.setPos(*center)
    pivot.setBillboardAxis()
    # A scalloped silhouette samples only the painted upper canopy. A cropped
    # rectangle would expose straight edges and pieces of the stock tree trunk.
    mesh=Mesh(name+'-leaves')
    for i in range(48):
        points=[(0,0,0)];uvs=[(.5,.75)]
        for a in (i*pi/24,(i+1)*pi/24):
            r=1+.055*sin(11*a)+.035*cos(7*a)
            points.append((cos(a)*width/2*r,0,sin(a)*height/2*r))
            uvs.append((.5+.45*cos(a),.75+.23*sin(a)))
        mesh.face(points,uvs,shade=False)
    node=mesh.attach(pivot)
    texture=app.loader.loadTexture('phase_3.5/maps/tree_big_top.jpg',
                                   'phase_3.5/maps/tree_big_top_a.rgb')
    node.setTexture(texture)
    node.setTransparency(TransparencyAttrib.MDual)
    node.setColorScale(*color)
    node.setTwoSided(True)


def soft_shadow(parent,radius):
    mesh=Mesh('oak-ground-shadow')
    for i in range(64):
        a,b=i*pi/32,(i+1)*pi/32
        # Separate vertex alpha produces a soft edge without a new raster asset.
        start=mesh.count
        for point,alpha in (((0,0,.12),.28),((radius*cos(a),radius*sin(a),.12),0),
                            ((radius*cos(b),radius*sin(b),.12),0)):
            mesh.v.addData3(*point);mesh.n.addData3(0,0,1)
            mesh.c.addData4(.16,.22,.08,alpha);mesh.uv.addData2(0,0);mesh.count+=1
        mesh.tri.addVertices(start,start+1,start+2)
    node=mesh.attach(parent)
    node.setTransparency(TransparencyAttrib.MAlpha)
    node.setBin('shadow',0);node.setDepthWrite(False)


def board(parent, name, center, size, color=CREAM, texture=WOOD):
    x, y, z = center
    a, b, c = [v/2 for v in size]
    pts = [(x+dx*a, y+dy*b, z+dz*c) for dx,dy,dz in
           ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
            (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))]
    mesh = Mesh(name, texture)
    for ids in ((0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)):
        mesh.face([pts[i] for i in ids], [(0,0),(1,0),(1,1),(0,1)], color)
    return mesh.attach(parent)


def text(parent, value, pos, size, color=CREAM):
    node = TextNode(value)
    node.setText(value)
    node.setFont(app.loader.loadFont('phase_3/models/fonts/MickeyFont'))
    node.setAlign(TextNode.ACenter)
    node.setTextColor(*color)
    path = parent.attachNewNode(node)
    path.setPos(*pos)
    path.setScale(size)
    # Bake font geometry rather than requiring a live TextNode in the model.
    baked = path.attachNewNode(node.generate())
    baked.wrtReparentTo(parent)
    path.removeNode()


def great_oak():
    root = NodePath('great-oak')
    soft_shadow(root,34)
    shell = Mesh('hollow-fluted-trunk', BARK)
    walls = collider(root, 'oak-walkthrough-walls', 1)
    # Two openings, south and north; the roots form a walk-through woodland gate.
    sides = 40
    levels = [(0,11.5),(4,9.5),(10,8.5),(17,7.4),(23,6.3),(31,4)]
    for j in range(len(levels)-1):
        z0,r0 = levels[j]; z1,r1 = levels[j+1]
        for i in range(sides):
            a,b = i*2*pi/sides,(i+1)*2*pi/sides
            opening = abs(cos((a+b)/2)) < (.40 if j<2 else .20)
            if j < 3 and opening:
                continue
            def point(angle,z,r,inside=False):
                radius = r + .65*cos(angle*7) - (2 if inside else 0)
                return (radius*cos(angle)+1.2*sin(z/14),radius*sin(angle),z)
            for inside in (False,True):
                pts = [point(a,z0,r0,inside),point(b,z0,r0,inside),
                       point(b,z1,r1,inside),point(a,z1,r1,inside)]
                if inside:
                    pts.reverse()
                shell.face(pts,[(a/pi, z0/16),(b/pi,z0/16),
                                (b/pi,z1/16),(a/pi,z1/16)],
                           (.83,.70,.48,1) if inside else (1,.91,.70,1))
                if j < 3:
                    collision_face(walls,pts)
    shell.attach(root)
    for i in range(7):
        a = i*2*pi/7+.12
        # Keep both passages clear of roots.
        if abs(cos(a)) < .50:
            continue
        tube(root,'buttress-root-%s'%i,
             [(cos(a)*5,sin(a)*5,11,3.7),(cos(a)*9,sin(a)*9,4,3),
              (cos(a+.1)*16,sin(a+.1)*16,1,1.8),
              (cos(a+.12)*22,sin(a+.12)*22,.25,.12)],
             color=(1,.88,.63,1),collide=True)
    for i in range(6):
        a=i*2*pi/6
        tube(root,'reaching-bough-%s'%i,
             [(1,0,21,4.7),(cos(a)*9,sin(a)*9,26,3),
              (cos(a+.2)*14,sin(a+.2)*14,29,.8)],
             color=(1,.91,.70,1))
        leaf_cluster(root,'outer-canopy-%s'%i,(cos(a)*19,sin(a)*16,39+(i%2)*4),
                     34,26,(1,.94,.72,1))
        leaf_cluster(root,'upper-canopy-%s'%i,(cos(a+.3)*10,sin(a+.3)*9,49+(i%2)*4),
                     30,26,(1,.97,.78,1))
    leaf_cluster(root,'oak-crown',(0,0,58),30,24,(1,1,.84,1))
    # A carved plaque hangs above the open hollow.
    board(root,'oak-plaque',(0,-8.5,17),(14,1,3.5),(.67,.39,.18,1))
    text(root,'THE GREAT OAK',(0,-9.1,16.2),1.2)
    return root


def bench():
    root = NodePath('woodland-bench')
    for x in (-3.4,3.4):
        tube(root,'bench-root-leg',[(x,0,0,.5),(x,0,2.6,.4)],color=(.65,.53,.34,1))
    for y in (-.7,0,.7):
        board(root,'seat-slat',(0,y,2.6),(9,.62,.35),(.88,.71,.44,1))
    for x in (-3.6,3.6):
        board(root,'back-support',(x,.9,3.8),(.4,.5,3.2),(.65,.53,.34,1))
    for z in (3.7,4.6):
        board(root,'back-slat',(0,1,z),(9,.4,.7),(.88,.71,.44,1))
    collider(root,'bench-barrier',1).addSolid(CollisionBox(Point3(0,0,2),4.5,1,2))
    return root


def catmull(points, steps=10):
    points = [Vec3(x,y,0) for x,y in points]
    p = [points[0]]+points+[points[-1]]
    out=[]
    for i in range(1,len(p)-2):
        a,b,c,d=p[i-1:i+3]
        for k in range(steps):
            t=k/steps
            v=(b*2+(-a+c)*t+(a*2-b*5+c*4-d)*t*t+(-a+b*3-c*3+d)*t*t*t)*.5
            out.append((v.x,v.y))
    out.append((points[-1].x,points[-1].y))
    return out


ROOT_ROUTE = [(0,-155),(0,-115),(30,-75),(40,-35),(35,5),(-15,50),
              (-25,95),(-10,135),(0,165)]


def ribbon(root, name, points, halfwidth, texture, z=.06, color=(1,1,1,1), edges=False):
    mesh = Mesh(name,texture)
    floor = collider(root,name+'-floor',2)
    distance=0
    left=[];right=[];uv=[]
    for i,(x,y) in enumerate(points):
        before=Vec3(*points[max(0,i-1)],0);after=Vec3(*points[min(len(points)-1,i+1)],0)
        tangent=(after-before).normalized();normal=Vec3(-tangent.y,tangent.x,0)
        left.append((x+normal.x*halfwidth,y+normal.y*halfwidth,z))
        right.append((x-normal.x*halfwidth,y-normal.y*halfwidth,z))
        if i: distance+=(Vec3(x,y,0)-before).length()
        uv.append(distance/14)
    for i in range(len(points)-1):
        pts=[left[i],right[i],right[i+1],left[i+1]]
        mesh.face(pts,[(0,uv[i]),(halfwidth/7,uv[i]),(halfwidth/7,uv[i+1]),(0,uv[i+1])],color,False)
        collision_face(floor,pts)
    mesh.attach(root, ground_layer=round(z*1000))
    if edges:
        for side in (left,right):
            tube(root,name+'-stone-edge',[(x,y,z,.30) for x,y,z in side],STONE,
                 (.85,.79,.62,1),sides=5)


def feathered_shoulder(root,points,width,texture,color):
    """A transparent painted shoulder blends paving into the neighborhood soil."""
    mesh=Mesh('soft-paving-shoulder',texture)
    for side in (-1,1):
        previous=None
        for i,(x,y) in enumerate(points):
            before=Vec3(*points[max(0,i-1)],0);after=Vec3(*points[min(len(points)-1,i+1)],0)
            tangent=(after-before).normalized();nx,ny=-tangent.y*side,tangent.x*side
            row=((x+nx*(width-.1),y+ny*(width-.1),.045),(x+nx*(width+3),y+ny*(width+3),.045))
            if previous:
                mesh.face([previous[0],previous[1],row[1],row[0]],color=color,shade=False)
                # Vertex opacity, in the same order as the quad above.
                for offset,alpha in enumerate((1,0,0,1)):
                    mesh.c.setRow(mesh.count-4+offset);mesh.c.setData4(*color[:3],alpha)
                mesh.c.setRow(mesh.count)
            previous=row
    node=mesh.attach(root,ground_layer=45);node.setTransparency(TransparencyAttrib.MAlpha)


def disk(root,name,center,rx,ry,texture,z=.07):
    mesh=Mesh(name,texture);floor=collider(root,name+'-floor',2)
    cx,cy=center
    for i in range(64):
        a,b=i*pi/32,(i+1)*pi/32
        pts=[(cx,cy,z),(cx+rx*cos(a),cy+ry*sin(a),z),(cx+rx*cos(b),cy+ry*sin(b),z)]
        mesh.face(pts,shade=False);collision_face(floor,pts)
    mesh.attach(root, ground_layer=round(z*1000))


def height(x,y,street):
    if street:return 0.0
    from toontown.expansion.WorldLayout import terrain_height
    return terrain_height(19000,x,y)


def terrain(street=False):
    root=NodePath('root-route-terrain' if street else 'acorn-terrain')
    mesh=Mesh('woodland-earth',DIRT)
    # Spatially separated collision patches avoid testing every terrain triangle
    # against each moving Toon on every frame.
    floor_patches={}
    xmin,xmax,ymin,ymax=(-125,125,-200,210) if street else (-165,165,-155,170)
    step=5
    for x in range(xmin,xmax,step):
        for y in range(ymin,ymax,step):
            key=(x//40,y//40)
            if key not in floor_patches:
                floor_patches[key]=collider(root,'terrain-floor-%s-%s'%key,2)
            floor=floor_patches[key]
            pts=[(xx,yy,height(xx,yy,street)) for xx,yy in
                 ((x,y),(x+step,y),(x+step,y+step),(x,y+step))]
            tint=(.88+.06*sin(x/32),.92+.05*cos(y/41),.74,1)
            mesh.face([pts[0],pts[1],pts[2]],color=tint)
            mesh.face([pts[0],pts[2],pts[3]],color=tint)
            collision_face(floor,pts)
    mesh.attach(root, ground_layer=0)
    if street:
        path=catmull(ROOT_ROUTE)
        ribbon(root,'grassy-verge',path,22,STONE,.035,(.85,.85,.73,1))
        ribbon(root,'root-route-sidewalk',path,18,STONE,.06,(1,.96,.84,1),True)
        ribbon(root,'winding-dirt-road',path,11,DIRT,.085,(1,.91,.71,1))
        for x,y in ((35,-34),(-22,88)):
            disk(root,'pocket-courtyard',(x,y),30,28,STONE,.065)
    else:
        disk(root,'village-cobblestones',(0,15),47,48,STONE,.04)
        disk(root,'village-square',(0,15),43,44,DIRT,.075)
        loop=[(46*cos(i*pi/40),30+46*sin(i*pi/40)) for i in range(81)]
        ribbon(root,'oak-garden-loop',loop,7,DIRT,.08,edges=True)
        for name,points,w in [
            ('root-route-arrival',[(0,-115),(0,-80),(-7,-48),(0,-20)],12),
            ('bramble-path',[(-120,20),(-90,20),(-65,12),(-40,5)],10),
            ('east-shop-walk',[(35,-25),(63,-8),(70,25),(56,55),(32,80)],8),
            ('west-shop-walk',[(-35,-28),(-57,-13),(-62,38),(-40,73)],8),
        ]:
            ribbon(root,name,catmull(points),w+1,STONE,.04)
            ribbon(root,name+'-path',catmull(points),w,DIRT,.09,edges=True)
    from toontown.expansion.Services import add_paths
    add_paths(root,19100 if street else 19000,sys.modules[__name__],STONE)
    if not street:
        from tools.world_dressing import perimeter
        perimeter(root,19000,sys.modules[__name__])
    # Invisible barrier beyond the scenery; the playable paths never touch it.
    walls=collider(root,'forest-boundary',1)
    for x,y,w,d in ((xmin,0,1,ymax-ymin),(xmax,0,1,ymax-ymin),
                    (0,ymin,xmax-xmin,1),(0,ymax,xmax-xmin,1)):
        walls.addSolid(CollisionBox(Point3(x,y,35),w/2,d/2,50))
    return root


def sign_model(value):
    root=NodePath('carved-sign')
    board(root,'painted-timber',(0,0,0),(18,.8,3.5),(.36,.40,.20,1))
    for x in (-8.5,8.5):
        board(root,'gold-edge',(x,-.45,0),(.3,.2,3.1),CREAM)
    text(root,value,(0,-.5,-.65),min(1.25,18/max(len(value),1)*1.45))
    return root


def shop_barrier():
    root=NodePath('shop-barrier')
    collider(root,'shop-wall',1).addSolid(CollisionBox(Point3(0,.5,.5),.5,.5,.5))
    return root


def shop_shell(style):
    # Stock landmarks were authored as street facades. Close the backs and sides
    # so they can stand around a freely explorable plaza without visible holes.
    root=NodePath('building-shell-'+style)
    # UV windows in the existing facade atlases keep siding colors and grain
    # consistent with the landmark, including its otherwise exposed rear.
    atlas,rect={
        'DG_A1':(1,(.16,.25,.36,.45)),
        'DG_A2':(2,(.03,.61,.23,.70)),
        'DG_B1':(2,(.03,.61,.23,.70)),
        'DG_C1':(2,(.29,.55,.47,.70)),
        'DG_D1':(1,(.55,.55,.70,.70)),
    }[style]
    mesh=Mesh('matching-clapboard',
              'phase_8/maps/daisys_garden_streets_palette_3cmla_%s.jpg'%atlas)
    pts=[(-.5,0,0),(.5,0,0),(.5,1,0),(-.5,1,0),
         (-.5,0,1),(.5,0,1),(.5,1,1),(-.5,1,1)]
    u,v,r,t=rect
    for ids in ((0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)):
        mesh.face([pts[i] for i in ids],[(u,v),(r,v),(r,t),(u,t)])
    mesh.attach(root)
    return root


def garden_fence():
    root=NodePath('woodland-picket-fence')
    for z in (1.4,3.5):
        board(root,'fence-rail',(0,0,z),(20,.55,.55),(.92,.82,.58,1))
    for i in range(9):
        x=-9+i*2.25
        board(root,'picket',(x,-.2,2.2),(.8,.65,4.4),(.96,.88,.65,1))
        tube(root,'picket-cap',[(x,-.2,4.4,.6),(x,-.2,5,.03)],WOOD,
             (.96,.88,.65,1),sides=4)
    collider(root,'fence-wall',1).addSolid(CollisionBox(Point3(0,0,2.2),10,.4,2.2))
    return root


def save(model,name):
    # Loader-resolved absolute texture filenames must not leak into distributable
    # models. Store model-path-relative references including alpha companions.
    resources=(ROOT/'resources').resolve()
    for tex in model.findAllTextures():
        for getter,setter in ((tex.getFilename,tex.setFilename),
                              (tex.getAlphaFilename,tex.setAlphaFilename)):
            f=getter()
            if not f.empty():
                path=Path(f.toOsSpecific())
                if path.is_absolute():
                    setter(Filename(path.relative_to(resources).as_posix()))
    # Encode into memory and let Python write atomically. Panda's direct .pz
    # writer can leave an incomplete zlib trailer on some offscreen build hosts.
    import zlib
    packed=OUT/(name+'.bam.pz')
    temporary=packed.with_suffix('.tmp')
    from panda3d.core import StringStream
    stream=StringStream()
    assert model.writeBamStream(stream)
    temporary.write_bytes(zlib.compress(stream.getData(),9))
    temporary.replace(packed)
    model.removeNode()


if __name__ == '__main__':
    import os
    os.chdir(ROOT)
    OUT.mkdir(parents=True,exist_ok=True)
    app=ShowBase()
    save(terrain(),'acorn_terrain')
    save(terrain(True),'root_route_terrain')
    save(great_oak(),'great_oak')
    save(bench(),'woodland_bench')
    save(shop_barrier(),'shop_barrier')
    for style in ('DG_A1','DG_A2','DG_B1','DG_C1','DG_D1'):
        save(shop_shell(style),'shop_shell_'+style)
    save(garden_fence(),'garden_fence')
    for code,name in [('root_sign','ROOT ROUTE'),('bramble_sign','BRAMBLE BEND'),
                       ('daisy_sign','DAISY GARDENS'),('acorn_sign','ACORN ACRESIDE'),
                       ('knot_sign','KNOT A PROBLEM'),('leaf_sign','LEAF IT TO ME'),
                       ('branch_sign','BRANCH OFFICE'),('acorny_sign','ACORNY JOKES'),
                       ('book_sign','BOOKS & BRANCHES'),('seed_sign','SEED MONEY'),
                       ('tea_sign','THE TEA LEAF'),('root_shop_sign','ROOT OF THE JOKE')]:
        save(sign_model(name),code)
    app.destroy()
    print('Built custom Acorn terrain, Great Oak, bench and carved signs.')
