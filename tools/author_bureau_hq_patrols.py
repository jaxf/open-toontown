"""Generate native patrol graphs from the shared collision-safe campus routes."""
import sys,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from toontown.expansion import BureauHQGlobals as H


def generate(zone):
    points=[];edges=set();loops=[]
    for route in H.patrol_paths(zone):
        start=len(points)
        for a,b in zip(route,route[1:]+route[:1]):
            count=max(1,math.ceil(math.dist(a,b)/12))
            points.extend((a[0]+(b[0]-a[0])*i/count,a[1]+(b[1]-a[1])*i/count) for i in range(count))
        indices=list(range(start,len(points)));loops.append(indices)
        for a,b in zip(indices,indices[1:]+indices[:1]):edges.add((a,b))
    if len(loops)>1:
        a=max(loops[0],key=lambda i:(points[i][1],points[i][0]))
        b=max(loops[1],key=lambda i:(points[i][1],-points[i][0]))
        # Broad rear promenade links the two plaza patrol circuits.
        previous=a
        count=math.ceil(math.dist(points[a],points[b])/12)
        for i in range(1,count):
            index=len(points)
            points.append(tuple(points[a][j]+(points[b][j]-points[a][j])*i/count for j in (0,1)))
            edges.add((previous,index));edges.add((index,previous));previous=index
        edges.add((previous,b));edges.add((b,previous))
    text=''.join('store_suit_point [ %s, STREET_POINT, %.4f %.4f .12 ]\n'%(i,x,y) for i,(x,y) in enumerate(points))
    text+='group "bureau-patrols" [ visgroup "%s" [ vis [ "%s" ]\n'%(zone,zone)
    text+=''.join('suit_edge [ %s %s ]\n'%edge for edge in sorted(edges))
    text+=''.join('battle_cell [ 20 20 %s %s .12 ]\n'%(x,y) for x,y in H.BATTLE_PADS[zone])
    return text+'] ]\n'


if __name__=='__main__':
    for zone in sorted(H.ZONES):
        path=ROOT/H.dna_path(zone);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(generate(zone))
