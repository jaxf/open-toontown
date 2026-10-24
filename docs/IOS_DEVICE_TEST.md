# First iPhone test

This is a development IPA for the full game. The build checks compilation,
payload completeness, framework links and signatures. Installation, startup,
server login and gameplay must still be tested on an actual iPhone/iPad.
No simulator is used. Mac and Windows launchers remain separate.

Build 1 installed on an iPhone but crashed before the connection screen.
Its symbolicated report identifies the DNA parser's global `Loader` constructor
reading Panda configuration during static initialization, before `main`.
Build 2 defers that dedicated loader until the first DNA model load. First
confirm that the connection screen opens; then proceed with login/gameplay.

The second IPA reached the form but failed at `ToontownLoadingScreen.py:12`
while loading `progress-background`. Build 3 synchronizes Panda's independent
VFS working directory with the game bundle and prepends absolute model roots.
The same failure was reproduced with a stale VFS cwd on the host; the fix loaded
all three original startup BAMs extracted from the IPA. This is asset-loading
evidence, not an iPhone rendering/login test. Build 3 also preserves the explicit
plist build number instead of using a shallow checkout's constant commit count.

## Install and connect

1. Save `OpenToontown.ipa` to Files. In AltStore Classic, open **My Apps**, tap
   **+**, and select the IPA. AltStore supplies your device provisioning and
   re-signs the app and its embedded frameworks. The build's ad-hoc signature
   alone does not authorize installation on your phone.
2. Connect the iPhone's Tailscale app to the same personal account as the
   `toontown-server` VM. Keep the VM running.
3. Open **Open Toontown**, allow the local-network prompt if shown, and enter
   the private server address `100.113.145.56`. The game uses port `7198`.
4. Enter your issued 43-character player token. If you have not issued one,
   run `bash host.sh account` in the VM's SSH terminal. Keep its output private;
   paste the token only into the app's **Player token** field.
5. Tap **Connect**. The first game startup may take time. The token is held
   only in memory, so restarting the app requires entering it again.

## What to test first

- Reach Toon selection/creation and enter a playground. Use the game's name
  picker initially; a native keyboard for in-game custom text is still pending.
- Walk and turn with the left joystick; hold movement while tapping **Jump**.
- Tap menus, Toon selection and the book. Confirm taps outside the overlay
  reach the game and do not become right-clicks when another finger is held.
- Check music/sound, rotate between the two landscape orientations, and briefly
  leave/return to the app. Held movement should clear when interrupted.
- Enter a street and return to the playground. Exit/reopen and confirm the
  same token brings back the same account/Toon.

If startup stops, tap **Copy error details** and send that text or a screenshot.
The copied report contains exception types and source locations, not the token
or exception-local values. If iOS closes the app entirely, report whether it
happened at launch, after Connect, during Toon selection or in the world.
If AltStore refuses installation, send its exact error before trying gameplay.

Activity-specific touch controls, in-game typing, audio interruption/route
recovery and long-session behavior remain unfinished. This first test must not
be treated as proof that every minigame or device lifecycle path works.
# Build 4 rendering correction

The real iPhone reached toon selection after joining the server's Tailscale
network, but transparent panels rendered black and obscured Make-a-Toon.
The pinned GLES fallback fragment shader did not implement AlphaTestAttrib;
binary and dual-pass transparency still relied on that test in CullResult.
The disposable iOS engine overlay now applies all comparison modes in the
fallback fragment shader, updating the reference and mode on state changes.
Desktop engine sources and custom game shaders are unchanged.

Validation: a surfaceless Mesa ES2 test compiles the actual patched fallback
fragment shader and reads back 55 pixels across all nine comparison modes and
repeated state changes. Startup and IPA packaging regressions also pass.
This is not a real iPhone gameplay result. Build 4 still needs device testing
of toon selection, character creation, and entry into the playground.

Local rendering regression command (prepared engine checkout required):
`TT_TEST_ENGINE=/path/to/engine python3 -m unittest discover -s tests -p test_gles_alpha.py -v`

