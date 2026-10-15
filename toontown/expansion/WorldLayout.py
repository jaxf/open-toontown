"""Authored road centerlines and native art palettes, shared by build tools/travel.

Coordinates are game feet. These winding streets deliberately extend far beyond
one view, with straight approach sections at both native tunnel mouths.
"""
from math import hypot, sin, cos

# Each route is a sequence of city blocks, not a stretched sine wave. Rounded
# corners preserve distinct turns while keeping tunnel approaches straight.
ROADS = {
    19100: [(0,-558),(0,-430),(-180,-430),(-180,-220),(40,-220),
            (40,-60),(210,-60),(210,160),(-90,160),(-90,390),(0,390),(0,627.75)],
    19200: [(0,-480.5),(0,-370),(210,-370),(210,-150),(-130,-150),
            (-130,80),(130,80),(130,330),(0,330),(0,534.75)],
    61100: [(0,-496),(0,-390),(-220,-390),(-220,-170),(40,-170),
            (40,40),(240,40),(240,270),(0,270),(0,511.5)],
    61200: [(0,-465),(0,-330),(190,-330),(190,-100),(-190,-100),
            (-190,170),(85,170),(85,340),(0,340),(0,465)],
    62100: [(0,-527),(0,-410),(-190,-410),(-260,-190),(-40,-190),
            (-40,40),(195,40),(250,250),(-90,250),(-90,440),(0,440),(0,589)],
    63100: [(0,-511.5),(0,-400),(240,-400),(240,-170),(0,-170),
            (0,60),(-240,60),(-240,310),(0,310),(0,503.75)],
    63200: [(0,-503.75),(0,-380),(-220,-380),(-220,-130),(120,-130),
            (220,60),(60,230),(-140,230),(-140,370),(0,370),(0,503.75)],
    64100: [(0,-550.25),(0,-420),(210,-420),(280,-170),(30,-170),
            (-170,20),(-240,250),(0,250),(0,627.75)],
}
SIDE_ROADS = {
    19100: [[(-180,-320),(-355,-320),(-355,280),(-90,280)]],
    19200: [[(210,-260),(390,-260),(390,210),(130,210)],
            [(-130,-40),(-290,-40),(-290,150)]],
    61100: [[(-220,-280),(-400,-280),(-400,155),(240,155)]],
    61200: [[(190,-220),(390,-220),(390,265),(85,265)],
            [(-190,40),(-340,40),(-340,240)]],
    62100: [[(-40,-70),(-410,-70),(-410,345),(-90,345)]],
    63100: [[(240,-290),(420,-290),(420,180),(0,180),(0,410)]],
    63200: [[(-220,-250),(-410,-250),(-410,120),(-140,120),(-140,315)]],
    64100: [[(30,-170),(30,-20),(220,120),(220,430),(0,430)]],
}
# Small terminal courts give selected side lanes a destination of their own.
POCKETS = {19200:[(-290,150,32)],61200:[(-340,240,34)],
           19100:[(-355,80,30)],61100:[(-400,40,34)],
           62100:[(-410,190,30)],63100:[(420,40,38)],
           63200:[(-410,-50,32)],64100:[(220,300,38)]}

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


def rounded_blocks(points, radius=60, steps=12):
    """Straight block fronts with quadratic corner fillets; no spline overshoot."""
    result=[tuple(points[0])]
    for a,b,c in zip(points,points[1:],points[2:]):
        ab=hypot(b[0]-a[0],b[1]-a[1]);bc=hypot(c[0]-b[0],c[1]-b[1])
        trim=min(radius,ab*.42,bc*.42)
        entry=tuple(b[j]+(a[j]-b[j])*trim/ab for j in (0,1))
        leave=tuple(b[j]+(c[j]-b[j])*trim/bc for j in (0,1))
        result.append(entry)
        for k in range(1,steps+1):
            t=k/steps
            result.append(tuple((1-t)**2*entry[j]+2*t*(1-t)*b[j]+t*t*leave[j] for j in (0,1)))
    result.append(tuple(points[-1]))
    return result


def road_paths(zone):
    return [rounded_blocks(ROADS[zone])]+[rounded_blocks(p) for p in SIDE_ROADS[zone]]


def street_bounds(zone, margin=95):
    points=[p for route in road_paths(zone) for p in route]
    return (min(p[0] for p in points)-margin,min(p[1] for p in points)-margin,
            max(p[0] for p in points)+margin,max(p[1] for p in points)+margin)


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
        return 0.0  # Street buildings, courtyards and their approaches stay level.
    else:
        rx,ry=(141,128) if zone==19000 else (170,151)
        edge=max(0,min(1,(max(abs(x)/rx,abs(y)/ry)-1)*8))
    return edge*edge*(3-2*edge)*(2.3+1.2*sin(x*.055)*cos(y*.045))
