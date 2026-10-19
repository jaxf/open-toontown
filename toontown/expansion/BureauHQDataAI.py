"""Native patrols, battles, and eight-player Director General instances."""
from toontown.hood.HoodDataAI import HoodDataAI
from . import BureauHQGlobals as H


class BureauHQDataAI(HoodDataAI):
    def __init__(self,air,zoneId):
        HoodDataAI.__init__(self,air,zoneId,zoneId)

    def startup(self):
        from panda3d.toontown import DNAStorage
        from toontown.suit.DistributedSuitPlannerAI import DistributedSuitPlannerAI
        self.fishingPonds=[]
        for zone in sorted(H.ZONES):
            store=DNAStorage()
            self.air.dnaStoreMap[zone]=store
            self.air.dnaDataMap[zone]=self.air.loadDNAFileAI(store,H.dna_path(zone))
            planner=DistributedSuitPlannerAI(self.air,zone)
            planner.generateWithRequired(zone)
            planner.d_setZoneId(zone)
            self.air.suitPlanners[zone]=planner
            self.suitPlanners.append(planner)
            planner.initTasks()
        self.createBossEntrance()

    def createBossEntrance(self):
        from .BureauBossLobbyAI import BureauBossLobbyAI
        from toontown.building.DistributedBureauBossElevatorAI import DistributedBureauBossElevatorAI
        from toontown.building.DistributedBoardingPartyAI import DistributedBoardingPartyAI
        lobby=BureauBossLobbyAI(self.air)
        lobby.generateWithRequired(H.MINISTRY);self.addDistObj(lobby)
        elevator=DistributedBureauBossElevatorAI(self.air,lobby,H.MINISTRY,antiShuffle=1)
        elevator.generateWithRequired(H.MINISTRY);self.addDistObj(elevator)
        party=DistributedBoardingPartyAI(self.air,[elevator.doId],8)
        party.generateWithRequired(H.MINISTRY);self.addDistObj(party)
