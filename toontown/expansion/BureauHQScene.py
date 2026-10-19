"""Editable low-poly Bureaubot campus geometry, shared by client and previews."""
import math
from panda3d.core import (NodePath,GeomVertexFormat,GeomVertexData,GeomVertexWriter,
    GeomVertexReader,CollisionNode,CollisionBox,CollisionPolygon,Point3,BitMask32,Texture,Triangulator)
from . import BureauHQGlobals as H
from .Geometry import box,cylinder,sphere,label,mesh
from toontown.suit.BureaubotModels import _prism,build_logo

STEEL=(.38,.43,.46,1);COPPER=(.42,.32,.25,1);PAPER=(.74,.72,.63,1)
DARK=(.16,.20,.22,1);GLASS=(.25,.39,.39,1);LIGHT=(1,.70,.23,1)
MINISTRY_OUTLINE=((-23,-196),(31,-196),(63,-158),(90,-151),(93,-126),
    (150,-133),(185,-107),(178,-48),(198,-5),(210,65),(211,131),
    (175,148),(168,181),(107,197),(42,188),(-35,205),(-124,179),
    (-164,128),(-190,107),(-184,58),(-207,36),(-207,-57),
    (-183,-69),(-193,-105),(-148,-165),(-78,-160))


def native(root,path,pos=(0,0,0),height=None,part=None,heading=0,size=None,solid=False,pitch=0):
    """Reuse authored resource art/UVs; props get bounded, explicit collision."""
    from direct.showbase.ShowBaseGlobal import base
    model=base.loader.loadModel(path)
    source=model.find('**/'+part) if part else model
    if source.isEmpty():raise ValueError('Missing native part: '+str(part))
    pivot=root.attachNewNode('native-'+(part or path.rsplit('/',1)[-1]))
    art=source.copyTo(pivot)
    if part:art.setMat(source.getMat(model))
    if pitch:art.setP(art.getP()+pitch)
    for collider in art.findAllMatches('**/+CollisionNode'):collider.removeNode()
    low,high=pivot.getTightBounds();extent=high-low
    if heading=='radial':
        heading=math.degrees(math.atan2(pos[1]+100,pos[0])-math.atan2((low.y+high.y)/2,(low.x+high.x)/2))
    art.setPos(art.getPos()-Point3((low.x+high.x)/2,(low.y+high.y)/2,low.z))
    scale=height/extent.z if height else 1
    if size:scales=tuple(size[i]/max(extent[i],.001) if size[i] else scale for i in range(3))
    else:scales=(scale,)*3
    pivot.setScale(*scales);pivot.setPos(*pos);pivot.setH(heading)
    if solid:
        collider=CollisionNode('native-prop-wall');collider.setFromCollideMask(BitMask32.allOff())
        collider.setIntoCollideMask(BitMask32(5))
        collider.addSolid(CollisionBox(Point3(0,0,extent.z/2),extent.x/2,extent.y/2,extent.z/2))
        pivot.attachNewNode(collider)
    pivot.setTag('source-model',path)
    # Architecture shares a cool charcoal palette; keep its original painted
    # details visible rather than carrying the pale Lawbot stone into this HQ.
    if path.endswith(('LawbotPlaza','LB_filing_cabA','LB_wall_panel','LB_pillar')):
        pivot.setColorScale(.48,.55,.60,1)
    elif path.endswith('suit_walls'):
        pivot.setColorScale(.64,.70,.75,1)
    return pivot


def texture(node,path,tile=24,flat=False):
    from direct.showbase.ShowBaseGlobal import base
    nodes=list(node.findAllMatches('**/+GeomNode'))
    if node.node().isGeomNode():nodes.insert(0,node)
    for item in nodes:
        for i in range(item.node().getNumGeoms()):
            geom=item.node().modifyGeom(i)
            data=GeomVertexData(geom.getVertexData().convertTo(GeomVertexFormat.getV3n3c4t2()))
            points=GeomVertexReader(data,'vertex');normals=GeomVertexReader(data,'normal');uv=GeomVertexWriter(data,'texcoord')
            while not points.isAtEnd():
                p=points.getData3();n=normals.getData3()
                if flat or abs(n.z)>.7:u,v=p.x,p.y
                elif abs(n.x)>.7:u,v=p.y,p.z
                else:u,v=p.x,p.z
                uv.addData2(u/tile,v/tile)
            geom.setVertexData(data)
    tex=base.loader.loadTexture(path);tex.setMinfilter(Texture.FTLinearMipmapLinear);tex.setMagfilter(Texture.FTLinear)
    node.setTexture(tex,1)
    return node


