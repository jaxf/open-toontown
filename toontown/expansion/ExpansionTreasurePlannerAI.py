from toontown.safezone.RegenTreasurePlannerAI import RegenTreasurePlannerAI
from toontown.safezone.DistributedDGTreasureAI import DistributedDGTreasureAI
from .Treasures import SPAWNS


class ExpansionTreasurePlannerAI(RegenTreasurePlannerAI):
    healAmount=10

    def __init__(self,zone):
        RegenTreasurePlannerAI.__init__(self,zone,DistributedDGTreasureAI,
            'expansion-laff-treasures',15,4)

    def initSpawnPoints(self):
        self.spawnPoints=[(x,y,.15) for x,y in SPAWNS[self.zoneId]]
