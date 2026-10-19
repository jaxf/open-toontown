"""Capture the real Acorn gateway and HQ scenery from several camera positions.

This renders production scene builders with staged actors, not a live client.
"""
import sys
import argparse
import math
from types import SimpleNamespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from panda3d.core import loadPrcFileData, CompassEffect, CullBinManager,Point3
loadPrcFileData('', 'window-type offscreen\nload-display p3headlessgl\n'
    'win-size 1600 1000\naudio-library-name null\nmodel-path resources\n'
    'default-model-extension .bam\nframebuffer-multisample true\nmultisamples 4')
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import DirectLabel
from toontown.expansion import BureauHQGlobals as H
from toontown.expansion.ExpansionScene import build_scene
from toontown.suit.BureaubotModels import make_actor
from tools.preview_bureaubots import capture


SHOTS = {
    H.ENTRY: (
        ('tunnel', (60,35,13), (118,20,19)),
        ('approach', (55,40,22), (118,20,15)),
        ('village', (225,-280,225), (0,25,15))),
    H.MINISTRY: (
        ('arrival', (0,-145,10), (29,143,53)),
        ('side', (-220,-245,145), (0,30,30)),
        ('records-court', (-112,-45,12), (-113,67,35)),
        ('ticket-court', (-21,-118,17), (18,-76,8))),
    H.ARCHIVES: (
        ('arrival', (0,-125,10), (-68,118,52)),
        ('side', (-225,-235,165), (0,28,40)),
        ('aisle', (-65,10,10), (30,95,55)),
        ('catalog', (-143,-32,14), (-108,-3,9))),
    H.WORKS: (
        ('arrival', (0,-125,10), (101,110,43)),
        ('side', (-225,-245,150), (15,15,30)),
        ('conveyor', (-111,-38,14), (-25,25,24)),
        ('press-apron', (-25,-133,17), (-4,-102,9))),
}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zone',type=int,choices=sorted(SHOTS))
    parser.add_argument('--revision',default='')
    parser.add_argument('--interactions',action='store_true',help='Render actual local machine UI and motion with a staged walk-state avatar.')
    args=parser.parse_args()
    app = ShowBase(); app.disableMouse()
    app.camLens.setNearFar(1,5000); app.camLens.setFov(63)
    for name, order in [('ground',14),('shadow',15)]:
        CullBinManager.getGlobalPtr().addBin(name,CullBinManager.BTFixed,order)
    font = app.loader.loadFont('phase_3/models/fonts/CourierBold')
    for zone, shots in SHOTS.items():
        if args.zone is not None and args.zone != zone: continue
        is_entry = zone == H.ENTRY
        sky = app.loader.loadModel('phase_3.5/models/props/TT_sky' if is_entry
                                   else 'phase_9/models/cogHQ/cog_sky')
        sky.reparentTo(app.camera)
        sky.setEffect(CompassEffect.make(app.render,CompassEffect.PRot))
        sky.setScale(1); sky.setBin('background',0)
        sky.setDepthWrite(False); sky.setDepthTest(False)
        if is_entry: sky.setColorScale(1,.97,.87,1)
        scene = build_scene(zone); scene.reparentTo(app.render)
        title = DirectLabel(parent=app.aspect2d,relief=None,
            text='ACORN ACRESIDE - BUREAUBOT HQ ENTRANCE' if is_entry else H.NAMES[zone].upper(),
            text_font=font,text_scale=.049,text_pos=(0,.91),
            text_fg=(1,.95,.81,1),text_shadow=(0,0,0,1))
        note = DirectLabel(parent=app.aspect2d,relief=None,
            text='Actual game scene render | '+('Entrance approach' if is_entry else 'Staged Cogs; facilities are placeholders'),
            text_scale=.026,text_pos=(0,.85),text_fg=(1,1,1,1),text_shadow=(0,0,0,1))
        actors=[]
        if not is_entry:
            route=H.PATROLS[zone];edges=list(zip(route,route[1:]+route[:1]))
            lengths=[math.dist(a,b) for a,b in edges];total=sum(lengths)
            count=sum(H.planner_rows()[sorted(H.ZONES).index(zone)][1:3])//2
            for i in range(count):
                distance=(i+.35)*total/count
                for (a,b),length in zip(edges,lengths):
                    if distance<=length:break
                    distance-=length
                t=distance/length;x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
                actor=make_actor(('red-tape','gatekeeper','head-honcho','bottleneck')[i%4],app.loader)
                actor.reparentTo(scene);actor.setPos(x,y,0)
                actor.setH(math.degrees(math.atan2(a[0]-b[0],b[1]-a[1])))
                actor.pose('walk',8+i%6);actor.update(force=True);actors.append(actor)
        for name, camera, target in shots:
            app.camera.setPos(*camera);app.camera.lookAt(*target)
            suffix='-'+args.revision if args.revision else ''
            capture(app,Path('docs/previews/bureau-tour-%s-%s%s.png' % (zone,name,suffix)))
        if args.interactions and not is_entry:
            from toontown.expansion.BureauHQInteractions import BureauHQInteractions
            app.localAvatar=scene.attachNewNode('preview-interactor')
            place=SimpleNamespace(fsm=SimpleNamespace(getCurrentState=lambda:SimpleNamespace(getName=lambda:'walk')))
            controller=BureauHQInteractions(app,place,scene)
            note['text']='Actual local machine/UI render | Staged interaction; not a multiplayer session'
            for machine in controller.machines:
                kind=machine.getTag('bureau-action')
                app.localAvatar.setPos(scene,machine.find('use-point').getPos(scene))
                controller.readyAt=0;controller.update(SimpleNamespace(cont=None))
                app.camera.setPos(scene,scene.getRelativePoint(machine,Point3(-16,-28,17)))
                app.camera.lookAt(scene.getRelativePoint(machine,Point3(0,0,7)))
                if kind=='registry':
                    app.camera.setPos(-108,70,13);app.camera.lookAt(-68,118,60)
                capture(app,Path('docs/previews/bureau-tour-%s-%s-ready%s.png'%(zone,kind,suffix)))
                if not controller.use():raise RuntimeError('Preview machine is not usable')
                controller.running.setT(.8)
                capture(app,Path('docs/previews/bureau-tour-%s-%s-active%s.png'%(zone,kind,suffix)))
                controller.reset_action();controller.message.hide()
            controller.destroy();app.localAvatar.removeNode();del app.localAvatar
        for actor in actors:actor.cleanup();actor.removeNode()
        title.destroy();note.destroy();scene.removeNode();sky.removeNode()
    app.destroy()


if __name__ == '__main__':main()
