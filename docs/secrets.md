# Manual inputs and excluded state

These inputs intentionally live outside Git. A clean OS plus this repository
cannot recreate private accounts, personal files or a licensed Windows VM from
nothing. Keep an independent backup and restore the items you still use.

| Input | Where/how to supply it |
| --- | --- |
| bren/root passwords | `passwd`; never copy shadow/gshadow |
| Fingerprints | Enroll again with `fprintd-enroll bren`; test with `fprintd-verify bren` |
| GitHub and SSH access | Authenticate gh; restore/generate private keys in `~/.ssh` with correct permissions |
| Git identity | `git config --global user.name ...` / `user.email ...`, supplied locally |
| Wi-Fi | Root-owned mode-0600 `home.conf`, `hotspot.conf`, `school.conf` under `/etc/wpa_supplicant` |
| Enterprise Wi-Fi | Institution-supplied EAP method, identity, password, CA/client certificate/key and server-name validation policy |
| Wallpaper | `~/Pictures/Screensaver/Screensaver` |
| Lockscreen image | `~/Pictures/Lockscreen/Lockscreen.jpg` |
| Windows VM | `~/VM/Windows/disk.qcow2` and its matching `OVMF_VARS.fd` from a cleanly shut-down VM backup |
| RDP login | `WINPASS` environment variable or mode-0600 `~/.config/windows-rdp.env`; optional WINUSER |
| Application/tool logins | Authenticate browsers, Steam/Prism, IPTV sources, development/cloud tools and streaming services normally |
| SSH host keys | Generate new keys with `ssh-keygen -A`, or restore deliberately from a private backup if identity continuity is required |
| Disk UUIDs/EFI number | Derive on the newly installed disk; render under ignored `local/boot` |

Never commit Wi-Fi files, identity certificates, SSH/GPG material, tokens,
`~/.config/gh/hosts.yml`, OBS stream/service settings,
browser profiles, shell history, VM firmware state/images, application databases,
game data, recordings, caches, logs or historical snapshots. Private-repository
visibility is not a reason to store credentials. Git ignore rules are a convenience;
an explicit allowlist and content review are the primary safeguards.

## Wi-Fi profiles

The captured service uses `/etc/wpa_supplicant/home.conf` initially. Create the
directory, then create/edit each profile locally. Use the examples only as guides;
do not overwrite an existing valid profile on a rerun:

```sh
doas install -d -m755 /etc/wpa_supplicant
doas vi /etc/wpa_supplicant/home.conf
doas chown root:root /etc/wpa_supplicant/home.conf
doas chmod 600 /etc/wpa_supplicant/home.conf
```

Keep the directory traversable (0755) while the files stay private (0600). The
existing unprivileged `net` helper checks whether a named profile exists before
using doas; changing the directory to 0700 would break that check.

For WPA-Personal, see `templates/wpa-personal.conf.example`. A PSK can be generated
locally using `wpa_passphrase 'YOUR_SSID'` with the passphrase supplied on stdin,
not as a command-line argument. Its output includes a commented cleartext
passphrase; remove that comment when saving. The generated PSK is still a secret.
The service's control directory is root:wheel mode 0770. The authenticated
reference profiles use `ctrl_interface=/run/wpa_supplicant`, `update_config=1`
and `country=US`, with no explicit GROUP option. Retain the observed header;
choose the correct country when installing in a different regulatory region.

Create hotspot.conf from the personal template and add `scan_ssid=1`, matching
the reference. Create school.conf using `templates/wpa-school.conf.example`:
WPA-EAP-SHA256, required protected management frames (`ieee80211w=2`), EAP-PEAP
and inner `auth=MSCHAPV2`. Supply the SSID, identity and password locally. These
method options follow the [upstream configuration format](https://chromium.googlesource.com/external/w1.fi/cgit/hostap/+/refs/tags/hostap_2_5/wpa_supplicant/wpa_supplicant.conf).

The reference school profile has no CA certificate or server-name validation
directives. Institution-specific CA/trust and server-name settings must be
obtained from the institution; none were available to capture. Certificates and
private identities remain outside Git. The template records the observed
authentication method without inventing institutional trust values.

Only `home.conf` is a prerequisite for the service stage. The verifier also checks
the presence/private permissions of hotspot and school, because the existing net
helper exposes all three; the protected verifier also checks the non-secret
settings in `manifests/wifi-methods.tsv`. If a profile is no longer used, record that deliberate
scope change rather than copying stale credentials.

## Desktop personal files

```sh
mkdir -p ~/Pictures/Screenshots ~/Pictures/Screensaver ~/Pictures/Lockscreen ~/Videos/Recordings
```

Restore the two image files from your personal backup. For a different image,
update its path in the appropriate original dotfile/script and capture the change
deliberately. Test `swaylock` with a missing/changed image before depending on the
hibernate wrapper; do not assume an absent asset has no effect on locking.

## Windows launcher

The captured `windows` script runs an existing QEMU guest, exposes RDP only on
127.0.0.1:3390, waits for RDP negotiation using its Python helper and launches
FreeRDP through XWayland. It does not provision Windows. The default guest username
is the existing configured name; override with WINUSER or a positional argument.
Never put WINPASS on the command line. Create the private configuration with a
local editor, based on `templates/windows-rdp.env.example`, and `chmod 600` it.

The helper's Framework defaults use CPUs 8–15, 6 GiB RAM and four virtual CPUs.
Set `PIN_CPUS`, `RAM` and `SMP` locally if restoring elsewhere. `DISK`, `VM`,
`OVMF_CODE`, `OVMF_VARS`, and `PORT` are also overridable. Only use a VM copy that
was shut down cleanly, with its matching mutable OVMF variables. The launcher can
initialize variables from the installed OVMF template when none exist, but that
is not equivalent to restoring the guest's previous firmware state. Windows,
Office, guest drivers, guest RDP enablement and licensing remain manual.

The existing FreeRDP behavior uses localhost, NTLM and `/cert:ignore`; that scope
is preserved for the local forwarded guest. No guest certificate or credential
is copied. The launcher passes RDP arguments via stdin rather than putting its
password in process arguments.

## Persistent configuration not to infer from state

The authenticated audit confirmed no cron spool/cron.d entries and no installed
crontab command. Monthly Btrfs scrub is an explicit manual maintenance task in the existing
dotfiles documentation, not a missing scheduler. No new scrub timer, balance,
defragmentation, snapshot pruning or smartd daemon is installed here. Protected
polkit/SSH policy is supplied by checked packages, with the recorded polkit
directory permission restored separately. Future custom policy or scheduled
entries are reported for review rather than assumed to be covered.
