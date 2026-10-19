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

### Platform compatibility contract

Mac and Windows retain their desktop launchers, keyboard/mouse controls and
saved window preferences. iOS is a separate native client with its own app
bundle, touch controls and writable sandbox; it connects directly to the
hosted server without a Mac or PC running the game. All three clients share
game content and the server protocol. Mobile settings apply only when the
embedded host explicitly enables `mobile-client`.

Engine patches in `ios/prepare_engine.py` apply only to the disposable iOS
build checkout. Desktop engine builds do not run that script. Changes to shared
Python code must preserve desktop defaults and be checked on Mac and Windows.
`.github/workflows/desktop-regression.yml` checks settings, platform isolation,
world routing and access rules on both operating systems. These checks use
stock Panda for the tested APIs; they do not replace custom-engine builds,
desktop launch/login or real gameplay checks. All three platforms must pass
their respective launch, input and multiplayer tests before release.

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
  actual Panda input-state machinery. `NativeControls` exposes the main-thread
  stick/jump callbacks used by the UIKit-to-Python adapter.
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

`.github/workflows/ios-native.yml` runs three compilation jobs on GitHub's
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
and ES2 state guardian, plus the UIKit/EAGL pipe and SDK OpenAL backend. Its CMake overlay follows the existing makepanda
source lists and excludes macOS-only AppKit/IOKit paths on iOS. It does not
include Python bindings, Python-dependent navigation, third-party codecs,
ODE or tested audio playback yet. A link-only graphics executable forces the new
pipe and rendering backend into a device binary. A green compile check establishes
only compilation of those named components, not game compatibility.

`bash ios/build_native.sh controls /absolute/build-folder` compiles the native
UIKit joystick/jump overlay with the device SDK and verifies its Mach-O target.
`TTControlsView` places a left movement stick and right Jump button inside the
safe area, accepts simultaneous touches, passes touches outside the controls
through to the game view, and releases held input on cancellation/background.
`TTGameInputBridge` forwards delegate calls into the real Python router, starts
with controls disabled, and cancels held input on app suspension or teardown.
The eventual app host must retain it, enable controls only in appropriate game
states, and invalidate it before Python shutdown. Its current mapping uses the
default arrows/Control bindings; saved mobile rebinding remains a release gate.
`TTPandaInputView` supplies the pointer bridge: one primary touch becomes a
left-button press/drag/release on `GraphicsWindowInputDevice`, with UIKit points
scaled to the actual framebuffer pixels. Other fingers never become right-clicks.
Cancellation clears the pointer before release; a normal tap retains its release
position for Panda's next frame. `TTGraphicsPipe` attaches that same input device
to its window and supplies drawable dimensions from `TTGLESView`.
Battle/minigame controls, keyboard entry, accessibility and device interaction remain
release requirements. Compiling the overlay does not establish working input.

`bash ios/build_native.sh bindings /absolute/build-folder` builds the pinned
host/device Python pair, compiles the UIKit-to-Python adapter, and builds static
`panda3d.core`, `.direct`, `.physics`, `.otp` and `.toontown` modules. This includes
Python-dependent navigation. The exact pinned host `interrogate` generator runs
on macOS; generated wrappers use the iOS Python framework headers/libraries.
`TTRegisterBuiltinModules` supplies their pre-interpreter registration table.
A link-only iPhone executable references every module initializer to detect
unresolved engine symbols; it is not an installable app or a runtime test.
The workflow runs `bindings`, `panda` and `controls`; the standalone `python`
command remains available for diagnosing the runtime separately.

All build commands leave detailed compiler output in the Actions logs. None
produces an IPA or runs a simulator. The Python ABI is a build candidate;
the full game still needs to be tested against it. Do not use a macOS wheel
to fill any missing iOS modules.

### Native graphics host contract

