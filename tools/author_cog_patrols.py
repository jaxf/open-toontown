"""Native bidirectional patrol graph, intersections and building door spurs."""
from pathlib import Path
from math import hypot, sin, cos, radians
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from toontown.expansion.WorldLayout import ROADS,road_paths,along
from toontown.expansion.CogPatrols import dna_path


def main():
    for zone in ROADS:
        points=[];edges=set();junctions=[]
        def link(a,b):
            if a!=b:edges.update(((a,b),(b,a)))
        for route_index,path in enumerate(road_paths(zone)):
            samples=list(along(path,12,80 if route_index==0 else 0))
            lanes=[[(x-ty*side*4,y+tx*side*4) for x,y,tx,ty in samples] for side in (-1,1)]
            loop=lanes[0]+list(reversed(lanes[1]));start=len(points)
            points.extend(loop)
            for i in range(len(loop)):link(start+i,start+(i+1)%len(loop))
            if route_index==0:main_count=len(points)
            else:
                for local_index in (0,len(lanes[0])-1,len(lanes[0]),len(loop)-1):
                    index=start+local_index;x,y=points[index]
                    nearest=min(range(main_count),key=lambda j:hypot(points[j][0]-x,points[j][1]-y))
                    link(index,nearest)
        parts=[f'store_suit_point [ {i}, STREET_POINT, {x:.4f} {y:.4f} .12 ]\n' for i,(x,y) in enumerate(points)]
        buildings=json.loads((ROOT/f'assets/expansion/patrols/buildings_{zone}.json').read_text())
        index=len(points)
        for row in buildings:
            a=radians(row['h']);x,y=row['x'],row['y'];block=row['block']
            front=(x+sin(a)*5,y-cos(a)*5)
            side=(front[0]+cos(a)*7,front[1]+sin(a)*7)
            for kind,pos in [('FRONT_DOOR_POINT',front),('SIDE_DOOR_POINT',side)]:
                parts.append(f'store_suit_point [ {index}, {kind}, {pos[0]:.4f} {pos[1]:.4f} .12, {block} ]\n')
                nearest=min(range(len(points)),key=lambda j:hypot(points[j][0]-pos[0],points[j][1]-pos[1]))
                link(index,nearest);index+=1
        parts.append(f'group "patrols" [ visgroup "{zone}" [ vis [ "{zone}" ]\n')
        for a,b in sorted(edges):parts.append(f'suit_edge [ {a} {b} ]\n')
        x,y=min(points,key=lambda p:abs(p[1]))
        parts.append(f'battle_cell [ 20 20 {x:.4f} {y:.4f} .12 ]\n] ]\n')
        path=ROOT/dna_path(zone);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(''.join(parts))

if __name__=='__main__':main()
