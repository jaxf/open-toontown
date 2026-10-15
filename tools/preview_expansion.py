"""Render the actual expansion scenes using standard Panda3D (no OTP needed).

Run from the repository root: python tools/preview_expansion.py
The full game still requires the project's Panda3D fork with OTP/Toontown.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from panda3d.core import loadPrcFileData, CullBinManager
loadPrcFileData('', 'window-type offscreen\nload-display p3tinydisplay\nwin-size 1280 960\naudio-library-name null\nmodel-path resources\ndefault-model-extension .bam')
from direct.showbase.ShowBase import ShowBase
from toontown.expansion import ExpansionGlobals as E
from toontown.expansion.ExpansionScene import build_scene

app=ShowBase()
CullBinManager.getGlobalPtr().addBin('ground', CullBinManager.BTFixed, 14)
CullBinManager.getGlobalPtr().addBin('shadow', CullBinManager.BTFixed, 15)
app.disableMouse()
app.camLens.setFov(52)
app.camLens.setNearFar(1,1000)
out=Path('docs/previews')
out.mkdir(parents=True,exist_ok=True)
for zone in E.NEIGHBORHOODS:
    scene=build_scene(zone)
    scene.reparentTo(app.render)
    app.setBackgroundColor(*E.NEIGHBORHOODS[zone]['sky'])
    app.camera.setPos(*((195,-275,215) if zone==E.ACORN else (125,-190,155)))
    app.camera.lookAt(0,5,0)
    for _ in range(3):
        app.graphicsEngine.renderFrame()
    app.win.saveScreenshot(str(out/(E.NEIGHBORHOODS[zone]['short']+'.png')))
    scene.removeNode()
app.destroy()
