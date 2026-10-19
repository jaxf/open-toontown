"""Street-map geometry derived from the same routes and DNA as the live world."""
import math
import re
from pathlib import Path
from panda3d.core import (NodePath, Point3, TextNode, Geom, GeomNode,
    GeomVertexData, GeomVertexFormat, GeomVertexWriter, GeomTriangles)
from toontown.expansion import ExpansionGlobals as E
from toontown.expansion.WorldLayout import road_paths, street_bounds, ROAD_PROFILES, POCKETS
from toontown.expansion.Services import placements, street_court


def bounds(zone):
    x0,y0,x1,y1=street_bounds(zone,110)
    span=max(x1-x0,y1-y0)
    cx,cy=(x0+x1)/2,(y0+y1)/2
    return (Point3(cx+span/2,cy+span/2,0),Point3(cx-span/2,cy-span/2,0))


def build_map(zone):
    root=NodePath('street-map-%s'%zone)
    top,bottom=bounds(zone)
    span=top.x-bottom.x
    data=GeomVertexData('painted-street-map',GeomVertexFormat.getV3c4(),Geom.UHStatic)
    vertex=GeomVertexWriter(data,'vertex');color=GeomVertexWriter(data,'color')
    triangles=GeomTriangles(Geom.UHStatic)
    count=0
    def polygon(points,tint):
        nonlocal count
        for x,y in points:
            vertex.addData3((x-bottom.x)/span-.5,0,(y-bottom.y)/span-.5)
            color.addData4(*tint)
        for i in range(1,len(points)-1):triangles.addVertices(count,count+i,count+i+1)
        count+=len(points)
    def disk(x,y,r,tint):
        polygon([(x+math.cos(i*math.tau/16)*r,y+math.sin(i*math.tau/16)*r) for i in range(16)],tint)
    def road(points,width,tint):
        for (x,y),(xx,yy) in zip(points,points[1:]):
            length=math.hypot(xx-x,yy-y);nx,ny=-(yy-y)/length*width,(xx-x)/length*width
            polygon([(x+nx,y+ny),(x-nx,y-ny),(xx-nx,yy-ny),(xx+nx,yy+ny)],tint)
        for x,y in points:disk(x,y,width,tint)
    paths=road_paths(zone)
    center,entrance=street_court(zone)
    paths.append([entrance,center])
    sidewalk=ROAD_PROFILES[zone]['sidewalk']
    for width,tint in ((sidewalk+9,(.28,.46,.19,1)),(sidewalk+5,(.93,.77,.28,1)),
                       (sidewalk,(1,.91,.51,1)),(ROAD_PROFILES[zone]['road'],(.78,.69,.49,1))):
        for points in paths:road(points,width,tint)
    for x,y,r in list(POCKETS[zone])+[(center[0],center[1],35)]:
        disk(x,y,r+4,(.95,.79,.34,1));disk(x,y,r,(.88,.80,.56,1))
    name=E.zone_name(zone).lower().replace(' ','_')
    dna=(Path(__file__).resolve().parents[2]/'assets/expansion/dna'/(name+'.dna')).read_text()
    buildings=re.findall(r'landmark_building[^\n]*?pos \[ ([^\]]+) \] nhpr \[ ([^\]]+) \]',dna)
    palette=((.88,.40,.24,1),(.32,.64,.58,1),(.72,.45,.68,1),(.95,.72,.27,1))
    for index,(pos,hpr) in enumerate(buildings):
        x,y,_=map(float,pos.split());h=math.radians(float(hpr.split()[0]))
        def box(w,d,tint):
            polygon([(x+dx*math.cos(h)-dy*math.sin(h),y+dx*math.sin(h)+dy*math.cos(h))
                     for dx,dy in ((-w,-d),(w,-d),(w,d),(-w,d))],tint)
        box(14,15,(.32,.34,.24,1));box(12,13,palette[index%4])
    geom=Geom(data);geom.addPrimitive(triangles)
    node=GeomNode('roads-and-roofs');node.addGeom(geom)
    painted=root.attachNewNode(node);painted.setDepthTest(False);painted.setDepthWrite(False)
    def label(name,text,x,y,scale,tint):
        tn=TextNode(name);tn.setText(text);tn.setAlign(TextNode.ACenter)
        tn.setTextColor(*tint);tn.setShadow(.035,.035);tn.setShadowColor(1,1,.8,1)
        np=root.attachNewNode(tn);np.setPos((x-bottom.x)/span-.5,-.01,(y-bottom.y)/span-.5)
        np.setScale(scale)
    hx,hy,_,_=placements(zone)['hq']
    label('hq','HQ',hx,hy,.024,(.08,.22,.47,1))
    for (x,y),destination in zip((paths[0][0],paths[0][-1]),E.connections(zone)):
        label('tunnel-label',E.zone_name(destination),x,y,.022,(.1,.17,.20,1))
    label('street-title',E.zone_name(zone),(top.x+bottom.x)/2,top.y-25,.034,(.12,.22,.18,1))
    return root
