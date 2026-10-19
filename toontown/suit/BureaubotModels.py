"""Editable Bureaubot meshes shared by live Cogs and model previews."""
import math

from direct.actor.Actor import Actor
from panda3d.core import (ColorAttrib, Geom, GeomNode, GeomTriangles, GeomVertexData,
                         GeomVertexFormat, GeomVertexWriter, NodePath,
                         Point3, Texture, Triangulator, PNMImage)

from .BureaubotGlobals import CATALOG, ANIMATIONS

PAPER = (.83, .81, .69, 1)
METAL = (.62, .64, .60, 1)
DARK = (.10, .11, .11, 1)
WHITE = (.96, .94, .83, 1)
RED = (.53, .12, .09, 1)
COPPER = (.56, .35, .21, 1)
TEAL = (.16, .29, .28, 1)


def _solid(parent, name, vertices, faces, color):
    data = GeomVertexData(name, GeomVertexFormat.getV3n3c4(), Geom.UHStatic)
    vertex = GeomVertexWriter(data, 'vertex')
    normal = GeomVertexWriter(data, 'normal')
    colors = GeomVertexWriter(data, 'color')
    tris = GeomTriangles(Geom.UHStatic)
    offset = 0
    for face in faces:
        points = [Point3(*vertices[i]) for i in face]
        n = (points[1] - points[0]).cross(points[2] - points[0])
        n.normalize()
        # Baked directional shading also reads correctly in the unlit book UI.
        shade = .82 + .13 * max(0, n.z) + .13 * max(0, -n.y)
        for p in points:
            vertex.addData3(p)
            normal.addData3(n)
            colors.addData4(*(min(1, c * shade) for c in color[:3]), color[3])
        for i in range(1, len(face) - 1):
            tris.addVertices(offset, offset + i, offset + i + 1)
        offset += len(face)
    geom = Geom(data)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    return parent.attachNewNode(node)


def _prism(parent, name, outline, depth, color, y=0):
    """Extrude a counterclockwise X/Z polygon along Y."""
    n = len(outline)
    verts = [(x, y - depth / 2, z) for x, z in outline]
    verts += [(x, y + depth / 2, z) for x, z in outline]
    # Ear triangulation preserves concave outlines (gear teeth, hair, ears).
    triangulator = Triangulator()
    for x,z in outline:
        triangulator.addPolygonVertex(triangulator.addVertex(x,z))
    triangulator.triangulate()
    faces = []
    for i in range(triangulator.getNumTriangles()):
        a,b,c = (triangulator.getTriangleV0(i),triangulator.getTriangleV1(i),
                 triangulator.getTriangleV2(i))
        faces.extend(((a,b,c),(c+n,b+n,a+n)))
    faces += [(i, i + n, (i + 1) % n + n, (i + 1) % n) for i in range(n)]
    return _solid(parent, name, verts, faces, color)


def _box(parent, name, center, size, color):
    x, y, z = center
    w, d, h = (v / 2 for v in size)
    return _prism(parent, name, [(x-w, z-h), (x+w, z-h),
                                (x+w, z+h), (x-w, z+h)], 2*d, color, y)


def _disc(parent, name, x, y, z, rx, rz, color, depth=.05, sides=16):
    return _prism(parent, name,
                  [(x + rx * math.cos(i * 2 * math.pi / sides),
                    z + rz * math.sin(i * 2 * math.pi / sides))
                   for i in range(sides)], depth, color, y)


def _stroke(parent, name, points, y, width, color):
    for i, ((x1, z1), (x2, z2)) in enumerate(zip(points, points[1:])):
        dx, dz = x2-x1, z2-z1
        length = math.hypot(dx, dz)
        nx, nz = -dz / length * width/2, dx / length * width/2
        _prism(parent, name + str(i), [(x1-nx,z1-nz), (x2-nx,z2-nz),
                                      (x2+nx,z2+nz), (x1+nx,z1+nz)],
               .025, color, y)