def curved_path(root,points,width=22,check_walk=True):
    """Bent painted paving, with an uneven route rather than a mirrored cross."""
    samples=[]
    for i in range(len(points)-1):
        a,b,c,d=(points[max(0,i-1)],points[i],points[i+1],points[min(len(points)-1,i+2)])
        for j in range(8):
            t=j/8
            samples.append(tuple(.5*(2*b[k]+(-a[k]+c[k])*t+(2*a[k]-5*b[k]+4*c[k]-d[k])*t*t+(-a[k]+3*b[k]-3*c[k]+d[k])*t*t*t) for k in (0,1)))
    samples.append(points[-1])
    if check_walk:
        route=root.attachNewNode('exploration-route')
        for i,p in enumerate(samples):route.attachNewNode('walk-sample-%s'%i).setPos(*p,0)
    for half,z,name,path in ((width/2+1,.12,'native-curb','phase_11/maps/LB_rustyMetal.jpg'),
                             (width/2,.18,'native-sidewalk','phase_9/maps/FootFactoryFloor.jpg')):
        verts=[];faces=[]
        for i,p in enumerate(samples):
            a=samples[max(0,i-1)];b=samples[min(len(samples)-1,i+1)]
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
            verts.extend(((p[0]-dy/length*half,p[1]+dx/length*half,z),
                          (p[0]+dy/length*half,p[1]-dx/length*half,z)))
            if i:faces.append((2*i-2,2*i-1,2*i+1,2*i))
        texture(mesh(root,name,verts,faces,(.75,.79,.81,1)),path,26,True)


def ground_patch(root,name,outline,path,tile=20):
    # Triangulate concave outlines rather than filling their recesses with fans.
    verts=[(x,y,.025) for x,y in outline]
    triangulator=Triangulator()
    for x,y in outline:triangulator.addPolygonVertex(triangulator.addVertex(x,y))
    triangulator.triangulate()
    faces=[(triangulator.getTriangleV0(i),triangulator.getTriangleV1(i),triangulator.getTriangleV2(i))
           for i in range(triangulator.getNumTriangles())]
    return texture(mesh(root,name,verts,faces,(1,1,1,1)),path,tile,True)


def paint_materials(root):
    """Tile native painted materials across the new meshes in model units."""
    from direct.showbase.ShowBaseGlobal import base
    materials={
        'stone':base.loader.loadTexture('phase_11/maps/LB_CementWall_5.jpg'),
        'metal':base.loader.loadTexture('phase_11/maps/LB_rustyMetal.jpg'),
        'paper':base.loader.loadTexture('phase_11/maps/LB_paper_stacks.jpg')}
    stone={'ministry-front','document-layer','perimeter','rear-perimeter','arrival-perimeter',
           'approval-hall','inspection-booth','records-front','stamp-plinth','hedge-planter'}
    metal={'archive-shell','drawer-face','clip-arm','clip-crown','clip-jaw','stamp-base',
           'stamp-grip','stamp-neck','stamp-grip-cap','pneumatic-pipe','pipe-cap','archive-skybridge','registry-spoke'}
    for path in root.findAllMatches('**/+GeomNode'):
        name=path.getName()
        kind='stone' if name in stone else 'metal' if name in metal else 'paper' if name=='archive-box' else None
        if not kind:continue
        for i in range(path.node().getNumGeoms()):
            geom=path.node().modifyGeom(i)
            data=GeomVertexData(geom.getVertexData().convertTo(GeomVertexFormat.getV3n3c4t2()))
            verts=GeomVertexReader(data,'vertex');normals=GeomVertexReader(data,'normal');uv=GeomVertexWriter(data,'texcoord')
            while not verts.isAtEnd():
                p=verts.getData3();n=normals.getData3()
                if abs(n.z)>.7:u,v=p.x,p.y
                elif abs(n.x)>.7:u,v=p.y,p.z
                else:u,v=p.x,p.z
                uv.addData2(u/24,v/24)
            geom.setVertexData(data)
        path.setTexture(materials[kind],1)
        if kind=='metal':path.setColorScale(1.4,1.4,1.4,1)


def wall(parent,name,pos,size,color=STEEL):
    node=box(parent,name,pos,size,color,True)
    node.find('**/+CollisionNode').node().setIntoCollideMask(BitMask32(5))
    return node


def emblem(parent,pos,scale=10):
    crest=build_logo();crest.reparentTo(parent);crest.setPos(*pos);crest.setScale(scale)
    crest.find('**/cast-clipboard').setHpr(0,0,0)
    return crest


