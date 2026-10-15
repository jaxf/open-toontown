"""Small flat-shaded mesh primitives; no generated binary assets required."""
from math import cos, sin, pi
from panda3d.core import (Geom, GeomNode, GeomTriangles, GeomVertexData,
                          GeomVertexFormat, GeomVertexWriter, CollisionNode,
                          CollisionBox, Point3, BitMask32, TextNode)


def mesh(parent, name, vertices, faces, color):
    data = GeomVertexData(name, GeomVertexFormat.getV3n3c4(), Geom.UHStatic)
    writer = GeomVertexWriter(data, 'vertex')
    normal = GeomVertexWriter(data, 'normal')
    colors = GeomVertexWriter(data, 'color')
    tris = GeomTriangles(Geom.UHStatic)
    row = 0
    for face in faces:
        a, b, c = [Point3(*vertices[i]) for i in face[:3]]
        n = (b - a).cross(c - a)
        n.normalize()
        # Baked shading also looks right in the unlit legacy renderer.
        shade = .72 + .28 * max(0, n.dot(Point3(-.3, -.5, .8)))
        for index in face:
            writer.addData3(*vertices[index])
            normal.addData3(n)
            colors.addData4(color[0] * shade, color[1] * shade, color[2] * shade, color[3])
        for j in range(1, len(face) - 1):
            tris.addVertices(row, row + j, row + j + 1)
        row += len(face)
    geom = Geom(data)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    result = parent.attachNewNode(node)
    result.setTwoSided(True)
    return result


def box(parent, name, pos, size, color, solid=False):
    x, y, z = [n / 2 for n in size]
    vertices = [(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),
                (-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    faces = [(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]
    node = mesh(parent, name, vertices, faces, color)
    node.setPos(*pos)
    if solid:
        collider = CollisionNode(name + '-wall')
        collider.setFromCollideMask(BitMask32.allOff())
        # OTP wall bit, kept explicit so this module can render standalone.
        collider.setIntoCollideMask(BitMask32.bit(0))
        collider.addSolid(CollisionBox(Point3(0, 0, 0), x, y, z))
        node.attachNewNode(collider)
    return node


def cylinder(parent, name, pos, radius, height, color, top=None, sides=12):
    top = radius if top is None else top
    verts = [(cos(i*2*pi/sides)*r, sin(i*2*pi/sides)*r, z)
             for r,z in ((radius,0),(top,height)) for i in range(sides)]
    faces = [tuple(reversed(range(sides))), tuple(range(sides, sides*2))]
    faces += [(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)]
    node = mesh(parent, name, verts, faces, color)
    node.setPos(*pos)
    return node


def label(parent, text, pos, scale=2, color=(1, .94, .74, 1)):
    node = TextNode('sign-' + text)
    node.setText(text)
    node.setAlign(TextNode.ACenter)
    node.setTextColor(*color)
    node.setWordwrap(18)
    path = parent.attachNewNode(node)
    path.setPos(*pos)
    path.setScale(scale)
    return path


def sphere(parent, name, pos, radius, color, rings=7, sides=12):
    verts=[]
    for j in range(rings+1):
        latitude=-pi/2+j*pi/rings
        for i in range(sides):
            longitude=i*2*pi/sides
            verts.append((radius*cos(latitude)*cos(longitude),
                          radius*cos(latitude)*sin(longitude),radius*sin(latitude)))
    faces=[]
    for j in range(rings):
        for i in range(sides):
            a=j*sides+i; b=j*sides+(i+1)%sides
            faces.append((a,b,b+sides,a+sides))
    node=mesh(parent,name,verts,faces,color)
    node.setPos(*pos)
    return node
