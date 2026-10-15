"""Shared service placements and native service DNA loading for all 13 zones."""
from math import hypot
from . import ExpansionGlobals as E
from .WorldLayout import ROADS,curve
STORAGE='assets/expansion/services/storage_services.dna'
LAYOUTS={z:'assets/expansion/services/service_%s.dna'%z for z in E.ALL_ZONES}
PLAYGROUND_SERVICES={
    19000:dict(hq=(-65,-58,0,130),gagshop=(62,-60,0,-130),trolley=(88,65,0,90)),
    61000:dict(hq=(-115,-85,0,100),gagshop=(62,-80,0,-155),trolley=(-100,85,0,0)),
    62000:dict(hq=(-120,-50,0,90),gagshop=(120,5,0,-90),trolley=(5,77,0,0)),
    63000:dict(hq=(-117,65,0,0),gagshop=(100,-100,0,-120),trolley=(-90,-105,0,90)),
    64000:dict(hq=(-120,-85,0,100),gagshop=(80,-115,0,-150),trolley=(-78,105,0,0)),
}


def street_court(zone):
    if zone==19100:
        points=curve([(0,-155),(0,-115),(30,-75),(40,-35),(35,5),(-15,50),(-25,95),(-10,135),(0,165)])
    else:points=curve(ROADS[zone])
    i=min(range(len(points)),key=lambda i:abs(points[i][1]))
    x,y=points[i]
    # Place the bay on the inside of the world footprint, away from the banks.
    side=-1 if x>0 else 1
    return (x+side*69,y),(x,y)


def placements(zone):
    if zone in PLAYGROUND_SERVICES:
        result=PLAYGROUND_SERVICES[zone]
    else:
        (x,y),_=street_court(zone)
        result=dict(hq=(x-25,y+27,0,0),gagshop=(x+24,y+27,0,0),trolley=(x-15,y-40,0,0))
    # Stock service facades face +Y; trolley platforms face -Y.
    return {kind:(x,y,z,h if kind=='trolley' else h+180)
            for kind,(x,y,z,h) in result.items()}


def theme(zone):
    hood=E.hood_id(zone)
    return {19000:('DG',8),61000:('DD',6),62000:('DL',8),
            63000:('MM',6),64000:('TT',4)}[hood]


def keep_scenery(zone,x,y):
    # Reserve the real models' footprints and door approaches. Trolley platforms
    # extend on the local +X/+Y side, so retain a generous clearance around them.
    for kind,(sx,sy,sz,h) in placements(zone).items():
        if hypot(x-sx,y-sy)<(52 if kind=='trolley' else 39):return False
    return True


def attach_services(root,zone,dna_store=None):
    from .AcornDNA import load_scene
    service=load_scene(zone,dna_store,STORAGE,LAYOUTS)
    service.reparentTo(root)


def register_npcs(npc_dict):
    # Clone native clerk/HQ roles, preserving stock dialogue, quests and shopping.
    # Stable NPC IDs are shared by client and AI; no saved Toon data is rewritten.
    templates=[('gagshop',2006),('gagshop',2011),('hq',2007),('hq',2008),('hq',2009),('hq',2010)]
    for index,zone in enumerate(sorted(E.ALL_ZONES)):
        for offset,(kind,source) in enumerate(templates):
            npc_id=50000+index*10+offset
            old=npc_dict[source]
            name=(['Chuckles','Giggles','Officer Oak','Officer Olive','Officer Penny','Officer Pip'][offset])
            npc_dict[npc_id]=(E.service_interior(zone,kind),name,old[2],old[3],1,old[5])


def add_paths(root,zone,model_tools,paving):
    """Bake level service aprons and their approaches into the terrain model."""
    from math import sin,cos,radians
    A=model_tools
    if zone not in PLAYGROUND_SERVICES:
        center,road=street_court(zone)
        A.disk(root,'service-court',center,62,63,paving,.105)
        A.ribbon(root,'service-court-approach',[road,center],15,paving,.11)
    else:
        anchors={19000:(0,-20),61000:(-37,-12),62000:(20,0),
                 63000:(0,0),64000:(-42,-31)}
        for kind,(x,y,z,h) in placements(zone).items():
            # Approach native buildings from +Y and trolley platforms from -Y.
            a=radians(h);side=-1 if kind=='trolley' else 1
            door=(x-sin(a)*18*side,y+cos(a)*18*side)
            anchor=anchors[zone]
            mid=((anchor[0]+door[0])*.5,(anchor[1]+door[1])*.5)
            A.ribbon(root,kind+'-approach',curve([anchor,mid,door]),8,paving,.105)
            A.disk(root,kind+'-apron',(x,y),29 if kind!='trolley' else 43,
                   30 if kind!='trolley' else 38,paving,.11)
