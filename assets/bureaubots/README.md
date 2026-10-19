# Bureaubot models

Eight original heads on the classic Toontown Cog A/B/C rigs, with burnt-orange
pinstripe suits and a pewter clipboard badge at the normal chest attachment.
The same badge appears on the gallery, upper building facade and exterior elevator. Heads and icons have
beveled edges and baked shading; the book portraits use a slight three-quarter
turn and hide the neck.

`toontown/suit/BureaubotModels.py` constructs the editable meshes and material.
`BureaubotGlobals.py` owns the shared catalog, DNA codes and attack pools.
`Suit.py` uses those meshes for live networked Cogs, including battle animations
and defeat actors. The alternative `want-new-cogs` setting also loads the
compatible classic rig for this department.

The individual full-body BAMs contain the skeleton, head, chest badge and
embedded textures. Animation clips are loaded from the normal resources
checkout, not embedded in these review exports.

From the repository root, with Panda3D and the resources checkout:

```sh
python tools/preview_bureaubots.py --export assets/bureaubots/models
python tools/preview_cog_gallery.py
python tools/preview_bureaubot_building.py
python tools/preview_cog_buildings.py
python -m unittest discover -s tests -p 'test_bureaubot*.py' -v
```

The Cog Gallery now uses the standard progress, radar and summon interactions
for all 40 entries. The standalone model viewer remains available to preview
tools; it no longer replaces the fifth row's game controls.

See [integration notes](../../docs/BUREAUBOTS_CONCEPT.md) for save compatibility,
server behavior, validation and deployment requirements.

`models/bureaubot-building.bam` is a standalone, embedded-texture landmark.
Its source is `toontown/building/BureaubotBuilding.py::build_building`; the
building preview script exports it before rendering the same asset the game
loads. It does not load or modify a Bossbot/Cashbot/Sellbot/Lawbot building.
The original elevator and sign remain shared game components. The comparison
preview shows all five actual landmark assets at a common model scale.
