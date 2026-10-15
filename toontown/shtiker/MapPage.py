from . import ShtikerPage
from toontown.toonbase import ToontownGlobals, TTLocalizer
from toontown.hood import ZoneUtil
from direct.gui.DirectGui import DirectButton
from toontown.expansion.ExpansionMap import ExpansionMap


class MapPage(ShtikerPage.ShtikerPage):
    """One illustrated map for the original world and all five new neighborhoods."""
    def __init__(self):
        ShtikerPage.ShtikerPage.__init__(self)

    def load(self):
        ShtikerPage.ShtikerPage.load(self)
        self.map=ExpansionMap(self,self.__buttonCallback)
        self.map.setScale(.84)
        self.map.setZ(.08)
        guiButton=loader.loadModel('phase_3/models/gui/quit_button')
        image=tuple(guiButton.find('**/'+name) for name in ('QuitBtn_UP','QuitBtn_DN','QuitBtn_RLVR'))
        self.safeZoneButton=DirectButton(parent=self,relief=None,image=image,
            image_scale=(1.3,1.1,1.1),pos=(.47,0,-.65),
            text=TTLocalizer.MapPageBackToPlayground,text_scale=TTLocalizer.MPsafeZoneButton,
            text_pos=(0,-.02),command=self.backToSafeZone)
        self.goHomeButton=DirectButton(parent=self,relief=None,image=image,
            image_scale=(.66,1.1,1.1),pos=(-.47,0,-.65),
            text=TTLocalizer.MapPageGoHome,text_scale=TTLocalizer.MPgoHomeButton,
            text_pos=(0,-.02),command=self.goHome)
        guiButton.removeNode()
        self.resetFrameSize()

    def unload(self):
        self.map.destroy()
        self.safeZoneButton.destroy()
        self.goHomeButton.destroy()
        ShtikerPage.ShtikerPage.unload(self)

    def enter(self):
        ShtikerPage.ShtikerPage.enter(self)
        self.map.refresh(self.book.safeMode,base.cr.hoodMgr.getAvailableZones())
        place=base.cr.playGame.getPlace()
        zone=place.getZoneId() if place else 0
        self.safeZoneButton['text']=(TTLocalizer.MapPageBackToCogHQ
            if ZoneUtil.isCogHQZone(base.localAvatar.lastHood) else TTLocalizer.MapPageBackToPlayground)
        self.safeZoneButton.hide()
        if zone and not ZoneUtil.isPlayground(zone) and not self.book.safeMode:
            self.safeZoneButton.show()
        self.goHomeButton.hide()
        at_home=(base.cr.playGame.getPlaceId()==ToontownGlobals.MyEstate
            and base.cr.playGame.hood.loader.atMyEstate())
        if base.housingEnabled and not at_home and not self.book.safeMode:
            self.goHomeButton.show()

    def exit(self):
        ShtikerPage.ShtikerPage.exit(self)

    def backToSafeZone(self):
        if self.book.safeMode:return
        self.doneStatus={'mode':'teleport','hood':base.localAvatar.lastHood}
        messenger.send(self.doneEvent)

    def goHome(self):
        if self.book.safeMode:return
        self.doneStatus={'mode':'gohome','hood':base.localAvatar.lastHood}
        messenger.send(self.doneEvent)

    def __buttonCallback(self,hood):
        if self.book.safeMode:return
        if hood in base.localAvatar.getTeleportAccess() and hood in base.cr.hoodMgr.getAvailableZones():
            base.localAvatar.sendUpdate('checkTeleportAccess',[hood])
            self.doneStatus={'mode':'teleport','hood':hood}
            messenger.send(self.doneEvent)
