"""Build textured expansion models. Layouts are authored separately in DNA.

Uses original game materials/modules, with custom geometry for landmarks,
terrain, shop backs, porches, awnings, rails and small props.
"""
import sys
from pathlib import Path
from math import sin, cos, pi, sqrt, atan2, degrees, hypot
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import build_acorn_models as A
from toontown.expansion import ExpansionGlobals as E
from toontown.expansion.WorldLayout import ROADS, PLAZA_GATES, PALETTES, ROAD_PROFILES, curve, road_paths, terrain_height
from panda3d.core import NodePath, Point3, CollisionBox, CollisionSphere, TransparencyAttrib, TextureStage
OUT=ROOT/'assets/expansion/models'
GOLD=(1,.78,.30,1); CREAM=(1,.94,.75,1); TEAL=(.28,.70,.64,1)
WOOD='phase_3.5/maps/panel_stucco.jpg'
TIMBER='phase_3.5/maps/wood1.jpg'
STONE='phase_8/maps/DL_bricks.jpg'


# Sample the plain painted center of the stock stucco atlas. The outer trim
# belongs to wall panels and must not tile across custom roofs and landmarks.
_board, _tube = A.board, A.tube

def painted_board(*args, **kwargs):
    node=_board(*args, **kwargs)
    if any(str(t.getFilename()).endswith('panel_stucco.jpg') for t in node.findAllTextures()):
        node.setTexScale(TextureStage.getDefault(),.16,.16)
        node.setTexOffset(TextureStage.getDefault(),.42,.42)
    return node

def painted_tube(*args, **kwargs):
    node=_tube(*args, **kwargs)
    if any(str(t.getFilename()).endswith('panel_stucco.jpg') for t in node.findAllTextures()):
        node.setTexScale(TextureStage.getDefault(),.08,.08)
        node.setTexOffset(TextureStage.getDefault(),.42,.42)
    return node

A.board, A.tube = painted_board, painted_tube


def ring(parent,name,z,radius,tube_radius,color=GOLD,center=(0,0)):
    pts=[(center[0]+radius*cos(i*pi/24),center[1]+radius*sin(i*pi/24),z,tube_radius) for i in range(49)]
    A.tube(parent,name,pts,WOOD,color,8)


def bulb(parent,name,pos,radius,color=CREAM):
    x,y,z=pos
    A.tube(parent,name,[(x,y,z-radius,.01),(x,y,z-radius*.7,radius*.7),
        (x,y,z,radius),(x,y,z+radius*.7,radius*.7),(x,y,z+radius,.01)],None,color,10)


def lantern(parent,pos):
    x,y,z=pos
    A.tube(parent,'lantern-post',[(x,y,z,.5),(x+.5,y,z+6,.35),(x,y,z+10,.4)],WOOD,TEAL)
    A.board(parent,'lantern-glass',(x,y,z+11),(2,2,3),CREAM,None)
    A.tube(parent,'lantern-cap',[(x,y,z+12.5,1.7),(x,y,z+14,.03)],WOOD,TEAL,8)


def western_lamp():
    root=NodePath('western-lantern')
    lantern(root,(0,0,0))
    A.collider(root,'lamp-post',1).addSolid(CollisionBox(Point3(0,0,5),.6,.6,5))
    return root


