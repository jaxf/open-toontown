from panda3d.core import LineSegs
from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton, DGG
from toontown.toonbase.ToonBaseGlobal import base
from . import ExpansionGlobals as E


class ExpansionMap(DirectFrame):
    def __init__(self, parent, travel, close):
        DirectFrame.__init__(self, parent=parent, relief=DGG.FLAT,
                             frameSize=(-1.06,1.06,-.72,.74), frameColor=(.94,.90,.78,1))
        self.initialiseoptions(ExpansionMap)
        self.travel=travel
        self.buttons={}
        DirectLabel(parent=self, text='BEYOND THE TUNNELS', text_scale=.065,
                    text_fg=(.18,.26,.27,1), pos=(0,0,.63), relief=None)
        DirectButton(parent=self, text='Original map', text_scale=.034,
                     pos=(.81,0,.66), frameSize=(-.17,.17,-.035,.035),
                     relief=DGG.FLAT, frameColor=(.27,.36,.35,1),text_fg=(1,1,1,1),command=close)
        for street,(name,hood,start,end) in E.STREETS.items():
            x1,z1=E.MAP_POSITIONS[start]
            x2,z2=E.MAP_POSITIONS[end]
            line=LineSegs('route-%s' % street)
            line.setThickness(3)
            line.setColor(.42,.46,.36,1)
            line.moveTo(x1,0,z1)
            line.drawTo(x2,0,z2)
            self.attachNewNode(line.create())
            vertical=abs(x1-x2)<.01
            DirectLabel(parent=self,text=name,text_scale=.025,
                text_fg=(.23,.28,.27,1),text_wordwrap=7 if vertical else 14,
                pos=((x1+x2)/2+(.135 if vertical else 0),0,(z1+z2)/2+(.01 if vertical else .12)),
                relief=None)
        for zone,(x,z) in E.MAP_POSITIONS.items():
            color=E.NEIGHBORHOODS[zone]['colors'][0] if zone in E.NEIGHBORHOODS else (.35,.44,.48,1)
            self.buttons[zone]=DirectButton(parent=self, text=E.zone_name(zone).replace(' ' , '\n', 1),
                text_scale=.033,text_wordwrap=13,text_fg=(1,1,.94,1),
                frameColor=color,relief=DGG.FLAT,frameSize=(-.20,.20,-.075,.075),
                pos=(x,0,z),command=self.choose,extraArgs=[zone])
        self.caption=DirectLabel(parent=self,
            text='Walk through tunnels to discover new playgrounds and unlock travel.',
            text_scale=.031,text_fg=(.22,.29,.29,1),pos=(0,0,-.61),relief=None)
        self.hide()

    def refresh(self, safeMode=False):
        self.safeMode=safeMode
        current=base.cr.playGame.getPlaceId()
        access=base.localAvatar.getTeleportAccess()
        for zone,button in self.buttons.items():
            button['text']=E.zone_name(zone).replace(' ', '\n', 1)
            button['frameColor'] = E.NEIGHBORHOODS[zone]['colors'][0] if zone in E.NEIGHBORHOODS else (.35,.44,.48,1)
            if zone == current:
                self.caption['text']='You are in ' + E.zone_name(zone) + '. Select an unlocked playground to travel.'
            button['text_fg']=(1,1,.94,1) if zone in access else (.8,.82,.80,1)
        self.show()

    def choose(self, zone):
        if self.safeMode:
            return
        if zone in base.localAvatar.getTeleportAccess():
            self.travel(zone)
        else:
            self.caption['text']='Discover %s through its tunnel first.' % E.zone_name(zone)
