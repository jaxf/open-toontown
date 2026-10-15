"""Rebuild the eight streets without replacing hand-adjusted playground DNA.

Run from the repo root with Panda3D, shapely >= 2.1 and stock resources present:
    python -m tools.rebuild_expansion_streets
No game server, window or screenshot renderer is started.
"""
from pathlib import Path
from panda3d.core import NodePath
from tools import build_acorn_models as A
from tools import build_world_models as W
from tools.author_world_layouts import street
from tools.author_services import main as services
from tools.author_cog_patrols import main as patrols
from toontown.expansion import ExpansionGlobals as E
from toontown.expansion.WorldLayout import ROADS, PALETTES


def main():
    A.app=A.ShowBase();A.OUT=W.OUT
    try:
        for hood in PALETTES:
            for index in range(4):
                model=W.shop(hood,index)
                A.save(model.copyTo(NodePath('export')),f'shop_{hood}_{index}')
                model.find('**/scenery-door').removeNode()
                A.save(model,f'building_{hood}_{index}')
        for zone in ROADS:
            name=E.zone_name(zone).lower().replace(' ','_')
            body=street(zone)
            path=Path('assets/expansion/dna')/(name+'.dna')
            path.write_text('// Authored city blocks, native doors and Cog takeovers.\n'+
                f'group "{name}" [ visgroup "{zone}:world" [ vis [ "{zone}:world" ]\n'+body+'] ]\n')
            A.save(W.terrain(zone),'terrain_'+str(zone))
            print('Rebuilt '+E.zone_name(zone),flush=True)
        services()
        patrols()
    finally:
        A.app.destroy()


if __name__=='__main__':main()
