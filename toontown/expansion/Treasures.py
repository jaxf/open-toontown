"""Playground Laff treasures: acorns, taffy, moons, movie stars and canteens."""
SPAWNS={
    19000:[(-20,-67),(28,-22),(-37,20),(20,70),(70,15),(-44,55)],
    61000:[(-30,-78),(-25,-15),(-111,25),(16,-60),(20,51),(63,75)],
    62000:[(25,-103),(51,-48),(9,8),(-33,30),(53,54),(-114,55)],
    63000:[(0,-120),(-13,-50),(22,25),(-47,49),(75,-70),(122,55)],
    64000:[(-23,-112),(-45,-50),(-75,-1),(-117,50),(23,37),(92,-54)],
}


def model_path(zone):
    return 'assets/expansion/models/laff_%s.bam'%zone


_MODEL_PATHS = frozenset(model_path(zone) for zone in SPAWNS)
_models = {}


def is_expansion_model(path):
    return path in _MODEL_PATHS


def load_model(loader, path):
    """Own the five pickup prototypes separately from DNA and Panda's caches."""
    if path not in _MODEL_PATHS:
        raise ValueError('Unknown expansion treasure model: '+path)
    if path not in _models:
        # These generated BAMs load successfully as uncached hood models on
        # the Mac engine, but the normal cached treasure load has segfaulted.
        # Bypass both disk and RAM model caches, retaining a Python reference
        # so subsequent pickups and holiday replacements reuse the prototype.
        print('[Expansion treasure] Loading uncached model: '+path, flush=True)
        model = loader.loadModel(path, noCache=True)
        if model is None or model.isEmpty():
            raise ValueError('Missing expansion treasure model: '+path)
        _models[path] = model
        print('[Expansion treasure] Model ready: '+path, flush=True)
    return _models[path]