def lighthouse():
    r=NodePath('loopy-lighthouse')
    A.tube(r,'stone-footing',[(0,0,0,12),(0,0,2,13),(0,0,3,11)],STONE,CREAM,24,True)
    for i in range(9):
        z=3+i*5
        dx=2.4*sin(z/20)
        A.tube(r,'painted-tapered-stripe',[(dx,0,z,10-z*.10),
            (2.4*sin((z+5)/20),0,z+5,10-(z+5)*.10)],WOOD,
            (.91,.31,.24,1) if i%2 else CREAM,24,True)
    x=2.4*sin(48/20)
    A.tube(r,'lookout-deck',[(x,0,48,8),(x,0,49,8)],WOOD,TEAL,24)
    for i in range(16):
        a=i*pi/8
        A.tube(r,'balcony-spindle',[(x+7*cos(a),7*sin(a),49,.16),
            (x+7*cos(a),7*sin(a),52,.16)],None,CREAM,6)
    ring(r,'balcony-rail',52,7,.22,CREAM,(x,0))
    A.tube(r,'golden-lantern',[(x,0,49,4.8),(x,0,57,4.8)],None,(1,.87,.41,1),12)
    for i in range(8):
        a=i*pi/4
        A.tube(r,'lantern-frame',[(x+4.9*cos(a),4.9*sin(a),49,.25),
            (x+4.9*cos(a),4.9*sin(a),57,.25)],WOOD,TEAL,6)
    A.tube(r,'lantern-roof',[(x,0,57,7),(x-.8,0,62,1),(x-1,0,64,.05)],WOOD,TEAL,16)
    A.board(r,'welcome-plaque',(0,-10.1,11),(15,1,4),TEAL,WOOD)
    A.text(r,'LOOPY LIGHT',(0,-10.7,10.2),1.3)
    for z in (18,31,41):
        A.board(r,'porthole-frame',(1,-(10-z*.1),z),(3,.7,4),TEAL,WOOD)
        A.board(r,'porthole-glass',(1,-(10-z*.1)-.4,z),(2,.2,3),CREAM,None)
    return r


def clock_tower():
    r=NodePath('backwards-clock-tower')
    A.board(r,'stone-base',(0,0,2),(23,20,4),(.64,.57,.74,1),STONE)
    A.collider(r,'clock-wall',1).addSolid(CollisionBox(Point3(0,0,24),10,8,24))
    for i in range(4):
        z=4+i*9
        A.board(r,'crooked-storey',(sin(i)*1.2,0,z+4.5),(18-i*1.3,15-i*.8,9),
                (.58,.51,.72,1),STONE).setR((-1 if i%2 else 1)*2)
        A.board(r,'cornice',(sin(i)*1.2,0,z+9),(20-i*1.3,17-i*.8,1),TEAL,WOOD)
        if i<3:
            for x in (-4.5,4.5):
                A.board(r,'tall-lit-window',(x,-8,z+4.3),(2.7,.3,5),CREAM,None)
                A.board(r,'window-cross',(x,-8.2,z+4.3),(.25,.2,5.2),TEAL,WOOD)
    face=r.attachNewNode('clock-face')
    face.setPos(0,-10,34);face.setP(90)
    A.disk(face,'ivory-face',(0,0),6.5,6.5,None,.1)
    dial=face.find('**/ivory-face');dial.clearBin();dial.setDepthWrite(True);dial.setColor(*CREAM)
    ring(face,'clock-rim',.3,6.6,.5,GOLD)
    # Backwards numerals are an intentional Toontown gag.
    for i in range(12):
        a=pi/2+i*pi/6
        x,y=4.9*cos(a),4.9*sin(a)
        mark=A.board(face,'clock-tick',(x,y,.4),(.3,1,.25),(.22,.19,.30,1),None)
        mark.setH(degrees(a)-90)
    A.board(face,'minute-hand',(0,1.7,.6),(.4,3.7,.2),(.17,.20,.25,1),None)
    A.board(face,'hour-hand',(-1,0,.8),(2.5,.45,.2),(.17,.20,.25,1),None)
    A.tube(r,'crooked-spire',[(0,0,40,14),(1,0,44,10),(-2,0,51,7),
        (1,0,58,3),(-3,0,66,.1)],WOOD,(.27,.32,.48,1),4)
    bulb(r,'moon-finial',(-3,0,67),1.8,GOLD)
    A.board(r,'tower-sign',(0,-9,13),(19,1,3),TEAL,WOOD)
    A.text(r,'BETTER LATE!',(0,-9.6,12.3),1.3)
    return r


def reel(parent,pos,radius=6):
    wheel=parent.attachNewNode('film-reel');wheel.setPos(*pos);wheel.setP(90)
    A.tube(wheel,'reel-disc',[(0,0,0,radius),(0,0,.6,radius)],WOOD,GOLD,24)
    ring(wheel,'reel-rim',.7,radius,.35,CREAM)
    for i in range(5):
        a=i*2*pi/5
        A.tube(wheel,'reel-hole',[(radius*.57*cos(a),radius*.57*sin(a),.7,radius*.19),
            (radius*.57*cos(a),radius*.57*sin(a),.8,radius*.19)],None,(.17,.25,.29,1),12)


