from direct.showbase.MessengerGlobal import messenger
from toontown.hood.ToonHood import ToonHood
from toontown.hood.Place import Place
from toontown.safezone.SafeZoneLoader import SafeZoneLoader
from toontown.safezone.Playground import Playground
from toontown.toonbase.ToonBaseGlobal import base
from . import ExpansionGlobals as E
from .ExpansionScene import build_scene


class ExpansionPlayground(Playground):
    def enterTeleportOut(self, requestStatus):
        # Playground's usual same-hood shortcut would retain the promenade
        # geometry when returning to its plaza. Always rebuild via the loader.
        Place.enterTeleportOut(self, requestStatus, self._teleportOutDone)

    def _teleportOutDone(self, requestStatus):
        from toontown.toonbase import ToontownGlobals
        if requestStatus['hoodId'] == ToontownGlobals.MyEstate:
            self.getEstateZoneAndGoHome(requestStatus)
            return
        self.doneStatus = requestStatus
        messenger.send(self.doneEvent)

    def enterTeleportIn(self, requestStatus):
        # Both plazas and connecting promenades have a clear central spawn.
        base.localAvatar.detachNode()
        base.localAvatar.setPosHpr(base.render, 0, -18, .1, 0, 0, 0)
        requestStatus['nextState'] = 'walk'
        Place.enterTeleportIn(self, requestStatus)


class ExpansionLoader(SafeZoneLoader):
    def __init__(self, hood, parentFSM, doneEvent, zoneId):
        SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)
        self.zoneId = zoneId
        self.playgroundClass = ExpansionPlayground
        self.musicFile = E.NEIGHBORHOODS[hood.id]['music']
        self.activityMusicFile = self.musicFile
        self.safeZoneStorageDNAFile = None
        self.dnaFile = None

    def createSafeZone(self, dnaFile):
        self.geom = build_scene(self.zoneId)
        self.geom.reparentTo(base.hidden)
        self.nodeList = [self.geom]
        self.holidayPropTransforms = {}
        self.animPropDict = {}

    def handlePlaygroundDone(self):
        # Force a loader rebuild when moving between an expansion plaza and
        # promenade, even when they share the same neighborhood ID.
        self.doneStatus = self.place.doneStatus
        messenger.send(self.doneEvent)


class ExpansionHood(ToonHood):
    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        ToonHood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)
        self.id = hoodId
        self.storageDNAFile = None
        self.skyFile = 'phase_3.5/models/props/TT_sky'
        self.titleColor = E.NEIGHBORHOODS[hoodId]['colors'][2]

    def getHoodText(self, zoneId):
        name = E.NEIGHBORHOODS[self.id]['name']
        return name + ('\n' + E.zone_name(zoneId) if zoneId in E.STREETS else '')

    def load(self):
        ToonHood.load(self)
        self.sky.setColorScale(*E.NEIGHBORHOODS[self.id]['sky'])
        self.parentFSM.getStateNamed('ExpansionHood').addChild(self.fsm)

    def unload(self):
        self.parentFSM.getStateNamed('ExpansionHood').removeChild(self.fsm)
        ToonHood.unload(self)

    def loadLoader(self, requestStatus):
        self.loader = ExpansionLoader(self, self.fsm.getStateNamed('safeZoneLoader'),
                                      self.loaderDoneEvent, requestStatus['zoneId'])
        self.loader.load()
