from toontown.hood.HoodDataAI import HoodDataAI


class ExpansionHoodDataAI(HoodDataAI):
    """Static exploration zones. No DNA building/suit managers until authored."""
    def __init__(self, air, zoneId):
        HoodDataAI.__init__(self, air, zoneId, zoneId)

    def startup(self):
        self.fishingPonds = []
