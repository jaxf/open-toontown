from .DistributedBossElevator import DistributedBossElevator
from .DistributedElevator import DistributedElevator


class DistributedBureauBossElevator(DistributedBossElevator):
    def setupElevator(self):
        from direct.showbase.ShowBaseGlobal import base
        from toontown.expansion.BureauBossScene import build_entrance_elevator
        locator=base.cr.playGame.hood.loader.geom.find('**/bureau-boss-elevator-locator')
        self.elevatorModel=build_entrance_elevator(locator)
        self.leftDoor=self.elevatorModel.find('**/left-door')
        self.rightDoor=self.elevatorModel.find('**/right-door')
        DistributedElevator.setupElevator(self)

    def getDestName(self):
        return 'The Final Review Chamber'
