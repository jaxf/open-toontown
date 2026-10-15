"""Persistent normal-play controls shared by the book, walkers and camera."""
from direct.showbase.DirectObject import DirectObject
from direct.showbase.ShowBaseGlobal import base
from direct.showbase.MessengerGlobal import messenger

BINDINGS = (
    ('forward','Move forward','arrow_up'),('reverse','Move backward','arrow_down'),
    ('turnLeft','Turn left / air steering','arrow_left'),('turnRight','Turn right / air steering','arrow_right'),
    ('jump','Jump','control'),('sprint','Hold to sprint','shift'),
    ('cameraNext','Next camera view','tab'),('cameraPrevious','Previous camera view','shift-tab'),
    ('cameraUp','Look up','page_up'),('cameraDown','Look down','page_down'),
    ('book','Shticker Book','f8'),('options','Options / close book','escape'),
    ('chat','Type chat','enter'),('pie','Throw pie (where available)','insert'),
    ('friends','Friends list','f7'),('quests','Hold to show tasks','end'),
    ('inventory','Hold to show gags','home'),('map','Street map','alt'),
    ('screenshot','Save screenshot','f9'),
    ('thinkPosition','Show position','shift-f1'),('marker','Place marker (developer)','f2'),
    ('cameraPosition','Print camera position','f12'),
    ('sync','Synchronize client','shift-f6'),('garbage','Debug memory','shift-f11'),
)
DEFAULTS={action:key for action,label,key in BINDINGS}
EVENTS={'cameraNext':'toon-camera-next','cameraPrevious':'toon-camera-previous',
        'cameraUp':'toon-camera-up','cameraDown':'toon-camera-down',
        'book':'toon-book','options':'toon-options',
        'friends':'toon-friends','quests':'toon-quests','inventory':'toon-inventory',
        'map':'toon-map','screenshot':'toon-screenshot','thinkPosition':'toon-think-position',
        'marker':'toon-marker','cameraPosition':'toon-print-camera','sync':'toon-sync','garbage':'toon-memory'}
HELD={'quests','inventory','map'}


def keys():
    saved=base.settings.getSetting('key-bindings',{})
    return {action:saved.get(action,key) for action,key in DEFAULTS.items()}


def field_of_view():
    return max(50,min(100,float(base.settings.getSetting('camera-fov',70))))


class Shortcuts(DirectObject):
    def __init__(self):
        self.accept('controls-changed',self.refresh)
        self.events=[]
        self.refresh()

    def refresh(self):
        for event in self.events:self.ignore(event)
        mapping=keys();self.events=[]
        for action in list(EVENTS)+['chat','pie']:
            key=mapping[action]
            if action=='pie':
                self.accept('time-'+key,self.pie,[False])
                self.accept('time-'+key+'-up',self.pie,[True])
                self.events.extend(['time-'+key,'time-'+key+'-up'])
            else:
                self.accept(key,self.dispatch,[action]);self.events.append(key)
                if action in HELD:
                    self.accept(key+'-up',messenger.send,[EVENTS[action]+'-up'])
                    self.events.append(key+'-up')

    def typing(self):
        avatar=getattr(base,'localAvatar',None)
        chat=getattr(avatar,'chatMgr',None)
        entry=getattr(getattr(chat,'chatInputNormal',None),'chatEntry',None)
        return entry is not None and entry['focus']

    def dispatch(self,action):
        if getattr(base,'capturingControl',False) or self.typing():return
        if action=='chat':
            avatar=getattr(base,'localAvatar',None)
            chat=getattr(avatar,'chatMgr',None)
            if chat and chat.fsm.getCurrentState().getName()=='mainMenu':
                chat.fsm.request('normalChat')
        else:messenger.send(EVENTS[action])

    def pie(self,release,time):
        if not getattr(base,'capturingControl',False) and not self.typing():
            messenger.send('toon-pie-up' if release else 'toon-pie',[time])

    def destroy(self):
        self.ignoreAll()
