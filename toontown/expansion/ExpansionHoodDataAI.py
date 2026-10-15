from toontown.hood.HoodDataAI import HoodDataAI
from . import ExpansionGlobals as E


class ExpansionHoodDataAI(HoodDataAI):
    """Native quest HQs, gag shops and multiplayer trolleys in every exterior."""
    def __init__(self,air,zoneId):
        HoodDataAI.__init__(self,air,zoneId,zoneId)
        self.serviceBuildings=[]

    def startup(self):
        from toontown.building.HQBuildingAI import HQBuildingAI
        from toontown.building.GagshopBuildingAI import GagshopBuildingAI
        from toontown.safezone.DistributedTrolleyAI import DistributedTrolleyAI
        self.fishingPonds=[]
        for zone in sorted(z for z in E.ALL_ZONES if E.hood_id(z)==self.zoneId):
            self.serviceBuildings.append(HQBuildingAI(self.air,zone,E.service_interior(zone,'hq'),E.SERVICE_BLOCKS['hq']))
            self.serviceBuildings.append(GagshopBuildingAI(self.air,zone,E.service_interior(zone,'gagshop'),E.SERVICE_BLOCKS['gagshop']))
            trolley=DistributedTrolleyAI(self.air)
            trolley.generateWithRequired(zone)
            trolley.start()
            self.addDistObj(trolley)

    def shutdown(self):
        for building in self.serviceBuildings:building.cleanup()
        self.serviceBuildings=[]
        HoodDataAI.shutdown(self)
