"""Shared world manifest. Keep this module independent of Panda3D.

61000-64999 are now static; dynamic instances start at 65000. Restart all
servers and clients together when upgrading (no live district migration).
"""
ACORN = 19000
BRINY = 61000
HUSH = 62000
DOODLEWOOD = 63000
TUMBLEWEED = 64000
DYNAMIC_ZONE_BEGIN = 65000

NEIGHBORHOODS = {
    ACORN: dict(name='Acorn Acreside', short='acorn', theme='woodland',
                colors=((.35, .48, .30, 1), (.80, .43, .18, 1), (.96, .85, .59, 1)),
                sky=(1, .97, .87, 1), music='phase_8/audio/bgm/DG_nbrhood.ogg',
                landmark='The Great Oak', source=5000),
    BRINY: dict(name='Briny Boardwalk', short='briny', theme='seaside',
                colors=((.27, .65, .68, 1), (.89, .41, .35, 1), (1, .88, .60, 1)),
                sky=(1, .94, .85, 1), music='phase_6/audio/bgm/DD_nbrhood.ogg',
                landmark='Loopy Lighthouse', source=1000),
    HUSH: dict(name='Hush Hollow', short='hush', theme='spooky',
               colors=((.32, .24, .43, 1), (.22, .49, .48, 1), (1, .68, .30, 1)),
               sky=(.38, .32, .57, 1), music='phase_8/audio/bgm/DL_nbrhood.ogg',
               landmark='Backwards Clock Tower', source=9000),
    DOODLEWOOD: dict(name='Doodlewood Studios', short='doodlewood', theme='studio',
                     colors=((.70, .22, .24, 1), (.94, .86, .69, 1), (.94, .65, .25, 1)),
                     sky=(.74, .86, 1, 1), music='phase_6/audio/bgm/MM_nbrhood.ogg',
                     landmark='The Reel Big Theater', source=4000),
    TUMBLEWEED: dict(name='Tumbleweed Terrace', short='tumbleweed', theme='desert',
                     colors=((.72, .39, .26, 1), (.39, .70, .61, 1), (.98, .80, .49, 1)),
                     sky=(.76, .85, .95, 1), music='phase_6/audio/bgm/GS_SZ.ogg',
                     landmark='Ten Gallon Water Tower', source=8000),
}
# Each street is a real, separate zone with a tunnel at both ends. These are
# winding streets have native Cog patrol paths and quest HQs.
STREETS = {
    19100: ('Root Route', ACORN, 5000, ACORN),
    61100: ('Taffy Terrace', BRINY, 1000, BRINY),
    62100: ('Forty Winks Way', HUSH, 9000, HUSH),
    63100: ('Encore Avenue', DOODLEWOOD, 4000, DOODLEWOOD),
    64100: ('Detour Drive', TUMBLEWEED, 8000, TUMBLEWEED),
    19200: ('Bramble Bend', ACORN, ACORN, HUSH),
    61200: ('Limelight Lane', BRINY, BRINY, DOODLEWOOD),
    63200: ('Stagecoach Street', DOODLEWOOD, DOODLEWOOD, TUMBLEWEED),
}
ALL_ZONES = frozenset(NEIGHBORHOODS) | frozenset(STREETS)
SOURCE_NAMES = {1000: "Donald's Dock", 2000: 'Toontown Central', 3000: 'The Brrrgh',
                4000: "Minnie's Melodyland", 5000: 'Daisy Gardens', 6000: 'Acorn Acres',
                8000: 'Goofy Speedway', 9000: "Donald's Dreamland", 10000: 'Bossbot HQ',
                11000: 'Sellbot HQ', 11200: 'Factory Exterior', 12000: 'Cashbot HQ',
                13000: 'Lawbot HQ', 17000: 'MiniGolf'}
