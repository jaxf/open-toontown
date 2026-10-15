# Expanded Toontown art kit

All five expansion playgrounds and eight connecting streets now use native DNA
layouts. This kit adds the four remaining playgrounds and seven remaining roads;
Acorn Acreside and Root Route use the woodland kit in `../acorn`. All 13 areas
now include native Toon HQ, gag-shop and trolley service DNA.

| Location | Design |
| --- | --- |
| Briny Boardwalk | Dock storefronts, striped Loopy Lighthouse, boardwalk, lagoon, rope rails, palms and barrels |
| Hush Hollow | Dreamland storefronts, crooked Backwards Clock Tower, teal trees and sleepy garden courts |
| Doodlewood Studios | Melodyland storefronts, custom art-deco Reel Big Theater, film-camera props and red carpet |
| Tumbleweed Terrace | Custom western shops, deep porches, cactus props, sandstone mesas and Ten Gallon Water Tower |
| Bramble Bend | Woodland street transitioning into Hush Hollow |
| Taffy Terrace | Long dockside street with boardwalk sidewalks and palms |
| Limelight Lane | Coastal storefronts transitioning into studio architecture |
| Forty Winks Way | Long winding Dreamland-style street with garden rest stops |
| Encore Avenue | Curving musical/studio street with camera props |
| Stagecoach Street | Studio storefronts transitioning into western shops and mesas |
| Detour Drive | Long desert street, timber sidewalks and western porches |

The seven roads span 600–760 units between tunnel mouths before accounting for
their curves. Each has a distinct centerline, two native tunnel approaches,
continuous shop rows, broad sidewalks, lamps and small rest courts. Shop names
are scenery signs. Every area also has a separate functional gag shop, quest HQ
and trolley using the original distributed service classes. Cog planners and
battles remain unimplemented in these peaceful areas.

## Screenshots

These are offscreen Panda3D renders of the committed scenes, not concept art.

![Briny Boardwalk](../../docs/previews/briny-boardwalk-walk.png)
![Taffy Terrace](../../docs/previews/taffy-terrace-walk.png)
![Hush Hollow](../../docs/previews/hush-hollow-walk.png)
![Doodlewood Studios](../../docs/previews/doodlewood-studios-walk.png)
![Tumbleweed Terrace](../../docs/previews/tumbleweed-terrace-walk.png)
![Detour Drive](../../docs/previews/detour-drive-walk.png)
![Unified world map](../../docs/previews/expansion-map.png)

## Edit in OpenLevelEditor

Use the editor's compatible Panda3D build and the game's original phase resources.
Add this repository root to `model-path`, copy `editor/WX.json` to the editor's
hood configuration directory, and start with `python ttle.py --hoods WX`.
Open any layout under `dna/`. `storage_world.dna` declares its model palette.
The matching `services/service_ZONE.dna` contains the native service buildings
and trolley; load `services/storage_services.dna` for that palette.
The game loads model catalogs through Panda's Python loader and registers each
node in native DNAStorage; layouts and door triggers still use the C++ DNA loader.
This bypasses the Mac crash observed inside native storage-file loading and logs
the specific model if lower-level loading fails. Standard-Panda3D tooling uses the
same strict preview reader as the Acorn kit. The custom-engine client/editor GUI
were not run for this update.

The committed DNA is the runtime source of placement. Move or rotate props and
storefront groups there. Keep the nested native tunnel origin/trigger transforms
and `linktunnel_*` names intact. Moving a tunnel requires updating the matching
travel transforms in `WorldLayout.py` / `ExpansionGlobals.py`.

- `tools/build_world_models.py`: builds custom meshes and complete storefront kits.
- `tools/author_world_layouts.py`: initial placement recipe. **Overwrites DNA**;
  run only when deliberately replacing authored layouts.
- `tools/author_services.py`: authors all 13 service layouts and clears scenery
  from their footprints. Rebuild terrain after moving service bays.
- `tools/preview_world.py`: walking-height and overview screenshots.
- `tools/preview_expansion_ui.py`: actual map/admin widgets with a mock avatar.

Model rebuilding does not overwrite DNA layouts. Compressed BAM files store
relative phase texture references, so no resource repository changes are needed.
The generated terrain follows the centerlines in `WorldLayout.py`; changes to
those centerlines require intentionally regenerating terrain and placements.

## World map

The map opens directly on one illustrated world. Original playgrounds, Cog HQs,
MiniGolf and all five expansion neighborhoods have labeled travel buttons.
There is no additional map/reveal button. Hovering a new neighborhood shows its
connecting street names and emphasizes those routes. Current location, locked
travel, unavailable districts and safe mode remain explicit; the existing server
teleport-access check is preserved. Home/playground return buttons stay available
in the book when permitted. The separate admin panel still provides direct street
teleports and max-Toon controls.

`WorldMapData.py` supplies precise pin anchors and road curves. New-road endpoints
come from the same tunnel manifest used by travel; original connections were read
from the stock DNA. The generated background is illustrative; it does not define
routes or click targets.

## Provenance and validation scope

Original facade modules, trees, lamps, doors, fonts and textures are referenced
from the project's phase resources. New models include the lighthouse, clock
tower, theater, water tower, western shops, cacti, mesas, rope rails, cameras,
terrain, building backs and signs. Map artwork was generated with the built-in
image-generation tool using the original map as a style reference, then integrated
as `maps/toontown_world.png`. The prompt requested a text-free expanded Toontown
painting with all five new districts and the original regions; exact geographic
labels and routes are supplied by code.

Per the requested workflow, no automated test suite was run for this update.
Screenshots were rendered for visual iteration. Live multiplayer travel and the
custom-engine runtime still need an in-game walkthrough.

## Native services in every new area

All five playgrounds and all eight streets have a Toon HQ with four quest officers,
a gag shop with two clerks, paired interior/exterior doors, and a multiplayer
trolley. The AI creates the original HQBuildingAI, GagshopBuildingAI and
DistributedTrolleyAI classes. NPC templates retain stock quest/shop behavior.
Service interiors occupy exterior + 519/520; they are static reserved zones.

Street trolleys use the parent neighborhood's stock minigame theme/difficulty,
and return to the street where the player boarded. Gag shops use the matching
stock interior palette. Placement and service aprons are shared by model authoring
and DNA generation, with scenery cleared from door and platform approaches.

The preview reader displays native service meshes and static door placement.
Only the custom C++ DNA loader builds the runtime door triggers. Screenshots do
not demonstrate quest, shopping, boarding, reward or return-trip interactions;
those still require a live custom-engine client/AI walkthrough.
