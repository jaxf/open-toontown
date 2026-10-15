"""Initial DNA authoring recipe. Re-run only to intentionally replace layouts.

The game/editor reads the committed DNA files, not this placement recipe.
"""
from pathlib import Path
import sys
from math import sin,cos,pi,degrees,atan2
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from toontown.expansion import ExpansionGlobals as E
from toontown.expansion.WorldLayout import ROADS,PLAZA_GATES,PALETTES,ROAD_PROFILES,curve,along,road_paths,distance_to_path
OUT=ROOT/'assets/expansion/dna'


def prop(name,code,pos=(0,0,0),h=0,scale=1,children='',color=None):
    if isinstance(scale,(int,float)):scale=(scale,)*3
    kind='node' if code=='DCS' else 'prop'
    code_line='' if code=='DCS' else f' code [ "{code}" ]\n'
    s=f'{kind} "{name}" [\n{code_line} pos [ {pos[0]:.4f} {pos[1]:.4f} {pos[2]:.4f} ]\n nhpr [ {h:.4f} 0 0 ]\n scale [ {scale[0]:.4f} {scale[1]:.4f} {scale[2]:.4f} ]\n'
    if color:s+=' color [ '+' '.join(map(str,color))+' ]\n'
    return s+children+']\n'


def gate(target,transform,hood):
    code=E.SOURCE_CODES.get(target,E.NEIGHBORHOODS[E.hood_id(target)]['short'] if E.hood_id(target) in E.NEIGHBORHOODS else 'tt')
    x,y,z,h=transform
    return prop(f'linktunnel_{code}_{target}','DCS',(x,y,z),h,children=
        prop('native-tunnel','tunnel_'+PALETTES[hood]['code'],(-60,-95,-6.6666))+
        prop('destination-sign','sign_'+str(target),(0,1,18),180))


NAMES={
 19000:['BRANCH OFFICE','FERN AND GAMES','THE NUT HOUSE','LEAF IT TO ME','BARKING MAD','ROOT BEER'],
 61000:['PIER PRESSURE','TAFFY TOGETHER','SHELL WE DANCE','BUOY OH BUOY','SALTWATER SMILES','FISHFUL THINKING'],
 62000:['THE BOO-TIQUE','REST IN PIECES','FRIGHT AND EARLY','THE CREAK EASY','NIGHT OWL BOOKS','SNOOZE NEWS'],
 63000:['TAKE TWO','REEL DEALS','PROPS TO YOU','STAR TREATMENT','THE CASTING CALL','FRAME OF MIND'],
 64000:['DRY HUMOR','HIGH NOON NOODLES','CACTUS PRACTICE','WELL I NEVER','SPUR OF THE MOMENT','DUST BUSTERS']}


def shop(hood,i,pos,h,scale=1,block=None):
    if block is not None:
        name=f'tb{block}:toon_landmark_shop_DNARoot'
        return (f'landmark_building "{name}" [ code [ "building_{hood}_{i%4}" ] '
            f'title [ "{NAMES[hood][i%6]}" ] pos [ {pos[0]:.4f} {pos[1]:.4f} .12 ] '
            f'nhpr [ {h:.4f} 0 0 ] scale [ {scale} {scale} {scale} ]\n'
            'door [ code [ "door_double_round_ur" ] color [ .82 .88 .68 1 ] ]\n'+
            prop('shop-name',f'shop_sign_{hood}_{i%6}',(0,-.8,14),scale=.95)+']\n')
    # Sign models are generated once per theme, outside the native modules.
    return prop('storefront-%s-%s'%(hood,i),'DCS',pos,h,scale,children=
        prop('painted-native-shop',f'shop_{hood}_{i%4}')+
        prop('shop-name',f'shop_sign_{hood}_{i%6}',(0,-.8,14),scale=.95))


def scenery(hood,index,pos,h=0):
    if hood==64000:return prop('cactus-'+str(index),'cactus',pos,h,1+(index%3)*.15)
    if hood==61000:alias='palm';s=1.2
    elif hood==62000:alias='dream_tree';s=1.7
    elif hood==63000:alias='music_tree';s=1.5
    else:alias='forest_tree';s=1.6
    return prop('tree-'+str(index),alias,pos,h,s)