def theater():
    r=NodePath('reel-big-theater')
    A.board(r,'theater-building',(0,7,18),(52,27,36),(.79,.40,.39,1),STONE)
    A.collider(r,'theater-wall',1).addSolid(CollisionBox(Point3(0,7,18),26,13.5,18))
    for x,h in ((-23,34),(-15,43),(0,52),(15,43),(23,34)):
        A.board(r,'art-deco-pier',(x,-7,h/2),(5,3,h),GOLD,WOOD)
        for dx in (-1.3,1.3):
            A.board(r,'gold-inlay',(x+dx,-8.6,h/2),( .3,.3,h-3),CREAM,None)
    for x in (-15,-7.5,7.5,15):
        A.board(r,'double-door-trim',(x,-7,5),(6,1,10),GOLD,WOOD)
        A.board(r,'dark-glass-door',(x,-7.6,5),(4.8,.3,8.5),(.24,.44,.45,1),None)
        A.board(r,'door-handle',(x+.9,-7.9,4),( .2,.3,2),GOLD,None)
    A.board(r,'marquee',(0,-12,15),(57,14,5),GOLD,WOOD)
    A.board(r,'marquee-letterboard',(0,-19.2,15),(52,.4,3.5),(.20,.28,.31,1),None)
    A.text(r,'THE REEL BIG THEATER',(0,-19.5,14.2),2)
    for x in range(-26,27,3):
        bulb(r,'marquee-bulb',(x,-19.5,12.8),.45)
        bulb(r,'marquee-bulb',(x,-19.5,17.2),.45)
    reel(r,(-7,-9,36));reel(r,(7,-9,36))
    A.text(r,'DOODLEWOOD',(0,-9,23),2.2)
    return r


def water_tower():
    r=NodePath('ten-gallon-water-tower')
    for x in (-8,8):
        for y in (-8,8):
            A.tube(r,'splayed-timber-leg',[(x*1.3,y*1.3,0,1.1),(x,y,27,.8)],WOOD,(.72,.44,.24,1),6,True)
    for z in (8,19):
        for y in (-8,8):
            A.tube(r,'cross-brace',[(-9,y,z-7,.42),(9,y,z+7,.42)],WOOD,CREAM,5)
            A.tube(r,'cross-brace',[(9,y,z-7,.42),(-9,y,z+7,.42)],WOOD,CREAM,5)
    A.tube(r,'barrel-water-tank',[(0,0,26,12),(0,0,31,13),(0,0,43,12)],TIMBER,(.89,.60,.32,1),24,True)
    for z in (27,30,40,43):ring(r,'iron-band',z,12.5,.4,(.26,.44,.41,1))
    A.tube(r,'hat-brim',[(0,0,44,18),(0,0,45,18)],WOOD,(.79,.45,.21,1),24)
    A.tube(r,'ten-gallon-hat',[(0,0,45,11),(1,0,50,10),(2,0,57,7),(0,0,59,6)],WOOD,(.79,.45,.21,1),24)
    ring(r,'hat-band',47,10.7,.8,TEAL)
    for z in range(2,29,2):A.board(r,'ladder-rung',(4,-12,z),(3,.5,.3),CREAM,WOOD)
    for x in (2.5,5.5):A.board(r,'ladder-rail',(x,-12,15),(.3,.5,29),TEAL,WOOD)
    A.board(r,'water-sign',(0,-13,35),(18,1,5),TEAL,WOOD)
    A.text(r,'TEN GALLONS',(0,-13.6,34),1.5)
    return r


def cactus():
    r=NodePath('crooked-saguaro')
    green=(.41,.67,.35,1)
    A.tube(r,'cactus-body',[(0,0,0,1.4),(.2,0,7,1.6),(-.6,0,13,1.2),(-.6,0,14,.1)],WOOD,green,10,True)
    for s,h in ((-1,7),(1,10)):
        A.tube(r,'upturned-arm',[(0,0,5,1),(s*3,0,5,1),(s*4,0,h,.8),(s*4,0,h+1,.05)],WOOD,green,10,True)
    for z in (3,6,9,12):
        for x in (-.7,.6):A.board(r,'painted-spine',(x,-1.25,z),(.08,.12,.6),CREAM,None)
    bulb(r,'cactus-flower',(-.6,0,14.2),.7,(1,.57,.44,1))
    return r


