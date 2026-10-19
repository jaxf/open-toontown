"""Render the production takeover facade and Cog models in a staged street.

This exercises real game assets, not a connected client/server session.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from panda3d.core import loadPrcFileData, TextNode, DepthOffsetAttrib, DecalEffect
loadPrcFileData('', 'window-type offscreen\nload-display p3headlessgl\n'
    'win-size 1440 1080\naudio-library-name null\nmodel-path resources\n'
    'default-model-extension .bam')
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import DirectLabel
from toontown.building.BureaubotBuilding import decorate_building, add_elevator_badge
from toontown.suit import BureaubotModels as B
from tools.preview_bureaubots import capture


def main():
    app=ShowBase()
    app.setBackgroundColor(.57,.74,.83,1)
    app.disableMouse()
    app.camLens.setFov(47)
    app.camera.setPos(61,-104,51)
    app.camera.lookAt(15,-2,22)
    building=app.loader.loadModel('phase_4/models/modules/suit_landmark_corp')
    building.reparentTo(app.render)
    decorate_building(building)
    elevator=app.loader.loadModel('phase_4/models/modules/elevator')
    elevator.reparentTo(building.find('**/*_door_origin'))
    add_elevator_badge(elevator)
    for light in elevator.findAllMatches('**/floor_light_?;+s'):
        light.setColor(.92,.75,.24,1)
    sign=TextNode('occupied-shop-sign')
    sign.setText('Pending Approval, Inc.\nBureaubots')
    sign.setAlign(TextNode.ACenter)
    sign.setTextColor(1,1,1,1)
    sign.setWordwrap(17)
    sign.setFont(app.loader.loadFont('phase_3/models/fonts/vtRemingtonPortable.ttf'))
    # Match DistributedBuilding.setupSuitBuilding's real sign geometry/layout.
    height=sign.getHeight()
    zscale=(height+2)/3.0
    panel=app.loader.loadModel('phase_5/models/modules/suit_sign')
    panel.reparentTo(building.find('**/sign_origin'))
    panel.setPosHprScale(0,0,height*.8/zscale,0,0,0,8,8,8*zscale)
    text=panel.attachNewNode(sign.generate())
    text.setPosHprScale(0,0,-.21+height*.1/zscale,0,0,0,.1,.1,.1/zscale)
    text.setAttrib(DepthOffsetAttrib.make(1))
    front=building.find('**/*_front/+GeomNode;+s')
    panel.wrtReparentTo(front)
    front.node().setEffect(DecalEffect.make())
    B._box(app.render,'sidewalk',(15,-3,-.4),(72,24,.8),(.62,.61,.56,1))
    B._box(app.render,'street',(15,-26,-.65),(100,25,.8),(.25,.29,.31,1))
    for x in range(-30,70,12):
        B._box(app.render,'road-mark',(x,-31,-.23),(5,.35,.02),(.87,.81,.53,1))
    actors=[]
    for key,x,y in [('paper-shuffler',-2,-14),('red-tape',8,-11),
                    ('gatekeeper',28,-13),('head-honcho',41,-14)]:
        actor=B.make_actor(key,app.loader)
        actor.reparentTo(app.render)
        actor.setPos(x,y,0)
        actor.setH(165)
        actor.stop();actor.pose('neutral',0);actor.update(force=True)
        actors.append(actor)
    DirectLabel(parent=app.aspect2d,relief=None,text='BUREAUBOT BUILDING TAKEOVER',
        text_scale=.063,text_pos=(0,.89),text_fg=(.13,.19,.22,1))
    DirectLabel(parent=app.aspect2d,relief=None,text='Engine preview | Clipboard tower, raised clip roof, original Cog metal textures',
        text_scale=.028,text_pos=(0,.82),text_fg=(.17,.23,.25,1))
    out=Path('docs/previews/bureaubot-building.png')
    capture(app,out)
    for actor in actors:
        actor.cleanup();actor.removeNode()
    app.destroy()
    print(out)


if __name__=='__main__':
    main()
