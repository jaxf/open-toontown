"""Bureaubot finish for the classic textured Cog landmark."""
from toontown.suit.BureaubotModels import build_logo


def decorate_building(building):
    """Modify only a copied landmark, preserving its doors/sign/collision nodes."""
    shell = building.find('**/*_building')
    if not shell.isEmpty():
        shell.setColorScale(1.0,.87,.73,1)
    front = building.find('**/*_front')
    if not front.isEmpty():
        front.setColorScale(1.0,.87,.73,1)
    # Keep the original textured windows, metal trim and silhouette. Department
    # identity comes from the warm metal finish and the standard elevator badge.
    building.setTag('department', 'u')
    return building


def add_elevator_badge(elevator):
    badge=build_logo()
    badge.reparentTo(elevator.find('**/elevator'))
    badge.setPos(0,6.79,6.8)
    badge.setScale(3)
    return badge
