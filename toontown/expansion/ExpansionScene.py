"""Authored neighborhood silhouettes, streets and native link tunnels."""
from math import cos, sin, pi
from panda3d.core import (NodePath, CollisionNode, CollisionPolygon, CollisionBox,
                          Point3, BitMask32)
from . import ExpansionGlobals as E
from .Geometry import box, cylinder, label, sphere

CREAM = (.98, .90, .70, 1)
DARK = (.17, .19, .23, 1)


def floor(parent, name, x, y, width, depth, z=0, color=CREAM):
    box(parent, name, (x, y, z-.22), (width, depth, .4), color)
    node = CollisionNode(name + '-floor')
    node.setFromCollideMask(BitMask32.allOff())
    node.setIntoCollideMask(BitMask32.bit(1))
    node.addSolid(CollisionPolygon(Point3(x-width/2,y-depth/2,z),
                                   Point3(x+width/2,y-depth/2,z),
                                   Point3(x+width/2,y+depth/2,z),
                                   Point3(x-width/2,y+depth/2,z)))
    parent.attachNewNode(node)


def tree(parent, x, y, color, scale=1):
    root = parent.attachNewNode('crooked-tree')
    root.setPos(x, y, 0)
    root.setScale(scale)
    cylinder(root, 'trunk', (0,0,0), 1.3, 9, (.40,.25,.13,1), .7)
    for dx,dy,z,r in ((0,0,7,5),(-2,1,10,4),(2,-1,12,3.4)):
        sphere(root, 'leaf-cluster', (dx,dy,z), r, color)
    box(root, 'trunk-collision', (0,0,3.5), (1.6,1.6,7), (.40,.25,.13,1), True)
    return root


def shop(parent, name, pos, heading, colors, theme, index):
    root = parent.attachNewNode('shop-' + name)
    root.setPos(*pos)
    root.setH(heading)
    height = 11 + (index % 3) * 2
    primary, secondary, accent = colors
    body = box(root, 'facade', (0,0,height/2), (13,10,height), primary, True)
    body.setR((-1 if index % 2 else 1) * 2)
    box(root, 'foundation', (0,0,.7), (14,11,1.4), secondary, True)
    if theme in ('woodland','spooky'):
        cylinder(root, 'storybook-roof', (0,0,height), 10, 6, secondary, 0, 4).setH(45)
    else:
        box(root, 'roof-cornice', (0,0,height), (15,12,1.4), secondary)
    # Storefronts face -Y, with deep trim and alternating striped awnings.
    box(root, 'door', (0,-5.15,3.1), (2.8,.3,5.5), DARK)
    for x in (-4.3,4.3):
        box(root, 'window-trim', (x,-5.2,5), (3.8,.4,4.4), secondary)
        box(root, 'window', (x,-5.45,5), (3,.1,3.6), accent)
        box(root, 'window-cross', (x,-5.55,5), (.2,.15,3.6), CREAM)
    for i in range(7):
        box(root, 'awning', (-6+i*2,-6.1,8), (2,3,.45), accent if i%2 else CREAM)
    box(root, 'signboard', (0,-5.5,height-1), (12,.5,2.5), secondary)
    label(root, name, (0,-5.85,height-1.5), .85)
    if theme == 'studio':
        for x in range(-6,7,2):
            cylinder(root, 'marquee-bulb', (x,-6.4,8.5), .24, .3, CREAM)
    if theme == 'desert':
        box(root, 'porch', (0,-7,.2), (14,5,.4), secondary)
        for x in (-6,6):
            box(root, 'porch-post', (x,-8,4), (.4,.4,8), secondary, True)
    return root


