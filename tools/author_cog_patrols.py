"""Build connected two-way Cog lanes following the actual winding road centers."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from toontown.expansion.WorldLayout import ROADS,curve,along
from toontown.expansion.CogPatrols import dna_path


def main():
    for zone,control in ROADS.items():
        samples=list(along(curve(control),12,80))
        lanes=[[(x-ty*side*4,y+tx*side*4) for x,y,tx,ty in samples] for side in (-1,1)]
        # A continuous loop travels up one side and back down the other.
        points=lanes[0]+list(reversed(lanes[1]))
        parts=[f'store_suit_point [ {i}, STREET_POINT, {x:.4f} {y:.4f} 0.12 ]\n' for i,(x,y) in enumerate(points)]
        parts.append(f'group "patrols" [ visgroup "{zone}" [ vis [ "{zone}" ]\n')
        for i in range(len(points)):
            j=(i+1)%len(points)
            parts.append(f'suit_edge [ {i} {j} ]\nsuit_edge [ {j} {i} ]\n')
        x,y,_,_=min(samples,key=lambda p:abs(p[1]))
        parts.append(f'battle_cell [ 20 20 {x:.4f} {y:.4f} 0.12 ]\n] ]\n')
        path=ROOT/dna_path(zone);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(''.join(parts))

if __name__=='__main__':main()
