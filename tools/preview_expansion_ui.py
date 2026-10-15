"""Render actual UI with a mock avatar; does not simulate a multiplayer login."""
import sys
from pathlib import Path
from types import SimpleNamespace, ModuleType
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from panda3d.core import loadPrcFileData, PNMImage, StringStream
loadPrcFileData('', 'window-type offscreen\nload-display p3headlessgl\nwin-size 1280 960\naudio-library-name null\nmodel-path resources\ndefault-model-extension .bam')
from direct.showbase.ShowBase import ShowBase
from toontown.expansion import ExpansionGlobals as E
app=ShowBase()
app.setBackgroundColor(.12,.17,.22,1)
app.cr=SimpleNamespace(playGame=SimpleNamespace(getPlaceId=lambda:E.ACORN,
    getPlace=lambda:SimpleNamespace(fsm=SimpleNamespace(getCurrentState=lambda:SimpleNamespace(getName=lambda:'walk')))))
app.localAvatar=SimpleNamespace(getTeleportAccess=lambda:list(E.destinations()),
    getAccessLevel=lambda:400,getTransitioning=lambda:False,hasActiveBoardingGroup=lambda:False)
module=ModuleType('toontown.toonbase.ToonBaseGlobal')
module.base=app
sys.modules[module.__name__]=module
from toontown.expansion.ExpansionMap import ExpansionMap
from toontown.expansion.AdminPanel import AdminPanel
def capture(path):
    shot=PNMImage();app.win.getScreenshot(shot)
    stream=StringStream();shot.write(stream,'preview.png')
    Path(path).write_bytes(stream.getData())

worldmap=ExpansionMap(app.aspect2d,lambda zone:None,lambda:None)
worldmap.refresh()
for _ in range(3):app.graphicsEngine.renderFrame()
capture('docs/previews/expansion-map.png')
worldmap.destroy()
admin=AdminPanel()
admin.toggle()
for _ in range(3):app.graphicsEngine.renderFrame()
capture('docs/previews/admin-panel.png')
admin.destroy()
app.destroy()
