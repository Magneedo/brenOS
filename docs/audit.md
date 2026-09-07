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

The sandbox maps unrelated users to nobody and hides host groups. Privileged
read-only audit is required to verify doas, protected PAM/polkit/SSH policy,
groups, capabilities, Btrfs subvolumes and scheduled jobs. doas -n requires
local authentication; any remaining blind spots must be reported honestly.
