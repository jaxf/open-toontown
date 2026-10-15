"""Author native HQ/gag shop/trolley DNA and reserve their scene footprints."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from toontown.expansion import Services as S, ExpansionGlobals as E
import re
OUT=ROOT/'assets/expansion/services'


def reserve_footprints(path, zone):
    # Preserve the authored DNA verbatim except for scenery in service bays.
    source=path.read_text()
    pattern=re.compile(r'(?:prop|node) "([^"\n]+)" \[')
    cursor=0; result=[]
    while True:
        match=pattern.search(source,cursor)
        if not match:result.append(source[cursor:]);break
        result.append(source[cursor:match.start()])
        depth=1;end=match.end()
        while depth:
            depth+=(source[end]=='[')-(source[end]==']');end+=1
        block=source[match.start():end]
        pos=re.search(r'pos \[ ([^]]+) \]',block)
        code=re.search(r'code \[ "([^"\n]+)" \]',block)
        essential=('terrain' in match[1] or 'ground' in match[1] or
                   match[1].startswith('linktunnel') or match[1]=='the-great-oak')
        if essential or not pos or S.keep_scenery(zone,*map(float,pos[1].split()[:2])):
            result.append(block)
        cursor=end
    path.write_text(''.join(result))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for zone in sorted(E.ALL_ZONES):
        folder='acorn' if zone==19000 else 'expansion'
        name=E.zone_name(zone).lower().replace(' ','_')+'.dna'
        reserve_footprints(ROOT/'assets'/folder/'dna'/name,zone)
    storage=[]
    for code,phase in [('TT',4),('DG',8),('DD',6),('DL',8),('MM',6)]:
        hqpath=('phase_3.5/models/modules/hqTT' if code in ('TT','DD') else f'phase_{phase}/models/modules/hq{code}')
        for category,alias,path,node in [
            ('toon_landmark','service_hq_'+code,hqpath,''),
            ('toon_landmark','service_gagshop_'+code,f'phase_{phase}/models/modules/gagShop_{code}',''),
            ('prop','service_trolley_'+code,f'phase_{phase}/models/modules/trolley_station_{code}','prop_trolley_station')]:
            storage.append(f'hood_model "{path}" [ store_node [ "{category}" "{alias}" "{node}" ] ]\n')
    for code in ['door_double_square_ur','door_double_round_ur']:
        storage.append(f'hood_model "phase_3.5/models/modules/doors_practical" [ store_node [ "door_double" "{code}" "{code}" ] ]\n')
    (OUT/'storage_services.dna').write_text(''.join(storage))
    for zone in sorted(E.ALL_ZONES):
        code,phase=S.theme(zone)
        parts=[]
        for kind,(x,y,z,h) in S.placements(zone).items():
            if kind=='trolley':
                parts.append(f'prop "prop_trolley_station_DNARoot" [ code [ "service_trolley_{code}" ] pos [ {x} {y} {z} ] nhpr [ {h} 0 0 ] ]\n')
            else:
                block=E.SERVICE_BLOCKS[kind]
                title='Toon HQ' if kind=='hq' else 'Gag Shop'
                parts.append(f'landmark_building "sz{block}:toon_landmark_service_{kind}_DNARoot" [\n code [ "service_{kind}_{code}" ]\n building_type [ "{kind}" ]\n title [ "{title}" ]\n pos [ {x} {y} {z} ]\n nhpr [ {h} 0 0 ]\n')
                if kind=='gagshop':parts.append(' door [ code [ "door_double_square_ur" ] color [ 1 .83 .58 1 ] ]\n')
                parts.append(']\n')
        (OUT/f'service_{zone}.dna').write_text(f'group "services-{zone}" [ visgroup "{zone}:services" [ vis [ "{zone}:services" ]\n'+''.join(parts)+'] ]\n')

if __name__=='__main__':main()
