"""Full-body model viewer owned by the Cog Gallery page."""
from direct.gui.DirectGui import DirectButton, DirectFrame, DirectLabel, DGG
from panda3d.core import TextNode
from toontown.suit import BureaubotModels
from toontown.toonbase import TTLocalizer, ToontownGlobals


class BureaubotViewer:
    def __init__(self, parent, model_loader, index, on_close):
        self.loader = model_loader
        self.on_close = on_close
        self.actor = None
        self.index = index
        self.frame = DirectFrame(parent=parent, relief=DGG.RIDGE,
            frameSize=(-.87,.87,-.59,.61), frameColor=(.94,.88,.70,1),
            borderWidth=(.012,.012), pos=(0,-5,0), sortOrder=100,
            state=DGG.NORMAL)
        self.frame.setBin('gui-popup',100)
        self.frame.setDepthTest(False)
        self.frame.setDepthWrite(False)
        self.title = DirectLabel(parent=self.frame, relief=None,
            text='', text_scale=.068, text_pos=(0,.48),
            text_font=ToontownGlobals.getSuitFont())
        DirectLabel(parent=self.frame, relief=None, text=TTLocalizer.BureaubotP,
            text_scale=.040, text_pos=(0,.405), text_fg=(.35,.22,.14,1))
        self.stage = self.frame.attachNewNode('model-stage')
        self.stage.setBin('gui-popup',101)
        self.stage.setDepthTest(True)
        self.stage.setDepthWrite(True)
        self.stage.setLightOff()
        self.stage.setPos(0,-.1,-.40)
        self.rank = DirectLabel(parent=self.frame, relief=None, text='',
            text_scale=.032, text_pos=(0,-.46))
        self._button(TTLocalizer.BureaubotPrevious,(-.62,0,-.51),lambda:self.change(-1))
        self._button(TTLocalizer.BureaubotNext,(.62,0,-.51),lambda:self.change(1))
        self._button(TTLocalizer.BureaubotTurnLeft,(-.35,0,-.51),lambda:self.rotate(-30))
        self._button(TTLocalizer.BureaubotTurnRight,(.35,0,-.51),lambda:self.rotate(30))
        self._button(TTLocalizer.lClose,(.70,0,.52),on_close,scale=.032)
        self.show(index)

    def _button(self,text,pos,command,scale=.036):
        return DirectButton(parent=self.frame, relief=DGG.RAISED,
            frameColor=(1,.83,.35,1), borderWidth=(.008,.008),
            frameSize=(-.12,.12,-.031,.041), text=text,text_scale=scale,
            pos=pos,command=command,pressEffect=True)

    def _clear_actor(self):
        if self.actor is not None:
            self.actor.stop()
            self.actor.cleanup()
            self.actor.removeNode()
            self.actor = None

    def show(self,index):
        self._clear_actor()
        self.index = index % len(BureaubotModels.CATALOG)
        key,name,_,_ = BureaubotModels.CATALOG[self.index]
        self.title['text'] = name
        self.rank['text'] = TTLocalizer.BureaubotRank % (self.index+1)
        self.actor = BureaubotModels.make_actor(key,self.loader)
        self.actor.reparentTo(self.stage)
        self.actor.setH(170)
        low,high = self.actor.getTightBounds(self.stage)
        scale = min(.76/(high.z-low.z),1.1/(high.x-low.x))
        self.stage.setScale(scale)
        self.actor.setZ(-low.z)

    def change(self,direction):
        self.show(self.index+direction)

    def rotate(self,degrees):
        self.actor.setH(self.actor.getH()+degrees)

    def destroy(self):
        self._clear_actor()
        self.frame.destroy()