def mesa():
    r=NodePath('layered-sandstone')
    for i in range(5):
        A.tube(r,'eroded-layer',[(0,0,i*5,14-i*1.4),(.5,0,(i+1)*5,13-i*1.5)],
            'phase_6/maps/Rural_dustroad.jpg',(1,.68+i*.03,.44+i*.02,1),7,True)
    return r


def seaside_rail():
    r=NodePath('rope-pier-rail')
    for x in (-8,8):
        A.tube(r,'piling',[(x,0,0,.7),(x,0,5.5,.65)],TIMBER,(.75,.59,.37,1),10)
        ring(r,'rope-wrap',4.5,.8,.15,CREAM,(x,0))
    for z in (2.2,4.5):
        A.tube(r,'sagging-rope',[(-8,0,z,.13),(-4,0,z-.6,.13),(0,0,z-.8,.13),
                (4,0,z-.6,.13),(8,0,z,.13)],WOOD,CREAM,6)
    A.collider(r,'pier-rail-wall',1).addSolid(CollisionBox(Point3(0,0,2.5),8,.6,2.5))
    return r


def movie_camera():
    r=NodePath('movie-camera')
    for a in (0,2*pi/3,4*pi/3):A.tube(r,'tripod',[(4*cos(a),4*sin(a),0,.25),(0,0,5,.25)],WOOD,TEAL,6)
    A.board(r,'camera-body',(0,0,7),(4,5,3),(.24,.36,.39,1),WOOD)
    lens=r.attachNewNode('camera-lens');lens.setPos(0,-3,7);lens.setP(90)
    A.tube(lens,'lens-barrel',[(0,0,0,1),(0,0,3,1.6)],WOOD,GOLD,12)
    A.tube(lens,'lens-glass',[(0,0,3.1,1.3),(0,0,3.2,1.3)],None,(.16,.30,.37,1),12)
    reel(r,(-1.7,-1,10),2);reel(r,(1.7,-1,10),2)
    A.collider(r,'camera-stand',1).addSolid(CollisionBox(Point3(0,0,4),2,2,4))
    return r


def western_shop(index):
    """Purpose-built false-front shops with porches and crooked cornices."""
    root=NodePath('western-storefront-'+str(index))
    color=[(.91,.66,.37,1),(.43,.73,.64,1),(.90,.47,.33,1),(.74,.65,.46,1)][index]
    height=[24,29,27,32][index]
    A.board(root,'painted-clapboard',(0,9,height/2),(26,18,height),color,WOOD)
    # Shallow plank grooves, exaggerated cream corner posts and shaped parapet.
    for z in range(2,height,2):
        A.board(root,'clapboard-line',(0,-.12,z),(26,.18,.11),tuple(c*.8 for c in color[:3])+(1,),None)
    for x in (-12.5,12.5):A.board(root,'corner-post',(x,-.4,height/2),(1.1,.8,height+1),CREAM,WOOD)
    for x in range(-12,13,2):
        crown=(4*(1-(abs(x)/13)**2) if index%2 else (4 if abs(x)<7 else 1.5))
        A.board(root,'shaped-parapet',(x,0,height+crown/2),(2.1,1.5,crown),color,WOOD)
        A.board(root,'parapet-cap',(x,-.15,height+crown),(2.2,1.9,.5),CREAM,WOOD)
    door=A.app.loader.loadModel('phase_4/models/modules/doors').find('**/door_single_round_ur').copyTo(root)
    door.setPos(0,-.035,0);door.setColorScale(.74,.86,.72,1);door.setName('scenery-door')
    root.attachNewNode('western_door_origin')
    suit=root.attachNewNode('suit_building_origin');suit.setPos(-13,0,0);suit.setScale(.87,1,1)
    for x in (-8,8):
        for z in (5.5,height-6):
            A.board(root,'window-frame',(x,-.5,z),(5.6,.8,6.4),CREAM,WOOD)
            A.board(root,'window-glass',(x,-.96,z),(4.5,.2,5.3),(.26,.50,.55,1),None)
            A.board(root,'window-mullion',(x,-1.12,z),(.25,.2,5.3),CREAM,None)
            A.board(root,'window-cross',(x,-1.12,z),(4.5,.2,.25),CREAM,None)
            A.board(root,'window-sill',(x,-1.2,z-3),(6,1.5,.5),color,WOOD)
    A.board(root,'porch-deck',(0,-3,.06),(29,7,.1),CREAM,TIMBER)
    roof=A.board(root,'porch-roof',(0,-2.5,10.5),(29,8,.6),color,TIMBER);roof.setP(-6)
    for x in (-12,12):
        A.tube(root,'turned-porch-post',[(x,-5,0,.42),(x,-5,3,.55),(x,-5,7,.35),(x,-5,10.4,.5)],WOOD,CREAM,8)
    A.board(root,'porch-valance',(0,-6.5,9.8),(29,.5,1.1),CREAM,WOOD)
    A.collider(root,'shop-wall',1).addSolid(CollisionBox(Point3(0,9,height/2),13,9,height/2))
    return root


