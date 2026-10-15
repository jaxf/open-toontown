# October 15: street and gameplay update

## Street block redesign and Cog takeover fix (October 15)

All eight expansion streets now use individually authored block routes with
rounded right-angle bends, offset intersections, side loops and pocket courts.
Root Route has a western garden loop; Bramble Bend and Limelight Lane have
terminal side courts; Taffy Terrace has a long quay crossing; Forty Winks Way
mixes angled blocks and a garden loop; Encore Avenue wraps a studio block;
Stagecoach Street has diagonal turns; Detour Drive follows an angled canyon loop.

Street paving is exported from joined polygons instead of overlapping ribbons.
One continuous ground foundation covers the wider footprint. Opaque themed
boundaries follow the actual road/courtyard perimeter, including inner block
edges, with tunnel openings and collision. HQ bays face their road approaches.
Storefronts use non-overlapping footprints and the shared shop models now have
closed side panels and rear-wall heights derived from actual native side walls,
preventing the oversized panels previously created from roof bounds.

The crash log reaches `DistributedBuilding.setupCogdo`: its field-office lookup
returned an empty NodePath. Expansion streets now load the complete native town
catalog (field office, Cog walls, doors and elevator) through the existing Python
palette loader before their exterior DNA. Cog lanes are directed loops with
separate return lanes, eliminating immediate reverse street edges flagged by
the native path search. Terminal courts do not connect through scenery to a
distant road.

Author with `python -m tools.rebuild_expansion_streets` from the repository root.
This requires Panda3D, the stock resource checkout, and `shapely>=2.1` on the build
machine only. The game reads committed BAM/DNA files and needs no Shapely install.
The asset rebuild completed for all eight streets. No game tests or screenshot
renders were run; the custom Mac engine still needs gameplay confirmation.

## Controls styling and tunnel entry fix (October 15)

Controls uses the existing fishing-book tab and yellow Options button models.
The FOV slider has a larger handle and supports immediate click-and-drag across
its track, with continuous camera updates and drag cleanup when leaving the page.

The supplied tunnel log identifies a native DNA syntax error at `scale` in a
`landmark_building`. That grammar accepts position and heading but no scale.
Removed the unsupported field from all 404 street landmarks across eight streets
and corrected the authoring generator. Buildings and their native doors now use
the model's original scale. No tests or screenshot renders were run; gameplay on
the custom Mac runtime still needs confirmation.

## Mac healing-pickup load fix (October 15)

The reported crash reaches `Exterior ready`, then faults in the native model
loader while `DistributedDGTreasure` generates. The same pickup assets load
successfully with `noCache=True` during palette loading. Expansion pickups now
use that uncached path and retain five small Python-owned model prototypes for
respawns and holiday replacements. They are excluded from the DNA scenery
catalog, including future catalog regeneration. Stock and holiday treasure
models retain their existing loading behavior.

This is a targeted workaround based on the supplied stack trace; the native
cache fault has not been reproduced on the custom Mac engine here. No game
tests or screenshots were run for this change.

- All eight streets have wider bends and looping side streets with two intersections each. Patrol graphs follow both routes and connect to shop doors.
- Street shops now use native distributed buildings: Toon interiors, Cog takeovers, elevators, building battles and victory returns. Service HQs are excluded from takeovers.
- Stock facade door sockets determine door placement. Acorn's older separate doors/backings have been replaced with the same completed storefront kit.
- Lamp palettes select one variant per placement; both variants alternate down streets. Props outside boundaries or in junction roadways are removed. Paving has blended shoulders, subtle color variation and low edge banks.
- Trolley stations have solid themed side/rear walls and collisions. Boarding remains at the open front. Playground skies receive their theme tint whenever they start.
- Each new playground has four respawning, server-owned Laff pickups, healing 10: acorns, saltwater taffy, crescent moons, movie stars or canteens.
- World-map destinations use invisible clickable areas over the artwork and names on hover. No yellow buttons or connecting lines.
- Admin controls sit farther left and support wheel/trackpad scrolling plus the scrollbar.
- **Escape → Controls** opens saved keyboard bindings and a **50–100° FOV** slider. Gameplay shortcuts, camera controls, sprint, movement, friends, map, gag/task overlays and screenshot keys are configurable. Activity-specific controls remain in each activity's instructions.
- Press **Enter** or the chat button for unrestricted typed chat. Opening chat pauses movement so remapped letter keys do not move the Toon while typing.
- **~maxgags** gives 999 of every gag; **~resetgags** clears every quantity, including level-seven gags, without resetting training. **~name Your New Name** renames only your own Toon. These commands do not require admin access.
- Inventory quantities over 255 use a versioned 16-bit blob; ordinary saved inventories remain readable. Extended inventories survive login repair. Restart all clients and servers together.
- The battle **Fast forward turn >>** button plays the current attack movie at 6× speed. Outcomes stay server-owned; other players must finish their movies before the server advances.

