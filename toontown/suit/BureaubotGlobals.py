"""Shared, deterministic Bureaubot data (safe to import on client and AI)."""
DEPT = 'u'
# DNA names must fit the existing three-byte wire field. Append, never reorder.
CODES = ('ps', 'rst', 'dj', 'cw', 'rt', 'bn', 'gk', 'hho')
CATALOG = (
    ('paper-shuffler', 'Paper Shuffler', 'c', .96),
    ('rubber-stamp', 'Rubber Stamp', 'c', .96),
    ('desk-jockey', 'Desk Jockey', 'a', .90),
    ('clock-watcher', 'Clock Watcher', 'b', .98),
    ('red-tape', 'Red Tape', 'b', 1.04),
    ('bottleneck', 'Bottleneck', 'b', 1.20),
    ('gatekeeper', 'Gatekeeper', 'a', 1.17),
    ('head-honcho', 'Head Honcho', 'c', 1.70),
)
BY_CODE = dict(zip(CODES, CATALOG))
MOVE_POOLS = (
    ('Shred', 'ClipOnTie', 'PoundKey'),
    ('RubberStamp', 'FingerWag', 'Watercooler'),
    ('Rolodex', 'RubberStamp', 'DoubleTalk'),
    ('HangUp', 'WriteOff', 'Spin'),
    ('RedTape', 'FingerWag', 'MumboJumbo'),
    ('FillWithLead', 'ParadigmShift', 'WriteOff'),
    ('RestrainingOrder', 'EvictionNotice', 'GlowerPower'),
    ('PowerTrip', 'Schmooze', 'PinkSlip'),
)
# Reuse actual body-compatible animation files, including C's phase 3.5 moves.
ANIMATIONS = {
    'c': (('shredder', 'shredder', 3.5), ('throw-paper', 'throw-paper', 3.5),
          ('phone', 'phone', 3.5), ('rubber-stamp', 'rubber-stamp', 5),
          ('finger-wag', 'finger-wag', 5), ('watercooler', 'watercooler', 5),
          ('magic1', 'magic1', 5), ('speak', 'speak', 5)),
    'b': (('pencil-sharpener', 'pencil-sharpener', 5), ('phone', 'phone', 5), ('hold-pencil', 'hold-pencil', 5),
          ('magic3', 'magic3', 5), ('throw-object', 'throw-object', 5),
          ('finger-wag', 'finger-wag', 5), ('speak', 'speak', 5),
          ('magic2', 'magic2', 5)),
    'a': (('roll-o-dex', 'roll-o-dex', 5), ('rubber-stamp', 'rubber-stamp', 5),
          ('speak', 'speak', 5), ('throw-paper', 'throw-paper', 5),
          ('throw-object', 'throw-object', 5), ('glower', 'glower', 5)),
}


def install_battle_catalog(attributes):
    """Rank-matched classic stats, with three weighted moves per Bureaubot.

    Pools are fixed on both peers; the existing AI attack selector rolls each
    turn. Damage and accuracy rise over the same five relative levels as Cogs.
    Existing MovieSuitAttack dispatch supplies each move's props and audio.
    """
    donors = ('f', 'p', 'ym', 'mm', 'ds', 'hh', 'cr', 'tbc')
    weights = ((50, 45, 40, 35, 30), (30, 30, 30, 30, 30), (20, 25, 30, 35, 40))
    for rank, code in enumerate(CODES):
        entry = dict(attributes[donors[rank]])
        name = BY_CODE[code][1]
        entry.update(name=name, singularname=name, pluralname=name + 's')
        entry['attacks'] = tuple((move,
            tuple(max(1, rank + 1 + level * (1 + rank // 3) + slot)
                  for level in range(5)),
            tuple(min(95, 65 + 5 * level + slot * 5) for level in range(5)),
            weights[slot]) for slot, move in enumerate(MOVE_POOLS[rank]))
        attributes[code] = entry


def street_weights(weights):
    """Add 20% Bureau to classic mixes; preserve explicit five-department mixes."""
    if len(weights)==5:return tuple(weights)
    scaled = [value * 80 // 100 for value in weights]
    # Largest remainder, with stable ordering, keeps the existing 0..99 RNG.
    remainder = 80 - sum(scaled)
    order = sorted(range(len(weights)), key=lambda i: -(weights[i] * 80 % 100))
    for i in order[:remainder]:
        scaled[i] += 1
    return tuple(scaled + [20])
