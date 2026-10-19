import math
from panda3d.core import CardMaker, TextNode, Point3
from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton
from direct.task import Task
from toontown.toon import NPCToons
from toontown.hood import ZoneUtil
from toontown.toonbase import ToontownGlobals
from toontown.quest import Quests
from toontown.suit import SuitPlannerBase
from . import QuestMapGlobals

class QuestMap(DirectFrame):

    def __init__(self, av, **kw):
        DirectFrame.__init__(self, relief=None, sortOrder=50)
        self.initialiseoptions(QuestMap)
        self.container = DirectFrame(parent=self, relief=None)
        self.marker = DirectFrame(parent=self.container, relief=None)
        self.cogInfoFrame = DirectFrame(parent=self.container, relief=None)
        self.cogInfoFrame['relief'] = 'flat'
        self.cogInfoFrame['frameColor'] = (1,.97,.80,.94)
        self.cogInfoFrame['frameSize'] = (-3,3,-1.55,1.55)
        self.cogInfoFrame.setScale(0.05)
        self.cogInfoFrame.setPos(0,0,.6)
        self.buildingMarkers = []
        self.av = av
        self.wantToggle = False
        if base.config.GetBool('want-toggle-quest-map', True):
            self.wantToggle = True
        self.updateMarker = True
        self.cornerPosInfo = None
        self.hqPosInfo = None
        self.fishingSpotInfo = None
        self.load()
        self.setScale(1.5)
        self.hoodId = None
        self.zoneId = None
        self.suitPercentage = {}
        for currHoodInfo in SuitPlannerBase.SuitPlannerBase.SuitHoodInfo:
            tracks = currHoodInfo[SuitPlannerBase.SuitPlannerBase.SUIT_HOOD_INFO_TRACK]
            self.suitPercentage[currHoodInfo[SuitPlannerBase.SuitPlannerBase.SUIT_HOOD_INFO_ZONE]] = tracks

        return

    def load(self):
        gui = loader.loadModel('phase_4/models/questmap/questmap_gui')
        icon = gui.find('**/tt_t_gui_qst_arrow')
        iconNP = aspect2d.attachNewNode('iconNP')
        icon.reparentTo(iconNP)
        icon.setR(90)
        self.marker['geom'] = iconNP
        self.marker['image'] = iconNP
        self.marker.setScale(0.05)
        iconNP.removeNode()
        self.mapOpenButton = DirectButton(image=(gui.find('**/tt_t_gui_qst_mapClose'), gui.find('**/tt_t_gui_qst_mapClose'), gui.find('**/tt_t_gui_qst_mapTryToOpen')), relief=None, pos=(1.25, 0, -0.63), scale=0.205, command=self.show)
        self.mapCloseButton = DirectButton(image=(gui.find('**/tt_t_gui_qst_mapOpen'), gui.find('**/tt_t_gui_qst_mapOpen'), gui.find('**/tt_t_gui_qst_mapTryToClose')), relief=None, pos=(1.25, 0, -0.63), scale=0.205, command=self.hide)
        self.mapOpenButton.hide()
        self.mapCloseButton.hide()
        gui.removeNode()
        icons = loader.loadModel('phase_3/models/gui/cog_icons')
        from toontown.suit.BureaubotModels import build_logo
        emblems=[icons.find('**/'+name) for name in ('CorpIcon','LegalIcon','MoneyIcon','SalesIcon')]
        emblems.append(build_logo())
        self.cogInfoLabels=[]
        for i,emblem in enumerate(emblems):
            x,z=((-1.65,.95),(1.35,.95),(-1.65,0),(1.35,0),(0,-.95))[i]
            label=DirectLabel(parent=self.cogInfoFrame,text='',text_fg=(.10,.13,.16,1),
                text_pos=(.40,-.20),text_scale=.65,text_align=TextNode.ALeft,
                geom=emblem,geom_pos=(-.20,0,0),geom_scale=.67,relief=None,pos=(x,0,z))
            self.cogInfoLabels.append(label)
        self.cInfo,self.lInfo,self.mInfo,self.sInfo,self.uInfo=self.cogInfoLabels
        emblems[-1].removeNode()
        icons.removeNode()
        return

    def updateCogInfo(self):
        currPercentage = self.suitPercentage.get(self.zoneId)
        if currPercentage is None:
            return
        for label,percent in zip(self.cogInfoLabels,currPercentage):
            label['text']='%s%%'%percent
        return

    def destroy(self):
        self.ignore('questPageUpdated')
        self.mapOpenButton.destroy()
        self.mapCloseButton.destroy()
        del self.mapOpenButton
        del self.mapCloseButton
        DirectFrame.destroy(self)

    def putBuildingMarker(self, pos, hpr = (0, 0, 0), mapIndex = None):
        if pos is None:
            return
        marker = DirectLabel(parent=self.container, text='', text_pos=(-0.05, -0.15), text_fg=(1, 1, 1, 1), relief=None)
        gui = loader.loadModel('phase_4/models/parties/schtickerbookHostingGUI')
        icon = gui.find('**/startPartyButton_inactive')
        iconNP = aspect2d.attachNewNode('iconNP')
        icon.reparentTo(iconNP)
        icon.setX(-12.0792 / 30.48)
        icon.setZ(-9.7404 / 30.48)
        marker['text'] = '%s' % mapIndex
        marker['text_scale'] = 0.7
        marker['image'] = iconNP
        marker['image_color'] = (1, 0, 0, 1)
        marker['image_scale'] = 6
        marker.setScale(0.05)
        relX, relY = self.transformAvPos(pos)
        marker.setPos(relX, 0, relY)
        self.buildingMarkers.append(marker)
        iconNP.removeNode()
        gui.removeNode()
        return

    def updateQuestInfo(self):
        for marker in self.buildingMarkers:
            marker.destroy()

        self.buildingMarkers = []
        dnaStore = base.cr.playGame.dnaStore
        for questIndex in list(self.av.questPage.quests.keys()):
            questDesc = self.av.questPage.quests.get(questIndex)
            if questDesc is None:
                continue
            mapIndex = questIndex + 1
            questId, fromNpcId, toNpcId, rewardId, toonProgress = questDesc
            quest = Quests.getQuest(questId)
            fComplete = quest.getCompletionStatus(self.av, questDesc) == Quests.COMPLETE
            if not fComplete:
                if quest.getType() == Quests.RecoverItemQuest:
                    if quest.getHolder() == Quests.AnyFish:
                        self.putBuildingMarker(self.fishingSpotInfo, mapIndex=mapIndex)
                    continue
                elif quest.getType() != Quests.DeliverGagQuest and quest.getType() != Quests.DeliverItemQuest and quest.getType() != Quests.VisitQuest and quest.getType() != Quests.TrackChoiceQuest:
                    continue
            if toNpcId == Quests.ToonHQ:
                self.putBuildingMarker(self.hqPosInfo, mapIndex=mapIndex)
            else:
                npcZone = NPCToons.getNPCZone(toNpcId)
                hoodId = ZoneUtil.getCanonicalHoodId(npcZone)
                branchId = ZoneUtil.getCanonicalBranchZone(npcZone)
                if self.hoodId == hoodId and self.zoneId == branchId:
                    for blockIndex in range(dnaStore.getNumBlockTitles()):
                        blockNumber = dnaStore.getTitleBlockAt(blockIndex)
                        zone = dnaStore.getZoneFromBlockNumber(blockNumber)
                        branchZone = zone - zone % 100
                        finalZone = branchZone + 500 + blockNumber
                        buildingType = dnaStore.getBlockBuildingType(blockNumber)
                        if npcZone == finalZone:
                            self.putBuildingMarker(dnaStore.getDoorPosHprFromBlockNumber(blockNumber).getPos(), dnaStore.getDoorPosHprFromBlockNumber(blockNumber).getHpr(), mapIndex=mapIndex)

        return

    def transformAvPos(self, pos):
        if self.cornerPosInfo is None:
            return (0, 0)
        topRight = self.cornerPosInfo[0]
        bottomLeft = self.cornerPosInfo[1]
        relativeX = (pos.getX() - bottomLeft.getX()) / (topRight.getX() - bottomLeft.getX()) - 0.5
        relativeY = (pos.getY() - bottomLeft.getY()) / (topRight.getY() - bottomLeft.getY()) - 0.5
        return (relativeX, relativeY)

    def update(self, task):
        if self.av:
            if self.updateMarker:
                relX, relY = self.transformAvPos(self.av.getPos())
                self.marker.setPos(relX, 0, relY)
                self.marker.setHpr(0, 0, -180 - self.av.getH())
        i = 0
        for buildingMarker in self.buildingMarkers:
            buildingMarker.setScale((math.sin(task.time * 16.0 + i * math.pi / 3.0) + 1) * 0.005 + 0.04)
            i = i + 1

        return Task.cont

    def updateMap(self):
        if self.av:
            try:
                hoodId = ZoneUtil.getCanonicalHoodId(self.av.getLocation()[1])
                zoneId = ZoneUtil.getCanonicalBranchZone(self.av.getLocation()[1])
                from toontown.expansion import ExpansionGlobals as E
                if zoneId in E.STREETS:
                    self.loadExpansionMap(hoodId,zoneId)
                    return
                if hoodId in E.NEIGHBORHOODS:
                    self.stop()
                    return
                mapsGeom = loader.loadModel('phase_4/models/questmap/%s_maps' % ToontownGlobals.dnaMap[hoodId])
                mapImage = mapsGeom.find('**/%s_%s_english' % (ToontownGlobals.dnaMap[hoodId], zoneId))
                if not mapImage.isEmpty():
                    self.container['image'] = mapImage
                    self.resetFrameSize()
                    self.cornerPosInfo = QuestMapGlobals.CornerPosTable.get('%s_%s_english' % (ToontownGlobals.dnaMap[hoodId], zoneId))
                    self.hqPosInfo = QuestMapGlobals.HQPosTable.get('%s_%s_english' % (ToontownGlobals.dnaMap[hoodId], zoneId))
                    self.fishingSpotInfo = QuestMapGlobals.FishingSpotPosTable.get('%s_%s_english' % (ToontownGlobals.dnaMap[hoodId], zoneId))
                    self.cogInfoPos = QuestMapGlobals.CogInfoPosTable.get('%s_%s_english' % (ToontownGlobals.dnaMap[hoodId], zoneId))
                    self.cogInfoFrame.setPos(self.cogInfoPos)
                    self.hide()
                    self.hoodId = hoodId
                    self.zoneId = zoneId
                    self.updateQuestInfo()
                    self.updateCogInfo()
                    taskMgr.add(self.update, 'questMapUpdate')
                else:
                    self.stop()
                mapsGeom.removeNode()
            except:
                self.stop()

    def loadExpansionMap(self,hoodId,zoneId):
        from .ExpansionStreetMap import build_map,bounds
        from toontown.expansion.Services import placements
        mapImage=build_map(zoneId)
        self.container['image']=mapImage
        # Keep the source NodePath valid: show/hide use the image option to
        # decide whether the bottom-right map toggle should be available.
        mapImage.detachNode()
        self.resetFrameSize()
        self.cornerPosInfo=bounds(zoneId)
        self.hqPosInfo=Point3(*placements(zoneId)['hq'][:3])
        self.fishingSpotInfo=None
        self.cogInfoFrame.setPos(.40,0,-.33)
        self.hoodId,self.zoneId=hoodId,zoneId
        self.hide()
        self.updateQuestInfo()
        self.updateCogInfo()
        taskMgr.remove('questMapUpdate')
        taskMgr.add(self.update,'questMapUpdate')

    def start(self):
        self.container.show()
        self.accept('questPageUpdated', self.updateMap)
        self.handleMarker()
        self.updateMap()

    def initMarker(self, task):
        if self.av:
            if not hasattr(base.cr.playGame.getPlace(), 'isInterior') or not base.cr.playGame.getPlace().isInterior:
                relX, relY = self.transformAvPos(self.av.getPos())
                self.marker.setPos(relX, 0, relY)
                self.marker.setHpr(0, 0, -180 - self.av.getH())
            self.marker['geom_scale'] = 1.4 * task.time % 0.5 * 10 + 1
            self.marker['geom_color'] = (1,
             1,
             1,
             0.8 - 1.4 * task.time % 0.5 * 2 / 0.8 + 0.2)
        if task.time < 1:
            return Task.cont
        else:
            self.marker['geom_color'] = (1, 1, 1, 0)
            return Task.done

    def show(self):
        taskMgr.add(self.initMarker, 'questMapInit')
        DirectFrame.show(self)
        self.mapOpenButton.hide()
        if self.container['image']:
            self.mapCloseButton.show()

    def hide(self):
        taskMgr.remove('questMapInit')
        DirectFrame.hide(self)
        if self.container['image']:
            self.mapOpenButton.show()
        self.mapCloseButton.hide()

    def toggle(self):
        if self.isHidden():
            self.show()
        else:
            self.hide()

    def obscureButton(self):
        self.mapOpenButton.hide()
        self.mapCloseButton.hide()

    def stop(self):
        self.container['image'] = None
        for marker in self.buildingMarkers:
            marker.destroy()

        self.buildingMarkers = []
        self.container.hide()
        self.hide()
        self.obscureButton()
        self.ignore('questPageUpdated')
        taskMgr.remove('questMapUpdate')
        return

    def handleMarker(self):
        if hasattr(base.cr.playGame.getPlace(), 'isInterior') and base.cr.playGame.getPlace().isInterior:
            self.updateMarker = False
        else:
            self.updateMarker = True

    def acceptOnscreenHooks(self):
        if self.wantToggle:
            self.accept(ToontownGlobals.MapHotkey, self.toggle)
        else:
            self.accept(ToontownGlobals.MapHotkeyOn, self.show)
            self.accept(ToontownGlobals.MapHotkeyOff, self.hide)
        self.updateMap()

    def ignoreOnscreenHooks(self):
        self.ignore(ToontownGlobals.MapHotkey)
        self.ignore(ToontownGlobals.MapHotkeyOn)
        self.ignore(ToontownGlobals.MapHotkeyOff)
        self.obscureButton()
