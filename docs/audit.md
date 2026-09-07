# Reference audit — 2026-09-06

The reference is Artix Linux, runit, Framework Laptop 13 with Intel i5-1240P.
This audit precedes implementation. No packages, services, home configuration,
boot entries or filesystem layout were changed to capture it.

## Existing sources of truth

| Repository | Published/local HEAD | Coverage |
| --- | --- | --- |
| Magneedo/dotfiles | `32f471b758181d440841aa7653869b4b84899644` | Bash, Vim, application config, user scripts, session/audio startup, selected runit overrides, doas, hibernate, previous machine/storage audit |
| Magneedo/dwl | `c4afddfae04c6904192aee81d8914d0ce6cd3b7b` | Patched compositor, config.h, wlroots 0.19 build, XWayland |
| Magneedo/dwlb | `b62ef6c0ed6fa6ccd9dcd16a912dccc9ee27931a` | Bar, config.h, build |

The existing checkouts are retained. Dotfiles has an unstaged deletion of its
Windows launcher; dwl has an unstaged config.h change adding the lf keybinding;
dwlb is clean. Live files also differ from dotfiles for dhcpcd/run,
wireless-regdom, btop, swaylock and dwl-autostart. Capture reviewed differences
as small patches and missing files here, pinned to existing repository commits.
Do not reset, stage, commit or push the user's existing worktrees.

## Working system and gaps

- Eleven enabled services: agetty-tty1, agetty-tty2, bluetoothd, chrony, dbus,
  dhcpcd, mullvad, seatd, sshd, udevd, wpa_supplicant. Definitions are in
  /etc/runit/sv; current points to default. Bluetooth, Mullvad and SSH have
  locally supplied service scripts, rather than installed *-runit packages.
- tty1 autologin as bren → Bash → dwl-session → dbus-run-session → dwl
  → dwl-autostart. The session starts foot server, dwlb/statusd, wallpaper,
  PipeWire, pipewire-pulse, WirePlumber and portals. No custom PipeWire or
  WirePlumber config files were found. Do not restore their mutable state.
- Native explicit package inventory and all eight foreign packages are available
  through Pacman. Native dependencies needed directly by builds/services/scripts
  must be promoted to a separate runtime manifest. Historical package versions
  are evidence, not a rolling-release downgrade lock.
- Pacman repositories: system, world, galaxy, lib32, extra, multilib, with Artix
  first and artix-archlinux-support installed. Capture repository setup without
  replacing mirror selections with a stale mirror snapshot.
- EFISTUB boot entry Artix loads \\vmlinuz-linux, \\intel-ucode.img, then
  \\booster-linux.img. Kernel parameters include root=UUID, rootflags=subvol=@,
  rootfstype=btrfs, rw, rootwait, init=/sbin/init, resume=UUID, quiet, loglevel=4.
  No GRUB or systemd-boot. Current Artix entry is 0000; firmware assigns new
  entry numbers on restore. Do not copy UUIDs or partition GUIDs.
- GPT: 512 MiB FAT32 ESP at /boot, approximately 899 GiB Btrfs containing @
  (including /home) and @snapshots mounted at /.snapshots; 32 GiB dedicated
  swap. Mount intent is in fstab: noatime, compress=zstd:3, ssd,
  discard=async, space_cache=v2, commit=30. Sandbox bind mounts are not the
  physical installation's mount policy.
- Booster uses a host-specific image, zstd, vconsole, Btrfs/NVMe modules,
  early i915 and busybox. Hibernation has already been physically tested in
  the previous audit; this task will not hibernate or reboot the machine.
- Missing system policy includes dhcpcd metrics (eth0 1000, wlan0 3000),
  Bluetooth DeviceID, PAM/limits differences, local power wrappers,
  kvm ignore_msrs, cros_usbpd_charger blacklist and webcam USB access rule.
- Wi-Fi profile names home/hotspot/school are inputs to net; credentials,
  identities and certificates must be supplied separately. Mullvad account
  state, SSH keys and host keys are also excluded.
- Noto fonts and fontconfig preferences are package/dotfile supplied. User
  font directory is empty. Wallpaper is a personal file at
  ~/Pictures/Screensaver/Screensaver and must be restored separately.
