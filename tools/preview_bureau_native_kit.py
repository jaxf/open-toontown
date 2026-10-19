"""Inspect original resource models before placing them in the HQ art pass."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from panda3d.core import loadPrcFileData,OrthographicLens,TextNode
loadPrcFileData('','window-type offscreen\nload-display p3headlessgl\nwin-size 1600 1100\naudio-library-name null\nmodel-path resources\ndefault-model-extension .bam')
from direct.showbase.ShowBase import ShowBase
from tools.preview_bureaubots import capture

app=ShowBase();app.disableMouse();app.setBackgroundColor(.23,.27,.30,1)
lens=OrthographicLens();lens.setFilmSize(72,49.5);lens.setNearFar(1,500)
app.cam.node().setLens(lens);app.camera.setPos(0,-120,6);app.camera.lookAt(0,0,6)
items=[
 ('Dreamland lamp','phase_8/models/props/streetlight_DL','prop_post_three_light'),
 ('Daisy planter tree','phase_8/models/props/trees_DG','prop_tree_DG_ur'),
 ('Filing cabinet A','phase_11/models/lawbotHQ/LB_filing_cabA',None),
 ('Wall panel','phase_11/models/lawbotHQ/LB_wall_panel',None),
 ('Native column','phase_11/models/lawbotHQ/LB_pillar',None),
 ('Street iron fence','phase_5/models/modules/street_low_fence','f_ironbar_brick'),
 ('Cog wall panel 2','phase_5/models/modules/suit_walls','wall_suit_build2_ul'),
 ('Cog wall panel 4','phase_5/models/modules/suit_walls','wall_suit_build4_ul'),
 ('Native Cog door','phase_5/models/modules/suit_door',None),
 ('Lawbot skyline 12','phase_11/models/lawbotHQ/LawbotPlaza','LB_BLD12'),
 ('Paper pallet','phase_11/models/lawbotHQ/LB_paper_stack_pallet',None),
 ('Cashbot pipework','phase_10/models/cashbotHQ/pipes_E',None)]
for i,(name,path,part) in enumerate(items):
    model=app.loader.loadModel(path);source=model.find('**/'+part) if part else model
    root=app.render.attachNewNode(name);obj=source.copyTo(root)
    if part:obj.setMat(source.getMat(model))
    for c in obj.findAllMatches('**/+CollisionNode'):c.removeNode()
    low,high=root.getTightBounds();size=high-low
    obj.setPos(obj.getPos()-(low+high)*.5)
    root.setScale(10/max(size.x,size.y,size.z));root.setPos(-27+i%4*18,0,22-i//4*16)
    root.setH(15 if size.y>1 else 0)
    label=TextNode(name);label.setText(name);label.setAlign(TextNode.ACenter);label.setTextColor(1,.95,.8,1)
    labelnode=app.render.attachNewNode(label);labelnode.setPos(-27+i%4*18,-8,15-i//4*16);labelnode.setScale(.75)
capture(app,Path('docs/previews/bureau-native-kit.png'));app.destroy()
