"""Small original collectible meshes using the expansion's painted palette."""
from tools import build_acorn_models as A
from tools.build_world_models import bulb, ring
from panda3d.core import NodePath
from math import sin,cos,pi
from pathlib import Path


def build(zone):
    root=NodePath('laff-'+str(zone))
    gold=(1,.78,.23,1);cream=(1,.95,.73,1)
    if zone==19000:
        A.tube(root,'acorn',[(0,0,.1,.1),(0,0,.6,1),(0,0,1.7,1.3),(0,0,2.1,1.1)],None,(.78,.43,.16,1),12)
        A.tube(root,'cap',[(0,0,1.9,1.5),(0,0,2.5,1.1),(0,0,2.7,.15)],A.WOOD,(.38,.24,.11,1),12)
        A.tube(root,'stem',[(0,0,2.5,.22),(.3,0,3.1,.15)],None,(.38,.24,.11,1),6)
    elif zone==61000:
        bulb(root,'saltwater-taffy',(0,0,1.3),1.25,(1,.48,.62,1))
        for side in (-1,1):
            wrap=root.attachNewNode('twisted-wrapper');wrap.setPos(side*1.15,0,1.3);wrap.setP(side*90);wrap.setH(90)
            A.tube(wrap,'wrapper',[(0,0,0,.25),(0,0,1,1)],None,cream,6)
        for x in (-.6,0,.6):A.board(root,'candy-stripe',(x,-1.05,1.3),(.22,.12,1.2),cream,None)
    elif zone==62000:
        # Extruded crescent silhouette, not an overlapping pair of full spheres.
        mesh=A.Mesh('crescent');outer=[];inner=[]
        for i in range(21):
            a=pi*.30+i*pi*1.40/20
            outer.append((1.45*cos(a),1.65+1.45*sin(a)))
            inner.append((.72+1.25*cos(a),1.65+1.25*sin(a)))
        for i in range(20):
            for y in (-.28,.28):
                mesh.face([(outer[i][0],y,outer[i][1]),(outer[i+1][0],y,outer[i+1][1]),
                    (inner[i+1][0],y,inner[i+1][1]),(inner[i][0],y,inner[i][1])],color=gold)
            for line in (outer,inner):
                mesh.face([(line[i][0],-.28,line[i][1]),(line[i][0],.28,line[i][1]),
                    (line[i+1][0],.28,line[i+1][1]),(line[i+1][0],-.28,line[i+1][1])],color=gold)
        mesh.attach(root).setTwoSided(True)
    elif zone==63000:
        mesh=A.Mesh('movie-star');points=[]
        for i in range(10):
            a=pi/2+i*pi/5;r=1.65 if i%2==0 else .8
            points.append((r*cos(a),1.8+r*sin(a)))
        for i in range(10):
            a,b=points[i],points[(i+1)%10]
            for y in (-.3,.3):mesh.face([(0,y,1.8),(a[0],y,a[1]),(b[0],y,b[1])],color=gold)
            mesh.face([(a[0],-.3,a[1]),(b[0],-.3,b[1]),(b[0],.3,b[1]),(a[0],.3,a[1])],color=cream)
        mesh.attach(root).setTwoSided(True)
    else:
        A.tube(root,'canteen',[(0,0,.1,.6),(0,0,.5,1.2),(0,0,2.2,1.2),(0,0,2.6,.65)],None,(.26,.65,.62,1),12)
        A.tube(root,'cork',[(0,0,2.6,.48),(0,0,3,.48)],A.WOOD,(.68,.40,.17,1),8)
        A.board(root,'canteen-band',(0,-1.18,1.4),(1.6,.12,.55),cream,None)
    root.setLightOff();root.flattenStrong();return root


def main():
    A.app=A.ShowBase();A.OUT=Path('assets/expansion/models')
    for zone in (19000,61000,62000,63000,64000):A.save(build(zone),'laff_'+str(zone))
    A.app.destroy()

if __name__=='__main__':main()
