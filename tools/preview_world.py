"""Actual committed DNA/model screenshots; no server login or test suite."""
import argparse,sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--zones',nargs='*',type=int)
    args=parser.parse_args();os.chdir(ROOT)
    from panda3d.core import loadPrcFileData,CullBinManager,CompassEffect,PNMImage,StringStream
    loadPrcFileData('', 'window-type offscreen\nload-display p3headlessgl\nwin-size 1440 900\n'
        'audio-library-name null\nmodel-path resources\ndefault-model-extension .bam\n'
        'framebuffer-multisample true\nmultisamples 4')
    from direct.showbase.ShowBase import ShowBase
    from toontown.expansion.ExpansionScene import build_scene
    from toontown.expansion import ExpansionGlobals as E
    from toontown.expansion.WorldLayout import ROADS
    app=ShowBase();app.disableMouse()
    for name,order in [('ground',14),('shadow',15)]:CullBinManager.getGlobalPtr().addBin(name,CullBinManager.BTFixed,order)
    app.camLens.setNearFar(1,2200);app.camLens.setFov(65)
    sky=app.loader.loadModel('phase_3.5/models/props/TT_sky');sky.reparentTo(app.camera)
    sky.setEffect(CompassEffect.make(app.render,CompassEffect.PRot))
    for zone in args.zones or sorted(set(ROADS)|{61000,62000,63000,64000}):
        scene=build_scene(zone);scene.reparentTo(app.render)
        sky.setColorScale(*E.NEIGHBORHOODS[E.hood_id(zone)]['sky'])
        name=E.zone_name(zone).lower().replace(' ','-')
        if zone in ROADS:
            y=ROADS[zone][0][1]
            views=[('walk',(0,y+55,8),(ROADS[zone][2][0],y+135,11)),
                   ('overview',(310,-440,480),(0,0,0))]
        else:views=[('walk',(0,-105,9),(0,38,21)),('overview',(215,-300,225),(0,15,9))]
        if zone in (61100,64100):
            from toontown.expansion.Services import street_court
            (x,y),_=street_court(zone)
            views.append(('services',(x-83,y-108,65),(x,y+10,18)))
        for kind,pos,target in views:
            app.camera.setPos(*pos);app.camera.lookAt(*target)
            for _ in range(4):app.graphicsEngine.renderFrame()
            capture=PNMImage();app.win.getScreenshot(capture);stream=StringStream();capture.write(stream,'preview.png')
            (ROOT/'docs/previews'/f'{name}-{kind}.png').write_bytes(stream.getData())
            print(name,kind,flush=True)
        scene.removeNode()
    app.destroy()

if __name__=='__main__':main()