def paving(root,zone):
    from direct.showbase.ShowBaseGlobal import base
    ground=box(root,'continuous-courtyard-ground',(0,0,-.4),(540,540,.8),(.64,.69,.73,1))
    # Native paving texture with world-sized UV tiles, not a stretched image.
    data=GeomVertexData(ground.node().getGeom(0).getVertexData().convertTo(GeomVertexFormat.getV3n3c4t2()))
    reader=GeomVertexReader(data,'vertex');uv=GeomVertexWriter(data,'texcoord')
    while not reader.isAtEnd():
        p=reader.getData3();uv.addData2(p.x/72,p.y/72)
    ground.node().modifyGeom(0).setVertexData(data)
    ground.setTexture(base.loader.loadTexture('phase_11/maps/LB_CementGround_2.jpg'),1)
    if zone==H.MINISTRY:
        # The visible plaza itself follows its concave boundary, not the old
        # rectangular slab. Keep the broad hidden floor under tunnel movies.
        ground.removeNode()
        ground=ground_patch(root,'ministry-irregular-footprint',MINISTRY_OUTLINE,
                            'phase_11/maps/LB_CementGround_2.jpg',72)
        ground.setZ(-.025);ground.setColorScale(.64,.69,.73,1)
    collider=CollisionNode('courtyard-floor');collider.setFromCollideMask(BitMask32.allOff())
    collider.setIntoCollideMask(BitMask32.bit(1))
    collider.addSolid(CollisionPolygon(Point3(-270,-270,0),Point3(270,-270,0),Point3(270,270,0),Point3(-270,270,0)))
    root.attachNewNode(collider)
    # A broad textured ground skirt closes the gap below the skyline from high views.
    texture(box(root,'outer-industrial-ground',(0,0,-1),(2200,2200,1),(.42,.46,.49,1)),
            'phase_9/maps/ground7.jpg',90,True)


def bureau_office(root,name,pos,variant,height,heading=0,solid=True):
    """Enclosed industrial annexes with native Cog panels, cabinets and machinery."""
    group=root.attachNewNode('bureau-annex-'+name);group.setPos(*pos);group.setH(heading)
    w=min(height*.55,34);depth=min(height*.38,24);front=-depth/2
    if variant=='files':
        # Offset stacked drawer sections form an uneven roof and recognizable
        # bureaucracy silhouette, with authored handles and riveted edges.
        for i in range(3):
            native(group,'phase_11/models/lawbotHQ/LB_filing_cabA',
                   ((i%2)*2-1,0,i*height*.29),size=(w-i*1.7,depth,height*.29),solid=solid)
        native(group,'phase_9/models/cogHQ/metalCrate',(2,1,height*.87),
               size=(w*.67,depth*.8,height*.13))
    else:
        lean=w*(.10 if variant=='vents' else -.12)
        outline=[(-w*.44,0),(w*.44,0),(w*.5,height*.58),
                 (w*.38+lean,height*.82),(-w*.4+lean,height*.9),(-w*.5,height*.58)]
        shell=_prism(group,'industrial-annex-shell',outline,depth,STEEL)
        texture(shell,'phase_11/maps/LB_rustyMetal.jpg',18)
        if solid:
            c=CollisionNode('annex-shell-wall');c.setFromCollideMask(BitMask32.allOff())
            c.setIntoCollideMask(BitMask32(5))
            c.addSolid(CollisionBox(Point3(0,0,height*.42),w/2,depth/2,height*.42))
            group.attachNewNode(c)
        for y,h in ((front-.15,0),(-front+.15,180)):
            native(group,'phase_5/models/modules/suit_walls',(0,y,height*.26),
                   part='wall_suit_build4_ul' if variant=='vents' else 'wall_suit_build2_ul',
                   size=(w*.72,None,height*.42),heading=h)
        for x in (-w*.42,w*.42):
            native(group,'phase_11/models/lawbotHQ/LB_pillar',(x,front,0),size=(2.8,3,height*.79))
        if variant=='vents':
            native(group,'phase_10/models/cashbotHQ/pipes_E',(lean,0,height*.79),
                   size=(w*.75,depth*.7,height*.22))
        else:
            cap=stamp(group,(lean,0,height*.85),.25)
            cap.setScale(w/29*.85,depth/22*.9,height*.15/35)
    native(group,'phase_5/models/modules/suit_door',(0,front-.7,0),
           size=(8,1.5,11)).setColorScale(.66,.73,.78,1)
    # Closed clerical annex: decorative, not a service building or active door.
    emblem(group,(0,front-1.5,height*.72),5)
    group.setTag('layout-role','court-divider')
    group.setTag('architecture','cog-'+variant)
    return group


def lamp(root,x,y):
    native(root,'phase_8/models/props/streetlight_DL',(x,y,0),18,'prop_post_three_light')


def windows(root,x,y,z,cols=5,rows=3,spacing=9):
    for row in range(rows):
        for col in range(cols):
            px=x+(col-(cols-1)/2)*spacing;pz=z+row*11
            box(root,'window-trim',(px,y,pz),(5.6,.5,8),DARK)
            box(root,'window',(px,y-.3,pz),(4.6,.15,6.8),GLASS if (row+col)%4 else (.64,.57,.30,1))
            box(root,'window-mullion',(px,y-.45,pz),(.3,.15,7.1),STEEL)


def closed_door(root,x,y,title,subtitle):
    wall(root,'closed-facility',(x,y,9),(22,2,18),DARK)
    door=native(root,'phase_9/models/cogHQ/cogHQ_elevator',(x,y-3,0),21)
    for decal in door.findAllMatches('**/decals'):decal.removeNode()
    emblem(root,(x,y-10.7,20),5.5)
    if not title:return
    native(root,'phase_11/models/lawbotHQ/LB_wall_panel',(x,y-5,24),size=(43,1.5,7))
    from direct.showbase.ShowBaseGlobal import base
    text=label(root,title,(x,y-6,27),2.4,PAPER);text.node().setFont(base.loader.loadFont('phase_3/models/fonts/CourierBold'))
    text.node().setWordwrap(28)
    text=label(root,subtitle,(x,y-6,23),1.1,LIGHT);text.node().setFont(base.loader.loadFont('phase_3/models/fonts/CourierBold'))
    text.node().setWordwrap(32)


