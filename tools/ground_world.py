"""Bake grounded aliases and normalize top-level DNA placements after authoring."""
from pathlib import Path
import re
from toontown.expansion import AcornDNA, ExpansionGlobals as E
from tools import build_acorn_models as A
from tools.world_dressing import planter, enclosure
from panda3d.core import NodePath
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
        if path.name=='storage_world.dna':continue
        source=path.read_text();cursor=0;out=[]
        pattern=re.compile(r'(?:prop|node) "([^"\n]+)" \[')
        while True:
            m=pattern.search(source,cursor)
            if not m:out.append(source[cursor:]);break
            out.append(source[cursor:m.start()]);depth=1;end=m.end()
            while depth:depth+=(source[end]=='[')-(source[end]==']');end+=1
            block=source[m.start():end]
            if not any(k in m[1] for k in ('terrain','ground','linktunnel')):
                block=re.sub(r'pos \[ ([^ ]+) ([^ ]+) [^ ]+ \]',r'pos [ \1 \2 0.12 ]',block,count=1)
            out.append(block);cursor=end
        path.write_text(''.join(out))
    # Acorn's original shop groups get closed courtyard backs as well.
    path=ROOT/'assets/acorn/dna/acorn_acreside.dna'
    s=path.read_text();pattern=re.compile(r'(?:prop|node) "([^"\n]+)" \[')
    cursor=0;out=[]
    while True:
        m=pattern.search(s,cursor)
        if not m:out.append(s[cursor:]);break
        out.append(s[cursor:m.start()]);depth=1;end=m.end()
        while depth:depth+=(s[end]=='[')-(s[end]==']');end+=1
        block=s[m.start():end]
        if 'shop_shell_' in block and 'screened-shop-yard' not in block:
            block=block[:-1]+'prop "screened-shop-yard" [ code [ "acorn_shop_fence" ] ]\n]'
        if not any(k in m[1] for k in ('terrain','ground','linktunnel')):
            block=re.sub(r'pos \[ ([^ ]+) ([^ ]+) [^ ]+ \]',r'pos [ \1 \2 0.12 ]',block,count=1)
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
    if '"acorn_shop_fence"' not in s:s+='\nhood_model "assets/expansion/models/acorn_shop_fence.bam" [ store_node [ "prop" "acorn_shop_fence" "" ] ]\n'
    path.write_text(s)
    A.app.destroy()

if __name__=='__main__':main()