`TTGraphicsPipe` supplies one UIKit window using an EAGL ES2 context, RGBA8
color and packed 24-bit depth / 8-bit stencil. The actual framebuffer dimensions drive the window size
and pointer conversion. Layout changes invalidate drawable storage without
submitting GL commands from UIKit layout callbacks. Frame entry reallocates it
when active, restores external bindings, and binds the nonzero iOS screen FBO
through Panda's state cache. Host-backed texture buffers share that context.
Unsupported framebuffer requests are subject to Panda's normal property checks;
this first surface does not provide MSAA or sRGB.

The eventual app host must:

1. Load PRC with empty `load-display`/`aux-display`/`threading-model`,
   `window-type onscreen` and `sync-video false` before registering the pipe:
   Panda caches display settings on first pipe-selection access.
2. Create and retain a visible UIKit container, then call
   `TTConfigureGraphicsHost(container)` before ShowBase window creation.
   The pipe rejects a draw thread.
   Call `TTSetGraphicsActive(YES)` after the application becomes active, before
   creating the Panda window. Add `TTControlsView` above the drawable.
3. Step the embedded client on the main thread from a display link. Stop frame
   delivery and disable the Python control bridge when resigning active.
   The drawable independently disables touch/rendering and finishes outstanding
   GPU work before backgrounding. Explicitly resume after activation.
4. Remove Panda outputs and invalidate the control bridge before finalizing
   Python, on the main thread while still in the foreground. Then call
   `TTClearGraphicsHost()`. Suspension retains the window instead of destroying it.

These sources still need the application lifecycle host, runtime validation,
asset dependencies and device gameplay. Compile/link checks do not demonstrate
that a frame or a DirectGUI click has worked on an iPhone.

References: Apple's [EAGLContext](https://developer.apple.com/documentation/opengles/eaglcontext)
and [drawable storage](https://developer.apple.com/documentation/opengles/eaglcontext/renderbufferstorage(_:from:))
contracts. OpenGL ES is deprecated by Apple; this stage uses the existing pinned
engine's ES2 renderer. A Metal migration is separate work.

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

Verified compilation/link checkpoint, 2026-10-19:

- [iPhone device build](https://github.com/jaxf/open-toontown/actions/runs/39308070672)
  at `99608a48e5fc44f70d51bfc02496944940f994b6`: all three jobs passed.
  CPython 3.13.9 and static `panda3d.core`, `.direct`, `.physics`, `.otp` and
  `.toontown` compiled against the iPhone SDK. Navigation is included in OTP.
  The module initializers linked into `tt_python_linkcheck`; `lipo` confirmed
  arm64 and Mach-O reports iOS 15.0 minimum / SDK 18.5. This verifies native
  symbol resolution, not Python imports or gameplay on a device.
- The same run compiled the UIKit joystick/Jump view, the UIKit-to-Python
  callback adapter, and the Panda tap/drag input view. The C++-only build also
  passed, including ES2 and SDK OpenAL. UIKit input code uses strict warnings;
  upstream Panda headers are treated as dependency headers for the tap view.
  No touch interaction, actual graphics window or audio playback was tested.
- [Desktop regression matrix](https://github.com/jaxf/open-toontown/actions/runs/39308079678):
  all 19 checks passed in all four Mac/Windows × Python 3.9/3.12 combinations:
  eight platform/input checks, six world-routing checks and five access-policy
  checks. This uses stock Panda only for those tested APIs, not the custom
  desktop game runtime. Full desktop launch/login/gameplay is still unverified.
- Local mobile/server suite: 29 tests passed. Local platform/input, expansion
  and administrator suites also passed (8 + 6 + 5 checks).

No IPA, UIKit/Panda display bridge, packaged runtime import test or actual
phone interaction has passed yet. Required native modules such as ODE and
image/font/audio dependencies still need device builds. The checks above are
compilation, linking and regression evidence only. No simulator was run.

`python -m unittest discover -s tests -p test_mobile_server.py -v`
tests token policy, state paths, config isolation, child failure handling,
content staging and input ownership (including real Panda event dispatch).
`PYTHONPATH=tests:. python -m unittest test_admin_endpoint` checks that ordinary
players still cannot invoke administrator mutations.

Neither suite is a live-server, complete-game, signing or device test.