def stamp(root,pos,scale=1):
    node=root.attachNewNode('rubber-stamp-landmark');node.setPos(*pos);node.setScale(scale)
    box(node,'stamp-pad',(0,0,2),(29,22,4),DARK)
    box(node,'stamp-base',(0,0,5),(27,20,4),COPPER)
    cylinder(node,'stamp-neck',(0,0,7),7,13,COPPER,4)
    cylinder(node,'stamp-grip',(0,0,20),10,12,COPPER,11)
    cylinder(node,'stamp-grip-cap',(0,0,32),11,3,STEEL,8)
    return node


def archive_tower(root,x,y,height=95,width=32):
    node=root.attachNewNode('filing-cabinet-tower');node.setPos(x,y,0)
    count=max(2,round(height/42));section=height/count
    for i in range(count):
        native(node,'phase_11/models/lawbotHQ/LB_filing_cabA',
            ((i%2)*1.2,0,i*section),size=(width,26,section),solid=True)
    # Every tower has an authored variation, stable across client loads.
    variant=int(abs(x*7+y*11))%5
    texture(box(node,'file-tab',(.6,0,height+1),(width+4,28,2),COPPER),
            'phase_11/maps/LB_rustyMetal.jpg',12)
    for j in range(1+variant%3):
        native(node,'phase_11/models/lawbotHQ/'+
               ('LB_paper_stacks','LB_paper_twist_stacks','LB_paper_big_stacks2')[(variant+j)%3],
               (-width*.22+j*width*.22,(-1)**j*3,height+2),
               size=(width*.33,17,5+(variant+j)%4*2),heading=-13+variant*7+j*11)
    # Offset service pipes break repeated fronts without building signage.
    if variant in (1,3):
        native(node,'phase_10/models/cashbotHQ/pipes_E',
               (width*.52,2,height*.18),size=(4,8,height*.57))
    return node


