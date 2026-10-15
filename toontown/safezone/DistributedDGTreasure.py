from . import DistributedSZTreasure

class DistributedDGTreasure(DistributedSZTreasure.DistributedSZTreasure):

    def __init__(self, cr):
        DistributedSZTreasure.DistributedSZTreasure.__init__(self, cr)
        self.modelPath = 'phase_8/models/props/flower_treasure'
        self.grabSoundPath = 'phase_4/audio/sfx/SZ_DD_treasure.ogg'

    def loadTreasureModel(self, modelPath):
        from toontown.expansion.Treasures import is_expansion_model, load_model
        if is_expansion_model(modelPath):
            return load_model(base.loader, modelPath)
        return DistributedSZTreasure.DistributedSZTreasure.loadTreasureModel(self, modelPath)

    def announceGenerate(self):
        from toontown.expansion.Treasures import SPAWNS, model_path
        if self.zoneId in SPAWNS:
            self.modelPath=model_path(self.zoneId)
        DistributedSZTreasure.DistributedSZTreasure.announceGenerate(self)