Models and layouts were rebuilt. Python 3.9 syntax and diffs were reviewed. No test suites or screenshots were run/rendered for this update. Full client/server behavior on the custom Mac Panda3D engine has not been verified on this host.

## Earlier update notes

## Street and playground finishing pass

- Streets have only Toon HQs; gag-shop interiors, clerks and trolleys are playground-only.
- Distinct perimeter fences and screened building/service yards have collision walls.
- Woodland earth, coastal sand, purple garden brick, studio paving and desert dust replace generic grass.
- Grounded prop aliases share level walking surfaces; deterministic clusters add benches, planters, palms, barrels, cameras and cacti.
- All eight streets have longer curved centerlines and native server-owned Cog patrols (8–14 per street). Native battle states/UI are connected; decorative buildings cannot be taken over.
- Hold Shift for 1.65× walking speed. Physical arrow polling preserves turning and the following camera while Ctrl-jumping.
- The world map no longer draws connecting route lines.

Scenes were rendered for visual review; no test suites were run. The custom Mac engine is unavailable on this host, so the client/AI gameplay changes still need a live walkthrough. Restart the complete local stack after pulling.

## Full world art update

The remaining four playgrounds and seven streets have been rebuilt with native
DNA, original textured modules and new themed models. The Shtiker map is now one
illustrated world with original and expansion destination buttons. See the
[art kit, screenshots and editor guide](../assets/expansion/README.md).

The test suite was not run for this update, as requested. Scene/UI previews were
rendered for visual iteration; a live custom-engine walkthrough remains outstanding.

# Beyond the Tunnels — first exploration build

Five new neighborhoods and eight connecting promenades extend the existing
world. This is a first playable implementation for layout testing, not a finished
quest/content expansion. New areas have authored native DNA scenery, native street Cog patrols,
landmarks, collisions, music, and two-way native tunnel travel.

**Art rebuild:** Acorn Acreside and Root Route now load editable native DNA,
textured Toontown storefronts and props, and custom modeled terrain and a hollow
Great Oak. Root Route has a curved road, sidewalks and pocket courtyards. All remaining neighborhoods and streets now use the expanded art kit as well.
See [the Acorn art kit and editor instructions](../assets/acorn/README.md).

![Acorn Acreside rebuilt](previews/acorn-acreside-walk.png)
![Root Route rebuilt](previews/root-route-walk.png)

![Expansion route map](previews/expansion-map.png)

## Locations and routes

| Playground | Zone | Design | Entrance from the original world |
| --- | --- | --- | --- |
| Acorn Acreside | 19000 | Autumn trees, a hollow Great Oak, timber storefronts | Daisy Gardens → Root Route |
| Briny Boardwalk | 61000 | Wooden boardwalk, pastel shops, lagoon, striped lighthouse | Donald's Dock → Taffy Terrace |
| Hush Hollow | 62000 | Plum and teal buildings, pumpkin props, crooked clock tower | Donald's Dreamland → Forty Winks Way |
| Doodlewood Studios | 63000 | Theater, film reel, red carpet, backlot facades | Minnie's Melodyland → Encore Avenue |
| Tumbleweed Terrace | 64000 | Adobe storefronts, cacti, dry creek, hat-shaped water tower | Goofy Speedway → Detour Drive |

Bramble Bend connects Acorn Acreside and Hush Hollow. Limelight Lane connects
Briny Boardwalk and Doodlewood Studios. Stagecoach Street connects Doodlewood
Studios and Tumbleweed Terrace. Every connection has a return tunnel.

Open the Shtickerbook map to see all original and new neighborhoods together.
Visiting a new neighborhood unlocks its playground teleport. The illustrated
map has directly selectable labeled buttons and curved route overlays.

