from toontown.hood.HoodDataAI import HoodDataAI
from . import ExpansionGlobals as E


class ExpansionHoodDataAI(HoodDataAI):
    """Quest HQs and native street patrols; shops and trolleys in playgrounds."""
    def __init__(self,air,zoneId):
        HoodDataAI.__init__(self,air,zoneId,zoneId)
        self.serviceBuildings=[]

    def startup(self):
        from toontown.building.HQBuildingAI import HQBuildingAI
        from toontown.building.GagshopBuildingAI import GagshopBuildingAI
        from toontown.safezone.DistributedTrolleyAI import DistributedTrolleyAI
        from .ExpansionTreasurePlannerAI import ExpansionTreasurePlannerAI
        self.treasurePlanner=ExpansionTreasurePlannerAI(self.zoneId)
        self.treasurePlanner.start()
        self.fishingPonds=[]
        for zone in sorted(z for z in E.ALL_ZONES if E.hood_id(z)==self.zoneId):
            self.serviceBuildings.append(HQBuildingAI(self.air,zone,E.service_interior(zone,'hq'),E.SERVICE_BLOCKS['hq']))
            if zone in E.NEIGHBORHOODS:
                self.serviceBuildings.append(GagshopBuildingAI(self.air,zone,E.service_interior(zone,'gagshop'),E.SERVICE_BLOCKS['gagshop']))
                trolley=DistributedTrolleyAI(self.air)
                trolley.generateWithRequired(zone)
                trolley.start()
                self.addDistObj(trolley)
            else:
                from panda3d.toontown import DNAStorage
                from toontown.building.DistributedBuildingMgrAI import DistributedBuildingMgrAI
                from toontown.suit.DistributedSuitPlannerAI import DistributedSuitPlannerAI
                from .WorldDNA import LAYOUTS
                store=DNAStorage()
                self.air.dnaStoreMap[zone]=store
                self.air.dnaDataMap[zone]=self.air.loadDNAFileAI(store,LAYOUTS[zone])
                manager=DistributedBuildingMgrAI(self.air,zone,store,self.air.trophyMgr)
                self.air.buildingManagers[zone]=manager
                self.buildingManagers.append(manager)
                planner=DistributedSuitPlannerAI(self.air,zone)
                planner.generateWithRequired(zone)
                planner.d_setZoneId(zone)
                self.air.suitPlanners[zone]=planner
                self.suitPlanners.append(planner)
                planner.initTasks()

    def shutdown(self):
        for building in self.serviceBuildings:building.cleanup()
        self.serviceBuildings=[]
        HoodDataAI.shutdown(self)