def landmark(parent, hood):
    spec = E.NEIGHBORHOODS[hood]
    a,b,c = spec['colors']
    root = parent.attachNewNode('landmark')
    root.setPos(0,25,0)
    if hood == E.ACORN:
        # Hollow trunk made of posts: entrance and central space stay walkable.
        for i in range(12):
            angle = i*2*pi/12
            if i in (8,9,10):
                continue
            x,y = cos(angle)*9,sin(angle)*9
            box(root, 'oak-wall', (x,y,10), (3,3,20), (.43,.27,.14,1), True)
        for i in range(7):
            ang=i*2*pi/7
            sphere(root, 'oak-crown', (cos(ang)*7,sin(ang)*7,25), 10, a if i%3 else b)
        sphere(root, 'oak-cap', (0,0,31), 11, a)
        floor(root,'oak-room',0,0,16,16,.08,(.65,.46,.28,1))
        box(root,'oak-sign',(0,-9,14),(17,1,3),b)
        label(root,'THE GREAT OAK',(0,-9.6,13),1.25)
    elif hood == E.BRINY:
        for i in range(6):
            cylinder(root,'lighthouse-stripe',(0,0,i*4),7-i*.55,4,c if i%2 else b,6.45-i*.55)
        cylinder(root,'lantern-room',(0,0,24),4,5,a,4)
        cylinder(root,'lantern-roof',(0,0,29),6,5,b,0)
        box(root,'tower-base',(0,0,9),(8,8,18),c,True)
        for x in (-2,2):
            box(root,'lantern-glow',(x,-3.8,26),(2,.3,3),CREAM)
    elif hood == E.HUSH:
        tower=box(root,'clock-tower',(0,0,13),(12,11,26),b,True)
        tower.setR(-4)
        cylinder(root,'clock-roof',(0,0,26),10,9,a,0,4).setH(45)
        face=cylinder(root,'clock-face',(0,-5.7,20),4,.2,CREAM,sides=24)
        face.setP(90)
        box(root,'clock-hand',(0,-6,21.2),(.3,.3,2.5),DARK)
        box(root,'clock-hand',(-1,-6,20),(2,.3,.3),DARK)
        for x in (-5,5):
            cylinder(root,'pumpkin',(x,-10,.3),2,2,c,1.6,10)
    elif hood == E.DOODLEWOOD:
        box(root,'theater',(0,0,13),(30,18,26),a,True)
        box(root,'theater-marquee',(0,-11,12),(35,7,3),c)
        label(root,'THE REEL BIG\nTHEATER',(0,-14.6,12),1.8)
        floor(root,'red-carpet',0,-21,12,17,.05,a)
        reel=cylinder(root,'film-reel',(0,-.5,31),8,2,b,sides=24)
        reel.setP(90)
        for i in range(5):
            ang=i*2*pi/5
            hole=cylinder(root,'reel-hole',(cos(ang)*4.5,-2.6,31+sin(ang)*4.5),1.6,.2,DARK,sides=12)
            hole.setP(90)
        for x in (-12,-6,0,6,12):
            box(root,'theater-door',(x,-9.2,4),(4,.4,8),DARK)
    else:
        for x in (-6,6):
            for y in (-5,5):
                box(root,'water-tower-leg',(x,y,11),(1.5,1.5,22),b,True)
        cylinder(root,'hat-brim',(0,0,22),13,1.5,b,13,20)
        cylinder(root,'hat-crown',(0,0,23.5),8,10,c,6,12)
        cylinder(root,'hat-band',(0,0,24),8.1,2,a,7.8,12)
    label(root,spec['landmark'],(0,-15,2),1.3)


def tunnel(parent, target, transform, colors):
    """Uses the existing tunnel movies, collision events, and return naming."""
    target_hood = E.hood_id(target)
    short = E.NEIGHBORHOODS[target_hood]['short'] if target_hood in E.NEIGHBORHOODS else E.SOURCE_CODES[target_hood]
    # Reuse the original curved tunnel and its collision/origin nodes: its
    # bend is authored to match DistributedToon's existing tunnel movies.
    from direct.showbase import ShowBaseGlobal
    root = parent.attachNewNode('linktunnel_%s_%s' % (short,target))
    model = ShowBaseGlobal.base.loader.loadModel('phase_4/models/modules/safe_zone_tunnel_TT')
    # Stock DNA places this model in world coordinates. Rebase its authored
    # tunnel origin before positioning it in our local scene.
    origin = model.find('**/tunnel_origin')
    inverse = origin.getTransform(model).getInverse()
    model.reparentTo(root)
    model.setTransform(inverse)
    root.setPos(*transform[:3])
    root.setH(transform[3])
    a,b,c = colors
    root.setColorScale(*c)
    floor(root,'tunnel-apron',0,8,25,20,0,b)
    plaque=box(root,'destination-sign',(0,2,17),(21,1,3.8),b)
    plaque.setColorScaleOff()
    text=label(root,E.zone_name(target),(0,2.7,16),1.15)
    text.setColorScaleOff()
    text.setH(180)

    return root


def add_tunnels(parent, zone):
    hood = E.hood_id(zone)
    if hood not in E.NEIGHBORHOODS:
        hood = E.hood_id(E.connections(zone)[0])
    colors = E.NEIGHBORHOODS[hood]['colors']
    for target, transform in zip(E.connections(zone),E.gate_transforms(zone)):
        tunnel(parent,target,transform,colors)


