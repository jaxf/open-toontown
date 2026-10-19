"""Render real campus meshes, not image-generated mockups or a live server."""
import sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from panda3d.core import loadPrcFileData,CompassEffect
loadPrcFileData('', 'window-type offscreen\nload-display p3headlessgl\n'
    'win-size 1600 1000\naudio-library-name null\nmodel-path resources\n'
    'default-model-extension .bam\nframebuffer-multisample true\nmultisamples 4')
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import DirectLabel
from toontown.expansion import BureauHQGlobals as H
from toontown.expansion.BureauHQScene import build_scene
from toontown.suit.BureaubotModels import make_actor
from tools.preview_bureaubots import capture


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--zone',type=int,choices=sorted(H.ZONES))
    parser.add_argument('--revision',default='r10')
    args=parser.parse_args()
    app=ShowBase();app.disableMouse();app.setBackgroundColor(.23,.25,.29,1)
    app.camLens.setNearFar(1,5000);app.camLens.setFov(63)
    sky=app.loader.loadModel('phase_9/models/cogHQ/cog_sky');sky.reparentTo(app.camera)
    sky.setEffect(CompassEffect.make(app.render,CompassEffect.PRot));sky.setScale(1)
    sky.setBin('background',0);sky.setDepthWrite(False);sky.setDepthTest(False)
    font=app.loader.loadFont('phase_3/models/fonts/CourierBold')
    for zone in ([args.zone] if args.zone else sorted(H.ZONES)):
        scene=build_scene(zone);scene.reparentTo(app.render)
        title=DirectLabel(parent=app.aspect2d,relief=None,text=H.NAMES[zone].upper(),
            text_scale=.055,text_font=font,text_pos=(0,.90),text_fg=(1,.91,.70,1),text_shadow=(0,0,0,1))
        note=DirectLabel(parent=app.aspect2d,relief=None,text=args.revision.upper()+' | Actual scene render, staged Cogs | Boss and training facilities are placeholders',
            text_scale=.026,text_pos=(0,.84),text_fg=(.85,.88,.90,1),text_shadow=(0,0,0,1))
        actors=[]
        for i,(x,y) in enumerate(H.BATTLE_PADS[zone]):
            actor=make_actor(('red-tape','gatekeeper','head-honcho','bottleneck')[i],app.loader)
            actor.reparentTo(scene);actor.setPos(x,y,0);actor.setH(150+i*40)
            actor.pose('walk',8);actor.update(force=True);actors.append(actor)
        arrivals={H.MINISTRY:((-43,-139,10),(-27,40,48)),
                  H.ARCHIVES:((-65,-112,10),(-60,110,50)),
                  H.WORKS:((-55,-121,10),(-26,75,40))}
        details={H.MINISTRY:((-112,-45,12),(-113,67,35)),
                 H.ARCHIVES:((-65,10,10),(30,95,55)),
                 H.WORKS:((-111,-38,14),(-25,25,24))}
        views=[('overview',(240,-360,265),(0,20,28)),
                                ('arrival',*arrivals[zone]),
                                ('detail',*details[zone])]
        if zone==H.MINISTRY:views.append(('tunnel',(30,-127,13),(0,-190,18)))
        for kind,pos,target in views:
            app.camera.setPos(*pos);app.camera.lookAt(*target)
            capture(app,Path('docs/previews/bureau-%s-%s-%s.png'%(zone,args.revision,kind)))
        for actor in actors:actor.cleanup();actor.removeNode()
        title.destroy();note.destroy();scene.removeNode()
    app.destroy()


if __name__=='__main__':main()
