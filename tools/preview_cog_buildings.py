"""Five actual department assets at a common scale for silhouette comparison."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from panda3d.core import loadPrcFileData
loadPrcFileData('', 'window-type offscreen\nload-display p3headlessgl\n'
    'win-size 1800 800\naudio-library-name null\nmodel-path resources\n'
    'default-model-extension .bam')
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import DirectLabel
from toontown.building.BureaubotBuilding import MODEL_PATH,add_elevator_badge
from tools.preview_bureaubots import capture


def main():
    app=ShowBase();app.setBackgroundColor(.075,.12,.20,1)
    DirectLabel(parent=app.aspect2d,relief=None,text='FIVE DEPARTMENTS / FIVE BUILDINGS',
        text_scale=.065,text_pos=(0,.83),text_fg=(.92,.91,.83,1))
    DirectLabel(parent=app.aspect2d,relief=None,text='Actual game assets — Bureaubot is a separately authored model',
        text_scale=.032,text_pos=(0,.73),text_fg=(.69,.75,.79,1))
    for i,(name,asset) in enumerate((('CASHBOT','money'),('SELLBOT','sales'),
            ('LAWBOT','legal'),('BOSSBOT','corp'),('BUREAUBOT',None))):
        stage=app.aspect2d.attachNewNode(name)
        stage.setPos(-1.8+i*.9,0,-.68)
        stage.setDepthTest(True);stage.setDepthWrite(True)
        model=app.loader.loadModel(MODEL_PATH if asset is None else
            'phase_4/models/modules/suit_landmark_'+asset)
        model.reparentTo(stage)
        elevator=app.loader.loadModel('phase_4/models/modules/elevator')
        elevator.reparentTo(model.find('**/*_door_origin'))
        if asset is None:add_elevator_badge(elevator)
        model.setH(-12)
        low,high=model.getTightBounds(stage)
        scale=.016
        model.setScale(scale)
        model.setPos(-(low.x+high.x)*scale/2,0,-low.z*scale)
        DirectLabel(parent=app.aspect2d,relief=None,text=name,
            text_scale=.048,text_pos=(-1.8+i*.9,-.82),
            text_fg=(.98,.78,.46,1) if asset is None else (.85,.89,.92,1))
    capture(app,Path('docs/previews/five-cog-buildings.png'))
    app.destroy()


if __name__=='__main__':main()
