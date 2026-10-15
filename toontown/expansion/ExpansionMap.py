"""The single illustrated Shtiker world map, including expansion destinations."""
from pathlib import Path
from panda3d.core import LineSegs, TextNode, Texture, Filename
from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton, DGG
from toontown.toonbase.ToonBaseGlobal import base
from . import ExpansionGlobals as E
from .WorldMapData import PINS, NAMES, map_point, road_points, STOCK_LINKS, stock_points


class ExpansionMap(DirectFrame):
    def __init__(self,parent,travel,close=None):
        DirectFrame.__init__(self,parent=parent,relief=None,frameSize=(-1.09,1.09,-.76,.82))
        self.initialiseoptions(ExpansionMap)
        self.travel=travel
        self.safeMode=False
        self.buttons={}
        self.routes={}
        self.available=set(PINS)
        font=base.loader.loadFont('phase_3/models/fonts/MickeyFont')
        button_model=base.loader.loadModel('phase_3/models/gui/quit_button')
        button_images=tuple(button_model.find('**/'+n) for n in ('QuitBtn_UP','QuitBtn_DN','QuitBtn_RLVR','QuitBtn_UP'))
        texture=base.loader.loadTexture(Filename.fromOsSpecific(str(
            Path(__file__).resolve().parents[2]/'assets/expansion/maps/toontown_world.png')))
        texture.setMinfilter(Texture.FTLinearMipmapLinear)
        self.art=DirectFrame(parent=self,relief=None,image=texture,
            image_scale=(1.06,1,.71),pos=(0,0,.05),state=DGG.DISABLED)
        self.title=DirectLabel(parent=self,text='TOONTOWN',relief=None,
            text_font=font,text_scale=.065,text_fg=(.20,.32,.33,1),text_shadow=(1,.98,.84,1),
            text_shadowOffset=(.04,.04),pos=(0,0,.725))
        for start,end,bend in STOCK_LINKS:
            for width,color in [(3,(.33,.33,.25,.48)),(1.5,(1,.96,.79,.85))]:
                line=LineSegs();line.setThickness(width);line.setColor(*color)
                for i,(x,z) in enumerate(stock_points(start,end,bend)):
                    (line.moveTo if i==0 else line.drawTo)(x,0,z)
                node=self.attachNewNode(line.create())
                node.setDepthTest(False);node.setDepthWrite(False)
        for street in E.STREETS:
            route=self.attachNewNode('map-road-'+str(street))
            points=road_points(street)
            # Cream center and muted ochre border echo the original painted map.
            for width,color in [(5,(.37,.32,.22,.8)),(2.5,(1,.90,.58,.95))]:
                line=LineSegs();line.setThickness(width);line.setColor(*color)
                for i,(x,z) in enumerate(points):
                    (line.moveTo if i==0 else line.drawTo)(x,0,z)
                route.attachNewNode(line.create())
            route.setDepthTest(False);route.setDepthWrite(False)
            self.routes[street]=route
        for zone,point in PINS.items():
            x,z=map_point(point)
            name=NAMES[zone]
            lines=name.replace(' ', '\n',1) if len(name)>15 else name
            button=DirectButton(parent=self,text=lines,text_font=font,text_scale=.026,
                image=button_images,image_scale=(.73,1,.65),image_pos=(0,0,-.01),
                text_align=TextNode.ACenter,text_fg=(.16,.25,.24,1),
                text_pos=(0,-.006),text_shadow=(1,1,.90,1),text_shadowOffset=(.04,.04),
                frameColor=((1,.96,.78,.93),(1,.84,.41,1),(1,.99,.91,1),(.83,.82,.75,.95)),
                frameSize=(-.115,.115,-.042,.025),relief=None,
                pos=(x,0,z),command=self.choose,extraArgs=[zone],pressEffect=True,sortOrder=5)
            button.bind(DGG.ENTER,self.describe,extraArgs=[zone])
            button.bind(DGG.EXIT,self.restore_caption)
            self.buttons[zone]=button
        button_model.removeNode()
        self.caption=DirectLabel(parent=self,text='',text_scale=.029,
            text_fg=(.20,.30,.29,1),text_wordwrap=69,relief=DGG.FLAT,
            frameColor=(1,.97,.86,.94),frameSize=(-1.05,1.05,-.055,.035),
            pos=(0,0,-.71))
        self.current=DirectLabel(parent=self,text='YOU',text_scale=.023,
            text_fg=(1,1,1,1),frameColor=(.20,.48,.40,1),frameSize=(-.037,.037,-.015,.025),
            relief=DGG.FLAT,sortOrder=7)
        self.current.hide()

    def refresh(self,safeMode=False,available=None):
        self.safeMode=safeMode
        self.available=set(PINS) if available is None else set(available)
        self.access=set(base.localAvatar.getTeleportAccess())
        self.place=base.cr.playGame.getPlaceId()
        current=E.hood_id(self.place) if self.place in E.ALL_ZONES else self.place
        self.current.hide()
        for zone,button in self.buttons.items():
            # Every district stays visible; unavailable/locked travel is explained
            # on hover and click instead of hiding the new world behind clouds.
            enabled=zone in self.available and zone in self.access and not safeMode
            button['text_fg']=(.13,.25,.23,1) if enabled else (.40,.39,.36,1)
            if zone==current:
                self.current.setPos(button.getX()-.10,0,button.getZ()+.04)
                self.current.show()
        self.default_caption=('Travel is unavailable right now.' if safeMode else
            'You are in '+NAMES.get(current,E.zone_name(self.place))+'. Select a neighborhood to travel.')
        self.caption['text']=self.default_caption
        self.show()

    def describe(self,zone,event=None):
        roads=', '.join(E.zone_name(z) for z in E.connections(zone)) if zone in E.ALL_ZONES or zone in E.SOURCE_GATES else ''
        if self.safeMode:status='Travel is unavailable right now.'
        elif zone not in self.available:status='Unavailable in this district.'
        elif zone not in self.access:status='Discover this neighborhood to unlock teleporting.'
        else:status='Click to teleport.'
        self.caption['text']=NAMES[zone]+' — '+status+('\nTunnels: '+roads if roads else '')
        for street,route in self.routes.items():
            route.setColorScale(1,1,1,1 if zone in E.STREETS[street][2:4] else .25)

    def restore_caption(self,event=None):
        self.caption['text']=getattr(self,'default_caption','Select a neighborhood.')
        for route in self.routes.values():route.clearColorScale()

    def choose(self,zone):
        self.describe(zone)
        if self.safeMode or zone not in self.available:
            return
        # Re-read access at click time, retaining the game's server check too.
        if zone in base.localAvatar.getTeleportAccess():self.travel(zone)
