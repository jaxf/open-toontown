"""Precise UI anchors over the illustrated world artwork (normalized image XY)."""
from . import ExpansionGlobals as E
# Pins sit below each painted landmark. All original playable destinations stay
# on the same page, including golf and the four Cog headquarters.
PINS={
    1000:(.69,.59),2000:(.49,.53),3000:(.74,.32),4000:(.56,.37),
    5000:(.33,.57),6000:(.62,.77),8000:(.42,.78),9000:(.36,.23),
    10000:(.88,.93),11000:(.12,.17),12000:(.31,.93),13000:(.89,.17),
    17000:(.68,.84),
    E.ACORN:(.14,.51),E.BRINY:(.88,.59),E.HUSH:(.21,.33),
    E.DOODLEWOOD:(.84,.79),E.TUMBLEWEED:(.16,.78),
}
NAMES=dict(E.SOURCE_NAMES)
NAMES.update({zone:data['name'] for zone,data in E.NEIGHBORHOODS.items()})
NAMES[17000]='MiniGolf'
# Each expansion road is drawn from the same manifest as the actual tunnels.
# Hand-shaped control points keep curves clear of landmark silhouettes.
BENDS={19100:(.23,.60),19200:(.13,.39),61100:(.79,.63),61200:(.95,.70),
       62100:(.28,.31),63100:(.76,.40),63200:(.50,.88),64100:(.28,.83)}


def map_point(point):
    x,y=point
    return ((x-.5)*2.12,(.5-y)*1.42+.05)


def road_points(street):
    _,_,start,end=E.STREETS[street]
    a=PINS[start];b=BENDS[street];c=PINS[end]
    return [map_point(((1-t)**2*a[0]+2*(1-t)*t*b[0]+t*t*c[0],
                       (1-t)**2*a[1]+2*(1-t)*t*b[1]+t*t*c[1]))
            for t in (i/32 for i in range(33))]

# Original links read from the stock street and safe-zone DNA. Paired streets
# between the same two playgrounds share one map route, as in the original map.
STOCK_LINKS=[
    (2000,5000,(.40,.54)),(2000,4000,(.48,.40)),(2000,1000,(.60,.53)),
    (1000,5000,(.52,.66)),(1000,3000,(.79,.44)),(4000,3000,(.64,.29)),
    (4000,9000,(.47,.24)),(5000,11000,(.15,.48)),(9000,12000,(.04,.66)),
    (3000,13000,(.83,.22)),(2000,8000,(.49,.68)),(1000,6000,(.71,.71)),
    (6000,17000,(.65,.82)),(17000,10000,(.80,.92)),
]


def stock_points(start,end,bend):
    a=PINS[start];c=PINS[end]
    return [map_point(((1-t)**2*a[0]+2*(1-t)*t*bend[0]+t*t*c[0],
                       (1-t)**2*a[1]+2*(1-t)*t*bend[1]+t*t*c[1]))
            for t in (i/32 for i in range(33))]