def ministry(root):
    # Three offset outdoor rooms, separated by real buildings. Neither exit
    # meets the other at a central crossing; the route reveals the hall in stages.
    for name,outline in (
        ('arrival-court',[(-106,-143),(-47,-159),(-13,-130),(-25,-90),(-81,-75),(-109,-102)]),
        ('records-court',[(-157,-48),(-117,-60),(-88,-25),(-91,12),(-133,25),(-158,-5)]),
        ('ministry-forecourt',[(17,28),(63,13),(110,42),(143,76),(132,117),(76,125),(22,96)])):
        ground_patch(root,name,outline,'phase_9/maps/FootFactoryFloor.jpg',30).setColorScale(.71,.77,.81,1)
    curved_path(root,[(0,-190),(0,-150),(-47,-129),(-65,-102),(-62,-55),
        (-30,-26),(15,9),(54,45),(61,83),(29,122)],24)
    curved_path(root,[(29,122),(29,138)],24,False)
    curved_path(root,[(-67,-62),(-121,-52),(-146,-24),(-180,-15)],20)
    curved_path(root,[(65,82),(111,105),(143,95),(180,95)],22)
    curved_path(root,[(-135,-40),(-125,7),(-96,-5),(-66,-41)],12)
    curved_path(root,[(-33,-25),(-12,-63),(-17,-113),(-42,-135)],12)
    curved_path(root,[(89,58),(125,33),(129,-9),(118,-23),(105,-13)],13)
    for name,pos,variant,height,heading in (
        ('FORMS & COPIES',(57,-12,0),'press',35,-18),
        ('TIMEKEEPING',(64,-64,0),'vents',72,33),
        ('IN TRIPLICATE',(60,-114,0),'files',51,-7),
        ('LATE FILINGS',(-64,30,0),'files',76,19),
        ('LOST RECORDS',(-105,76,0),'press',53,16),
        ('INDEX OFFICE',(-139,52,0),'vents',66,-31),
        ('PENDING',(-90,117,0),'files',65,-12),
        ('MAIL INTAKE',(-154,-106,0),'press',43,-24),
        ('REDIRECTIONS',(-116,-150,0),'vents',47,24),
        ('DISPATCH',(128,-77,0),'vents',64,12),
        ('DUPLICATES',(164,-53,0),'files',51,51),
        ('RECHECKS',(160,14,0),'press',44,88)):
        bureau_office(root,name,pos,variant,height,heading)
    # Offset and cant the document hall; it does not sit on a symmetry axis.
    courtyard=root;root=courtyard.attachNewNode('ministry-document-hall')
    root.setPos(19,8,0);root.setH(-4)
    # A fan of misfiled volumes: different heights, setbacks and rotations,
    # rather than three centered rectangular tiers.
    for x,y,w,h,heading in ((-53,157,39,76,-12),(0,165,77,112,0),(48,170,31,139,8)):
        volume=root.attachNewNode('ministry-volume');volume.setPos(x,y,0);volume.setH(heading)
        wall(volume,'document-layer',(0,0,h/2),(w,32,h),STEEL)
        native(volume,'phase_5/models/modules/suit_walls',(0,-16.2,12),
               part='wall_suit_build4_ul',size=(w-8,None,h-24))
        for dx in (-w/2,w/2):
            native(volume,'phase_11/models/lawbotHQ/LB_pillar',(dx,-16,0),size=(3,5,h))
        box(volume,'clip-jaw',(0,-1,h+1),(w+3,36,3),COPPER)
    # Leave a full-size native boss elevator opening, including its cabin depth.
    for x in (-31,31):wall(root,'ministry-front',(x,139,45),(10,12,90),STEEL)
    wall(root,'ministry-front',(0,139,69),(52,12,42),STEEL)
    # Native Cog facade panels carry their original painted windows and UVs.
    native(root,'phase_5/models/modules/suit_walls',(0,132.5,50),
        part='wall_suit_build2_ul',size=(62,None,24))
    for x in (-36,36):native(root,'phase_11/models/lawbotHQ/LB_pillar',(x,133,0),size=(5,6,94))
    _prism(root,'ministry-left-eye',[(-36,88),(-4,83),(-10,78),(-26,80)],1,PAPER,y=131.5)
    _prism(root,'ministry-right-eye',[(4,83),(36,88),(26,80),(10,78)],1,PAPER,y=131.5)
    for x in (-17,17):box(root,'ministry-pupil',(x,130.8,82),(3,.3,5),DARK)
    # Binder clip crowns the document stack; an open center reads against sky.
    for x in (-14,14):box(root,'clip-arm',(x,167,124),(4,8,25),COPPER)
    box(root,'clip-crown',(0,167,137),(31,8,4),COPPER)
    box(root,'clip-jaw',(0,132,98),(48,8,10),COPPER)
    emblem(root,(0,126,97),16)
    root.attachNewNode('bureau-boss-elevator-locator').setPos(0,131,0)
    native(root,'phase_11/models/lawbotHQ/LB_wall_panel',(0,130,48),size=(43,1.5,7))
    label(root,'FINAL REVIEW',(0,128,49),2.4,PAPER)
    for y in (106,113):
        for x in (-12,-4,4,12):cylinder(root,'boss-group-pad',(x,y,.05),2.5,.15,COPPER)
    root=courtyard
    statue=stamp(root,(2,69,0),.62);statue.setH(-18)
    wall(root,'stamp-plinth',(2,69,1),(24,22,2),STEEL)
    # A sheltered dead-end waiting nook and a loading yard, not roadside scatter.
    native(root,'phase_11/models/lawbotHQ/LB_couchA',(-166,16,0),6,heading=65,solid=True)
    native(root,'phase_8/models/props/mailbox_DL',(-119,-88,0),8,heading=20,solid=True).setColorScale(.4,.45,.48,1)
    native(root,'phase_11/models/lawbotHQ/LB_bookshelfA',(-178,3,0),13,heading=90,solid=True)
    for x,y,h in ((112,-50,9),(134,-8,8),(105,-108,10),(-160,-66,7),(-39,37,9)):
        native(root,'phase_11/models/lawbotHQ/LB_CardBoardBoxX3',(x,y,0),h,heading=-15,solid=True)
    for x,y,h in ((98,-38,7),(141,-40,11),(-166,-58,8)):
        native(root,'phase_11/models/lawbotHQ/LB_paper_big_stacks3',(x,y,0),h,heading=15,solid=True)
    for x,y,h in ((-158,-56,13),(-171,67,9),(107,-120,17)):
        native(root,'phase_9/models/cogHQ/SellbotHQExterior',(x,y,0),h,part='Barrel9',solid=True)
    # Distant landmarks occupy the same left/right bearings as their gates.
    for x,y,h in ((-165,200,135),(-125,220,170),(-200,230,155)):
        archive_tower(root,x,y,h)
    bridge=box(root,'distant-archive-skybridge',(-160,210,114),(90,15,12),STEEL)
    native(root,'phase_5/models/modules/suit_walls',(-160,202,109),part='wall_suit_build4_ul',size=(85,None,12))
    stamp(root,(155,205,0),4.3)