- Current Windows launcher and Python RDP readiness helper are absent from the
  published configuration. Launcher reads WINPASS from the environment or
  ~/.config/windows-rdp.env; preserve scripts, exclude that file and VM disks.
- No cron directories, custom Pacman hooks, modules-load.d, sysctl.d or active
  user service tree were found in the initial read-only scan. Monthly Btrfs
  scrub is manual per existing storage-maintenance.md; do not add a scheduler.
- Python, C build utilities, Java and Deno are installed. Go/Rust/Node/npm/pnpm,
  Flutter/Dart, CMake and Ninja are absent from the current executable/package
  environment. Old language caches are not evidence to reinstall these tools.

## Audit boundaries

Never copy /etc or $HOME wholesale. Review an explicit file allowlist.
Exclude credentials, certificates, browser/application state, personal files,
VM and game data, caches, logs, machine-id, generated host keys and historical
snapshots. Application scene/service files in dotfiles need an explicit review
before inclusion; the bootstrap must not blindly deploy the entire repository.

The initial sandbox mapped unrelated users to nobody and hid host groups.
Those observations were supplemented by host inspection and an authenticated,
read-only audit on 2026-09-07. See the protected findings below; raw reports
remain in ignored `local/` and are not part of this repository.

## Final capture decisions

GitHub confirmed all three pins above. There are 130 explicit packages: 122
native, seven available through AUR RPC, and mullvad-vpn-cli whose original AUR
recipe was recovered from surviving Git history. The recipe at
`1f542474a3e05301c3025a46f54ac8c1234c8ed0` matches the installed version and install
script and is the sole local package recipe retained here. The full native
dependency closure was also resolved against an empty local Pacman database;
no installed native package was left out of that simulated restoration.

68 files are managed through the explicit allowlist, including staged desktop
build artifacts. btop's version/default additions and swaylock/autostart changes
are preserved as a small dotfiles patch. Wireless-regdom's added comment lines
and unchanged pacman-contrib defaults need no override. Existing OBS recording
intent is retained as a small seed profile plus the two original encoder files;
scenes, cookies, streaming-service data and GUI state are excluded. The installed
dwl manpage is older than the source and is informational drift only.

Real host observations confirmed groups audio/input/kvm/network/seat/storage/video/
wheel; the recorded capabilities; dash as /bin/sh; bren's subordinate ID ranges;
New York timezone; current EFI parameters; and the active audio/desktop processes.
No user-installed fonts or additional active language toolchains were discovered.

## Authenticated protected findings — 2026-09-07

- Live doas policy matches the pinned dotfiles source exactly. Its root-owned
  mode is 0600; the deployment manifest now captures that mode.
- All eleven runit supervisors reported running services. Protected crypttab,
  default/useradd, libaudit.conf and sshd_config match their package backup hashes.
- The polkit rule `99-artix.rules` and SSH includes `99-artixlinux.conf` and
  `20-elogind-userdb.conf` are supplied by polkit, openssh and elogind. The last
  include is a package symlink to `/usr/lib/elogind/sshd_config.d/`. File contents
  match package integrity checks; reinstall their packages, without local copies.
- `/etc/polkit-1/rules.d` is root:polkitd, mode 0750. The package archive records
  root:root, so the group difference is explicitly captured in directories.tsv
  and restored by the permissions stage. Pacman integrity verification permits
  only this specific warning and verifies the actual directory owner/group/mode.
- No cron spool entries or cron.d entries exist and crontab is not installed.
  The protected inspection found no extra local SSH includes or polkit rules.
- All three Wi-Fi profiles are root-owned mode 0600. Their non-secret settings
  use `/run/wpa_supplicant`, update_config=1 and country=US; hotspot additionally
  uses scan_ssid=1. School uses WPA-EAP-SHA256, ieee80211w=2, PEAP and inner
  MSCHAPV2. Methods are recorded in wifi-methods.tsv and secret-free templates;
  SSIDs, PSKs, identities and passwords are excluded. No CA or server-name
  validation directives were present; institutional trust settings remain manual.
- Btrfs contains the intended @ and @snapshots plus historical snapshots and old
  root subvolumes. Those historical contents/layout remnants are state, not
  additional subvolumes required by the restore.

The complete procedure and validation limits are in install.md and validation.md.