def build_scene(zone, dna_store=None):
    if zone in (E.ACORN, 19100):
        from .AcornDNA import load_scene
        return load_scene(zone, dna_store)
    hood = E.hood_id(zone)
    spec = E.NEIGHBORHOODS[hood]
    a,b,c = spec['colors']
    root=NodePath('expansion-%s' % zone)
    street=zone in E.STREETS
    width,depth=(86,210) if street else (210,210)
    floor(root,'ground',0,0,width,depth,color=a if hood==E.ACORN else c)
    # Invisible fall-proof boundary sits beyond the tunnel interiors.
    for x,y,w,d in ((-width/2,0,2,depth),(width/2,0,2,depth),
                    (0,-depth/2,width,2),(0,depth/2,width,2)):
        wall=box(root,'boundary',(x,y,5),(w,d,10),a,True)
        wall.hide()
    if street:
        floor(root,'promenade',0,0,20,175,.03,(.71,.60,.45,1))
        names=('Window Shopping','A Little Offbeat','Pun Intended','Open Sesame','The Last Laugh','Small Change')
        for i,y in enumerate((-48,-6,36)):
            for side in (-1,1):
                index=i*2+(side==1)
                shop(root,names[index],(side*29,y,0),side*-90,spec['colors'],spec['theme'],index)
                if hood in (E.ACORN,E.HUSH):
                    tree(root,side*29,y+17,b if i%2 else a,.7)
        # The far end introduces the next neighborhood's palette.
        destination=E.STREETS[zone][3]
        if destination in E.NEIGHBORHOODS and destination != hood:
            other=E.NEIGHBORHOODS[destination]
            shop(root,'Around the Bend',(-29,66,0),90,other['colors'],other['theme'],0)
    else:
        floor(root,'central-plaza',0,-12,40,70,.03,(.78,.68,.50,1))
        floor(root,'cross-path',0,0,140,16,.04,(.78,.68,.50,1))
        names={E.ACORN:('Knot a Problem','Acorny Jokes','Leaf It to Me','Branch Office'),
               E.BRINY:('Saltwater Smiles','Pier Pressure','Taffy Together','Shell We Dance'),
               E.HUSH:('Boo-tique','Rest in Pieces','Fright & Early','The Creak Easy'),
               E.DOODLEWOOD:('Take Two','Reel Deals','Props to You','Star Treatment'),
               E.TUMBLEWEED:('Dry Humor','High Noon Noodles','Cactus Practice','Well I Never')}[hood]
        layouts = {
            E.ACORN: ((-39,-32,135),(39,-32,-135),(-39,35,45),(39,35,-45)),
            E.BRINY: ((-43,42,0),(40,42,0),(-35,-30,150),(35,-30,-150)),
            E.HUSH: ((-36,25,50),(36,35,-50),(-30,-35,135),(38,-27,-120)),
            E.DOODLEWOOD: ((-40,32,90),(40,32,-90),(-40,-32,90),(40,-32,-90)),
            E.TUMBLEWEED: ((-30,-38,90),(38,-20,-90),(-36,24,90),(37,45,-90)),
        }
        for i,(x,y,h) in enumerate(layouts[hood]):
            shop(root,names[i],(x,y,0),h,spec['colors'],spec['theme'],i)
        landmark(root,hood)
        # Each neighborhood has a different ground treatment and silhouette.
        if hood == E.BRINY:
            for y in range(-45,54,6):
                box(root,'boardwalk', (0,y,.04),(122,5.8,.06),(.64,.46,.31,1))
        elif hood == E.HUSH:
            cylinder(root,'cobblestone-plaza',(0,12,.04),32,.04,(.49,.47,.53,1),sides=24)
        elif hood == E.DOODLEWOOD:
            box(root,'studio-carpet',(0,-20,.08),(16,70,.08),a)
            for y in range(-45,18,12):
                for x in (-12,12):
                    cylinder(root,'velvet-rope-post',(x,y,0),.3,3,c)
        elif hood == E.TUMBLEWEED:
            for x,y,h in ((-5,-55,-20),(0,-25,12),(-4,5,-20),(2,35,15)):
                box(root,'dry-creek',(x,y,.03),(12,35,.04),(.58,.36,.22,1)).setH(h)
            box(root,'creek-footbridge',(0,0,.12),(30,11,.15),(.64,.46,.31,1))
        if hood in (E.ACORN,E.HUSH):
            for i in range(12):
                ang=i*2*pi/12
                # Keep the three tunnel paths clear.
                if i in (0,6,9):
                    continue
                tree(root,cos(ang)*82,sin(ang)*82,b if i%3 else a,1.2)
        elif hood==E.BRINY:
            floor(root,'lagoon',0,76,125,28,.02,(.18,.59,.71,1))
            for x in range(-55,56,5):
                box(root,'boardwalk-plank',(x,54,.18),(4.8,16,.35),(.65,.45,.28,1))
            for x in (-49,49):
                cylinder(root,'parasol',(x,18,9),7,3,b,0,12)
                box(root,'parasol-pole',(x,18,4.5),(.4,.4,9),CREAM,True)
        elif hood==E.DOODLEWOOD:
            for x in (-67,67):
                box(root,'backlot-wall',(x,50,10),(18,3,20),b,True)
                label(root,'STAGE '+str(abs(x)//10),(x,48,10),1.4,DARK)
        else:
            for x,y in ((-75,50),(75,50),(-75,-40),(75,-40)):
                cylinder(root,'cactus',(x,y,0),1.4,11,b,1)
                box(root,'cactus-arm',(x+2,y,6),(5,2,2),b,True)
                cylinder(root,'mesa',(x,y+30,0),16,20,a,12,7)
    add_tunnels(root,zone)
    return root
