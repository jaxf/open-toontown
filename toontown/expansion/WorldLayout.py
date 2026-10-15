"""Authored road centerlines and native art palettes, shared by build tools/travel.

Coordinates are game feet. These winding streets deliberately extend far beyond
one view, with straight approach sections at both native tunnel mouths.
"""
from math import hypot, sin, cos

ROADS = {
    19100: [(0,-360),(0,-305),(35,-230),(64,-150),(35,-65),(-28,15),
            (-62,100),(-24,190),(25,275),(0,355),(0,405)],
    19200: [(0,-310),(0,-265),(-36,-210),(-68,-145),(-42,-80),(18,-25),
            (50,45),(36,115),(-20,185),(-18,255),(0,310),(0,345)],
    61100: [(0,-320),(0,-270),(45,-215),(70,-145),(48,-65),(-15,5),
            (-62,80),(-55,150),(-12,220),(0,280),(0,330)],
    61200: [(0,-300),(0,-250),(-45,-195),(-62,-115),(-24,-45),(38,25),
            (60,100),(30,180),(0,240),(0,300)],
    62100: [(0,-340),(0,-290),(-42,-220),(-60,-150),(-20,-75),(38,0),
            (62,80),(32,155),(-25,225),(-15,290),(0,345),(0,380)],
    63100: [(0,-330),(0,-280),(42,-210),(58,-130),(15,-50),(-42,30),
            (-62,105),(-35,180),(0,255),(0,325)],
    63200: [(0,-325),(0,-275),(-38,-205),(-58,-125),(-15,-45),(48,35),
            (70,110),(42,185),(0,255),(0,325)],
    64100: [(0,-355),(0,-300),(48,-230),(73,-155),(38,-80),(-28,-5),
            (-65,75),(-43,160),(12,240),(12,305),(0,365),(0,405)],
}
# More distance between bends; each route keeps its own silhouette.
ROADS = {zone:[(round(x*1.48,2), round(y*1.55,2)) for x,y in points]
         for zone,points in ROADS.items()}

PLAZA_GATES = {
    61000: ((0,-140,0,0),(-155,25,0,-90)),
    62000: ((25,-135,0,0),(-150,55,0,-90)),
    63000: ((0,-155,0,0),(-160,-25,0,-90),(160,55,0,90)),
    64000: ((-20,-150,0,0),(-170,50,0,-90)),
}
# Deliberately different street proportions and pacing for each district.
ROAD_PROFILES={
    19100:dict(road=11,sidewalk=21,frontage=32,spacing=35,court=7),
    19200:dict(road=11,sidewalk=20,frontage=30,spacing=34,court=7),
    61100:dict(road=13,sidewalk=25,frontage=35,spacing=31,court=8),
    61200:dict(road=14,sidewalk=24,frontage=34,spacing=33,court=9),
    62100:dict(road=10,sidewalk=20,frontage=30,spacing=35,court=6),
    63100:dict(road=17,sidewalk=28,frontage=38,spacing=32,court=8),
    63200:dict(road=15,sidewalk=25,frontage=35,spacing=34,court=7),
    64100:dict(road=16,sidewalk=26,frontage=36,spacing=38,court=5),
}
# Native building modules preserve original silhouettes, painted surfaces and UVs.
PALETTES = {
    19000: dict(code='DG', phase=8, ground='phase_3.5/maps/dustroad.jpg',
                paving='phase_3.5/maps/cobblestone_brown.jpg', road='phase_3.5/maps/dustroad.jpg',
                tint=(.89,.96,.77,1)),
    61000: dict(code='DD', phase=6, ground='phase_3.5/maps/dustroad.jpg',
                paving='phase_3.5/maps/boardwalk_floor.jpg', road='phase_3.5/maps/cobblestone_brown.jpg',
                tint=(1,.96,.84,1)),
    62000: dict(code='DL', phase=8, ground='phase_8/maps/brick_floor_Ncont_purple.jpg',
                paving='phase_8/maps/DL_brick_floor.jpg', road='phase_8/maps/brick_floor_Ncont_purple.jpg',
                tint=(.65,.72,.88,1)),
    63000: dict(code='MM', phase=6, ground='phase_6/maps/brick_floor_grey.jpg',
                paving='phase_6/maps/brick_floor_Ncont_red.jpg', road='phase_6/maps/brick_floor_grey.jpg',
                tint=(.95,.97,.87,1)),
    64000: dict(code='DG', phase=8, ground='phase_6/maps/Rural_dustroad.jpg',
                paving='phase_3.5/maps/boardwalk_floor.jpg', road='phase_6/maps/Rural_dustroad.jpg',
                tint=(1,.84,.61,1)),
}

def curve(points, steps=12):
    p=[points[0]]+list(points)+[points[-1]]
    result=[]
    for i in range(1,len(p)-2):
        a,b,c,d=p[i-1:i+3]
        for k in range(steps):
            t=k/steps
            result.append(tuple(.5*(2*b[j]+(-a[j]+c[j])*t+
                (2*a[j]-5*b[j]+4*c[j]-d[j])*t*t+
                (-a[j]+3*b[j]-3*c[j]+d[j])*t*t*t) for j in (0,1)))
    return result+[tuple(points[-1])]


def along(points, spacing=32, margin=48):
    """Even arc-length placements; each includes a unit tangent for facades."""
    distances=[0]
    for a,b in zip(points,points[1:]):
        distances.append(distances[-1]+hypot(b[0]-a[0],b[1]-a[1]))
    target=margin
    i=1
    while target < distances[-1]-margin:
        while distances[i] < target:
            i+=1
        a,b=points[i-1:i+1]
        length=distances[i]-distances[i-1]
        t=(target-distances[i-1])/length
        yield (a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,
               (b[0]-a[0])/length,(b[1]-a[1])/length)
        target+=spacing


def road_paths(zone):
    """Main winding street plus a curving loop with two actual T junctions."""
    control=ROADS[zone]
    first,last=control[3],control[6]
    # Alternate the side and bend rhythm, retaining clear tunnel approaches.
    side=-1 if zone in (19100,61200,63100,64100) else 1
    edge=side*157
    dy=last[1]-first[1]
    branch=[first,(first[0]+side*42,first[1]+14),
            (edge-side*12,first[1]+dy*.23),(edge,first[1]+dy*.50),
            (edge-side*23,first[1]+dy*.80),(last[0]+side*43,last[1]-12),last]
    return [curve(control),curve(branch)]


def distance_to_path(x,y,path):
    best=float('inf')
    for (ax,ay),(bx,by) in zip(path,path[1:]):
        dx,dy=bx-ax,by-ay
        t=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/max(.001,dx*dx+dy*dy)))
        best=min(best,hypot(x-ax-t*dx,y-ay-t*dy))
    return best


def terrain_height(zone,x,y):
    # Keep all authored footprints and routes level. Low, smoothly blended banks
    # at the perimeter create terrain without burying doors or floating props.
    if zone in ROADS:
        edge=max(0,min(1,(abs(x)-183)/25))
    else:
        rx,ry=(141,128) if zone==19000 else (170,151)
        edge=max(0,min(1,(max(abs(x)/rx,abs(y)/ry)-1)*8))
    return edge*edge*(3-2*edge)*(2.3+1.2*sin(x*.055)*cos(y*.045))