def archives(root):
    # A filing district: narrow branching aisles between interior tower banks,
    # one cross-aisle shortcut, and separate sorting pockets at the branch ends.
    curved_path(root,[(0,-170),(-14,-125),(-67,-96),(-76,-48),(-34,-12),
        (-44,43),(-83,84),(-65,108)],20)
    curved_path(root,[(-65,108),(-66,123)],20,False)
    curved_path(root,[(-76,-48),(-122,-30),(-122,3),(-97,24)],13)
    curved_path(root,[(-34,-12),(28,-22),(79,13),(106,62),(80,96)],16)
    curved_path(root,[(28,-22),(50,-71),(96,-92)],15)
    curved_path(root,[(-44,43),(6,56),(43,42),(79,13)],12)
    for name,outline in (
        ('intake-sorting-court',[(-100,-121),(-51,-132),(-36,-98),(-55,-69),(-95,-76)]),
        ('east-sorting-dock',[(43,-119),(105,-119),(115,-85),(78,-70),(43,-83)]),
        ('index-junction',[(41,20),(77,11),(99,36),(86,61),(47,56)])):
        ground_patch(root,name,outline,'phase_9/maps/FootFactoryFloor.jpg',25).setColorScale(.65,.72,.77,1)
    for x,y,h,w in ((-139,-67,95,38),(128,-102,69,34),(157,-1,138,38),
                    (-147,37,116,45),(-169,155,164,42),(133,138,110,38),(-28,175,183,32),
                    (17,-100,38,26),(35,8,115,32),(-93,52,105,24),
                    (80,-52,83,28),(29,96,103,28),(116,36,140,26)):
        archive_tower(root,x,y,h,w)
    bureau_office(root,'DOCUMENT INTAKE',(119,-135,0),'press',35,-12)
    bureau_office(root,'CROSS REFERENCE',(-7,20,0),'files',39,16)
    courtyard=root;root=courtyard.attachNewNode('records-annex')
    root.setPos(-95,-10,0);root.setH(-12)
    # Registry wheel: large circular index-file framing, not a Cashbot vault.
    wheel=root.attachNewNode('rotary-registry');wheel.setPos(0,131,85)
    for i in range(16):
        a=i*math.tau/16
        spoke=box(wheel,'registry-spoke',(math.cos(a)*22,4,math.sin(a)*22),(2,3,42),STEEL)
        spoke.setR(90-math.degrees(a))
        card=native(wheel,'phase_11/models/lawbotHQ/LB_paper_stacks',
            (math.cos(a)*40,0,math.sin(a)*40),size=(10,14,20))
        for shadow in card.findAllMatches('**/*hadow*'):shadow.removeNode()
        card.setR(90-math.degrees(a))
    wall(root,'records-front',(0,147,22),(80,16,44),STEEL)
    for x in (-26,26):box(root,'registry-support',(x,143,61),(5,10,40),COPPER)
    emblem(root,(0,120,85),32)
    closed_door(root,0,137,'RECORDS PROCESSING','TRAINING FACILITY - CLOSED')
    root=courtyard
    for a,b,z in (((-147,37),(-169,155),83),((157,-1),(133,138),66),
                 ((35,8),(116,36),77),((17,-100),(80,-52),29)):
        bridge=root.attachNewNode('cabinet-connector')
        bridge.setPos((a[0]+b[0])/2,(a[1]+b[1])/2,z)
        bridge.setH(math.degrees(math.atan2(b[1]-a[1],b[0]-a[0])))
        width=math.dist(a,b)
        box(bridge,'archive-skybridge',(0,0,0),(width,15,12),STEEL)
        native(bridge,'phase_5/models/modules/suit_walls',(0,-7.6,-5),
            part='wall_suit_build4_ul',size=(width,None,11))
        native(bridge,'phase_5/models/modules/suit_walls',(0,7.6,-5),
            part='wall_suit_build4_ul',size=(width,None,11),heading=180)
    for i,(x,y) in enumerate(((-111,-121),(-139,-6),(-161,98),(150,-56),(164,64),
                            (58,109),(-8,-63),(11,90),(-77,60),(139,-62))):
        native(root,'phase_11/models/lawbotHQ/LB_paper_big_stacks3',(x,y,0),
            size=(11+i%3*2,10,7+i%3*2),heading=i*29,solid=True)
    native(root,'phase_11/models/lawbotHQ/LB_deskA',(108,99,0),7,heading=18,solid=True)
    native(root,'phase_11/models/lawbotHQ/LB_CardBoardBoxX3',(131,107,0),10,solid=True)
    for x,y,heading in ((-114,36,80),(-29,-77,0),(60,-64,-20),(10,71,15)):
        native(root,'phase_11/models/lawbotHQ/LB_bookshelfA',(x,y,0),
               size=(12,5,13),heading=heading,solid=True)


