from .DistributedBossElevatorAI import DistributedBossElevatorAI
from .ElevatorConstants import REJECT_MINLAFF


class DistributedBureauBossElevatorAI(DistributedBossElevatorAI):
    def checkBoard(self, av):
        # Unfinished suit/promotion progression must not lock the test entrance.
        return 0 if av.getHp()>0 and av.zoneId==self.zone else REJECT_MINLAFF
