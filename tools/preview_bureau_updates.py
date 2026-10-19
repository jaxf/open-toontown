"""Real UI smoke checks, called after the gallery preview installs OTP adapters."""
import ast
import builtins
import sys
from pathlib import Path
from types import SimpleNamespace
from panda3d.core import Point3
from tools.preview_bureaubots import capture
from tools.preview_cog_gallery import module, ROOT


def preview_updates(app,avatar,out):
    from toontown.toonbase import ToontownGlobals as G
    from toontown.suit import SuitDNA, BureaubotGlobals as B
    from toontown.battle import SuitBattleGlobals as Battle
    from toontown.coghq import CogDisguiseGlobals as C
    from toontown.shtiker.DisguisePage import DisguisePage
    for i,code in enumerate(SuitDNA.suitHeadTypes):Battle.SuitAttributes[code]['level']=i%8
    avatar.cogTypes=[0]*5;avatar.cogLevels=[0]*5
    avatar.cogParts=[0]*5;avatar.cogMerits=[0]*5
    avatar.readyForPromotion=lambda i:avatar.cogMerits[i]>=C.getTotalMerits(avatar,i)
    disguise=DisguisePage();disguise.reparentTo(app.aspect2d);disguise.load();disguise.enter()
    assert len(disguise.tabs)==5
    for i in range(5):disguise.doTab(i)
    capture(app,out/'bureaubot-disguise-empty.png')
    avatar.cogParts=list(C.PartsPerSuitBitmasks);avatar.cogMerits=[0,0,0,0,45]
    disguise.updatePage()
    capture(app,out/'bureaubot-disguise.png')
    assert disguise.cogPartRatio['text']=='17/17'
    assert disguise.cogMeritRatio['text']=='45/100'
    avatar.cogTypes=[7]*5;avatar.cogLevels=[49]*5
    for i in range(5):disguise.doTab(i)
    assert disguise.cogName['text']=='Head Honcho'
    disguise.exit();disguise.unload();disguise.destroy()

    from toontown.expansion import ExpansionGlobals as E
    from toontown.expansion.CogPatrols import hood_rows
    from toontown.expansion.WorldLayout import road_paths
    module('toontown.toonbase.ToonBaseGlobal',base=app)
    G.ExpansionGlobals=E
    G.dnaMap={1000:'donalds_dock',2000:'toontown_central',3000:'the_burrrgh',
              4000:'minnies_melody_land',5000:'daisys_garden',9000:'donalds_dreamland'}
    module('toontown.hood.ZoneUtil',getCanonicalHoodId=lambda z:E.hood_id(z),
           getCanonicalBranchZone=lambda z:z-z%100)
    module('toontown.quest.Quests')
    tree=ast.parse((ROOT/'toontown/suit/SuitPlannerBase.py').read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
    rows=ast.literal_eval(next(n.value for n in cls.body if isinstance(n,ast.Assign)
        and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='SuitHoodInfo'))+hood_rows()
    for row in rows:row[8]=B.street_weights(row[8])
    module('toontown.suit.SuitPlannerBase',SuitPlannerBase=SimpleNamespace(
        SuitHoodInfo=rows,SUIT_HOOD_INFO_TRACK=8,SUIT_HOOD_INFO_ZONE=0))
    from toontown.quest.QuestMap import QuestMap
    avatar.questPage=SimpleNamespace(quests={})
    zone=[2100]
    avatar.getLocation=lambda:(1,zone[0])
    avatar.getPos=lambda:Point3(*E.spawn_point(zone[0])[:3]) if zone[0] in E.STREETS else Point3(0,0,0)
    avatar.getH=lambda:0
    app.cr.playGame.getPlace=lambda:SimpleNamespace(isInterior=False)
    street=QuestMap(avatar)
    # These are walking-HUD overlays, never book pages. Stage a real street
    # behind the actual QuestMap widget and its original bottom-right toggle.
    from toontown.expansion.ExpansionScene import build_scene
    from panda3d.core import CullBinManager
    for name,order in [('ground',14),('shadow',15)]:
        CullBinManager.getGlobalPtr().addBin(name,CullBinManager.BTFixed,order)
    app.previewBook.hide()
    scene=build_scene(19100);scene.reparentTo(app.render)
    app.setBackgroundColor(.38,.67,.89,1)
    app.camera.setPos(0,-535,8);app.camera.lookAt(0,-430,12)
    app.camLens.setNearFar(1,2200);app.camLens.setFov(65)
    street.start();street.show()
    assert [label['text'] for label in street.cogInfoLabels]==['20%']*5
    capture(app,out/'street-map-classic.png')
    from toontown.quest.QuestMapGlobals import CornerPosTable
    for key in CornerPosTable:
        if not key.split('_')[-2].isdigit():continue
        current=int(key.split('_')[-2])
        zone[0]=current;street.start();street.show()
        street.update(SimpleNamespace(time=0))
        assert street.zoneId==current,current
        assert street.uInfo['text']=='20%'
        assert sum(int(label['text'][:-1]) for label in street.cogInfoLabels)==100
    for current in E.STREETS:
        zone[0]=current;street.start();street.show()
        street.update(SimpleNamespace(time=0))
        assert street.container['image'] is not None,current
        assert street.zoneId==current
        assert len(street.cogInfoLabels)==5
        assert sum(int(label['text'][:-1]) for label in street.cogInfoLabels)==100
        assert street.uInfo['text']=='20%'
        assert street.hqPosInfo is not None
        assert not street.mapCloseButton.isHidden()
        low=street.cornerPosInfo[1];high=street.cornerPosInfo[0]
        for path in road_paths(current):
            for x,y in path:
                mx,my=street.transformAvPos(Point3(x,y,0))
                assert -.5<=mx<=.5 and -.5<=my<=.5
        if current==19100:capture(app,out/'street-map-root-route.png')
        if current==63100:capture(app,out/'street-map-encore-avenue.png')
    # Exercise the live lower-right toggle in both directions.
    street.mapCloseButton['command']()
    assert street.container.isHidden()
    assert not street.mapOpenButton.isHidden()
    capture(app,out/'street-map-toggle-closed.png')
    street.mapOpenButton['command']()
    assert not street.container.isHidden()
    assert not street.mapCloseButton.isHidden()
    street.stop();street.destroy()
    scene.removeNode();app.previewBook.show()
    app.setBackgroundColor(.05,.13,.35,1)

    from toontown.expansion.ExpansionMap import ExpansionMap
    from toontown.toontowngui.CogButtons import fast_forward_button
    avatar.getTeleportAccess=lambda:list(E.destinations())
    app.cr.playGame.getPlaceId=lambda:E.ACORN
    world=ExpansionMap(app.aspect2d,lambda zone:None)
    world.refresh();world.describe(E.HUSH)
    capture(app,out/'world-map-hover.png')
    world.destroy()
    button=fast_forward_button(app.aspect2d,lambda:None)
    button.setPos(0,0,0);button.setScale(2)
    capture(app,out/'fast-forward-button.png');button.destroy()
    check_chat(app,avatar)
    print('Updates: five disguise tabs; eight expansion maps; five percentages; chat keyboard/send/cancel checks passed.')


def check_chat(app,avatar):
    from direct.fsm import ClassicFSM, State
    from direct.showbase.DirectObject import DirectObject
    from otp.otpbase import OTPGlobals
    from toontown.toonbase import TTLocalizer
    from toontown.expansion import ControlSettings as Controls
    OTPGlobals.getInterfaceFont=lambda:app.loader.loadFont(TTLocalizer.InterfaceFont)
    from toontown.chat.TTChatInputNormal import TTChatInputNormal
    app.settings=SimpleNamespace(getSetting=lambda key,default:default)
    avatar.avatarControlsEnabled=True
    avatar.disableAvatarControls=lambda:setattr(avatar,'avatarControlsEnabled',False)
    avatar.enableAvatarControls=lambda:setattr(avatar,'avatarControlsEnabled',True)
    avatar.getTransitioning=lambda:False
    app.cr.playGame.getPlace=lambda:SimpleNamespace(fsm=SimpleNamespace(
        getCurrentState=lambda:SimpleNamespace(getName=lambda:'walk')))
    sent=[]
    app.talkAssistant=SimpleNamespace(findName=lambda *_:None,sendOpenTalk=sent.append)
    tree=ast.parse((ROOT/'otp/chat/ChatManager.py').read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
    selected=['enterMainMenu','exitMainMenu','enterNormalChat','exitNormalChat']
    ns={}
    for node in cls.body:
        if isinstance(node,ast.FunctionDef) and node.name in selected:
            exec(compile(ast.Module(body=[node],type_ignores=[]),'chat-method','exec'),ns)
    Manager=type('Manager',(DirectObject,),{name:ns[name] for name in selected})
    manager=Manager();manager.checkObscurred=lambda:None
    manager.localAvatar=avatar;manager.cr=SimpleNamespace(wantMagicWords=False)
    avatar.canChat=lambda:True;manager.wantBackgroundFocus=True;manager.execChat=False
    manager.normalButton=manager.scButton=SimpleNamespace(hide=lambda:None)
    manager.chatInputWhiteList=SimpleNamespace(isActive=lambda:False)
    manager.chatInputNormal=TTChatInputNormal(manager)
    avatar.chatMgr=manager
    manager.fsm=ClassicFSM.ClassicFSM('test-chat',[
        State.State('off',lambda:None,lambda:None),
        State.State('mainMenu',manager.enterMainMenu,manager.exitMainMenu),
        State.State('normalChat',manager.enterNormalChat,manager.exitNormalChat)],'off','off')
    manager.fsm.enterInitialState();manager.fsm.request('mainMenu')
    assert manager.chatInputNormal.chatEntry['backgroundFocus']==1
    shortcuts=Controls.Shortcuts()
    # Opening Enter must not submit. Submitting Enter must not reopen on key-up.
    originalWindow=app.win
    app.win=SimpleNamespace(closeIme=lambda:None)  # Offscreen buffers have no IME.
    app.messenger.send('enter');assert manager.fsm.getCurrentState().getName()=='mainMenu'
    app.messenger.send('enter-up');assert manager.chatInputNormal.chatEntry['focus']==1
    assert not avatar.avatarControlsEnabled
    manager.chatInputNormal.chatEntry.enterText('Hello Toontown!')
    app.messenger.send('enter')
    manager.chatInputNormal.sendChat(manager.chatInputNormal.chatEntry.get())
    app.messenger.send('enter-up')
    assert sent==['Hello Toontown!']
    assert manager.fsm.getCurrentState().getName()=='mainMenu'
    assert avatar.avatarControlsEnabled
    app.messenger.send('enterNormalChat')
    manager.chatInputNormal.cancelButtonPressed()
    assert manager.fsm.getCurrentState().getName()=='mainMenu'
    app.settings.getSetting=lambda key,default: {'forward':'w'} if key=='key-bindings' else default
    assert not Controls.type_to_chat_enabled()
    shortcuts.destroy();manager.ignoreAll();manager.chatInputNormal.delete()
    app.win=originalWindow
