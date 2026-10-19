"""Render the production SuitPage with local avatar/OTP adapters.

Uses the real page, resource geometry, fonts, original head assets, and new
models. Only multiplayer/OTP services are replaced. Not a logged-in game test.
Run from the repo root: python tools/preview_cog_gallery.py
"""
import ast
import builtins
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from panda3d.core import loadPrcFileData, VBase4, PNMImage
loadPrcFileData('', 'window-type offscreen\nload-display p3headlessgl\n'
    'win-size 1280 960\naudio-library-name null\nmodel-path resources\n'
    'default-model-extension .bam')
from direct.showbase.ShowBase import ShowBase
from tools.preview_bureaubots import capture
loadPrcFileData('', 'win-size 1280 960')


def module(name,**attrs):
    result = ModuleType(name)
    result.__dict__.update(attrs)
    sys.modules[name] = result
    return result


def main():
    app = ShowBase()
    app.setBackgroundColor(.05,.15,.4,1)
    from toontown.toonbase import TTLocalizer
    font = app.loader.loadFont(TTLocalizer.SuitFont,pixelsPerUnit=40,
                               spaceAdvance=.25,lineHeight=1.0)
    module('toontown.toonbase.ToontownGlobals',getSuitFont=lambda:font,
        getSignFont=lambda:font,EmblemTypes=SimpleNamespace(Silver=0,Gold=1))
    module('toontown.shtiker.ShtikerBook')
    module('toontown.shtiker.SummonCogDialog')
    from toontown.suit import SuitDNA
    # Read names from the production battle catalog, without importing OTP.
    tree = ast.parse((ROOT/'toontown/battle/SuitBattleGlobals.py').read_text())
    attrs = next(n.value for n in tree.body if isinstance(n,ast.Assign)
                 and any(isinstance(t,ast.Name) and t.id=='SuitAttributes' for t in n.targets))
    names = {}
    for key,value in zip(attrs.keys,attrs.values):
        name = next(v for k,v in zip(value.keys,value.values) if k.value=='name')
        names[key.value] = {'name':getattr(TTLocalizer,name.attr)}
    module('toontown.battle.SuitBattleGlobals',SuitAttributes=names)
    # Parse the original model/texture choices from Suit.generateSuit itself.
    tree = ast.parse((ROOT/'toontown/suit/Suit.py').read_text())
    klass = next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Suit')
    method = next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='generateSuit')
    parts = {}
    for n in ast.walk(method):
        if (isinstance(n,ast.If) and isinstance(n.test,ast.Compare)
            and isinstance(n.test.left,ast.Attribute) and n.test.left.attr=='name'):
            key = n.test.comparators[0].value
            heads,texture,color = [],None,None
            for stmt in n.body:
                if (isinstance(stmt,ast.Expr) and isinstance(stmt.value,ast.Call)
                    and isinstance(stmt.value.func,ast.Attribute)
                    and stmt.value.func.attr=='generateHead'):
                    heads.append(stmt.value.args[0].value)
                if isinstance(stmt,ast.Assign):
                    target = stmt.targets[0]
                    if isinstance(target,ast.Attribute) and target.attr=='headTexture':
                        texture = stmt.value.value
                    if isinstance(target,ast.Attribute) and target.attr=='headColor':
                        color = eval(compile(ast.Expression(stmt.value),'head-color','eval'),{'VBase4':VBase4})
            parts[key] = (heads,texture,color)

    def attach_head(parent,key):
        body = SuitDNA.getSuitBodyType(key)
        phase = '3.5' if body=='c' else '4'
        source = app.loader.loadModel('phase_'+phase+'/models/char/suit'+body.upper()+'-heads')
        head = parent.attachNewNode('head')
        heads,texture,color = parts[key]
        for name in heads:
            for part in source.findAllMatches('**/'+name):
                copy = part.copyTo(head)
                if texture:
                    copy.setTexture(app.loader.loadTexture('phase_'+phase+'/maps/'+texture),1)
                if color:
                    copy.setColor(color)
        head.setH(180)
        head.setDepthTest(True)
        head.setDepthWrite(True)
        source.removeNode()
        return head

    module('toontown.suit.Suit',attachSuitHead=attach_head)
    avatar = SimpleNamespace(cogs=[5]*32,cogCounts=[45,40,35,30,25,20,15,10]*4,
        cogRadar=[1]*4,buildingRadar=[1]*4,emblems=[0,0],
        uniqueName=lambda name:name,hasCogSummons=lambda index:False)
    builtins.localAvatar = app.localAvatar = avatar
    app.cr = SimpleNamespace(wantEmblems=False,currSuitPlanner=None)
    from direct.gui.DirectGui import DirectFrame
    from toontown.shtiker.SuitPage import SuitPage
    # Same book art as the live Shtickerbook.
    book = app.loader.loadModel('phase_3.5/models/gui/stickerbook_gui')
    pageArt = book.find('**/big_book')
    if not pageArt.isEmpty():
        DirectFrame(parent=app.aspect2d,relief=None,image=pageArt,
                    image_scale=(2,1,1.5),pos=(0,1,.1))
    page = SuitPage()
    page.reparentTo(app.aspect2d)
    page.load()
    page.enter()
    out = ROOT/'docs/previews'
    out.mkdir(parents=True,exist_ok=True)
    capture(app,out/'cog-gallery-bureaubots.png')
    assert len(page.panels)==32 and len(page.bureaubotPanels)==8
    assert len(page.radarButtons)==4
    for i in range(8):
        page.showBureaubot(i)
        page.bureaubotViewer.rotate(30)
        page.bureaubotViewer.change(1)
        page.bureaubotViewer.change(-1)
        page.closeBureaubot()
    page.showBureaubot(7)
    capture(app,out/'bureaubot-model-viewer.png')
    # Catch draw-order regressions that place the viewer behind the book art.
    viewerShot = PNMImage()
    app.win.getScreenshot(viewerShot)
    center = viewerShot.getXel(viewerShot.getXSize()//2,viewerShot.getYSize()//2)
    assert max(center) < .8, 'The model must be visible in front of the book.'
    page.closeBureaubot()
    # Legacy radar and incomplete collections still use exactly 32 slots.
    for dept in range(4):
        page.toggleRadar(dept)
        page.toggleRadar(dept)
    avatar.cogs=[1,2,3,4,5,2,3,5]*4
    page.updatePage()
    capture(app,out/'cog-gallery-progress.png')
    page.exit()
    page.enter()
    page.exit()
    page.unload()
    assert page.bureaubotViewer is None
    assert not app.taskMgr.hasTaskNamed('showCogRadarLater')
    assert not app.taskMgr.hasTaskNamed('activateButtonLater')
    app.destroy()
    print('Gallery: 40 cards; 8 models; four legacy radar rows; lifecycle checks passed.')


if __name__=='__main__':
    main()
