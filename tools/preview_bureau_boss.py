"""Render the production boss and chamber; this is not a multiplayer capture."""
import sys
import ast
from types import SimpleNamespace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from panda3d.core import loadPrcFileData, Point3
loadPrcFileData('','window-type offscreen\nload-display p3headlessgl\nwin-size 1600 1000\n'
    'audio-library-name null\nmodel-path resources\ndefault-model-extension .bam\n'
    'framebuffer-multisample true\nmultisamples 4')
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import DirectLabel, DirectButton, DirectWaitBar
from toontown.expansion.BureauBossScene import build_room
from toontown.expansion import BureauBossGlobals as G
from toontown.suit.BureauBossModel import make_preview
from tools.preview_bureaubots import capture

app=ShowBase();app.disableMouse();app.setBackgroundColor(.055,.065,.075)
app.camLens.setNearFar(.5,2000);app.camLens.setFov(64)
room=build_room();room.reparentTo(app.render)
boss=make_preview(app.loader);boss.reparentTo(room);boss.setPosHpr(*G.BOSS_POS)
title=DirectLabel(relief=None,text=G.ROOM.upper(),text_scale=.05,text_pos=(0,.92),
    text_fg=(.96,.89,.74,1),text_shadow=(0,0,0,1))
note=DirectLabel(relief=None,text='Production geometry preview | Not a live multiplayer session',
    text_scale=.027,text_pos=(0,.86),text_fg=(1,1,1,1),text_shadow=(0,0,0,1))
for name,pos,target in [('arrival',(-47,-50,12),(7,52,29)),
                        ('gallery',(63,-65,37),(-9,34,30)),
                        ('reverse',(34,72,38),(-18,-38,21)),
                        ('director',(45,24,24),(12,65,22))]:
    app.camera.setPos(*pos);app.camera.lookAt(*target)
    capture(app,Path('docs/previews/bureau-boss-'+name+'.png'))
# Execute the production HUD constructor without importing unavailable native
# OTP classes. This is a staged UI capture, not a simulated multiplayer claim.
tree=ast.parse(Path('toontown/suit/DistributedBureauBoss.py').read_text())
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
constructor=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='createHud')
namespace={'base':app,'G':G,'DirectLabel':DirectLabel,'DirectButton':DirectButton,'DirectWaitBar':DirectWaitBar}
exec(compile(ast.Module(body=[constructor],type_ignores=[]),'<production HUD>','exec'),namespace)
ui=SimpleNamespace(useStation=lambda:None)
namespace['createHud'](ui)
title.hide();note['text']='Production scene and HUD | Staged final-phase preview';note.setZ(.09)
ui.banner['text']='Left sorter: 2/3   Right sorter: 1/3  |  Carrying a form'
ui.progress.show();ui.progress['value']=75
ui.button['text']='Feed left sorter';ui.button.show()
app.camera.setPos(-37,5,11);app.camera.lookAt(12,65,23)
capture(app,Path('docs/previews/bureau-boss-paperwork.png'))
for item in ui.hud:item.destroy()
ui.buttonArt.removeNode();title.show();note.setZ(0)
note['text']='Production geometry preview | Not a live multiplayer session'
boss.wrtReparentTo(app.render);room.hide();boss.setPosHpr(0,0,0,0,0,0)
title['text']=G.NAME.upper()
for name,pos in [('model',(36,-57,27)),('model-side',(-45,-31,24))]:
    app.camera.setPos(*pos);app.camera.lookAt(0,0,14)
    capture(app,Path('docs/previews/bureau-boss-'+name+'.png'))
boss.cleanup();boss.removeNode();room.removeNode()
from toontown.expansion.BureauHQScene import build_scene
from toontown.expansion.BureauBossScene import build_entrance_elevator
plaza=build_scene(14000);plaza.reparentTo(app.render)
locator=plaza.find('**/bureau-boss-elevator-locator')
elevator=build_entrance_elevator(locator)
title['text']='MINISTRY PLAZA - FINAL REVIEW ELEVATOR'
app.camera.setPos(plaza.getRelativePoint(locator,Point3(-32,-57,17)))
app.camera.lookAt(plaza.getRelativePoint(locator,Point3(0,-5,22)))
capture(app,Path('docs/previews/bureau-boss-elevator.png'))
app.destroy()
