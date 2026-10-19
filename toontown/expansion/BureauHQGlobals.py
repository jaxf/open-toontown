"""Shared Bureaubot campus layout; no engine dependency."""
MINISTRY=14000
ARCHIVES=14200
WORKS=14300
ENTRY=19000
NAMES={MINISTRY:'Ministry Plaza',ARCHIVES:'Endless Archives',WORKS:'Approval Works'}
ZONES=frozenset(NAMES)
SPEC=dict(name='Bureaubot HQ',short='bureau',theme='bureau',
    colors=((.31,.35,.36,1),(.46,.29,.17,1),(.73,.68,.55,1)),
    sky=(.32,.34,.39,1),music='phase_9/audio/bgm/encntr_suit_HQ_nbrhood.ogg',
    landmark='The Ministry',source=5000)
LINKS={MINISTRY:(ENTRY,ARCHIVES,WORKS),ARCHIVES:(MINISTRY,),WORKS:(MINISTRY,)}
GATES={MINISTRY:((0,-190,0,0),(-180,-15,0,-90),(180,95,0,90)),
       ARCHIVES:((0,-170,0,0),),WORKS:((0,-170,0,0),)}
ENTRY_GATE=(118,20,0,90)
SPAWNS={MINISTRY:(0,-145,.3,0,0,0),ARCHIVES:(0,-125,.3,0,0,0),WORKS:(0,-125,.3,0,0,0)}
# Patrols and battles stay away from entrances, landmarks and closed facilities.
PATROLS={MINISTRY:((-85,-130),(-82,-95),(-98,-53),(-132,-33),(-136,-4),
                  (-102,2),(-73,-28),(-30,-21),(17,12),(35,49),(40,84),
                  (80,101),(121,100),(127,77),(85,47),(55,18),(20,-13),
                  (-30,-51),(-45,-88),(-40,-134)),
         ARCHIVES:((-85,-110),(-92,-74),(-93,-39),(-65,-17),(-55,22),(-38,57),
                   (-8,64),(18,55),(55,44),(80,23),(85,-5),(45,-28),(34,-56),
                   (53,-87),(93,-107),(107,-78),(111,-31),(93,1),(67,-10),
                   (28,-40),(-22,-36),(-49,-66),(-51,-113)),
         WORKS:((-71,-110),(-79,-72),(-101,-36),(-106,3),(-98,45),(-44,64),
                (0,91),(30,95),(53,62),(60,17),(71,-12),(54,-37),
                (15,-51),(-30,-70),(-43,-110))}
SECOND_PATROLS={}
BATTLE_PADS={MINISTRY:((-64,-110),(-120,-22),(52,55),(115,92)),
             ARCHIVES:((-67,-91),(-62,-13),(75,-93),(70,35)),
             WORKS:((-60,-94),(-100,24),(62,-25),(18,87))}


def patrol_paths(zone):
    return (PATROLS[zone],)+( (SECOND_PATROLS[zone],) if zone in SECOND_PATROLS else () )


def planner_rows():
    return [[zone,18,24,0,0,0,4,(1,5,10,40,60,80),(0,0,0,0,100),
             (8,9,10),[]] for zone in sorted(ZONES)]


def dna_path(zone):
    return 'assets/bureaubots/hq/patrol_%s.dna'%zone
