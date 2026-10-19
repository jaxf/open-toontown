"""Own dynamic instances and release them on completion or hood shutdown."""
from toontown.coghq.LobbyManagerAI import LobbyManagerAI
from toontown.suit.DistributedBureauBossAI import DistributedBureauBossAI


class BureauBossLobbyAI(LobbyManagerAI):
    def __init__(self, air):
        LobbyManagerAI.__init__(self,air,DistributedBureauBossAI)
        self.instances={}

    def createBossOffice(self, ids):
        zone=self.air.allocateZone()
        boss=self.bossConstructor(self.air)
        boss.setRoster(list(dict.fromkeys(i for i in ids if i))[:8])
        boss.generateWithRequired(zone)
        self.instances[zone]=boss
        self.acceptOnce(boss.uniqueName('BossDone'),self.destroyBossOffice,[boss])
        boss.b_setState('WaitForToons')
        return zone

    def destroyBossOffice(self, boss):
        if self.instances.pop(boss.zoneId,None) is not None:
            self.ignore(boss.uniqueName('BossDone'))
            LobbyManagerAI.destroyBossOffice(self,boss)

    def delete(self):
        for boss in list(self.instances.values()):self.destroyBossOffice(boss)
        LobbyManagerAI.delete(self)
