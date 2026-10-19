"""Final Review Chamber: native Cog architecture, materials and boss rig."""
from panda3d.core import NodePath, Point3, CollisionNode, CollisionPolygon, BitMask32
from .BureauHQScene import native, texture, emblem, wall, STEEL, DARK, COPPER
from .BureauHQDetails import paper_load, machine
from .Geometry import box, mesh, cylinder
from . import BureauBossGlobals as G


def elevator_cabin(art):
    # The stock HQ asset supplies doors/threshold but relies on its containing
    # lobby for the cabin. Enclose our freestanding entrance at native scale.
    for pos,size in (((0,14,15),(25,2,30)),((-12.5,7.5,15),(1,13,30)),
                     ((12.5,7.5,15),(1,13,30)),((0,7.5,30),(26,13,1))):
        texture(wall(art,'bureau-elevator-cabin',pos,size,(.38,.42,.46,1)),
                'phase_9/maps/metal_plate_256_irregular.jpg',18)


def build_entrance_elevator(locator):
    from direct.showbase.ShowBaseGlobal import base
    art=base.loader.loadModel('phase_9/models/cogHQ/cogHQ_elevator')
    art.reparentTo(locator)
    art.find('**/big_frame').hide()
    elevator_cabin(art)
    emblem(art,(0,-1.7,34),7)
    return art


def floor(root, name, points):
    texture(mesh(root, name, points, [tuple(range(len(points)))], (.63,.68,.72,1)),
            'phase_11/maps/LB_CementGround_2.jpg', 28, True)
    col = CollisionNode(name+'-floor')
    col.setFromCollideMask(BitMask32.allOff()); col.setIntoCollideMask(BitMask32.bit(1))
    for i in range(1, len(points)-1):
        col.addSolid(CollisionPolygon(Point3(*points[0]), Point3(*points[i]), Point3(*points[i+1])))
    root.attachNewNode(col)


def build_room():
    root = NodePath('bureau-final-review-chamber')
    floor(root, 'review-floor', [(-81,-90,0),(81,-90,0),(81,86,0),(-81,86,0)])
    # Unequal side wings leave an unobstructed 100-unit combat apron.
    for x,y,w,d,h in ((-84,2,6,184,83),(84,2,6,184,83),(0,89,174,6,83),
                      (-72,-94,24,8,83),(20,-94,124,8,83)):
        texture(wall(root,'chamber-wall',(x,y,h/2),(w,d,h)),
                'phase_11/maps/LB_CementWall_5.jpg',25)
    texture(box(root,'coffered-ceiling',(0,0,83),(174,190,3),(.35,.39,.43,1)),
            'phase_11/maps/LB_rustyMetal.jpg',32)
    for y in (-72,-24,23,70):
        for x in (-78,78):
            native(root,'phase_11/models/lawbotHQ/LB_pillar',(x,y,0),size=(7,9,73))
        native(root,'phase_11/models/lawbotHQ/LB_wall_panel',(0,y,75),size=(159,4,7))
    # The archive gallery is taller on the left; the stamping wing is lower.
    for i,(x,y,h,w) in enumerate(((-72,48,62,16),(-72,7,48,16),(-70,-49,57,16),
                                  (-43,80,65,24),(-14,82,72,25),(52,81,58,24),
                                  (72,59,46,15),(73,15,35,15))):
        for row in range(3):
            native(root,'phase_11/models/lawbotHQ/LB_filing_cabA',
                   (x+(row%2)*1.2,y,row*h/3),size=(w,10,h/3),solid=True,
                   heading=(90 if x < -60 else -90 if x>60 else 0))
        paper_load(root,(x,y,h),i*11,.65,i,False)
    native(root,'phase_10/models/cashbotHQ/pipes_E',(69,43,40),size=(15,43,22))
    native(root,'phase_10/models/cashbotHQ/pipes_E',(67,-46,24),size=(16,32,29),heading=90)
    # Shelves support the paper stacks; nothing floats in the gallery.
    for x,y,z in ((-68,65,8),(-67,34,17),(69,67,4)):
        native(root,'phase_11/models/lawbotHQ/LB_wall_panel',(x,y,z-2),size=(19,15,2))
        for dx in (-6,6):
            texture(wall(root,'gallery-bracket',(x+dx,y,z/2),(1.5,10,z)),
                    'phase_11/maps/LB_rustyMetal.jpg',8)
    for pos in ((-68,65,8),(-67,34,17),(69,67,4),(69,-60,0)):
        paper_load(root,pos,17,.8,2)
    # Dais and two different-width ramps. Floors use real sloping collision.
    floor(root,'director-dais',[(-29,54,6),(51,54,6),(51,85,6),(-29,85,6)])
    texture(wall(root,'dais-face',(12,55,2.9),(80,2,5.8)),
            'phase_11/maps/LB_rustyMetal.jpg',18)
    floor(root,'left-ramp',[(-48,35,0),(-30,35,0),(-30,68,6),(-48,68,6)])
    floor(root,'right-ramp',[(52,47,0),(65,47,0),(65,75,6),(52,75,6)])
    floor(root,'left-landing',[(-48,68,6),(-29,68,6),(-29,85,6),(-48,85,6)])
    floor(root,'right-landing',[(51,75,6),(65,75,6),(65,85,6),(51,85,6)])
    native(root,'phase_11/models/lawbotHQ/LB_wall_panel',(12,84,28),size=(37,3,35))
    emblem(root,(12,81,48),24)
    for i,(x,y,z) in enumerate(G.STATIONS):
        group = machine(root,G.STATION_NAMES[i], 'ticket' if i<2 else 'stamp' if i==4 else 'drawer',
                        (x,y+9,z))
        group.setTag('boss-station',str(i))
        group.clearTag('bureau-action')
        if i<2: paper_load(root,(x+(-9 if i==0 else 9),y+11,0),i*20,.55,i)
    for x,y in ((-66,-5),(64,31),(-55,73)):
        native(root,'phase_9/models/cogHQ/metalCrate',(x,y,0),size=(7,8,6),solid=True)
    # Arrival uses the original full-size eight-Toon elevator interior.
    elevator = root.attachNewNode('bureau-arrival-elevator')
    elevator.setPosHpr(*G.ELEVATOR_POS)
    from direct.showbase.ShowBaseGlobal import base
    art=base.loader.loadModel('phase_9/models/cogHQ/cogHQ_elevator')
    art.reparentTo(elevator)
    elevator_cabin(art)
    # Native doors face -Y; the parent turns them toward the chamber (+Y).
    art.find('**/big_frame').hide()
    emblem(elevator,(0,-1.7,34),7)
    return root
