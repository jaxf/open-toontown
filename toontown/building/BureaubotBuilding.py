"""Archive-office facade on the standard Cog building collision/door shell."""
from panda3d.core import TextNode
from toontown.suit.BureaubotModels import _box, build_logo


def decorate_building(building):
    """Modify only a copied landmark, preserving its doors/sign/collision nodes."""
    shell = building.find('**/*_building')
    if not shell.isEmpty():
        shell.setColorScale(.78,.62,.47,1)
    front = building.find('**/*_front')
    if not front.isEmpty():
        front.setColorScale(.78,.62,.47,1)
    details = building.attachNewNode('bureaubot-archive-facade')
    steel = (.34,.37,.38,1)
    copper = (.44,.22,.10,1)
    inset = (.22,.24,.24,1)
    silver = (.72,.75,.74,1)
    _box(details,'archive-backing',(15,-3.18,30),(30,.22,21.7),steel)
    # Stacked filing drawers above the original shop sign and elevator opening.
    for floor, z in enumerate((23.,30.,37.)):
        for column,x in enumerate((5.,15.,25.)):
            _box(details,'drawer-frame-%s-%s' % (floor,column),(x,-3.30,z),(9.2,.22,6.1),steel)
            _box(details,'drawer-panel',(x,-3.47,z),(8.5,.22,5.4),copper)
            _box(details,'label-recess',(x,-3.62,z+1.25),(3.4,.10,.85),inset)
            _box(details,'file-label',(x,-3.69,z+1.25),(2.9,.04,.50),silver)
            _box(details,'handle-shadow',(x,-3.61,z-.75),(4.3,.17,.60),inset)
            _box(details,'drawer-handle',(x,-3.94,z-.55),(3.7,.45,.24),silver)
    for x in (.2,29.8):
        _box(details,'archive-pilaster',(x,-3.48,24.),(.5,.5,34.),steel)
    _box(details,'department-header',(15,-3.50,18.9),(29,.4,2.5),inset)
    label=TextNode('bureau-department-name')
    label.setText('B U R E A U B O T S')
    label.setAlign(TextNode.ACenter)
    label.setTextColor(.91,.88,.78,1)
    text=details.attachNewNode(label)
    text.setPos(15,-3.75,18.5)
    text.setScale(1.45)
    badge=build_logo()
    badge.reparentTo(details)
    badge.setPos(15,-3.6,43.)
    badge.setScale(4.8)
    details.setTag('department','u')
    return building


def add_elevator_badge(elevator):
    badge=build_logo()
    badge.reparentTo(elevator.find('**/elevator'))
    badge.setPos(0,6.79,6.8)
    badge.setScale(3)
    return badge