# Origins face into the playable space (+Y). Existing playground gates are
# compact freestanding tunnel pavilions on walkable plazas, not wall edits.
# Arrival visgroups verified against the existing DNA's playground tunnels.
STOCK_STREETS = {
    2132: 'Silly Street', 2226: 'Loopy Lane', 2301: 'Punchline Place',
    1101: 'Barnacle Boulevard', 1225: 'Seaweed Street', 1301: 'Lighthouse Lane',
    4127: 'Alto Avenue', 4222: 'Baritone Boulevard', 4340: 'Tenor Terrace',
    5102: 'Elm Street', 5201: 'Maple Street', 5301: 'Oak Street',
    9101: 'Lullaby Lane', 9201: 'Pajama Place',
    3126: 'Walrus Way', 3233: 'Sleet Street', 3301: 'Polar Place',
}
SOURCE_CODES = {5000: 'dg', 1000: 'dd', 9000: 'dl', 4000: 'mm', 8000: 'gs'}
SOURCE_GATES = {5000: (115, 90, .02, 90), 1000: (95, 10, 5.69, 90),
                9000: (60, 100, .02, 180), 4000: (-50, -80, 6.52, 0),
                8000: (55, -25, .09, 90)}
MAP_POSITIONS = {5000: (-.78, .45), ACORN: (-.78, .16), HUSH: (-.78, -.20),
                 9000: (-.78, -.49), 1000: (-.26, .45), BRINY: (-.26, .16),
                 DOODLEWOOD: (.29, .16), 4000: (.29, .45),
                 TUMBLEWEED: (.80, .16), 8000: (.80, -.20)}


def hood_id(zone):
    return STREETS[zone][1] if zone in STREETS else zone - zone % 1000


def zone_name(zone):
    if zone in STREETS:
        return STREETS[zone][0]
    if zone in NEIGHBORHOODS:
        return NEIGHBORHOODS[zone]['name']
    return SOURCE_NAMES.get(zone, str(zone))


def connections(zone):
    if zone in STREETS:
        return STREETS[zone][2:4]
    return tuple(street for street, data in STREETS.items() if zone in data[2:4])


def gate_transforms(zone):
    # Keep this travel manifest aligned with the editable Acorn DNA layouts.
    if zone == ACORN:
        return ((0, -110, 0, 0), (-118, 20, 0, -90))
    from .WorldLayout import ROADS, PLAZA_GATES
    if zone in ROADS:
        return ((0, ROADS[zone][0][1], 0, 0), (0, ROADS[zone][-1][1], 0, 180))
    if zone in PLAZA_GATES:
        return PLAZA_GATES[zone]
    if zone in SOURCE_GATES:
        return (SOURCE_GATES[zone],)
    if zone in STREETS:
        return ((0, -80, 0, 0), (0, 80, 0, 180))
    # Open paths to each gate; landmarks sit behind the central plaza.
    return ((0, -66, 0, 0), (-66, 0, 0, -90), (66, 0, 0, 90))[:len(connections(zone))]


def destinations():
    """Allowlist shared by the admin UI and server; never accept arbitrary IDs."""
    return dict(list(SOURCE_NAMES.items()) + list(STOCK_STREETS.items()) +
                [(z, zone_name(z)) for z in sorted(ALL_ZONES)])


def spawn_point(zone):
    # Root Route bends east here; the original center spawn is inside a shop.
    from .WorldLayout import ROADS
    if zone in ROADS:
        return (0, ROADS[zone][0][1]+30, .3, 0, 0, 0)
    return (0, -18, .3, 0, 0, 0)

# Native service interiors keep the stock branch + 500 + block convention.
SERVICE_BLOCKS = {'gagshop': 19, 'hq': 20}
INTERIOR_EXTERIORS = {zone+500+block: zone for zone in ALL_ZONES
                      for kind,block in SERVICE_BLOCKS.items()
                      if kind=='hq' or zone in NEIGHBORHOODS}
SERVICE_INTERIORS = frozenset(INTERIOR_EXTERIORS)


def exterior_zone(zone):
    return INTERIOR_EXTERIORS.get(zone, zone)


def service_interior(zone, kind):
    return zone+500+SERVICE_BLOCKS[kind]


def minigame_theme(zone):
    hood=hood_id(exterior_zone(zone))
    if hood in NEIGHBORHOODS:
        source=NEIGHBORHOODS[hood]['source']
        return 2000 if source==8000 else source
    return hood