def works(root):
    # Three staggered production yards connected by a dogleg service road.
    # The diagonal conveyor divides the middle yard; branch lanes end at work
    # stations rather than making the same paired loops as the other areas.
    curved_path(root,[(0,-170),(0,-144),(-42,-125),(-61,-70),(0,-40),(43,-40),(75,3),(94,62)],25)
    curved_path(root,[(94,62),(95,83)],25,False)
    curved_path(root,[(-62,-73),(-98,-27),(-100,10),(-98,45),(-44,64),(0,91),(30,95)],18)
    curved_path(root,[(14,-41),(28,10),(18,50),(43,82)],15)
    curved_path(root,[(-43,-126),(17,-144),(77,-136),(108,-107)],13)
    for name,outline in (
        ('receiving-yard',[(-91,-125),(-35,-133),(-21,-101),(-36,-67),(-85,-67)]),
        ('west-service-yard',[(-116,-4),(-84,-8),(-78,35),(-96,59),(-116,43)]),
        ('dispatch-court',[(-6,67),(31,62),(48,86),(38,112),(-1,119),(-22,96)])):
        ground_patch(root,name,outline,'phase_9/maps/FootFactoryFloor.jpg',32).setColorScale(.64,.70,.75,1)
    for name,pos,variant,height,heading in (
        ('PRESS CONTROL',(45,-105,0),'vents',39,-17),
        ('QUALITY ASSURANCE',(-12,30,0),'press',32,12),
        ('OUTGOING ORDERS',(-64,91,0),'files',78,-9),
        ('PNEUMATICS',(118,30,0),'vents',47,25)):
        bureau_office(root,name,pos,variant,height,heading)
    courtyard=root;root=courtyard.attachNewNode('approval-stamp-hall')
    root.setPos(58,-32,0);root.setH(-18)
    wall(root,'approval-hall',(0,147,20),(100,48,40),STEEL)
    stamp(root,(0,150,40),2.7)
    emblem(root,(0,121,35),22)
    closed_door(root,0,121,'CENTRAL APPROVAL','OPERATIONS - CLOSED')
    for x in (-38,38):
        native(root,'phase_5/models/modules/suit_walls',(x,122.5,8),
            part='wall_suit_build4_ul',size=(18,None,25))
    root=courtyard
    # Keep shipments in the belt's local frame so bundles sit on the rotated
    # conveyor, with walking space around both ends.
    line=root.attachNewNode('diagonal-processing-line');line.setPos(-48,15,0);line.setH(-42)
    native(line,'phase_12/models/bossbotHQ/food_belt1_model',size=(18,115,8),solid=True)
    for y in range(-44,50,14):
        native(line,'phase_11/models/lawbotHQ/LB_paper_big_stacks3',(-2,y,3.12),size=(10,9,3.2))
    for i,(x,y,h) in enumerate(((145,-107,9),(152,-24,-7),(-134,92,12))):
        booth=root.attachNewNode('inspection-station');booth.setPos(x,y,0);booth.setH(h)
        wall(booth,'inspection-booth',(0,0,15),(32,30,30),STEEL)
        closed_door(booth,0,-16,None,None)
        cylinder(booth,'status-lamp',(0,-17,32),1.3,2,LIGHT)
    for x,y,h in ((-158,-80,43),(-166,68,57),(174,132,36)):
        native(root,'phase_10/models/cashbotHQ/pipes_E',(x,y,0),h,solid=True)
    for x,y,h in ((-153,-128,12),(-163,21,9),(111,-131,8),
                  (-26,-103,8),(69,-117,7),(-85,62,6),(37,49,7),(127,-65,9)):
        native(root,'phase_9/models/cogHQ/metalCrate',(x,y,0),h,heading=13,solid=True)
    native(root,'phase_9/models/cogHQ/FactoryGearBpost',(-80,155,0),38,solid=True)
    native(root,'phase_9/models/cogHQ/FactoryGearB',(-80,155,34),size=(22,22,5))
    native(root,'phase_9/models/cogHQ/PaintMixer',(-153,140,0),25,solid=True)
    native(root,'phase_9/models/cogHQ/PaintMixer',(-136,-70,0),32,solid=True)
    native(root,'phase_10/models/cashbotHQ/pipes_E',(-49,141,0),46,solid=True)
    for x,y in ((-145,-18),(-140,-3),(30,-81),(134,-51)):
        native(root,'phase_9/models/cogHQ/SellbotHQExterior',(x,y,0),
               12,part='Barrel9',solid=True)


def boundaries(root,zone):
    # Deliberately irregular campus edges, inset yards and angled boundaries.
    outlines={
      H.MINISTRY:MINISTRY_OUTLINE,
      H.ARCHIVES:((-23,-196),(28,-196),(68,-155),(151,-139),(188,-80),
        (175,-19),(200,33),(187,150),(123,187),(34,202),(-84,186),
        (-179,166),(-190,84),(-212,9),(-187,-102),(-100,-163)),
      H.WORKS:((-24,-196),(28,-196),(70,-153),(159,-159),(188,-111),
        (183,-39),(210,11),(204,109),(154,180),(72,196),(-35,188),
        (-121,204),(-184,145),(-195,64),(-173,-31),(-191,-115),(-92,-166))}
    polygon=outlines[zone]
    for i,(a,b) in enumerate(zip(polygon,polygon[1:]+polygon[:1])):
        middle=((a[0]+b[0])/2,(a[1]+b[1])/2)
        if i==0:continue
        length=math.dist(a,b);count=math.ceil(length/22)
        heading=math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
        for j in range(count):
            t=(j+.5)/count
            pos=(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)
            if any(math.dist(pos,gate[:2])<44 for gate in H.GATES[zone]):continue
            native(root,'phase_11/models/lawbotHQ/LB_wall_panel',
                (*pos,0),
                size=(length/count+.1,4,13+(i%3)*2),heading=heading,solid=True)
    # Reuse actual painted skyline meshes, not untextured background boxes.
    for i,(x,y,h) in enumerate(((-330,177,126),(-304,271,170),(-238,295,213),
        (-164,303,154),(-92,293,195),(-23,320,178),(42,310,225),(107,284,153),
        (177,311,194),(246,277,215),(319,246,165),(343,142,109))):
        native(root,'phase_11/models/lawbotHQ/LawbotPlaza',(x,y,-3),
            part=('LB_BLD12','LB_BLD20','LB_BLD16')[i%3],heading='radial',
            size=(56+i%3*9,55,h))


