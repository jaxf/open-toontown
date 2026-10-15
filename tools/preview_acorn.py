"""Render the committed DNA and models, without bootstrapping an AI server.

python tools/preview_acorn.py
python tools/preview_acorn.py --display p3tinydisplay  # fallback without EGL
"""
import argparse
from pathlib import Path
import os
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--display',default='p3headlessgl')
    args=parser.parse_args()
    os.chdir(ROOT)
    from panda3d.core import loadPrcFileData, CullBinManager, CompassEffect, PNMImage, StringStream
    loadPrcFileData('', 'window-type offscreen\nload-display %s\nwin-size 1600 1000\n'
                        'audio-library-name null\nmodel-path resources\n'
                        'default-model-extension .bam\nframebuffer-multisample true\n'
                        'multisamples 4' % args.display)
    from direct.showbase.ShowBase import ShowBase
    from toontown.expansion.ExpansionScene import build_scene
    app=ShowBase()
    for name,order in [('ground',14),('shadow',15)]:
        CullBinManager.getGlobalPtr().addBin(name,CullBinManager.BTFixed,order)
    app.disableMouse()
    app.camLens.setNearFar(1,1800)
    app.camLens.setFov(58)
    app.setBackgroundColor(.64,.82,.86,1)
    sky=app.loader.loadModel('phase_3.5/models/props/TT_sky')
    sky.reparentTo(app.camera)
    sky.setEffect(CompassEffect.make(app.render,CompassEffect.PRot))
    sky.setColorScale(1,.97,.87,1)
    shots=[
        (19000,'acorn',(195,-275,215),(0,12,5)),
        (19000,'acorn-walk',(0,-102,9),(0,38,24)),
        (19100,'root-route',(370,-690,520),(0,0,0)),
        (19100,'root-route-walk',(0,-503,9),(41,-423,14)),
    ]
    destination=ROOT/'docs/previews'
    destination.mkdir(exist_ok=True)
    for zone,name,camera,target in shots:
        scene=build_scene(zone)
        scene.reparentTo(app.render)
        app.camera.setPos(*camera)
        app.camera.lookAt(*target)
        for _ in range(4):
            app.graphicsEngine.renderFrame()
        capture=PNMImage()
        assert app.win.getScreenshot(capture)
        encoded=StringStream()
        assert capture.write(encoded,'preview.png')
        (destination/(name+'.png')).write_bytes(encoded.getData())
        scene.removeNode()
    app.destroy()


if __name__=='__main__':
    main()
