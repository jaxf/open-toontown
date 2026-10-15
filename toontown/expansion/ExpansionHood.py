from direct.showbase.MessengerGlobal import messenger
from toontown.hood.ToonHood import ToonHood
from toontown.hood.Place import Place
from toontown.battle.BattlePlace import BattlePlace
from direct.fsm.State import State
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
        # Authored streets may curve away from the old central spawn.
        base.localAvatar.detachNode()
        base.localAvatar.setPosHpr(base.render, *E.spawn_point(requestStatus['zoneId']))
        requestStatus['nextState'] = 'walk'
        Place.enterTeleportIn(self, requestStatus)


class ExpansionStreet(BattlePlace, ExpansionPlayground):
    def __init__(self, loader, parentFSM, doneEvent):
        ExpansionPlayground.__init__(self, loader, parentFSM, doneEvent)
        self.fsm.addState(State('WaitForBattle',self.enterWaitForBattle,self.exitWaitForBattle,['battle','walk']))
        self.fsm.addState(State('battle',self.enterBattle,self.exitBattle,['walk','teleportOut','died']))
        for name in ('walk','stickerBook','teleportIn'):
            state=self.fsm.getStateNamed(name)
            state.addTransition('WaitForBattle');state.addTransition('battle')

    def load(self):
        ExpansionPlayground.load(self)

    def enter(self, requestStatus):
        ExpansionPlayground.enter(self,requestStatus)
        # The playground base turns collisions into native tunnel/door events;
        # battle entry uses the stock TownBattle UI and server-owned suits.
        base.localAvatar.setGeom(self.loader.geom)

    def exit(self):
        ExpansionPlayground.exit(self)
        base.localAvatar.setGeom(base.render)

    def enterTeleportOut(self, requestStatus):
        if 'battle' in requestStatus:
            self._teleportOutDone(requestStatus)
        else:
            ExpansionPlayground.enterTeleportOut(self,requestStatus)


class ExpansionLoader(SafeZoneLoader):
    def __init__(self, hood, parentFSM, doneEvent, zoneId):
        SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)
        self.zoneId = zoneId
        self.playgroundClass = ExpansionStreet if zoneId in E.STREETS else ExpansionPlayground
        self.musicFile = E.NEIGHBORHOODS[hood.id]['music']
        self.activityMusicFile = self.musicFile
        self.safeZoneStorageDNAFile = None
        self.dnaFile = None

    def load(self):
        SafeZoneLoader.load(self)
        if self.zoneId in E.STREETS:
            from toontown.town.TownBattle import TownBattle
            from toontown.toon import Toon
            Toon.loadBattleAnims()
            self.battleMusic=base.loader.loadMusic('phase_3.5/audio/bgm/encntr_general_bg.ogg')
            self.townBattle=TownBattle('expansion-town-battle-done')
            self.townBattle.load()

    def unload(self):
        if hasattr(self,'townBattle'):
            from toontown.toon import Toon
            Toon.unloadBattleAnims()
            self.townBattle.unload()
            self.townBattle.cleanup()
            self.battleMusic.stop()
            del self.townBattle,self.battleMusic
        SafeZoneLoader.unload(self)

    def createSafeZone(self, dnaFile):
        self.geom = build_scene(self.zoneId, self.hood.dnaStore)
        print('[Expansion DNA] Attaching exterior %s' % self.zoneId, flush=True)
        self.geom.reparentTo(base.hidden)
        if self.zoneId in E.ALL_ZONES:
            print('[Expansion DNA] Building visibility dictionaries', flush=True)
            self.makeDictionaries(self.hood.dnaStore)
            print('[Expansion DNA] Exterior ready', flush=True)
        else:
            self.nodeList = [self.geom]
        self.holidayPropTransforms = {}
        self.animPropDict = {}

    def handlePlaygroundDone(self):
        status=self.place.doneStatus
        if status.get('loader') == 'minigame':
            self.hood.trolleyReturnZone = self.zoneId
        if E.exterior_zone(status['zoneId'])==self.zoneId and status.get('shardId') is None:
            self.fsm.request('quietZone',[status])
        else:
            self.doneStatus=status
            messenger.send(self.doneEvent)

    def handleToonInteriorDone(self):
        self.handlePlaygroundDone()


class ExpansionHood(ToonHood):
    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        ToonHood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)
        self.id = hoodId
        self.trolleyReturnZone = hoodId
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
                                      self.loaderDoneEvent, E.exterior_zone(requestStatus['zoneId']))
        self.loader.load()

    def handlePurchaseDone(self):
        status = self.purchase.getDoneStatus()
        if status['where'] == 'playground':
            self.fsm.request('quietZone', [{'loader': 'safeZoneLoader',
                'where': 'playground', 'how': 'teleportIn',
                'hoodId': self.hoodId, 'zoneId': self.trolleyReturnZone,
                'shardId': None, 'avId': -1}])
        else:
            ToonHood.handlePurchaseDone(self)
