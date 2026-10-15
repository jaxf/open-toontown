"""Bake connected street paving and enclosing yards (requires shapely >= 2.1).

Shapely is an authoring dependency only. The game reads the exported BAMs.
"""
from shapely import constrained_delaunay_triangles
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union
from toontown.expansion.WorldLayout import road_paths, ROAD_PROFILES, PALETTES, POCKETS, street_bounds
from toontown.expansion import ExpansionGlobals as E, Services
from panda3d.core import NodePath


def corridor(zone, width):
    return unary_union([LineString(p).buffer(width, quad_segs=8) for p in road_paths(zone)])


def surface(root, A, shape, name, texture, z, color, collide=False):
    mesh=A.Mesh(name,texture)
    floor=A.collider(root,name+'-floor',2) if collide else None
    for triangle in constrained_delaunay_triangles(shape).geoms:
        points=list(triangle.exterior.coords)[:3]
        a,b,c=points
        if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<0:points.reverse()
        points=[(x,y,z) for x,y in points]
        mesh.face(points,color=color,shade=False)
        if floor is not None:A.collision_face(floor,points)
    mesh.attach(root,ground_layer=round(z*1000))


def build(zone,A):
    from tools.world_dressing import fence,perimeter
    hood=E.hood_id(zone);spec=PALETTES[hood];profile=ROAD_PROFILES[zone]
    root=NodePath('terrain-'+str(zone))
    road=corridor(zone,profile['road'])
    paving=corridor(zone,profile['sidewalk'])
    yards=corridor(zone,profile['frontage']+26)
    center,anchor=Services.street_court(zone)
    service=Point(center).buffer(45,quad_segs=12)
    approach=LineString([anchor,center]).buffer(16,quad_segs=8)
    paving=unary_union([paving,service,approach]+[
        Point(x,y).buffer(r,quad_segs=12) for x,y,r in POCKETS.get(zone,[])])
    yards=unary_union([yards,paving.buffer(12,quad_segs=8)])
    # One continuous foundation extends beyond every boundary, including at
    # wide FOV. The paved polygons are unions, so junctions cannot tear/overlap.
    surface(root,A,box(*street_bounds(zone,140)),'continuous-ground',spec['ground'],0,spec['tint'],True)
    surface(root,A,paving,'connected-sidewalks',spec['paving'],.055,spec['tint'],True)
    surface(root,A,road,'connected-road',spec['road'],.09,spec['tint'],True)
    boundary=root.attachNewNode('enclosed-street-blocks')
    gates=E.gate_transforms(zone)
    polygons=list(yards.geoms) if hasattr(yards,'geoms') else [yards]
    for polygon in polygons:
        for ring in [polygon.exterior]+list(polygon.interiors):
            # Short segments allow precise openings at tunnel mouths.
            line=LineString(ring.coords);count=max(1,int(line.length/7))
            for i in range(count):
                a=line.interpolate(i/count,normalized=True)
                b=line.interpolate((i+1)/count,normalized=True)
                mid=line.interpolate((i+.5)/count,normalized=True)
                if any(abs(mid.x-gx)<30 and abs(mid.y-gy)<72 for gx,gy,gz,h in gates):continue
                fence(boundary,hood,A,[(a.x,a.y),(b.x,b.y)],13)
    boundary.flattenStrong()
    perimeter(root,zone,A)  # Native HQ enclosure; street perimeter is above.
    return root
