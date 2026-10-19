from toontown.coghq.CogHQLoader import CogHQLoader
from toontown.coghq.CogHQBossBattle import CogHQBossBattle
from .BureauBossScene import build_room


class BureauBossPlace(CogHQBossBattle):
    def enter(self,status):
        from toontown.suit import DistributedBureauBoss
        from direct.showbase.ShowBaseGlobal import base
        self.loader.hood.stopSky()
        self.loader.geom.reparentTo(base.render)
        base.localAvatar.setGeom(self.loader.geom)
        CogHQBossBattle.enter(self,status,DistributedBureauBoss.OneBossCog)

    def exit(self):
        from direct.showbase.ShowBaseGlobal import base
        CogHQBossBattle.exit(self)
        base.localAvatar.setGeom(base.render)


class BureauBossLoader(CogHQLoader):
    musicFile='phase_11/audio/bgm/LB_courtyard.ogg'

    def loadPlaceGeom(self,zoneId):
        from direct.showbase.ShowBaseGlobal import base
        self.geom=build_room();self.geom.reparentTo(base.render)
        self.zoneId=zoneId

    def unloadPlaceGeom(self):
        self.geom.removeNode()

    def getBossPlaceClass(self):
        return BureauBossPlace

    def isInThisHq(self,status):
        return status.get('loader')=='cogHQLoader' and status.get('where')=='cogHQBossBattle'

    def exit(self):
        self.fsm.requestFinalState()
        CogHQLoader.exit(self)