def street(zone):
    hood=E.hood_id(zone);end=E.STREETS[zone][3]
    path=curve(ROADS[zone]);parts=[prop('winding-terrain','terrain_'+str(zone))]
    for target,tr in zip(E.connections(zone),((0,path[0][1],0,0),(0,path[-1][1],0,180))):parts.append(gate(target,tr,hood))
    profile=ROAD_PROFILES[zone]
    routes=road_paths(zone)
    placements=[]
    for route_index,route in enumerate(routes):
        placements.extend((route_index,)+point for point in along(route,profile['spacing']+5,65))
    from toontown.expansion.Services import keep_scenery
    building_rows=[];block=0
    for i,(route_index,x,y,tx,ty) in enumerate(placements):
        # Cross-neighborhood streets introduce the destination's storefronts.
        theme=end if end in PALETTES and i>len(placements)*.65 else hood
        nx,ny=-ty,tx
        for side in (-1,1):
            sx,sy=x+nx*side*profile['frontage'],y+ny*side*profile['frontage']
            # Junction sightlines and the far side of each loop remain open.
            if abs(sx)>175 or any(distance_to_path(sx,sy,other)<profile['sidewalk']+19
                for j,other in enumerate(routes) if j!=route_index):continue
            h=degrees(atan2(ty,tx))+(180 if side==-1 else 0)
            idx=i*2+(side==1)
            # Small pocket squares punctuate long continuous shop frontages.
            if i%profile['court']==profile['court']//2:
                parts.append(scenery(theme,idx,(x+nx*side*37,y+ny*side*37,0),h))
                parts.append(prop('rest-bench-'+str(idx),'bench',(x+nx*side*29,y+ny*side*29,0),h,1.2))
                if theme==63000:parts.append(prop('camera-'+str(idx),'movie_camera',(x+nx*side*45,y+ny*side*45,0),h))
            else:
                if keep_scenery(zone,sx,sy):
                    block+=1
                    if block>99:raise ValueError("Too many buildings in street %s"%zone)
                    if block==19:block=21  # native service block IDs
                    scale=.94+(i%3)*.03
                    parts.append(shop(theme,idx,(sx,sy,0),h,scale,block=block))
                    building_rows.append(dict(block=block,x=round(sx,4),y=round(sy,4),h=round(h,4),scale=scale))
            if i%3==0:
                parts.append(prop('streetlight-'+str(idx),('western_lamp' if theme==64000 else ('lamp_alt_' if i%2 else 'lamp_')+PALETTES[theme]['code']),
                    (x+nx*side*(profile['sidewalk']-3),y+ny*side*(profile['sidewalk']-3),0),h,1.15))
            if i%3==0:
                parts.append(scenery(theme,idx+200,(x+nx*side*71,y+ny*side*71,0),h))
            if theme==64000 and i%4==0:
                parts.append(prop('sandstone-'+str(idx),'mesa',(x+nx*side*103,y+ny*side*103,0),h,1.3))
    import json
    directory=ROOT/'assets/expansion/patrols';directory.mkdir(parents=True,exist_ok=True)
    (directory/f'buildings_{zone}.json').write_text(json.dumps(building_rows,indent=2)+'\n')
    return ''.join(parts)


