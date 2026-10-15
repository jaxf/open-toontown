"""Bake grounded aliases and normalize top-level DNA placements after authoring."""
from pathlib import Path
import re
from toontown.expansion import AcornDNA, ExpansionGlobals as E
from tools import build_acorn_models as A
from tools.world_dressing import planter, enclosure
from panda3d.core import NodePath
from toontown.expansion.WorldLayout import terrain_height, road_paths, distance_to_path, ROAD_PROFILES, street_bounds
ROOT=Path(__file__).resolve().parents[1]


def main():
    A.app=A.ShowBase();A.OUT=ROOT/'assets/expansion/models'
    for hood in E.NEIGHBORHOODS:A.save(planter(hood,A),'planter_'+str(hood))
    for storage in ('assets/expansion/dna/storage_world.dna','assets/acorn/dna/storage_acorn.dna'):
        models=AcornDNA.storage_models(A.app.loader,storage)
        text=(ROOT/storage).read_text()
        aliases=[]
        for alias,model in models.items():
            if alias.startswith(('lamp_','tree_')) or alias in ('palm','dream_tree','music_tree','forest_tree','forest_tree_b','pink_flowers','fountain','barrel','anchor','music_planter','garden_table','garden_lamp','garden_tree','flowerbox','small_tree','bench','woodland_bench'):
                root=NodePath('grounded-'+alias);child=model.copyTo(root)
                lo,hi=child.getTightBounds();child.setZ(-lo.z)
                name='grounded_'+alias;A.save(root,name)
                # Replace only the matching palette entry, retaining its alias.
                pattern=r'hood_model "[^"]+" \[\s*store_node \[ "prop" "'+re.escape(alias)+r'" "[^"]*" \]\s*\]'
                text=re.sub(pattern,f'hood_model "assets/expansion/models/{name}.bam" [ store_node [ "prop" "{alias}" "" ] ]',text)
        for hood in E.NEIGHBORHOODS:
            if f'"planter_{hood}"' not in text:text+=f'\nhood_model "assets/expansion/models/planter_{hood}.bam" [ store_node [ "prop" "planter_{hood}" "" ] ]\n'
        (ROOT/storage).write_text(text)
    for path in (ROOT/'assets/expansion/dna').glob('*.dna'):
        if path.name.startswith('storage_'):continue
        zone=next(z for z in E.ALL_ZONES if E.zone_name(z).lower().replace(' ','_')==path.stem)
        source=path.read_text();cursor=0;out=[]
        pattern=re.compile(r'(?:prop|node|landmark_building) "([^"\n]+)" \[')
        while True:
            m=pattern.search(source,cursor)
            if not m:out.append(source[cursor:]);break
            out.append(source[cursor:m.start()]);depth=1;end=m.end()
            while depth:depth+=(source[end]=='[')-(source[end]==']');end+=1
            block=source[m.start():end]
            if not any(k in m[1] for k in ('terrain','ground','linktunnel')):
                pos=re.search(r'pos \[ ([^ ]+) ([^ ]+) [^ ]+ \]',block)
                if pos:
                    x,y=map(float,pos.groups())
                    if zone in ROAD_PROFILES and block.startswith('prop'):
                        x0,y0,x1,y1=street_bounds(zone)
                        if not (x0<x<x1 and y0<y<y1) or min(distance_to_path(x,y,r) for r in road_paths(zone))<ROAD_PROFILES[zone]['road']+3:
                            cursor=end;continue
                    z=.12+terrain_height(zone,x,y)
                    block=block[:pos.start()]+f'pos [ {x:.4f} {y:.4f} {z:.4f} ]'+block[pos.end():]
            out.append(block);cursor=end
        path.write_text(''.join(out))
    # Acorn's original shop groups get closed courtyard backs as well.
    path=ROOT/'assets/acorn/dna/acorn_acreside.dna'
    s=path.read_text();pattern=re.compile(r'(?:prop|node|landmark_building) "([^"\n]+)" \[')
    cursor=0;out=[]
    while True:
        m=pattern.search(s,cursor)
        if not m:out.append(s[cursor:]);break
        out.append(s[cursor:m.start()]);depth=1;end=m.end()
        while depth:depth+=(s[end]=='[')-(s[end]==']');end+=1
        block=s[m.start():end]
        if 'shop_shell_' in block:
            # Replace the old independent door/backing with the same complete,
            # origin-aligned native shop kit used by the other playgrounds.
            style=re.search(r'shop_shell_DG_([A-D])',block)[1]
            index='ABCD'.index(style)
            sign=re.search(r'code \[ "([^"]+_sign)" \]',block)
            prefix=block[:block.index('prop "')]
            block=prefix+f'prop "complete-acorn-shop" [ code [ "shop_19000_{index}" ] ]\n'
            if sign:block+=f'prop "shop-sign" [ code [ "{sign[1]}" ] pos [ 0 -.8 14 ] ]\n'
            block+=']'
        if not any(k in m[1] for k in ('terrain','ground','linktunnel')):
            pos=re.search(r'pos \[ ([^ ]+) ([^ ]+) [^ ]+ \]',block)
            if pos:
                x,y=map(float,pos.groups());z=.12+terrain_height(19000,x,y)
                block=block[:pos.start()]+f'pos [ {x:.4f} {y:.4f} {z:.4f} ]'+block[pos.end():]
        out.append(block);cursor=end
    source=''.join(out)
    if 'acorn-flower-cluster' not in source:
        from tools.author_world_layouts import prop
        clusters=''.join(prop('acorn-flower-cluster-'+str(i),'planter_19000',(x,y,.12),h)
            for i,(x,y,h) in enumerate([(-28,-55,20),(30,-40,-25),(-36,36,40),(45,30,70),
                (-12,88,10),(34,100,-20),(-107,83,60),(115,-23,80),(20,-85,-10)]))
        source=source.rstrip()[:-1]+clusters+'\n]\n'
    path.write_text(source)
    root=NodePath('acorn-shop-fence');enclosure(root,19000,A,(-18,-3,18,30),-1);A.save(root,'acorn_shop_fence')
    path=ROOT/'assets/acorn/dna/storage_acorn.dna';s=path.read_text()
    for index in range(4):
        alias=f'shop_19000_{index}'
        if f'"{alias}"' not in s:s+=f'\nhood_model "assets/expansion/models/{alias}.bam" [ store_node [ "prop" "{alias}" "" ] ]\n'
    if '"acorn_shop_fence"' not in s:s+='\nhood_model "assets/expansion/models/acorn_shop_fence.bam" [ store_node [ "prop" "acorn_shop_fence" "" ] ]\n'
    path.write_text(s)
    A.app.destroy()

if __name__=='__main__':main()