def shop(hood,index):
    if hood==64000:
        root=western_shop(index)
        from tools.world_dressing import enclosure
        enclosure(root,hood,A,(-15,-5,15,21),front_open=-1)
        return root
    spec=PALETTES[hood];code=spec['code'];phase=spec['phase']
    style=code+'_'+('A1','B1','C1','D1')[index]
    root=NodePath('complete-'+str(hood)+'-shop-'+str(index))
    m=A.app.loader.loadModel(f'phase_{phase}/models/modules/{style}')
    lo,hi=m.getTightBounds()
    scale=27/(hi.x-lo.x)
    origin=m.find('**/*door_origin')
    doorpos=origin.getPos(m)
    # Align the ACTUAL entrance to our placement origin. Stock modules have
    # asymmetric trim/awnings; their bounding-box front is not their door plane.
    m.reparentTo(root);m.setScale(scale)
    m.setPos(-doorpos.x*scale,-doorpos.y*scale,-lo.z*scale)
    color={19000:(.70,.72,.48,1),61000:(.93,.36,.28,1),62000:(.51,.57,.68,1),
           63000:(1,.85,.47,1)}[hood]
    door=A.app.loader.loadModel('phase_4/models/modules/doors').find('**/door_single_round_ur').copyTo(origin)
    door.setPos(0,-.035,0);door.setColorScale(*color)
    door.wrtReparentTo(root);door.setName('scenery-door')
    # The stock modules use *_sideL / *_sideR, not *building_sides. Using
    # the entire roof bounds here produced tall rectangular walls above roofs.
    sides=[part for part in m.findAllMatches('**/+GeomNode') if 'side' in part.getName().lower()]
    bounds=[part.getTightBounds(m) for part in sides]
    blo=Point3(*(min(b[0][j] for b in bounds) for j in range(3))) if bounds else lo
    bhi=Point3(*(max(b[1][j] for b in bounds) for j in range(3))) if bounds else hi
    x0=(blo.x-doorpos.x)*scale;x1=(bhi.x-doorpos.x)*scale
    back=(bhi.y-doorpos.y)*scale
    height=(bhi.z-lo.z)*scale
    A.board(root,'rear-wall',((x0+x1)/2,back-.18,height/2),
            (x1-x0,.4,height),color,WOOD)
    # Closed, textured side panels sit inside the native ornament and roof.
    # They remain opaque from either direction at corners and wide FOV.
    for x in (x0+.3,x1-.3):
        A.board(root,'closed-side',(x,back/2,height/2),(.55,back,height),color,WOOD)
    # Prevent entering the scenery through either side, its rear, or the door.
    depth=max(3,back)
    A.collider(root,'shop-walls',1).addSolid(CollisionBox(Point3((x0+x1)/2,depth/2,height/2),
        (x1-x0)/2,depth/2,height/2))
    # Deep striped canvas adds the characteristic playful street rhythm.
    if hood!=62000:
        for i in range(8):
            awning=A.board(root,'striped-awning',(-11.2+i*3.2,-2.4,11),(3.2,5,.35),
                CREAM if i%2 else color,WOOD)
            awning.setP(-12)
            A.board(root,'scalloped-valance',(-11.2+i*3.2,-4.8,10.4),(3.1,.3,1),
                CREAM if i%2 else color,WOOD)
    from tools.world_dressing import enclosure
    enclosure(root,hood,A,(x0-1,-1,x1+1,back+1),front_open=-1)
    return root