def district_backdrop(root,zone):
    """Dressed 360-degree outskirts, outside all traversable courts and gates."""
    district=root.attachNewNode('layered-industrial-outskirts')
    # Middle distance: low roofs, water towers, pipes and freight, not a void
    # between a short perimeter fence and a row of isolated tall buildings.
    for i,(x,y,h,heading) in enumerate((
        (-248,-140,65,-55),(-259,-64,84,-76),(-254,58,72,-102),
        (-225,152,105,-129),(-185,238,83,-157),(-68,257,63,174),
        (64,249,70,168),(192,230,88,148),(252,160,94,113),
        (265,46,78,92),(249,-61,69,67),(214,-163,91,43),
        (120,-233,62,23),(-127,-238,75,-20))):
        bureau_office(district,('RECORD STORAGE','VENTILATION','PROCESSING')[i%3],
                      (x,y,0),('files','vents','press')[i%3],h,heading+180,solid=False)
        if i%2==0:
            native(district,'phase_9/models/cogHQ/SellbotHQExterior',
                   (x+24,y+12,-1),42+i%3*12,part='WaterTower',heading=heading)
        else:
            native(district,'phase_10/models/cashbotHQ/pipes_E',
                   (x-23,y-8,-1),35+i%4*7,heading=heading)
        for j in range(2):
            native(district,'phase_9/models/cogHQ/metalCrate',
                (x-18+j*19,y-22,0),12+j*7,heading=heading+17*j)
    # Side and rear skyline wraps behind the player's arrival, too.
    for i,angle in enumerate(range(0,360,20)):
        radians=math.radians(angle);radius=390+(i%3)*24
        x,y=math.cos(radians)*radius,math.sin(radians)*radius
        native(district,'phase_11/models/lawbotHQ/LawbotPlaza',(x,y,-4),
               part=('LB_BLD12','LB_BLD16','LB_BLD20')[i%3],heading='radial',
               size=(66+i%4*11,65,100+i%5*22))
    # Zone-specific border silhouettes retain each area's identity.
    if zone==H.ARCHIVES:
        for x,y,h,w in ((-222,95,92,32),(-212,201,145,45),(223,-110,81,34),
                        (211,213,164,38),(-80,250,125,34),(101,264,154,40)):
            archive_tower(district,x,y,h,w).setH((x+y)%23-11)
        for x,y in ((-173,-125),(178,77),(-165,113)):
            native(root,'phase_11/models/lawbotHQ/LB_paper_stack_pallet',(x,y,0),
                   size=(21,18,2.5),heading=17,solid=True)
            native(root,'phase_11/models/lawbotHQ/LB_paper_big_stacks3',(x,y,2.5),
                   size=(16,13,9),heading=17,solid=True)
    elif zone==H.WORKS:
        for x,y,h in ((-229,187,80),(228,-99,60),(199,211,91)):
            native(district,'phase_9/models/cogHQ/PaintMixer',(x,y,0),h)
        native(district,'phase_12/models/bossbotHQ/food_belt1_model',
               (-217,-60,19),size=(17,270,9),heading=-8)
    else:
        for x,y,h in ((-221,128,102),(218,149,85)):
            bureau_office(district,'REGISTRY ANNEX',(x,y,0),
                          'files',h,-25 if x<0 else 25,solid=False)


def build_scene(zone,with_tunnels=True):
    root=NodePath('bureau-campus-%s'%zone)
    world=root.attachNewNode('%s:world'%zone)
    paving(world,zone);boundaries(world,zone);district_backdrop(world,zone)
    {H.MINISTRY:ministry,H.ARCHIVES:archives,H.WORKS:works}[zone](world)
    from .BureauHQDetails import dress_zone
    dress_zone(world,zone)
    if zone==H.MINISTRY:
        for x,y in ((-23,-158),(-101,-101),(-153,-43),(-81,-8),(5,1),(24,101),(146,87),(120,14)):
            lamp(world,x,y)
    else:
        for x in (-95,95):
            for y in (-125,10,105):lamp(world,x,y)
    paint_materials(world)
    if with_tunnels:
        from .ExpansionScene import tunnel
        for target,transform in zip(H.LINKS[zone],H.GATES[zone]):
            gateway=tunnel(world,target,transform,H.SPEC['colors'],cog=True)
            emblem(gateway,(0,3,32),8).setH(180)
    root.setTag('bureau-zone',str(zone))
    return root