def _face(root, y, z, width=.48, mouth=True, sleepy=False):
    for side in (-1, 1):
        x = side * width / 2
        _disc(root, 'eye', x, y, z, width*.42, .19, WHITE)
        _disc(root, 'pupil', x - side*.03, y-.05, z-.025, .065, .095, DARK)
        if sleepy:
            _box(root, 'lid', (x, y-.075, z+.14), (width*.86,.04,.16), METAL)
        else:
            _stroke(root, 'brow', [(x-side*.19,z+.12),(x+side*.17,z+.24)],
                    y-.08, .115, DARK)
    if mouth:
        _stroke(root, 'frown', [(-width*.7,z-.49),(0,z-.39),(width*.7,z-.49)],
                y-.03, .055, DARK)


def build_logo():
    """Embossed pewter clipboard; the same relief icon on book, chest and doors."""
    root = NodePath('bureaubot-emblem')
    edge = (.30,.32,.33,1)
    silver = (.69,.72,.73,1)
    highlight = (.88,.90,.90,1)
    _prism(root,'clipboard-bevel',[(-.32,-.46),(.32,-.46),(.38,-.38),
        (.38,.33),(.29,.42),(-.29,.42),(-.38,.33),(-.38,-.38)],.13,edge)
    _box(root,'metal-face',(0,-.085,-.015),(.64,.04,.76),silver)
    _box(root,'paper-relief',(0,-.12,-.035),(.51,.025,.60),highlight)
    _box(root,'clip-shadow',(0,-.15,.34),(.30,.05,.15),edge)
    _box(root,'clip',(0,-.185,.37),(.24,.025,.10),silver)
    for z in (.13,.02,-.09):
        _box(root,'engraved-rule',(0,-.155,z),(.33,.018,.027),edge)
    _stroke(root,'approval',[(-.14,-.22),(-.04,-.31),(.17,-.15)],-.16,.045,edge)
    _stroke(root,'rim-glint',[(-.35,-.39),(-.35,.33),(-.28,.39)],-.085,.025,highlight)
    return root


_texture_cache = {}


def apply_clothes(actor, model_loader):
    """Burnt-orange cloth, preserving the original mapped pinstripes/collar."""
    for part, texture in (('torso','blazer'),('arms','sleeve'),('legs','leg')):
        if texture not in _texture_cache:
            source = model_loader.loadTexture('phase_3.5/maps/c_' + texture + '.jpg')
            pixels = PNMImage()
            source.store(pixels)
            for y in range(pixels.getYSize()):
                for x in range(pixels.getXSize()):
                    rgb = pixels.getXel(x,y)
                    light = max(rgb)
                    # Preserve the white shirt and bright tie detail.
                    if light < .63:
                        value = min(1., .15 + light * 2.7)
                        pixels.setXel(x,y,value*.78,value*.29,value*.075)
            tex = Texture('bureaubot-' + texture)
            tex.load(pixels)
            tex.setMinfilter(Texture.FTLinearMipmapLinear)
            tex.setMagfilter(Texture.FTLinear)
            _texture_cache[texture] = tex
        mesh = actor.find('**/' + part)
        if not mesh.isEmpty():
            mesh.setTexture(_texture_cache[texture],1)
    hands = actor.find('**/hands')
    if not hands.isEmpty():
        hands.setColor(*METAL)
    for mesh in actor.findAllMatches('**/+GeomNode'):
        for i in range(mesh.node().getNumGeoms()):
            state = mesh.node().getGeomState(i)
            tint = state.getAttrib(ColorAttrib)
            if tint is not None:
                color = tint.getColor()
                if (.02 < color.x < .07 and .03 < color.y < .07
                        and .04 < color.z < .10):
                    mesh.node().setGeomState(i,state.setAttrib(
                        ColorAttrib.makeFlat((.32,.12,.035,1))))


def attach_badge(actor):
    chest = actor.find('**/joint_attachMeter')
    emblem = build_logo()
    emblem.reparentTo(chest)
    emblem.setPosHprScale(.02,.05,.04,180,0,0,.51,.51,.51)
    return emblem


