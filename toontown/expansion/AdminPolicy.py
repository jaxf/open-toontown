"""Pure server authorization policy, shared with focused regression tests."""
from .ExpansionGlobals import destinations

ADMIN_LEVEL = 300


def validate_request(toon, action, zone):
    if toon is None or toon.getAccessLevel() < ADMIN_LEVEL:
        return 'Admin access is required.'
    if action not in ('max', 'teleport'):
        return 'Unknown admin action.'
    if action == 'teleport' and zone not in destinations():
        return 'That destination is not available.'
    return None
