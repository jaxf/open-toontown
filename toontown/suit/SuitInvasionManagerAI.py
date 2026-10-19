"""District invasions shared by ordinary and summoned Cogs of every department."""
from direct.directnotify import DirectNotifyGlobal
from direct.showbase.DirectObject import DirectObject
from direct.task.TaskManagerGlobal import taskMgr
from . import SuitDNA


class SuitInvasionManagerAI(DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('SuitInvasionManagerAI')
    # Wire values from ToontownGlobals, kept here without client-only imports.
    BEGIN, UPDATE, END, BULLETIN = range(4)

    def __init__(self, air):
        self.air = air
        self.cogType = None
        self.numRemaining = 0
        self.skeleton = False
        self.taskName = 'suit-invasion-%s' % id(self)
        self.accept('avatarEntered', self.sendCurrentInvasion)

    def getInvadingCog(self):
        return self.cogType, int(self.skeleton)

    def getInvading(self):
        return self.cogType is not None

    def _announce(self, status, avatarId=None):
        news = self.air.newsManager
        if news is None or self.cogType is None:
            return
        args = [status, self.cogType, self.numRemaining, int(self.skeleton)]
        if avatarId is None:
            news.sendUpdate('setInvasionStatus', args)
        else:
            news.sendUpdateToAvatarId(avatarId, 'setInvasionStatus', args)

    def startInvasion(self, cogType, numCogs, skeleton=False):
        if self.getInvading() or cogType not in SuitDNA.suitHeadTypes or numCogs <= 0:
            return False
        self.cogType = cogType
        self.numRemaining = int(numCogs)
        self.skeleton = bool(skeleton)
        self._announce(self.BEGIN)
        taskMgr.doMethodLater(1800, self._timeout, self.taskName)
        return True

    def sendCurrentInvasion(self, toon):
        if self.getInvading():
            self._announce(self.BULLETIN, toon.doId)

    def cogDefeated(self, cogType, skeleton=False):
        if cogType != self.cogType or bool(skeleton) != self.skeleton:
            return
        self.numRemaining = max(0, self.numRemaining - 1)
        if self.numRemaining == 0:
            self.stopInvasion()
        elif self.numRemaining % 100 == 0:
            self._announce(self.UPDATE)

    def stopInvasion(self):
        if not self.getInvading():
            return
        taskMgr.remove(self.taskName)
        self._announce(self.END)
        self.cogType = None
        self.numRemaining = 0
        self.skeleton = False

    def _timeout(self, task):
        self.stopInvasion()
        return task.done

    def delete(self):
        self.stopInvasion()
        self.ignoreAll()