def build_head(key):
    """Build original, editable low-poly head geometry for one catalog entry."""
    root = NodePath(key + '-head')
    _box(root, 'neck', (0,0,.05), (.42,.45,.28), METAL)
    if key == 'paper-shuffler':
        for i in range(9):
            sheet = _box(root, 'paper-%02d' % i,
                         (((i % 3)-1)*.035,0,.22+i*.13),
                         (1.36,.87,.125), PAPER if i % 2 else WHITE)
            sheet.setH(((i % 3)-1)*3)
        _face(root,-.48,.85,.52,sleepy=True)
        for z in (.30,.42,1.12):
            _stroke(root,'paper-edge',[(-.60,z),(.59,z+.01)],-.45,.013,METAL)
    elif key == 'rubber-stamp':
        _box(root,'stamp-pad',(0,0,.20),(1.22,.92,.35),DARK)
        _box(root,'stamp-block',(0,-.015,.42),(1.20,.9,.33),COPPER)
        _prism(root,'wood-handle',[(-.32,.57),(.32,.57),(.20,.96),
               (.22,1.38),(.49,1.74),(.47,2.00),(.26,2.20),
               (-.26,2.20),(-.47,2.00),(-.49,1.74),(-.22,1.38),(-.20,.96)],
               .65,RED)
        _face(root,-.37,.89,.37,mouth=False)
        _stroke(root,'stamp-mouth',[(-.30,.44),(0,.49),(.30,.44)],-.49,.05,DARK)
    elif key == 'desk-jockey':
        _prism(root,'horse-skull',[(-.48,.20),(.43,.20),(.58,1.20),
               (.30,1.78),(-.28,1.92),(-.55,1.30)],.88,PAPER)
        _box(root,'muzzle',(0,-.58,.58),(.95,.64,.66),METAL)
        for side in (-1,1):
            _prism(root,'ear',[(side*.30,1.60),(side*.50,2.16),
                   (side*.65,1.64)],.31,PAPER)
            _disc(root,'nostril',side*.24,-.918,.67,.085,.06,DARK)
        for i in range(6):
            _box(root,'mane',(0,.50,.50+i*.26),(.42,.36,.30),DARK)
        _face(root,-.49,1.31,.51,mouth=False)
        _stroke(root,'sneer',[(-.34,.43),(.20,.39),(.34,.46)],-.922,.045,DARK)
    elif key == 'clock-watcher':
        _box(root,'jaw',(0,-.03,.29),(.42,.53,.65),METAL)
        _disc(root,'clock-case',0,0,1.35,.94,.94,COPPER,depth=.39,sides=24)
        _disc(root,'clock-face',0,-.225,1.35,.84,.84,PAPER,sides=24)
        for i in range(12):
            a=math.pi*2*i/12
            _stroke(root,'hour',[(math.sin(a)*.66,1.35+math.cos(a)*.66),
                    (math.sin(a)*.76,1.35+math.cos(a)*.76)],-.27,.038,DARK)
        _face(root,-.30,1.47,.59,mouth=False,sleepy=True)
        _stroke(root,'hands',[(-.52,.94),(0,1.27),(.40,.91)],-.38,.075,DARK)
        _disc(root,'clock-pin',0,-.42,1.27,.09,.09,COPPER)
        _box(root,'pendulum-mouth',(0,-.32,.37),(.07,.03,.18),DARK)
    elif key == 'red-tape':
        _prism(root,'skull',[(-.71,.14),(.68,.14),(.56,1.55),
               (-.46,1.66),(-.67,1.18)],.92,PAPER)
        _face(root,-.50,.96,.55)
        for z, slope in ((.30,.18),(1.42,-.28)):
            _prism(root,'tape-front',[(-.75,z-.10),(.71,z+slope-.10),
                    (.71,z+slope+.10),(-.75,z+.10)],.045,RED,y=-.54)
            _box(root,'tape-back',(0,.50,z), (1.46,.05,.21),RED)
            for side in (-1,1):
                _box(root,'tape-side',(side*.72,0,z),( .05,1,.21),RED)
        _box(root,'tape-crown',(0,0,1.70),(.92,.9,.16),RED)
    elif key == 'bottleneck':
        _prism(root,'bottle',[(-.58,.20),(.58,.20),(.57,.64),(.35,1.18),
               (.14,1.74),(.14,2.48),(-.14,2.48),(-.14,1.74),
               (-.35,1.18),(-.57,.64)],.65,(.38,.55,.48,1))
        _box(root,'cap',(0,0,2.50),(.40,.76,.14),TEAL)
        _face(root,-.36,.89,.40)
    elif key == 'gatekeeper':
        _box(root,'face',(0,0,.95),(1.16,.75,1.57),METAL)
        _face(root,-.43,1.12,.56,mouth=False)
        _box(root,'teeth',(0,-.43,.59),(.83,.08,.26),WHITE)
        for x in (-.27,-.09,.09,.27):
            _box(root,'tooth-gap',(x,-.48,.59),(.022,.025,.25),DARK)
        for z in (.15,1.85):
            _box(root,'gate-frame',(0,-.54,z),(1.53,.25,.17),METAL)
        for x in (-.68,-.34,0,.34,.68):
            _box(root,'gate-bar',(x,-.55,1.0),(.085,.12,1.57),METAL)
        for x in (-.66,.66):
            for z in (.15,1.85):
                _disc(root,'rivet',x,-.69,z,.045,.045,DARK)
    elif key == 'head-honcho':
        _prism(root,'chin',[(-1.03,.18),(1.03,.18),(.91,.82),
               (.56,1.56),(-.56,1.56),(-.91,.82)],1.12,PAPER)
        _prism(root,'hair',[(-.64,1.29),(-.52,1.80),(.44,1.82),
               (.66,1.51),(.31,1.57),(-.23,1.62),(-.43,1.29)],1.10,DARK)
        _face(root,-.61,1.20,.60,mouth=False)
        _stroke(root,'scowl',[(-.51,.68),(-.10,.73),(.37,.68),(.51,.59)],-.61,.055,DARK)
        _box(root,'nose',(0,-.66,.98),(.22,.24,.24),METAL)
    else:
        root.removeNode()
        raise ValueError('Unknown Bureaubot: ' + str(key))
    root.setDepthTest(True)
    root.setDepthWrite(True)
    return root


