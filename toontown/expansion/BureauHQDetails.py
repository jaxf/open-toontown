"""Native Cog set dressing and small, client-local courtyard machines.

Keep large props out of the main approaches and all battle clearances. Machines
are optional scenery interactions, not progression or distributed rewards.
"""
from . import BureauHQGlobals as H
from .BureauHQScene import (native,texture,wall,emblem,curved_path,ground_patch,
                           STEEL,COPPER,PAPER,DARK,LIGHT)
from .Geometry import box,cylinder


def paper_load(root,pos,heading=0,size=1,variant=0,solid=True):
    group=root.attachNewNode('sorted-paper-load');group.setPos(*pos);group.setH(heading)
    group.setScale(size)
    native(group,'phase_11/models/lawbotHQ/LB_paper_stack_pallet',
           size=(12,10,1.2),solid=solid)
    native(group,'phase_11/models/lawbotHQ/'+
           ('LB_paper_stacks','LB_paper_twist_stacks','LB_paper_big_stacks2')[variant%3],
           (0,0,1.2),size=(10,8,4+variant%3*2),heading=variant*9,solid=solid)
    return group


def machine(root,name,kind,pos,heading=0,target=None):
    """Inspectable machine; moving art is separate from its fixed footprint."""
    group=root.attachNewNode('bureau-machine-'+name)
    group.setPos(*pos);group.setH(heading)
    group.setTag('bureau-action',kind);group.setTag('action-title',name)
    group.attachNewNode('use-point').setPos(0,-9,0)
    native(group,'phase_9/models/cogHQ/metalCrate',size=(9,7,4.5),solid=True)
    emblem(group,(0,-3.65,2.8),2.1)
    light=cylinder(group,'ready-light',(3,-2,4.5),.5,.8,LIGHT)
    group.setPythonTag('status-light',light)
    motion=group.attachNewNode('machine-motion')
    if kind=='stamp':
        native(group,'phase_11/models/lawbotHQ/LB_paper_stacks',
               (0,-.5,4.5),size=(6,5,1.1))
        native(motion,'phase_5/models/props/rubber-stamp',
               (0,0,7.1),height=6,pitch=90)
        for x in (-3.7,3.7):
            texture(cylinder(group,'press-guide',(x,1,4.5),.45,9,STEEL),
                    'phase_11/maps/LB_rustyMetal.jpg',4)
        group.setTag('action-response','APPROVED. Please submit two more copies.')
    elif kind=='drawer':
        native(group,'phase_11/models/lawbotHQ/LB_filing_cabA',
               (0,1,4.5),size=(8,5,9),solid=True)
        texture(box(motion,'catalog-tray',(0,-1,7),(6,4,.4),STEEL),
                'phase_11/maps/LB_rustyMetal.jpg',6)
        native(motion,'phase_11/models/lawbotHQ/LB_paper_stacks',
               (0,-1,7.2),size=(5,3,1.3))
        texture(box(motion,'drawer-front',(0,-3,7.5),(7,.5,2),STEEL),
                'phase_11/maps/LB_rustyMetal.jpg',5)
        cylinder(motion,'drawer-pull',(0,-3.5,7.5),.4,1,COPPER)
        group.setTag('action-response','Record located. Filed under: Pending indefinitely.')
    elif kind=='ticket':
        native(group,'phase_11/models/lawbotHQ/LB_filing_cabA',
               (0,0,4.5),size=(7,5,6),solid=True)
        box(group,'ticket-slot',(0,-2.6,7),(4,.4,.6),DARK)
        native(motion,'phase_11/models/lawbotHQ/LB_paper_stacks',
               (0,-1,6.8),size=(3,3,.2))
        group.setTag('action-response','Your number is 404. This queue cannot be found.')
    else:
        native(group,'phase_9/models/cogHQ/CogDoor_Button',
               (0,-.5,4.5),size=(4,3,3))
        motion.removeNode();motion=target
        group.setTag('action-response','Registry advanced. Your request remains in the queue.')
    group.setPythonTag('action-node',motion)
    return group


def roof_details(root):
    # A mix of roof cargo, short vents and crooked stacks, not the same cap on
    # every building. Bounds are local so rotated annexes remain coherent.
    for i,annex in enumerate(root.findAllMatches('**/=architecture')):
        if i%3==0:continue
        lo,hi=annex.getTightBounds(annex)
        if i%3==1:
            paper_load(annex,(-3,2,hi.z),i*17,.55+(i%4)*.09,i,False)
        else:
            native(annex,'phase_10/models/cashbotHQ/pipes_E',
                   (4,1,hi.z),size=(6,7,7+i%4*2),heading=i*23)


