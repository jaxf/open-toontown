# Private always-on district for friends

Status: deployment foundation, **not deployed or live-tested**. No cloud account,
VM, billing setting, firewall or DNS has been created/changed. Public-internet
launch is not approved by these changes: use an encrypted private network for
this small friends-only test. Local Mac launchers remain unchanged.

## Free hosting target

First candidate: an Oracle Always Free Ubuntu **Ampere A1 ARM64 VM**. As checked
on 2026-10-19, Oracle documents a free-account total of **2 OCPUs / 12 GB RAM**
and 200 GB combined block-volume storage. Older guides often show 4/24; do not
assume that quota applies to a new free tenancy. Check the console's actual
Always Free eligibility and estimated cost before creating anything.

Start with one VM, one district and modest disk allocation. A 2-core/4–6 GB
runtime allocation is a measurement starting point, not a benchmarked guarantee;
engine compilation may need more memory. The expanded game simulates many
areas even with few connected players. Measure RSS, CPU and game tick behavior
before deciding the smallest reliable size. Build Astron and the custom engine
for Linux ARM64, not macOS ARM64.

Free capacity can be unavailable. Oracle may reclaim idle instances; therefore
free does not mean guaranteed 24/7 availability. Do not generate fake load to
evade reclamation. Keep off-VM backups and a restore procedure. Don't enable
paid upgrades/resources just to bypass capacity limits.

Sources: [Always Free resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm),
[Free Tier FAQ](https://www.oracle.com/cloud/free/faq/).

## Network and authority boundary

- Device → encrypted private network (for example WireGuard) → VM clientagent,
  TCP **7198**, bound to that private interface only.
- Message Director **7199/TCP** and Event Logger **7197/UDP** bind to loopback.
  Databases and AI/UD services are not public endpoints.
- Permit only the chosen VPN's transport and restricted administrator SSH in
  the provider firewall. Do **not** open 7197–7199 to the internet. Also enforce
  this with the guest firewall. Private addressing alone does not encrypt data.
- A signed iPhone app will connect using its own invitation, with a VPN client
  active for this initial deployment. Public TLS/auth infrastructure without a
  VPN can be a later, separately tested deployment mode.
- Legacy `dev` login creates administrators in the local setup. Dedicated
  startup requires the new `invite` backend and defaults to ordinary players.
  Issued 256-bit secrets are stored only as hashes, expire, and can be revoked.
  Never share one credential among friends or embed it in an IPA/repository.

This does not constitute a complete adversarial security audit of the legacy
game protocol. There is no public registration/password reset, internet-facing
TLS gateway, anti-abuse rate limiter, or public launch hardening in this pass.

## Prepare the VM (operator steps, not yet executed)

1. Obtain user approval for the provider/account/region and confirm $0 resource
   limits. Use an Always Free eligible Ubuntu ARM64 image, not a paid shape.
2. Install compatible build tools and a Python environment; build the fork
   recorded in `ios/engine.lock` for **Linux** with OTP/Toontown features and
   ODE/physics as required. Do not substitute stock `pip install panda3d`.
   Build a compatible Astron binary separately. Pin tested revisions before
   making the deployment repeatable. Native builds are not supplied by this PR.
3. Put the game checkout and full resources checkout under `/opt/open-toontown`.
   Use `/opt/open-toontown/venv/bin/python` with the custom native modules and
   `requirements.txt`. Put the Linux executable at `bin/astrond`.
4. Create an unprivileged service user/group `toontown`. The app/code/resources
   should be readable but not writable by that user. State belongs in
   `/var/lib/open-toontown` (0700, owned by `toontown`). This is a **fresh**
   hosted database, not an automatic migration of local Toons.
5. Configure the encrypted private network and provider/guest firewall. Copy
   `deploy/systemd/server.env.example` to `/etc/open-toontown/server.env` and
   set `TOONTOWN_BIND` to the VM's VPN IPv4 address. The example is loopback
   deliberately; it accepts no remote players until configured.
6. Check dependencies, without launching anything:

```sh
cd /opt/open-toontown
venv/bin/python -m server.run --astron /opt/open-toontown/bin/astrond --state /var/lib/open-toontown --bind 10.70.0.1 --check
```

7. As the service user, issue one credential per identity. Output is the secret;
   deliver privately, do not paste it into a PR or logs. The same identity can
   receive a replacement credential without losing its Toon/account link.

```sh
sudo -u toontown venv/bin/python -m server.accounts --db /var/lib/open-toontown/accounts.sqlite3 issue friend_name
```

Default expiry is 30 days; `--days` accepts 1–365. Existing privileges are not
changed by issuing another credential. Only deliberately designated staff
should be created with `--access ADMIN`. No staff account is created automatically.

8. Copy the provided service to `/etc/systemd/system/open-toontown.service`,
   review the paths, then enable it:

```sh
sudo systemctl daemon-reload
sudo systemctl enable --now open-toontown
sudo journalctl -u open-toontown -f
```

The supervisor starts Astron, waits for its ports, starts UD, waits for its
readiness message, then starts AI and waits for its readiness message. Startup
times out after 180 seconds per service. Any unexpected child exit fails the
whole stack, and systemd restarts the dependency chain. Rapid repeated failures
are rate-limited instead of spinning forever. A process lock prevents duplicates.
Only the supervisor's child process groups are stopped, never other processes.

Install `deploy/logrotate/open-toontown` in `/etc/logrotate.d/` to bound logs.
The normal distro logrotate timer must be enabled. `copytruncate` can lose a
small amount of concurrent log output; this is not used for account data.

## Connect without any local server

On the existing Mac (VPN connected), from a complete game checkout using the
working custom Panda Python:

```sh
python3.9 -m tools.play_remote --server 10.70.0.1 --user-data /Users/YOUR_USER/Library/ApplicationSupport/OpenToontownRemote
```

Use an actual writable path outside the checkout. Paste the invitation into
the hidden prompt. Do **not** run `start-all.command`; it starts local servers.
This launcher starts only the game, against the specified private endpoint.
It is also the Python-side connection route being prepared for the native app.

## Persistence, backups and acceptance checks

Keep **all** of `/var/lib/open-toontown`: Astron YAML accounts/Toons, the SQLite
identity bridge, world state and spellbook configuration. Backing up only one
database loses the identity/account relationship. For this small server, stop
the service for a consistent snapshot, archive the state as administrator,
copy it to private off-VM storage, then restart. Do not tar the live YAML/SQLite
files as if that were a consistent backup. Test restoring to an isolated VM
with the same code/DC/resources before relying on a backup. No automatic
backup service or external storage has been provisioned by this PR.

Revocation blocks future login, not an already active session; disconnect that
account or restart the private stack when immediate revocation is needed:

```sh
sudo -u toontown venv/bin/python -m server.accounts --db /var/lib/open-toontown/accounts.sqlite3 revoke friend_name
```

Before calling it live, verify: two separate friends can connect; no public
game/admin/database ports; `dev` is rejected; nonstaff cannot run admin commands;
Toons survive VM restart; one killed service recovers the complete stack;
routine battle/elevator/zone changes work; a backup restores; no secrets appear
in logs. Then profile the busiest expanded HQ and an eight-Toon boss instance.