def fit_head(parent, key):
    """Center an undistorted portrait inside the same box as other Cog heads."""
    holder = parent.attachNewNode(key + '-portrait')
    head = build_head(key)
    head.reparentTo(holder)
    low, high = head.getTightBounds()
    scale = min(.245 / (high.x-low.x), .255 / (high.z-low.z))
    head.setPos(-(low.x+high.x)/2, 0, -(low.z+high.z)/2)
    holder.setScale(scale)
    holder.setZ(-.005)
    return holder


def make_actor(key, model_loader):
    """Create an owned Actor; callers must stop/cleanup/remove it on close."""
    entry = next((item for item in CATALOG if item[0] == key), None)
    if entry is None:
        raise ValueError('Unknown Bureaubot: ' + str(key))
    _, name, body, scale = entry
    prefix = 'suit' + body.upper() + '-'
    phase = 'phase_3.5' if body == 'c' else 'phase_4'
    actor = Actor('phase_3.5/models/char/' + prefix + 'mod',
                  {'neutral': phase + '/models/char/' + prefix + 'neutral',
                   'walk': phase + '/models/char/' + prefix + 'walk'})
    apply_clothes(actor,model_loader)
    actor.loadAnims({anim: 'phase_%s/models/char/%s%s' % (phase,prefix,file)
                     for anim,file,phase in ANIMATIONS[body]})
    joint = actor.exposeJoint(None,'modelRoot','joint_head')
    head = build_head(key)
    head.reparentTo(joint)
    head.setH(180)
    if key in ('desk-jockey','gatekeeper'):
        head.setScale(1.16)
    actor.pose('neutral',0)
    actor.update()
    attach_badge(actor)
    actor.setScale(scale)
    actor.setName(name)
    actor.setTag('department','Bureaubots')
    actor.setTag('catalog-key',key)
    actor.loop('neutral')
    return actor