def ministry_details(root):
    # Civic layout: a low queue court on the freed arrival sightline and a
    # second, enclosed service pocket east of the main pedestrian route.
    ground_patch(root,'clerical-queue-court',[(1,-107),(33,-105),(39,-81),
        (29,-57),(4,-59),(-1,-78)],'phase_9/maps/FootFactoryFloor.jpg',23)
    curved_path(root,[(-16,-88),(-1,-93),(18,-94)],10)
    machine(root,'Take a number','ticket',(18,-79,0))
    for x,y,h in ((4,-65,0),(30,-64,180)):
        native(root,'phase_11/models/lawbotHQ/LB_couchA',(x,y,0),
               size=(12,5,5),heading=h,solid=True)
    for x in (8,26):
        for y in (-99,-91):
            cylinder(root,'queue-post',(x,y,0),.65,4,STEEL)
        texture(box(root,'queue-rail',(x,-95,3),(1,8,.8),COPPER),
                'phase_11/maps/LB_rustyMetal.jpg',4)
    ground_patch(root,'east-certification-pocket',[(96,-41),(124,-39),
        (126,-16),(102,-9),(92,-22)],'phase_9/maps/FootFactoryFloor.jpg',20)
    machine(root,'Certify a form','stamp',(107,-31,0),180)
    for p,h,v in (((146,-74,0),9,1),((-155,81,0),-22,2),((-166,-124,0),18,0)):
        paper_load(root,p,h,.9,v)
    # Courthouse detail stays at the side wings; the central door and emblem
    # are kept exposed. Paper bundles sit on the stepped document roof.
    hall=root.find('**/ministry-document-hall')
    for p,h,v in (((-50,160,78),-12,1),((47,169,141),8,2)):
        paper_load(hall,p,h,1.5,v,False)
    for x,y in ((-37,103),(81,141)):
        native(root,'phase_11/models/lawbotHQ/LB_pillar',(x,y,0),size=(5,6,17),solid=True)
        emblem(root,(x,y-3.2,13),4)


def archives_details(root):
    # A low intake apron now opens the view to the registry; the tall interior
    # banks stay on the east side. Two narrow aisles end in working alcoves.
    curved_path(root,[(-122,-15),(-111,-21),(-108,-14)],9)
    machine(root,'Search the catalog','drawer',(-108,-5,0))
    curved_path(root,[(-80,87),(-95,88),(-99,96)],9)
    machine(root,'Advance the registry','registry',(-99,105,0),
            target=root.find('**/rotary-registry'))
    for p,h,v,s in (((-137,13,0),11,1,.8),((-163,-38,0),-13,2,1),
                      ((148,96,0),-27,0,1.1),((61,121,0),17,2,1.1),
                      ((-40,144,0),8,0,.85),((142,-117,0),-15,1,.7)):
        paper_load(root,p,h,s,v)
    # A stepped, raised storage bank gives the west alcove a defined back wall.
    for i,(x,y,h) in enumerate(((-168,-12,25),(-175,14,34),(-168,54,22))):
        native(root,'phase_11/models/lawbotHQ/LB_filing_cabA',
               (x,y,0),size=(18,13,h),heading=18-i*12,solid=True)
        paper_load(root,(x,y,h),i*19,.9,i,False)
    for x,y,h in ((-135,114,24),(161,121,31)):
        native(root,'phase_11/models/lawbotHQ/LB_bookshelfA',
               (x,y,0),size=(19,8,h),heading=23,solid=True)


def works_details(root):
    # Receiving apron, diagonal production line, and tall pipe-yard at the
    # western edge make this a factory rather than another cabinet district.
    ground_patch(root,'press-test-apron',[(-11,-129),(23,-123),(29,-89),
        (5,-80),(-13,-95)],'phase_9/maps/FootFactoryFloor.jpg',20)
    curved_path(root,[(17,-144),(-4,-127),(-4,-111)],11)
    machine(root,'Test the stamping press','stamp',(-4,-102,0))
    curved_path(root,[(-99,-19),(-120,-26),(-129,-18)],10)
    machine(root,'Open the dispatch drawer','drawer',(-129,-9,0),-10)
    line=root.find('**/diagonal-processing-line')
    # A high gantry frames the conveyor only, clear of the hall landmark.
    for x in (-12,12):
        texture(wall(line,'conveyor-gantry-leg',(x,10,11),(3,6,22),STEEL),
                'phase_11/maps/LB_rustyMetal.jpg',8)
    texture(box(line,'conveyor-gantry',(0,10,23),(29,8,4),STEEL),
            'phase_11/maps/LB_rustyMetal.jpg',8)
    emblem(line,(0,5.8,23),5)
    for i,p in enumerate(line.findAllMatches('**/=source-model')):
        if 'paper_big' in p.getTag('source-model'):
            p.setH((i%3-1)*9);p.setScale(p.getScale()*(.85+i%3*.12))
            p.setTag('bureau-ambient','conveyor')
    gear=root.find('**/native-FactoryGearB')
    if not gear.isEmpty():gear.setTag('bureau-ambient','gear')
    for p,h,v,s in (((-144,-109,0),18,0,1.1),((88,-137,0),-7,1,.8),
                      ((143,17,0),13,2,1),((-106,120,0),24,1,.9),
                      ((150,68,0),-18,0,1.1)):
        paper_load(root,p,h,s,v)
    for x,y,z,h in ((-151,12,0,30),(-144,43,0,39),(168,78,0,27)):
        native(root,'phase_10/models/cashbotHQ/pipes_E',(x,y,z),h,solid=True)
    # Long rear utility runs layer the industrial horizon without crossing any
    # landmark or player route. Original texture, deliberately bent alignment.
    for x,y,h in ((-115,168,38),(3,174,46),(165,151,34)):
        native(root,'phase_10/models/cashbotHQ/pipes_E',(x,y,0),
               size=(49,14,h),heading=-14+x%19)


def dress_zone(root,zone):
    {H.MINISTRY:ministry_details,H.ARCHIVES:archives_details,H.WORKS:works_details}[zone](root)
    roof_details(root)