## Admin testing

The **Admin** button appears in the upper-right while walking with an account
whose existing server-assigned access level is ADMIN (300) or SYSTEM_ADMIN (400).
It hides during battles, transitions, boarding groups, and other activities.
This change does not alter account roles or the login provider's default role.

![Admin testing controls](previews/admin-panel.png)

**Max my Toon + unlock travel** uses the existing server max-toon routine:
137 Laff, all seven gag tracks and maximum experience, maximum gag capacity,
full inventory, jellybeans/bank, four task slots, maximum Cog disguises, final
quest tier, and travel access. It permanently clears the active task list.
It does not award every fishing/gardening/racing collectible or cosmetic.

The scrollable destination list includes the new playgrounds and promenades,
original playgrounds, Cog HQ exteriors, factory exterior, MiniGolf, and all 17
original streets. Original street teleports arrive through their actual playground
tunnel instead of carrying over coordinates from another zone. Instanced battles,
private estates, and unallocated zone IDs are intentionally not listed.

Requests affect only the authenticated sender's Toon. The AI independently checks
ADMIN access, the action and destination allowlists, tutorial state, and a one-second
rate limit. Mutations use the existing server setters and are logged. Editing a
client or making the button visible cannot grant admin access.

Finish or use the game's existing skip option for the introductory tutorial first;
the testing controls are available once walking in the world. No progression
through the main game is needed.

## Running this branch

1. Keep the resources checkout described in the main README. No separate resource
   repository edits are needed. The Acorn models are included under `assets/acorn`;
   keep both `assets/acorn` and `assets/expansion` with the game checkout.
2. Stop the game client, AI, UberDOG, and Astron. Update all of them to this branch.
3. Restart in the normal order: Astron → UberDOG → AI → client.
4. Open **Admin**, max the test Toon, and select **Acorn Acreside** (or any other
   listed location). Use the physical tunnels to exercise the complete route graph.

A full restart is required: `etc/toon.dc` adds an RPC and the dynamic allocator now
starts at **65000**, reserving **61000–64999** for static neighborhoods. Existing
Welcome Valley and legacy 20000–21999 mappings are unchanged. Do not mix old and
new clients/servers or hot-reload this into a running district with allocated
instances in the reserved range. No saved Toon IDs or account IDs are renumbered.

The project still requires its custom Panda3D fork with `panda3d.otp` and
`panda3d.toontown` to play. Standard Panda3D can render the scene/UI previews and
run geometry tests, but cannot run the complete legacy client/server.

## Previous validation (before this update)

- `python -m unittest discover -s tests -v` — 17 checks covering all reciprocal
  routes, reachability, static/dynamic boundaries, the actual routing functions,
  permission denial, the actual admin RPC with fake transport, rate limiting,
  scene construction, tunnel origins, authored walking routes, the hollow oak
  passage, floor/wall collision probes, and portable model texture references.
- Both `etc/otp.dc` and `etc/toon.dc` parse with Panda3D's DCFile parser.
- All 17 original street arrival visgroups were checked against resource DNA.
- `python tools/preview_expansion.py` renders the actual five neighborhood scenes.
- `python tools/preview_acorn.py` renders Acorn and Root Route from overview and
  walking-height cameras. Their storage and layouts also passed the Python DNA
  parser bundled with OpenLevelEditor; native-loader/editor-GUI testing remains.
- `python tools/preview_expansion_ui.py` renders actual UI widgets with mock avatar
  state; it is not a multiplayer session.
- Source entrance floor/wall probes use the original neighborhood terrain models.
  They do not include every DNA-placed prop, NPC, or distributed building.

Full client/AI integration, travel movies in a live district, multiplayer visibility,
reconnect/persistence, and source entrances with the complete DNA scene still need
an in-game pass using the custom engine. Keep the PR in draft until that pass.

## Remaining content work

Every new area has a Toon HQ. Gag shops and trolleys are playground-only, with
quest officers, clerks, door wiring and stock minigame flow.
Playground decorative shops remain scenery. New bespoke NPC task chains,
fishing gameplay, ambient animations, custom music and further
art/terrain polish remain future work. The
lagoon and creek are visual scenery. Existing game content is unchanged.

