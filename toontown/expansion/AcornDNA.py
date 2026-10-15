"""Native DNA loading for the two art-pass locations.

The game always uses its C++ DNA loader. The deliberately limited preview reader
is only for standard Panda3D tooling; it rejects unsupported DNA instead of
silently producing a misleading preview. Layouts remain the source of truth.
"""
from pathlib import Path
import re
from panda3d.core import NodePath, Filename, getModelPath

ASSETS = Path(__file__).resolve().parents[2] / 'assets/acorn'
# The game launches from its root, but editor/preview entry points may not.
getModelPath().appendDirectory(Filename.fromOsSpecific(str(ASSETS.parents[1])))
STORAGE = 'assets/acorn/dna/storage_acorn.dna'
LAYOUTS = {19000: 'assets/acorn/dna/acorn_acreside.dna',
           19100: 'assets/acorn/dna/root_route.dna'}


def load_scene(zone, dna_store=None, storage=STORAGE, layouts=LAYOUTS):
    from direct.showbase import ShowBaseGlobal
    loader = ShowBaseGlobal.base.loader
    if dna_store is not None:
        loader.loadDNAFile(dna_store, storage)
        node = loader.loadDNAFile(dna_store, layouts[zone])
        if node is None:
            raise RuntimeError('Failed to load DNA: '+layouts[zone])
        return NodePath(node)
    return preview_scene(zone, loader, storage, layouts)


def parse(path):
    """Read the editor's bracketed DNA syntax, retaining nested prop transforms."""
    source = Path(path).read_text()
    source = re.sub(r'//[^\n]*', '', source)
    tokens = re.findall(r'"[^"\n]*"|\[|\]|[^\s\[\]]+', source)
    position = 0

    def block(nested=False):
        nonlocal position
        entries = []
        while position < len(tokens):
            token = tokens[position]
            position += 1
            if token == ']':
                if not nested:
                    raise ValueError('Unexpected ] in '+str(path))
                return entries
            if token == '[':
                entries.append(block(True))
            else:
                entries.append(token[1:-1] if token.startswith('"') else token)
        if nested:
            raise ValueError('Unclosed DNA block in '+str(path))
        return entries
    return block()


def storage_models(loader, storage=STORAGE):
    data = parse(ASSETS.parents[1]/storage)
    models = {}
    for i in range(0, len(data), 3):
        kind, filename, entries = data[i:i+3]
        if kind not in ('model', 'hood_model', 'place_model'):
            raise ValueError('Unsupported storage node '+kind)
        model = loader.loadModel(filename)
        if model is None or model.isEmpty():
            raise ValueError('Missing model '+filename)
        for j in range(0, len(entries), 2):
            command, values = entries[j:j+2]
            if command != 'store_node':
                raise ValueError('Unsupported storage command '+command)
            category, code = values[:2]
            name = values[2] if len(values) > 2 else code
            node = model if not name else model.find('**/'+name)
            if node.isEmpty():
                raise ValueError('Missing model node '+code)
            # Keep the loaded model alive through its selected NodePath.
            models[code] = node
    return models


def preview_scene(zone, loader, storage=STORAGE, layouts=LAYOUTS):
    models = storage_models(loader, storage)
    root = NodePath('expansion-%s' % zone)

    def traverse(entries, parent):
        i = 0
        while i < len(entries):
            kind = entries[i]
            if kind in ('group', 'visgroup', 'node', 'prop', 'landmark_building'):
                name, children = entries[i+1:i+3]
                if kind in ('prop','landmark_building'):
                    code = children[children.index('code')+1][0]
                    node = parent.attachNewNode(name) if code == 'DCS' else models[code].copyTo(parent)
                    node.setName(name)
                else:
                    node = parent.attachNewNode(name)
                traverse(children, node)
                i += 3
            elif kind in ('pos', 'nhpr', 'scale', 'color'):
                value = tuple(map(float, entries[i+1]))
                {'pos': parent.setPos, 'nhpr': parent.setHpr,
                 'scale': parent.setScale, 'color': parent.setColorScale}[kind](*value)
                i += 2
            elif kind == 'door':
                children=entries[i+1]
                code=children[children.index('code')+1][0]
                door=models[code].copyTo(parent)
                origin=parent.find('**/door_origin')
                if not origin.isEmpty():
                    door.setMat(origin.getMat(parent))
                i += 2
            elif kind in ('code', 'vis', 'title', 'building_type'):
                i += 2
            else:
                raise ValueError('Unsupported preview DNA node '+kind)
    traverse(parse(ASSETS.parents[1]/layouts[zone]), root)
    return root
