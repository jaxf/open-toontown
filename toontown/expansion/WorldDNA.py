"""Native DNA scenes for every expansion location after the Acorn art pass."""
from . import ExpansionGlobals as E
from . import AcornDNA
from .WorldLayout import ROADS, PLAZA_GATES
STORAGE='assets/expansion/dna/storage_world.dna'
LAYOUTS={zone:'assets/expansion/dna/'+E.zone_name(zone).lower().replace(' ','_')+'.dna'
         for zone in set(ROADS)|set(PLAZA_GATES)}

def load_scene(zone,dna_store=None):
    if zone in ROADS and dna_store is not None:
        from direct.showbase.ShowBaseGlobal import base
        # Expansion streets use the original building/elevator/field-office
        # state machines, so they need the complete native town model catalog.
        AcornDNA.storage_models(base.loader,'assets/expansion/dna/storage_cogs.dna',dna_store)
    return AcornDNA.load_scene(zone,dna_store,STORAGE,LAYOUTS)
