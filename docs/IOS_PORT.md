# Full-game iPhone/iPad port

Status: **foundation only; no installable IPA, no on-device gameplay yet**.
This is a native full-game port, not a web wrapper, streaming client, or a
standalone Ministry Plaza viewer. Keep this PR in draft until the gates below
are actually verified. Desktop behavior remains the default.

## Architecture

The device embeds Python, Panda3D and the game's custom native extensions and
loads the existing client code, art, textures, audio, DNA and DC schema. It
connects to a separately hosted district. It never launches Astron, UberDOG,
the AI district, or an account database. Desktop and iOS must use the same game
protocol/schema and server content revision.

The initial hosted test is invite-only over an encrypted private network.
See [dedicated hosting](DEDICATED_SERVER.md). This is independent of iOS:
desktop clients can test hosted gameplay before the native renderer is ready.

## Engine audit, 2026-10-19

Audited `open-toontown/panda3d` at
`06615744481946654610833679a0893589114504` (also recorded in `ios/engine.lock`).

- The custom `makepanda` targets include nametags/movement/navigation (`otp`)
  and DNA/suits/pets (`toontown`). Stock pip Panda3D does not replace these.
- `panda/src/iphone/ipfreeze.py` targets ARMv6, iPhone OS 2.0, Python 2.5 and
  old developer-specific paths. It is not a modern IPA export script.
- `panda/src/iphonedisplay/eaglView.mm` creates an OpenGL ES 1 context.
- `iPhoneGraphicsWindow.mm::handle_button_delta` maps the *number of touches*
  to mouse buttons. That does not provide independent joystick/action touches.
- No working modern iOS build was established by this audit. A macOS arm64
  wheel is not an iOS arm64 framework: same CPU, different platform/ABI.
- The game imports `panda3d.core`, `.direct`, `.ode`, `.otp`, `.physics` and
  `.toontown`; dynamically imported plugins/dependencies must also be audited.

Run `python -m ios.check_environment` on the build Mac. It reports Xcode/SDK
availability and scans native imports, but deliberately returns failure until
the native port/build gates are implemented. This workspace is Linux, has no
Xcode/iPhone SDK, and has only stock Panda3D, not the custom native extensions.

Primary reference: [CPython iOS embedding](https://docs.python.org/3/using/ios.html).
Modern CPython supports an embedded framework model, but that does **not**
establish compatibility with this game's existing Python 3.9 engine build.
Select and test a supported Python/native ABI together. Full Xcode is needed;
the command-line-tools-only installation used for desktop development is not
enough. Native modules must be packaged/signed for iOS, not copied from Mac.

## Implemented in this first pass

- `toontown.mobile.Session`: explicit private endpoint and issued credential,
  no implicit `dev` account, no failover onto unrelated ports, secrets excluded
  from repr/config output.
- `toontown.mobile.Client`: remote-only launch of the existing full game.
  An embedded entry point can step the native task manager without starting
  its blocking desktop loop. It **requires** a future native host and its
  graphics/audio configuration; it is not an iOS renderer.
- `TouchInput`: independent contact ownership, simultaneous keys, dead zone,
  timestamped game events and release-on-cancel/background. Tests drive the
  actual Panda input-state machinery. No UIKit overlay is wired up yet.
- Settings, launcher logs/error files and screenshots can use an external
  writable sandbox through `TOONTOWN_USER_DATA`. Bundled assets remain read-only.
  Mobile mode no longer applies saved desktop window dimensions.
- `ios.stage_game` prepares all game Python, department assets, DC/PRC and
  resource phases 3–13 with per-file SHA-256 hashes. It excludes local state,
  secrets and git internals, rejects symlinks, and never overwrites an archive.
  This is **content staging, not an IPA**, and does not include the native
  engine, Python runtime or third-party dependencies such as `pytz`.

Example, from a complete game checkout:

```sh
python -m ios.stage_game --output /tmp/open-toontown-game-content.zip
```

## Remaining release gates (full game, not a scene demo)

### Cloud device compilation

`.github/workflows/ios-native.yml` runs two compilation jobs on GitHub's
standard `macos-15` runner when this branch's iOS build sources change. No
local Xcode installation is needed to run that workflow. It is restricted to
public repositories; it uses no larger runners, cache or artifact uploads.

`bash ios/build_native.sh python /absolute/build-folder` builds a host
interpreter and an arm64 **iPhoneOS** Python framework from the same pinned
CPython 3.13.9 commit. It checks the binary's architecture and Mach-O platform.
Third-party native standard-library dependencies are not yet supplied; this
is not the final Python runtime bundle.

`bash ios/build_native.sh panda /absolute/build-folder` cross-compiles the
pinned custom engine's C++ core, physics, nametags, movement, DNA, suits, pets
and ES2 state guardian. Its CMake overlay follows the existing makepanda
source lists and excludes macOS-only AppKit/IOKit paths on iOS. It does not
include Python bindings, Python-dependent navigation, third-party codecs,
ODE, the UIKit window/context, or audio yet. A green compile check establishes
only compilation of those named components, not game compatibility.

Both scripts leave detailed compiler output in the Actions logs. Neither
produces an IPA or runs a simulator. The Python ABI is a build candidate;
the full game still needs to be tested against it. Do not use a macOS wheel
to fill any missing iOS modules.

### Release checklist

| Gate | Required evidence |
| --- | --- |
| Native runtime | Reproducible iOS arm64 build of Python/Panda/custom modules, display/audio, no missing native imports |
| App host | UIKit lifecycle/display link, safe-area landscape layout, proper frame pacing, memory warnings and resource loading |
| Input | Multi-touch overlay, DirectGUI pointer, native text keyboard, Keychain credential storage, context controls and saved-binding support |
| Multiplayer | Two independent devices connect to hosted Astron; accounts/Toons persist after all clients quit and server restarts |
| Core game | Login, Toon creation/tutorial, all playgrounds/streets, interiors, tunnels, NPC quests, gags, shop, trolley and book |
| Activities | All trolley games, fishing, golf, racing/ODE, estates, gardening, pets, parties, cannons and controls specific to each |
| Cogs | Street/building battles, factories/mints/offices/courses, four native bosses, Bureaubot HQ and Director General encounter |
| Mobile resilience | Keyboard focus, interruptions, app suspend/resume, session expiry, disconnect/reconnect, low memory, battery and thermal performance |
| Distribution | Signed device archive/IPA installable using the chosen legitimate signing route; actual iPhone/iPad testing |

No activities should silently be disabled to claim that the port is complete.
Short vertical tests establish feasibility first; they do not reduce the final
scope. Existing unfinished desktop content remains unfinished on mobile too.
In particular, Archives suit-part progression and boss-specific rewards are
still deferred desktop features, not features delivered by this port.

The background hook releases touches and pauses audio. It does not promise
that iOS will keep a multiplayer socket alive while suspended. Reconnection
UI/session handling still needs implementation and device verification.

## Validation so far

`python -m unittest discover -s tests -p test_mobile_server.py -v`
tests token policy, state paths, config isolation, child failure handling,
content staging and input ownership (including real Panda event dispatch).
`PYTHONPATH=tests:. python -m unittest test_admin_endpoint` checks that ordinary
players still cannot invoke administrator mutations.

Neither suite is a live-server, complete-game, signing or device test.
