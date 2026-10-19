"""Native street population settings, shared by the AI and client planners."""
from .ExpansionGlobals import STREETS, hood_id


def hood_rows():
    mixes={19000:(10,30,10,50),61000:(55,15,20,10),62000:(15,45,25,15),
           63000:(35,15,15,35),64000:(20,20,45,15)}
    from .BureauHQGlobals import planner_rows
    return [[zone,10,17,1,5,20,4,(1,5,10,40,60,80),mixes[hood_id(zone)],
             (2,3,4,5),[]] for zone in sorted(STREETS)]+planner_rows()


def dna_path(zone):
    from . import BureauHQGlobals as H
    if zone in H.ZONES:return H.dna_path(zone)
    return 'assets/expansion/patrols/street_%s.dna'%zone