def playground(zone):
    parts=[prop('playground-terrain','terrain_'+str(zone))]
    for target,tr in zip(E.connections(zone),PLAZA_GATES[zone]):parts.append(gate(target,tr,zone))
    landmark={61000:('lighthouse',(90,78,0),1),62000:('clock_tower',(-48,45,0),1),
              63000:('theater',(35,78,0),1.1),64000:('water_tower',(75,62,0),1)}[zone]
    parts.append(prop('neighborhood-landmark',landmark[0],landmark[1],0,landmark[2]))
    # Each playground has its own street plan, frontage rhythm and open spaces.
    spots={
      61000:[(-53,-107,115),(-76,-72,92),(-77,-35,80),(-65,9,42),
             (-94,61,0),(-132,62,0),(14,-96,175),(51,-69,155),(93,-32,-95)],
      62000:[(-84,-9,100),(-94,30,75),(-80,87,30),(-36,112,5),
             (14,125,-10),(63,111,-35),(109,65,-85),(96,-17,-105),
             (79,-84,-150),(-21,-88,140)],
      63000:[(-51,-112,85),(-57,-67,95),(-59,-23,85),(-110,30,10),
             (-73,92,0),(-22,94,-15),(49,-112,-95),(65,-73,-90),
             (121,-43,-75),(132,10,-70),(99,94,-15)],
      64000:[(-81,-104,140),(-106,-69,100),(-115,-25,90),(-79,25,45),
             (-30,84,10),(20,103,-10),(117,77,-80),(132,25,-90),
             (124,-26,-110),(85,-85,-145),(31,-116,175)],
    }[zone]
    for i,(x,y,h) in enumerate(spots):
        parts.append(shop(zone,i,(x,y,0),h,[.88,1.12,.96,1.04][i%4]))
    trees={
      61000:[(-100,-105),(-108,-50),(-68,78),(-27,9),(27,-51),(76,10),(130,111)],
      62000:[(-133,109),(-104,80),(-8,115),(39,117),(107,101),(128,5),
              (70,-105),(-18,-62),(-105,-64),(-132,-12),(4,55)],
      63000:[(-82,-140),(-91,-88),(-148,2),(-120,85),(12,126),(126,116),
              (153,-34),(101,-102),(57,-144),(-47,35)],
      64000:[(-150,-105),(-142,-14),(-120,110),(-64,133),(26,137),(133,118),
              (159,19),(144,-91),(49,-145),(-58,-141)],
    }[zone]
    for i,(x,y) in enumerate(trees):
        parts.append(scenery(zone,i,(x,y,0),i*41))
        if zone==64000:
            parts.append(prop('mesa-'+str(i),'mesa',(x*1.12,y*1.08,0),i*29,1.1+i%3*.4))
    furniture={
      61000:[(-53,-88,90),(-52,-28,90),(-13,28,25),(27,38,25),(68,52,25),(65,-22,-50)],
      62000:[(9,-105,0),(72,-49,-90),(39,-8,35),(-15,32,-80),(-61,65,30),(56,84,0)],
      63000:[(-32,-120,90),(19,-90,-90),(-34,-44,90),(34,-12,-50),(-78,22,0),(93,23,0)],
      64000:[(-63,-76,75),(-73,-37,90),(-37,8,45),(40,44,-30),(94,37,-90),(101,-53,-90)],
    }[zone]
    for i,(x,y,h) in enumerate(furniture):
        parts.append(prop('plaza-lamp-'+str(i),('western_lamp' if zone==64000 else 'lamp_'+PALETTES[zone]['code']),(x,y,0),h,1.25))
        if i%2==0:parts.append(prop('rest-bench-'+str(i),'bench',(x+5,y+4,0),h,1.2))
    if zone==61000:
        for i,(x,y,h) in enumerate([(22,34,25),(37,43,25),(53,52,25),(70,59,25),
                                    (6,62,25),(21,70,25),(38,79,25),(55,88,25),(110,99,-35)]):
            parts.append(prop('pier-rail-'+str(i),'pier_rail',(x,y,0),h))
        for i,(x,y) in enumerate([(-43,-58),(-93,37),(70,81),(-17,39)]):
            parts.append(prop('dock-barrel-'+str(i),'barrel',(x,y,0),i*20,2))
        parts.append(prop('anchor-monument','anchor',(-13,-62,0),-20,1.6))
    elif zone==63000:
        for i,(x,y,h) in enumerate([(-68,48,-40),(85,-54,55),(13,30,20)]):
            parts.append(prop('studio-camera-'+str(i),'movie_camera',(x,y,0),h,1.4))
        for i,(x,y) in enumerate([(-60,62),(76,-36),(48,26)]):
            parts.append(prop('music-planter-'+str(i),'music_planter',(x,y,0),0,1.8))
    elif zone==62000:
        for i,(x,y) in enumerate([(60,-30),(-43,12),(36,79)]):
            parts.append(prop('garden-table-'+str(i),'garden_table',(x,y,0),i*34,1.2))
    # Deterministic scattered clusters: retain clear doors, paths and landmark views.
    import random,re
    from toontown.expansion.Services import keep_scenery
    from toontown.expansion.Treasures import SPAWNS
    rng=random.Random(zone)
    occupied=[tuple(map(float,m)) for m in re.findall(r'pos \[ ([^ ]+) ([^ ]+) [^ ]+ \]', ''.join(parts))]
    added=0
    for attempt in range(250):
        x,y=rng.uniform(-130,130),rng.uniform(-118,125)
        if not keep_scenery(zone,x,y):continue
        if any((x-a)**2+(y-b)**2<12**2 for a,b in SPAWNS[zone]):continue
        if any((x-a)**2+(y-b)**2<21**2 for a,b in occupied):continue
        if abs(x)<20 or (zone==61000 and x>0 and y>30):continue
        kit={61000:['planter_61000','barrel','palm'],62000:['planter_62000','garden_table','dream_tree'],
             63000:['planter_63000','movie_camera','music_planter'],64000:['planter_64000','cactus','barrel']}[zone]
        parts.append(prop('garden-cluster-'+str(added),kit[added%3],(x,y,.12),rng.randrange(360),1.2 if added%3 else 1))
        if added%3==0:parts.append(prop('cluster-bench-'+str(added),'bench',(x+8,y+2,.12),rng.randrange(360)))
        occupied.append((x,y));added+=1
        if added>=18:break
    return ''.join(parts)


