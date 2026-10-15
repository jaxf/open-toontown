"""Themed ground-level boundaries, protected service yards and small prop kits."""
from math import hypot, atan2, degrees, sin, cos, pi
from panda3d.core import NodePath, CollisionCapsule, Point3
from toontown.expansion import ExpansionGlobals as E, Services
from toontown.expansion.WorldLayout import ROADS, curve, PALETTES

COLORS={19000:((.53,.32,.16,1),(.91,.75,.40,1)),
        61000:((.28,.61,.64,1),(.98,.87,.64,1)),
        62000:((.27,.29,.44,1),(.67,.58,.81,1)),
        63000:((.64,.22,.24,1),(1,.83,.38,1)),
        64000:((.67,.37,.20,1),(.93,.70,.38,1))}
WOOD='phase_6/maps/outdoor_zone_wood_boards.jpg'


def fence(root, hood, A, points, height=8):
    """Opaque lower panels conceal backs; themed tops mark real collision edges."""
    dark,light=COLORS[hood]
    wall=A.collider(root,'fence-wall',1)
    for a,b in zip(points,points[1:]):
        distance=hypot(b[0]-a[0],b[1]-a[1])
        count=max(1,round(distance/8))
        for i in range(count):
            t,u=i/count,(i+1)/count
            p=(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)
            q=(a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u)
            length=hypot(q[0]-p[0],q[1]-p[1]);h=degrees(atan2(q[1]-p[1],q[0]-p[0]))
            n=root.attachNewNode('themed-fence');n.setPos(p[0],p[1],.10);n.setH(h)
            A.board(n,'solid-yard-screen',(length/2,0,height*.36),(length,.65,height*.72),dark,WOOD)
            for z in (height*.17,height*.69):
                A.board(n,'painted-rail',(length/2,-.45,z),(length+1,.45,.55),light,WOOD)
            A.tube(n,'crooked-post',[(0,0,0,.48),(0,0,height,.48),(0,0,height+.8,.05)],WOOD,light,5)
            if hood==61000:
                A.tube(n,'harbor-rope',[(0,0,height,.16),(length/2,0,height-1,.16),(length,0,height,.16)],None,light,6)
            elif hood==62000:
                for x in (length*.28,length*.72):
                    A.tube(n,'moon-spire',[(x,0,height*.6,.16),(x,0,height+1,.16),(x,0,height+1.6,.01)],None,light,4)
            elif hood==63000:
                A.board(n,'studio-gold-inset',(length/2,-.4,height*.46),(length*.60,.2,height*.25),light,None)
            elif hood==19000:
                for x in (length*.25,length*.65):
                    A.board(n,'woodland-picket',(x,-.5,height*.55),(.7,.4,height*.90),light,WOOD)
            wall.addSolid(CollisionCapsule(Point3(*p,1),Point3(*q,1),.8))
            # Full-height wall prevents jumping through opaque screens.
            from panda3d.core import CollisionBox
            col=A.collider(n,'fence-panel-wall',1)
            col.addSolid(CollisionBox(Point3(length/2,0,height/2),length/2,.65,height/2))


def enclosure(root,hood,A,bounds,front_open=1):
    root=root.attachNewNode('screened-courtyard')
    x0,y0,x1,y1=bounds
    points=[(x0,y1),(x0,y0),(x1,y0),(x1,y1)] if front_open==1 else [(x0,y0),(x0,y1),(x1,y1),(x1,y0)]
    fence(root,hood,A,points,9)
    root.flattenStrong()


