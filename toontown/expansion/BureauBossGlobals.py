"""Shared geometry and encounter rules. No client-supplied damage values."""
import math

HOOD = 14000
NAME = 'The Director General'
ROOM = 'The Final Review Chamber'
MAX_PLAYERS = 8
BOSS_POS = (12, 65, 6, 0, 0, 0)
BATTLE_ORIGIN = (0, -12, 0, -90, 0, 0)
ELEVATOR_POS = (-56, -78, 0, 180, 0, 0)
# IDs are stable across the client, AI and production scene builder.
STATIONS = ((-59, -20, 0), (59, -12, 0), (-29, 35, 0),
            (39, 35, 0), (-8, 40, 0))
STATION_NAMES = ('Collect paperwork', 'Collect paperwork', 'Feed left sorter',
                 'Feed right sorter', 'Stamp rejection')
USE_RADIUS = 10
COPIES_PER_SORTER = 3
EXPOSE_SECONDS = 16
HIT_DAMAGE = 25
MAX_DAMAGE = 100
STAMP_DAMAGE = 12
STAMP_RADIUS = 11
STAMP_WARNING = 3
STAMP_INTERVAL = 9
STAMP_TARGETS = ((-34, -22), (28, -14), (-18, 27), (38, 23), (0, -48))


def wave_roster(rng, wave, players):
    """Native internal levels 8..11 display as levels 9..12; legal rank ranges."""
    count = max(4, min(8, players + 3))
    result = []
    for _ in range(count):
        rank = rng.choice((6, 7, 8))
        level = rng.randint(max(8, rank - 1), min(11, rank + 3))
        result.append((rank, level, wave == 2))
    return result


class PaperworkCycle:
    """Pure authoritative rules; the AI owns time, identity and position."""
    def __init__(self):
        self.loads = [0, 0]
        self.carrying = set()
        self.last_use = {}
        self.exposed_until = 0
        self.damage = 0
        self.cycle = 0

    def expire(self, now):
        if self.exposed_until and now >= self.exposed_until:
            self.loads[:] = [0, 0]
            self.exposed_until = 0
            self.cycle += 1
            return True
        return False

    def use(self, avatar, station, position, now):
        self.expire(now)
        if (station not in range(len(STATIONS)) or self.damage >= MAX_DAMAGE or
                now - self.last_use.get(avatar, -100) < 1 or
                not all(math.isfinite(v) for v in position) or
                math.dist(position, STATIONS[station]) > USE_RADIUS):
            return False
        if station < 2:
            if avatar in self.carrying or self.exposed_until:
                return False
            self.carrying.add(avatar)
        elif station < 4:
            side = station - 2
            if avatar not in self.carrying or self.exposed_until or self.loads[side] >= COPIES_PER_SORTER:
                return False
            self.carrying.remove(avatar)
            self.loads[side] += 1
            if self.loads == [COPIES_PER_SORTER] * 2:
                self.exposed_until = now + EXPOSE_SECONDS
        else:
            if not self.exposed_until or now >= self.exposed_until:
                return False
            self.damage += HIT_DAMAGE
            self.loads[:] = [0, 0]
            self.carrying.clear()
            self.exposed_until = 0
            self.cycle += 1
        self.last_use[avatar] = now
        return True

    def remove(self, avatar):
        self.carrying.discard(avatar)
        self.last_use.pop(avatar, None)