def main():
    import json
    OUT.mkdir(parents=True,exist_ok=True)
    entries=[]
    def alias(code,path,node=''):
        entries.append(f'hood_model "{path}" [\n store_node [ "prop" "{code}" "{node}" ]\n]\n')
    for p in sorted((ROOT/'assets/expansion/models').glob('*.bam.pz')):
        # Native DNA replaces the final extension with bam. Let Panda resolve
        # the compressed .bam.pz file from its logical .bam filename.
        if not p.name.startswith('building_'):
            alias(p.name[:-7],p.relative_to(ROOT).as_posix()[:-3])
    alias('bench','assets/acorn/models/woodland_bench.bam')
    for code,phase in [('DD',6),('DL',8),('MM',6),('DG',8)]:
        alias('tunnel_'+code,f'phase_{phase}/models/modules/safe_zone_tunnel_{code}','prop_safe_zone_tunnel')
        alias('lamp_'+code,f'phase_{phase}/models/props/streetlight_{code}',
            dict(DD='streetlight_DD_left',DL='prop_post_one_light',MM='MM_flute_lamp',DG='prop_DG_flower_lamp1')[code])
        alias('lamp_alt_'+code,f'phase_{phase}/models/props/streetlight_{code}',
            dict(DD='streetlight_DD_right',DL='prop_post_three_light',MM='MM_trumpets_lamp',DG='prop_DG_flower_lamp2')[code])
    for code,path,node in [
      ('forest_tree','phase_3.5/models/props/trees','prop_tree_large_no_box_ul'),
      ('palm','phase_6/models/props/palm_tree_topflat',''),
      ('dream_tree','phase_8/models/props/trees_DL','prop_tree_DL_brickbox_ur'),
      ('music_tree','phase_6/models/props/trees_MM','prop_tree_small_ur'),
      ('barrel','phase_6/models/props/small_round_barrel',''),
      ('anchor','phase_6/models/props/anchor',''),
      ('music_planter','phase_6/models/props/minnie_planter',''),
      ('garden_table','phase_8/models/props/daisy_park_table','')]:alias(code,path,node)
    for hood in PALETTES:
        for i in range(4):alias(f'building_{hood}_{i}',f'assets/expansion/models/building_{hood}_{i}.bam')
    alias('door_double_round_ur','phase_3.5/models/modules/doors_practical','door_double_round_ur')
    for track,model in [('c','corp'),('s','sales'),('l','legal'),('m','money')]:
        for level in range(1,6):alias(f'suit_landmark_{track}{level}',f'phase_4/models/modules/suit_landmark_{model}')
    (OUT/'storage_world.dna').write_text('// Native expansion model palette.\n'+''.join(entries))
    for zone in sorted(set(ROADS)|set(PLAZA_GATES)):
        name=E.zone_name(zone).lower().replace(' ','_')
        body=street(zone) if zone in ROADS else playground(zone)
        (OUT/(name+'.dna')).write_text('// Authored scene; street landmarks support native interiors and Cog takeovers.\n'+
            f'group "{name}" [\n visgroup "{zone}:world" [\n vis [ "{zone}:world" ]\n'+body+']\n]\n')
    (ROOT/'assets/expansion/editor/WX.json').write_text(json.dumps({'name_longhand':'expanded_toontown',
        'storage_files':['assets/expansion/dna/storage_world.dna','assets/expansion/services/storage_services.dna']},indent=2)+'\n')

if __name__=='__main__':
    main()
    from tools.author_services import main as services
    services()