def perimeter(root,zone,A):
    root=root.attachNewNode('district-boundaries')
    hood=E.hood_id(zone)
    gates=E.gate_transforms(zone)
    if zone in ROADS:
        # The street builder follows the actual joined block/courtyard outline.
        outline=[]
    else:
        # Rounded, irregular outlines give the neighborhoods different silhouettes.
        rx,ry={19000:(151,139),61000:(181,159),62000:(179,160),63000:(184,164),64000:(184,160)}[zone]
        outline=[(-rx+20,-ry),(rx-24,-ry),(rx,-ry+27),(rx,ry-24),
                 (rx-26,ry),(-rx+27,ry),(-rx,ry-28),(-rx,-ry+22),(-rx+20,-ry)]
    # Leave broad open corridors connecting the outline to every tunnel.
    for a,b in zip(outline,outline[1:]):
        n=max(1,round(hypot(b[0]-a[0],b[1]-a[1])/8))
        for i in range(n):
            p=tuple(a[j]+(b[j]-a[j])*i/n for j in (0,1))
            q=tuple(a[j]+(b[j]-a[j])*(i+1)/n for j in (0,1))
            x,y=(p[0]+q[0])/2,(p[1]+q[1])/2
            opening=any((abs(x-gx)<28 and ((h==0 and y<gy+25) or (abs(h)==180 and y>gy-25))) or
                        (abs(y-gy)<28 and ((h==-90 and x<gx+25) or (h==90 and x>gx-25)))
                        for gx,gy,gz,h in gates)
            if not opening:fence(root,hood,A,[p,q],10 if zone not in ROADS else 8)
    # Native services keep their stock transforms. Screens wrap only sides/back,
    # leaving doors, trolley boarding and departure tracks unobstructed.
    code,phase=Services.theme(zone)
    for kind,(x,y,z,h) in Services.placements(zone).items():
        yard=root.attachNewNode(kind+'-screened-yard');yard.setPos(x,y,.12);yard.setH(h)
        if kind=='trolley':
            from panda3d.core import CollisionBox
            dark,light=COLORS[hood]
            # The native station is a stage facade. Add an enclosed station yard
            # around its sides/back, with the player approach entirely open.
            for name,pos,size in [
                ('station-back',(15,32,11.5),(48,2,23)),
                ('station-left',(-8,14,11.5),(2,36,23)),
                ('station-right',(38,14,11.5),(2,36,23))]:
                A.board(yard,name,pos,size,dark,WOOD)
                A.board(yard,name+'-cap',(pos[0],pos[1],23.6),(size[0]+.8,size[1]+.8,1.2),light,WOOD)
                A.collider(yard,name+'-wall',1).addSolid(CollisionBox(Point3(*pos),size[0]/2,size[1]/2,size[2]/2))
            fence(yard,hood,A,[(-8,-4),(1,-4)],8)
            fence(yard,hood,A,[(30,-4),(38,-4)],8)
        else:
            path=('phase_3.5/models/modules/hqTT' if code in ('TT','DD') else f'phase_{phase}/models/modules/hq{code}') if kind=='hq' else f'phase_{phase}/models/modules/gagShop_{code}'
            model=A.app.loader.loadModel(path);lo,hi=model.getTightBounds()
            enclosure(yard,hood,A,(lo.x-3,lo.y-3,hi.x+3,hi.y-2),1)
            model.removeNode()
    root.flattenStrong()


def planter(hood,A):
    root=NodePath('neighborhood-planter');dark,light=COLORS[hood]
    A.board(root,'painted-planter',(0,0,1.25),(7,4,2.5),dark,WOOD)
    A.board(root,'soil',(0,0,2.55),(6.5,3.5,.15),(.27,.19,.12,1),None)
    for i,x in enumerate((-2.3,0,2.3)):
        A.tube(root,'stem',[(x,0,2.5,.12),(x+.4,0,5+(i%2),.12)],None,(.28,.49,.26,1),5)
        for k in range(5):
            a=k*2*pi/5
            A.tube(root,'flower-petal',[(x+.4+.6*cos(a),.6*sin(a),5+i%2,.48),
                (x+.4+.6*cos(a),.6*sin(a),5.35+i%2,.1)],None,light,6)
    from panda3d.core import CollisionBox
    A.collider(root,'planter-wall',1).addSolid(CollisionBox(Point3(0,0,1.25),3.5,2,1.25))
    return root
