# Verification and troubleshooting

## Safe rehearsals

After preparing sources and building/staging the desktop:

```sh
scripts/check
python3 tests/rehearsal.py
python3 tests/installer.py
python3 tests/bootstrap.py
scripts/files --profile framework --scope all --root .work/rehearsal
scripts/files --profile framework --scope all --root .work/rehearsal --apply
scripts/files --profile framework --scope all --root .work/rehearsal --apply
scripts/verify --profile framework --root .work/rehearsal
```

`--root` is a filesystem rehearsal, not a chroot or installer. It only copies
allowlisted files into that directory. It does not install packages, assign real
system ownership, run services or touch firmware. The second apply should report
zero changes. Tests cover no-write previews, conflict preflight, backed-up
replacement, symlink escape refusal, boot-input validation and default previews.
Installer tests use fake stage commands and a temporary local Git recipe with a
stubbed makepkg call. They check stop/resume behavior, privilege boundaries,
manual boot gates, failure propagation and the fresh yay bootstrap path without
installing packages or touching the running system. The real top-level preview is
`./install --profile framework --dry-run`. Phase-0 tests also cover missing tools,
wrong OS/init/account, ESP checks, policy creation/refusal, root boundaries,
reruns and handoff using fake commands and temporary paths.
`./bootstrap --dry-run` needs no Python and changes nothing.

`scripts/check` ensures all 129 intended explicit packages have a manifest, every local
file source is tracked, destinations are unique, source inputs exist, scripts
parse and obvious secret/binary artifacts are absent. Stage intended files before
running it, since it inspects Git's file list. It is a useful check, not a complete
secret detector: review new content and staged diffs before each commit.

## Installed-host comparison

Run from an ordinary terminal outside a sandbox. The sandbox used during capture
maps host groups/owners and mount flags differently and cannot read some service
status files. For a complete privileged comparison after graphical login:

```sh
cd ~/Projects/artix-bootstrap
doas scripts/verify --profile framework
umask 077
mkdir -p local
doas -n scripts/audit-privileged \
  > local/privileged-audit.json
doas -n scripts/verify --profile framework --json \
  > local/verification.json
```

Authenticate on the first command, where the fingerprint/password prompt is
visible. The optional report commands use cached authentication in the same
terminal; `-n` fails if it has expired. Rerun the first command if needed. The
backslashes continue commands across lines; never split a script/file name at
its hyphen. Reports stay in ignored `local/` with a private umask.

The collector reads a protected configuration allowlist, metadata and selected
non-secret Wi-Fi method settings. Review its report locally; do not commit or
publish it wholesale. It extracts allowed settings and field names from private
Wi-Fi profiles but excludes SSIDs, PSKs, identities and passwords from the report.
It never opens private keys, certificates or password databases.
The collector does list cron entries if present, so review those privately too.
Account passwords/shadow contents are never captured.

When run as root, the verifier also collects current protected audit data and
flags changed protected package defaults, custom polkit/SSH include files and
scheduled entries that lack a restoration definition. `pacman -Qkk` checks the
three packages supplying protected policy. Its one known polkit directory GID
warning is accepted only alongside a separate root:polkitd/0750 comparison;
additional warnings or changed rule contents still fail. When run unprivileged, a
saved report is only historical evidence and is labelled for review.

Verifier exit codes: 0 means the automated comparisons passed, 1 means managed
state is missing/different, 2 means a comparison was incomplete (for example
permission denied). `REVIEW` identifies extra packages/services or the reference's
older manpage; `MANUAL` records required physical tests. Zero is not proof that
the machine boots or that hibernation works.

Comparisons include managed contents/modes/owners, required packages, repository
order, groups, subordinate ranges, capabilities, directory permissions, enabled/running services,
desktop library resolution, Noto fonts, user audio/portal/session processes,
fstab and mounted filesystem UUIDs/subvolumes, EFI kernel entry, kernel arguments,
resume partition, private profile methods and manual asset/profile presence. OBS is checked against its
managed key subset; extra application state is not compared or exported.

The binaries are tested by rebuilding their pinned sources and checking installed
runtime libraries, not by demanding identical binary hashes across compilers or
build paths. The reference's manpage predates its source checkout; restoring the
current source manpage is an informational documentation difference.

## Physical acceptance tests

1. Boot via the new Artix EFI entry. Confirm tty1 autologin and dwl, and tty2
   password login. Confirm `doas` works with password fallback as well as any
   newly enrolled fingerprint.
2. Exercise launcher/terminal/lf, browser, screenshots and clipboard, brightness,
   volume/mute, bar status and wallpaper. Check screen lock and both password
   and fingerprint unlock before relying on power actions.
3. Use home/hotspot/school Wi-Fi as applicable and Ethernet.
   Verify DNS and routing. Pair/test Bluetooth devices.
4. Check speakers/headphones/microphone, video acceleration, screen sharing and a
   short OBS recording. Reauthorize portal source selection after reinstalling.
5. Restore a cleanly shut-down Windows VM backup and private RDP configuration;
   run `windows`, verify clipboard/session behavior and shut down the guest normally.
6. Save work, confirm active swap/resume UUID, then test ordinary suspend and
   separately run `hibernate` from Wayland. Check that resume returns to a locked
   session and unlock works. Do this on the target, not as an unattended test.

## Troubleshooting and rollback

- **File stage conflict:** it did not overwrite the conflicting file without
  `--replace`. Review both files. If replacing, use the backed-up apply option.
  To roll back, copy the particular saved file back with its correct owner/mode;
  do not copy the whole backup directory over `/`.
- **Root ownership or permissions:** run home scope as bren and system scope
  with doas. Log out after group changes. Check seatd/socket, KVM device, PAM,
  capabilities and setuid bits. Reapply only the affected permission stage.
- **Desktop compile/link failure:** confirm wlroots-0.19, wayland-protocols,
  xcb-util-wm and fcft are installed. Review ABI changes and source pins; never
  alias a different wlroots library to the required soname. Fix the source/build
  against the new ABI only as a deliberate maintenance change.
- **Source checksum mismatch:** a prepared source file changed. Preserve any
  intended edits outside `.work`, update the original repo or patch, and generate
  a new version. Do not disable the checksum check to hide unknown source edits.
- **No desktop on tty1:** use tty2; check executable bits on dwl/session/autostart,
  Bash startup files, runtime-directory ownership and seat group/socket. Keep
  the working tty2/root console while fixing autologin or PAM.
- **Runit service down:** inspect `doas sv status`, missing `run`/`conf`, a `down`
  file, missing profile/resource directory or logger directory. Never substitute
  a second init system to make a service command work.
- **No network/audio/screen share:** follow [network-audio.md](network-audio.md)
  and inspect private runtime logs locally. Do not commit logs or cached state as
  a configuration fix.
- **Boot/resume failure:** use the live-media procedure in [boot.md](boot.md),
  verify mounts and new UUIDs, and restore/rebuild a matching kernel/image pair.
- **Package upgrade overwrote policy/capabilities:** inspect `.pacnew` and compare
  manifests. Reapply the intended files/permissions after review. This is the
  reference's accepted normal maintenance process; no automatic overwrite hook
  races package upgrades.

Storage maintenance remains manual: on AC power, run a monthly
`doas btrfs scrub start -B --limit 256M /`, inspect `doas btrfs scrub status /`
and `doas btrfs device stats /`, and occasionally use smartctl for NVMe health.
The existing dotfiles `docs/storage-maintenance.md` contains the full rationale.
Do not schedule pruning, balance, defragmentation or firmware changes as part of
this restoration.
