# Networking, services and audio

## Runit

The restore enables ten links in `/etc/runit/runsvdir/default`:
agetty-tty1, agetty-tty2, bluetoothd, chrony, dbus, dhcpcd, seatd, sshd,
udevd and wpa_supplicant. `current -> default`; `/run/runit/service` selects it.
The standard Artix service definitions live in `/etc/runit/sv`.
[Artix runit implementation](https://github.com/artix-linux/runit-artix)

agetty/udev come through the base runit packages; dbus-runit, chrony-runit,
dhcpcd-runit, seatd-runit and wpa_supplicant-runit are installed. The reference
does not install bluez-runit or openssh-runit: Bluetooth and SSH have small
captured local definitions. Bluetooth also has an svlogd service;
its log directory is created, but old logs are not restored.

tty1 autologins bren, tty2 remains a password login. seatd runs with group `seat`
and checks `/run/seatd.sock`. Bluetooth waits for the system D-Bus socket, then
runs foreground with the battery plugin disabled. SSH runs foreground and uses
package-default OpenSSH configuration, the packaged Artix/elogind include files
and separately generated host keys. chrony is the
time service. elogind, polkit, rtkit and user D-Bus services may be activated on
demand; they are not extra runit links to invent. The polkit rule comes from its
package; the permissions stage preserves `/etc/polkit-1/rules.d` as root:polkitd,
mode 0750, using the target's group ID rather than a copied numeric allocation.

Use `doas sv status /run/runit/service/*` to inspect supervisors. To deliberately
restart one after a config change, use e.g. `doas sv restart /run/runit/service/seatd`
from a suitable console. The bootstrap does not restart the active desktop or
network. Upgrades can replace package-owned overrides; compare `.pacnew` files
and run verification. The prior audit explicitly accepted this normal maintenance
model; no automatic repair/upgrade-protection mechanism is introduced.

## Wi-Fi and Ethernet

The networking stack is wpa_supplicant + dhcpcd, not NetworkManager or iwd.
The Framework profile uses `wlan0` and `eth0`. dhcpcd runs foreground with
`-B -q -w`, uses private IPv6 SLAAC, and assigns IPv4 route metrics 1000 for
Ethernet and 3000 for Wi-Fi. `/etc/resolv.conf` and DHCP leases are generated
runtime state; do not copy their current nameservers or leases.

`/etc/runit/sv/wpa_supplicant/conf` chooses `/etc/wpa_supplicant/home.conf`
and wlan0 by default. The captured run script creates `/run/wpa_supplicant`
root:wheel mode 0770. The actual profiles specify
`ctrl_interface=/run/wpa_supplicant`, without an explicit GROUP option. The
templates retain that configuration. See [secrets.md](secrets.md) for private profile
creation; home, hotspot and school are logical names, not saved SSIDs.

After supplying profiles, `net home`, `net hotspot`, `net school`, and `net eth`
use the existing dotfiles helper to switch connections. It writes the selected
profile into the runit service configuration; a later boot uses that choice.
Consequently the verifier may report intentional drift from the home default
after selecting a different profile. Don't reapply home merely to clear a report
if you intend to stay on another network.

On different hardware, inspect `ip -br link`. Update the service configuration,
dhcpcd interface sections and the helper's `WIFI_IFACE`/`ETH_IFACE` environment
overrides together. The service script's Framework preflight explicitly requires
wlan0, so adjust that check when maintaining a different hardware profile. No
MAC-address rule or stored wireless secret is used to force device naming.

`wireless-regdb` is installed. All country assignments in the reference
`/etc/conf.d/wireless-regdom` are commented out; the file's difference from
dotfiles is only an updated list of comments. Package defaults are sufficient.
Supply the correct regulatory country locally where required rather than copying
a country inferred from a Wi-Fi SSID. The authenticated audit confirmed that
each private profile separately sets `country=US`; the templates and method
manifest capture that observed value. Adjust it deliberately when operating in
a different regulatory region.

For problems, use `ip -br link`, `ip route`, `wpa_cli -i wlan0 status`, and the
runit status commands. These can print SSIDs/IP addresses; do not paste their
output into Git. Diagnose association and address/DNS acquisition separately.
Confirm no second standalone wpa_supplicant/dhcpcd instance from temporary
installation networking is competing with the supervised service.

## Audio, portals and session startup

tty1 → Bash → `~/.local/bin/dwl-session` → `dbus-run-session -- dwl` →
`~/.local/bin/dwl-autostart`. The wrapper sets the dwl/Wayland XDG variables and
uses `/run/user/1000` when available, otherwise a user-owned mode-0700 temporary
runtime directory. Autostart updates the D-Bus activation environment before
starting applications.

The existing script starts PipeWire, waits for its socket, then starts WirePlumber
and pipewire-pulse if not already running. There are no additional PipeWire or
WirePlumber config files in `/etc` or `~/.config`. Packages supply ALSA/JACK/Pulse
integration; mutable volumes, selected devices and Bluetooth pairings are not
versioned. The captured patch removes an older repository-only command that reset
volume to 50% and unmuted it on every login, matching the live session script.

xdg-desktop-portal and xdg-desktop-portal-wlr run in the same user bus/session.
`portals.conf` selects gtk generally and wlr for ScreenCast/Screenshot. Do not add
systemd user service commands or a second runit audio stack. foot server, wallpaper,
dwlb and statusd are started by the same session; the Noto font packages and
fontconfig aliases provide the terminal/bar/status glyphs.

After login, run `wpctl status` and `wpctl get-volume @DEFAULT_AUDIO_SINK@`, test
playback and microphone recording, and test screen sharing through a browser or
OBS. Use runtime logs under `$XDG_RUNTIME_DIR` for diagnosis; they are not captured.
If audio/portals are missing, check the session's XDG variables and user D-Bus
before starting duplicate daemons. A clean logout/login is often the simplest
way to apply session changes.

Pair devices anew with bluetui/bluetoothctl. Bluetooth uses the captured
`DeviceID = bluetooth:004C:0000:0000` and the existing `-P battery` service flag.
Do not restore pairing keys from `/var/lib/bluetooth` through Git.

OBS gets a small recording profile derived from the existing dotfiles: advanced
output, x264 MKV recordings in `~/Videos/Recordings`, 2880×1920 at 60 FPS,
48 kHz stereo, the existing encoder settings, and VAAPI selection. Scene/source
IDs, portal grants, service/stream keys, window state and cookies are excluded.
Select the Untitled profile, create a fresh screen-capture source and grant the
portal permission interactively; add the desired audio sources and verify a short
recording before relying on it.
