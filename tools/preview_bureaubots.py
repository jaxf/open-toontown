"""Render the actual animated models; optionally export head/body BAM assets.

Run from the repo root with the resources checkout and standard Panda3D:
  python tools/preview_bureaubots.py
  python tools/preview_bureaubots.py --export local/bureaubots
The full game itself still needs the project's OTP-enabled Panda3D fork.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from panda3d.core import loadPrcFileData, PNMImage, StringStream
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import DirectLabel
from toontown.suit import BureaubotModels as B


def capture(app,path):
    for _ in range(3):
        app.graphicsEngine.renderFrame()
    shot = PNMImage()
    app.win.getScreenshot(shot)
    stream = StringStream()
    shot.write(stream,'preview.png')
    Path(path).write_bytes(stream.getData())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export',type=Path)
    parser.add_argument('--output',type=Path,default=Path('docs/previews/bureaubots-models.png'))
    args = parser.parse_args()
    loadPrcFileData('', 'window-type offscreen\nload-display p3headlessgl\n'
        'win-size 1600 1100\naudio-library-name null\nmodel-path resources\n'
        'default-model-extension .bam\ntextures-power-2 none\n'
        'bam-texture-mode rawdata')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    app = ShowBase()
    app.setBackgroundColor(.93,.90,.82,1)
    font = app.loader.loadFont('phase_3/models/fonts/vtRemingtonPortable.ttf')
    DirectLabel(parent=app.aspect2d,relief=None,text='BUREAUBOTS',
                text_font=font,text_scale=.09,text_pos=(0,.86),text_fg=(.26,.17,.12,1))
    DirectLabel(parent=app.aspect2d,relief=None,text='In-engine models | Original Cog bodies and animations',
                text_scale=.033,text_pos=(0,.78),text_fg=(.36,.28,.20,1))
    actors=[]
    for i,(key,name,body,scale) in enumerate(B.CATALOG):
        stage = app.aspect2d.attachNewNode(key+'-stage')
        stage.setDepthTest(True)
        stage.setDepthWrite(True)
        stage.setLightOff()
        stage.setPos(-1.04+(i%4)*.69,0,.00-(i//4)*.81)
        actor = B.make_actor(key,app.loader)
        actor.reparentTo(stage)
        actor.setH(168)
        actor.stop()
        actor.pose('neutral',0)
        actor.update()
        low,high=actor.getTightBounds(stage)
        factor=min(.65/(high.z-low.z),.54/(high.x-low.x))
        actor.setScale(actor.getScale()*factor)
        actor.setZ(-low.z*factor)
        DirectLabel(parent=app.aspect2d,relief=None,text=name,text_font=font,
            text_scale=.038,text_pos=(-1.04+(i%4)*.69,-.065-(i//4)*.81),
            text_fg=(.25,.16,.10,1))
        if args.export:
            args.export.mkdir(parents=True,exist_ok=True)
            B.build_head(key).writeBamFile(str(args.export/(key+'-head.bam')))
            # Export at native game scale, without the sheet's display transform.
            actor.setH(0)
            actor.setPos(0,0,0)
            actor.setScale(scale)
            actor.writeBamFile(str(args.export/(key+'-model.bam')))
            actor.setH(168)
            actor.setScale(scale*factor)
            actor.setZ(-low.z*factor)
        actors.append(actor)
    if args.export:
        B.build_logo().writeBamFile(str(args.export/'bureaubot-emblem.bam'))
    capture(app,args.output)
    for actor in actors:
        actor.cleanup()
        actor.removeNode()
    app.destroy()


if __name__ == '__main__':
    main()
