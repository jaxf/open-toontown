from direct.directnotify import DirectNotifyGlobal
from toontown.suit import SuitDNA
from .CogPageGlobals import (COG_QUOTAS, COG_UNSEEN, COG_BATTLED, COG_DEFEATED,
                             COG_COMPLETE1, COG_COMPLETE2, pad_collection)


class CogPageManagerAI:
    notify = DirectNotifyGlobal.directNotify.newCategory('CogPageManagerAI')

    def __init__(self, air):
        self.air = air

    @staticmethod
    def _eligible(toon, records):
        for record in records:
            name = record.get('type')
            if (name in SuitDNA.suitHeadTypes
                    and toon.doId in record.get('activeToons', ())
                    and not record.get('isVirtual', False)):
                yield SuitDNA.suitHeadTypes.index(name)

    def toonKilledCogs(self, toon, suitsKilled, zoneId):
        size = len(SuitDNA.suitHeadTypes)
        statuses = pad_collection(toon.getCogStatus(), size, COG_UNSEEN)
        counts = pad_collection(toon.getCogCount(), size)
        summons = pad_collection(toon.getCogSummonsEarned(), size)
        changed = False
        for index in self._eligible(toon, suitsKilled):
            rank = index % SuitDNA.suitsPerDept
            oldStatus = statuses[index]
            counts[index] = min(COG_QUOTAS[1][rank], counts[index] + 1)
            status = COG_DEFEATED
            if counts[index] >= COG_QUOTAS[1][rank]:
                status = COG_COMPLETE2
            elif counts[index] >= COG_QUOTAS[0][rank]:
                status = COG_COMPLETE1
            statuses[index] = max(oldStatus, status)
            # One consumable set on first completion; subsequent kills do not
            # refill used summons. CJ rewards/restock retain their usual rules.
            if oldStatus < COG_COMPLETE2 and statuses[index] == COG_COMPLETE2:
                summons[index] |= 7
            changed = True
        if not changed:
            return
        toon.b_setCogSummonsEarned(summons)
        toon.b_setCogStatus(statuses)
        toon.b_setCogCount(counts)
        radars = pad_collection(toon.getCogRadar(), len(SuitDNA.suitDepts))
        buildings = pad_collection(toon.getBuildingRadar(), len(SuitDNA.suitDepts))
        for dept in range(len(SuitDNA.suitDepts)):
            row = statuses[dept * 8:(dept + 1) * 8]
            radars[dept] = int(bool(radars[dept]) or min(row) >= COG_COMPLETE1)
            buildings[dept] = int(bool(buildings[dept]) or min(row) >= COG_COMPLETE2)
        toon.b_setCogRadar(radars)
        toon.b_setBuildingRadar(buildings)

    def toonEncounteredCogs(self, toon, suitsEncountered, zoneId):
        statuses = pad_collection(toon.getCogStatus(), len(SuitDNA.suitHeadTypes), COG_UNSEEN)
        changed = False
        for index in self._eligible(toon, suitsEncountered):
            if statuses[index] < COG_BATTLED:
                statuses[index] = COG_BATTLED
                changed = True
        if changed:
            toon.b_setCogStatus(statuses)