def terrain(zone):
    if zone in ROADS:
        from tools.street_geometry import build
        return build(zone,A)
    from toontown.expansion import Services
    hood=E.hood_id(zone);spec=PALETTES[hood];street=zone in ROADS
    root=NodePath('terrain-'+str(zone))
    path=curve(ROADS[zone]) if street else None
    ymin,ymax=(int(path[0][1])-40,int(path[-1][1])+40) if street else (-175,180)
    xmin,xmax=(-215,215) if street else (-190,190)
    mesh=A.Mesh('painted-banks',spec['ground']);patches={}
    for x in range(xmin,xmax,10):
        for y in range(ymin,ymax,10):
            key=(x//50,y//50)
            floor=patches.setdefault(key,None)
            if floor is None:floor=patches[key]=A.collider(root,'terrain-patch-%s-%s'%key,2)
            def height(xx,yy):
                return terrain_height(zone,xx,yy)
            pts=[(xx,yy,height(xx,yy)) for xx,yy in ((x,y),(x+10,y),(x+10,y+10),(x,y+10))]
            variation=.96+.04*sin(x*.043)*cos(y*.037)
            tint=tuple(c*variation for c in spec['tint'][:3])+(1,)
            mesh.face(pts,color=tint);A.collision_face(floor,pts)
    mesh.attach(root,ground_layer=0)
    if street:
        profile=ROAD_PROFILES[zone]
        for lane,route in enumerate(road_paths(zone)):
            A.ribbon(root,'curved-sidewalk-'+str(lane),route,profile['sidewalk'],spec['paving'],.055,spec['tint'])
            A.ribbon(root,'winding-street-'+str(lane),route,profile['road'],spec['road'],.09,spec['tint'])
            A.feathered_shoulder(root,route,profile['sidewalk'],spec['paving'],spec['tint'])
        # Rounded intersection aprons connect the looping side streets cleanly.
        for route in road_paths(zone)[1:]:
            for x,y in (route[0],route[-1]):
                A.disk(root,'junction-apron',(x,y),profile['sidewalk'],profile['sidewalk'],spec['paving'],.06)
                A.disk(root,'junction-road',(x,y),profile['road'],profile['road'],spec['road'],.095)

        # Woodland clearings, dock overlooks, garden courts, studio forecourts
        # and desert trading stops break up the individual street silhouettes.
        from toontown.expansion.WorldLayout import along
        for i,(x,y,tx,ty) in enumerate(along(path,profile['spacing'],62)):
            if i%profile['court']==profile['court']//2:
                side=-1 if i%2 else 1
                A.disk(root,'roadside-court',(x-ty*side*25,y+tx*side*25),
                    25 if hood!=64000 else 33,24,spec['paving'],.06)
    elif hood==61000:
        # A wandering shore promenade opens onto a long lighthouse pier. Shops
        # cluster along the landward side rather than surrounding a central ring.
        water=A.Mesh('harbor-water')
        pts=[(2,38,.02),(153,38,.02),(153,139,.02),(2,139,.02)]
        water.face(pts,color=(.20,.62,.76,1),shade=False);water.attach(root,ground_layer=20)
        A.disk(root,'arrival-market',(-25,-62),44,29,spec['road'],.04)
        for name,points,width in [
            ('shore-promenade',[(0,-140),(-20,-105),(-40,-65),(-37,-12),(-15,30),(18,44)],18),
            ('lighthouse-pier',[(-15,30),(20,52),(60,74),(103,83)],16),
            ('western-quay',[(-155,25),(-116,25),(-78,8),(-37,-12)],14),
            ('south-shop-walk',[(-40,-65),(4,-63),(45,-42),(75,-3)],11),
        ]:A.ribbon(root,name,curve(points),width,spec['paving'],.09,edges=True)
        A.disk(root,'lighthouse-deck',(90,78),25,23,spec['paving'],.095)
    elif hood==62000:
        # Two offset garden squares connected by narrow winding paths.
        for name,center,rx,ry in [('clock-court',(-38,30),38,33),('moon-court',(52,-38),29,31)]:
            A.disk(root,name,center,rx+3,ry+3,spec['paving'],.04)
            A.disk(root,name+'-center',center,rx,ry,spec['road'],.065)
        for name,points,width in [
            ('sleepy-walk',[(25,-135),(20,-102),(45,-77),(52,-38),(30,-5),(-12,10),(-38,30)],12),
            ('bramble-garden',[(-150,55),(-115,55),(-79,36),(-38,30)],12),
            ('upper-garden',[(-38,30),(-19,75),(22,94),(67,71),(77,28),(52,-38)],9),
        ]:A.ribbon(root,name,curve(points),width,spec['paving'],.085,edges=True)
    elif hood==63000:
        # An asymmetric theater boulevard with two production lots and alleys.
        for name,points,width in [
            ('premiere-boulevard',[(0,-155),(-8,-110),(-12,-55),(0,0),(24,35),(35,55)],29),
            ('west-backlot',[(-160,-25),(-115,-25),(-78,-7),(-45,0),(0,0)],17),
            ('east-backlot',[(160,55),(125,55),(100,27),(70,10),(24,15)],18),
        ]:A.ribbon(root,name,curve(points),width,spec['paving'],.065,edges=True)
        A.ribbon(root,'premiere-red-carpet',curve([(0,-130),(-12,-55),(0,0),(35,55)]),
            9,spec['road'],.095,(1,.40,.32,1))
        A.disk(root,'camera-lot',(-68,48),33,30,spec['road'],.07)
        A.disk(root,'star-court',(85,-54),32,29,spec['road'],.07)
    elif hood==64000:
        # Loose western trading square, creek crossing and a separate water yard.
        A.disk(root,'trading-square',(-42,-31),53,43,spec['road'],.06)
        creek=curve([(-165,83),(-105,70),(-50,38),(5,30),(60,50),(150,82)])
        A.ribbon(root,'dry-arroyo',creek,9,spec['road'],.035,(.60,.53,.40,1))
        for name,points,width in [
            ('dusty-main-street',[(-20,-150),(-28,-104),(-42,-55),(-42,-31),(-23,1),(7,24),(47,46),(75,62)],16),
            ('stagecoach-trail',[(-170,50),(-125,50),(-90,24),(-60,-8),(-42,-31)],13),
            ('porch-walk',[(35,-100),(75,-66),(98,-20),(94,18)],9),
        ]:A.ribbon(root,name,curve(points),width,spec['road'],.08)
        A.ribbon(root,'creek-footbridge',[(-16,8),(2,28),(19,47)],12,spec['paving'],.1)
        A.disk(root,'water-yard',(75,62),29,26,spec['paving'],.065)
    Services.add_paths(root,zone,A,spec['paving'])
    from tools.world_dressing import perimeter
    perimeter(root,zone,A)
    boundary=A.collider(root,'scenery-boundary',1)
    for x,y,w,d in ((xmin,(ymin+ymax)/2,1,ymax-ymin),(xmax,(ymin+ymax)/2,1,ymax-ymin),
                    (0,ymin,xmax-xmin,1),(0,ymax,xmax-xmin,1)):
        boundary.addSolid(CollisionBox(Point3(x,y,35),w/2,d/2,50))
    return root


def main():
    import os
    from direct.showbase.ShowBase import ShowBase
    os.chdir(ROOT);OUT.mkdir(parents=True,exist_ok=True)
    A.app=ShowBase();A.OUT=OUT
    for name,fn in [('lighthouse',lighthouse),('clock_tower',clock_tower),('theater',theater),
        ('water_tower',water_tower),('cactus',cactus),('mesa',mesa),('pier_rail',seaside_rail),('movie_camera',movie_camera),('western_lamp',western_lamp)]:
        A.save(fn(),name)
    for hood in PALETTES:
        for index in range(4):
            model=shop(hood,index)
            A.save(model.copyTo(NodePath('export')),f'shop_{hood}_{index}')
            model.find('**/scenery-door').removeNode()
            A.save(model,f'building_{hood}_{index}')
    for zone in list(ROADS)+list(PLAZA_GATES):A.save(terrain(zone),'terrain_'+str(zone))
    for zone in sorted(E.ALL_ZONES | set(E.SOURCE_GATES)):
        A.save(A.sign_model(E.zone_name(zone).upper()),'sign_'+str(zone))
    from tools.author_world_layouts import NAMES
    for hood,names in NAMES.items():
        for i,name in enumerate(names):A.save(A.sign_model(name),f'shop_sign_{hood}_{i}')
    A.app.destroy()
    print('Built expansion terrain, textured storefronts and custom landmark/prop kit.')

if __name__=='__main__':main()
