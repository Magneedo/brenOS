# Manual inputs and private files

Run `brenos` as root on the fresh, bootable Artix runit install. It asks for a
username (default `bren`) and sets a password for a new account. Supply the rest
locally after installation. Keep an independent private backup.
- Set the root password yourself; never copy shadow/gshadow into Git.
- Enroll and check a fingerprint with `fprintd-enroll` and `fprintd-verify`.
- Authenticate GitHub/SSH and set Git user.name/user.email locally.
- Restore desktop images, Windows files and application logins privately.
- Derive disk UUIDs and EFI entry numbers on the target; see [boot setup](boot.md).

Never commit credentials, SSIDs, institution names, identities, certificates,
private keys, tokens, serials or this machine's UUIDs. Browser profiles, gh
hosts.yml, stream settings, history, VM images/firmware, databases, recordings,
logs and snapshots stay outside the public repository too.

## Wi-Fi profiles
`brenos` enables the Framework Wi-Fi service but supplies no private profiles.
Use `templates/wpa-personal.conf.example` for home.conf or hotspot.conf:

```sh
cd ~/Projects/brenOS
doas install -d -m755 /etc/wpa_supplicant
doas install -m600 templates/wpa-personal.conf.example /etc/wpa_supplicant/home.conf
doas vi /etc/wpa_supplicant/home.conf
```
Copy a template only when the destination is new; preserve working profiles.
Keep profiles root-owned, mode 0600, and the directory 0755. The `net` helper
uses doas to switch profiles. Choose the correct country code locally.
Generate a PSK with `wpa_passphrase 'YOUR_SSID'`, entering the password on stdin.
Remove its commented cleartext password; the generated PSK is also secret.
For a hidden hotspot, add `scan_ssid=1`.

Enterprise Wi-Fi starts with `templates/wpa-school.conf.example`. Its example
uses PEAP/MSCHAPV2, WPA-EAP-SHA256 and required management-frame protection.
Obtain the institution's EAP method, CA and server-name validation policy first;
the template alone is incomplete. Supply SSID, identity and password privately.
Store any certificates/keys locally. Restart the service or select a profile
with `net` once it is ready.

## Vault and agents
`brenos` does not clone Vault or add its bind mount. As the desktop user,
authenticate GitHub, then clone your private Vault without replacing an existing one:

```sh
git lfs install
gh repo clone Magneedo/vault ~/Vault
cd ~/Vault
git lfs pull
```
`codexclaude` expects `~/Vault/Agents`. `dwl-session` exports CLAUDE_CONFIG_DIR
and CODEX_HOME to its `.claude` and `.codex` directories; add nothing to shell
profiles. Restore credentials privately or log in normally. Settings alone do
not restore memories, authentication or local skill links; follow your Vault rules.

Create both directories as the desktop user. Preserve any files in the mount
target before mounting over it:

```sh
mkdir -p ~/Vault/Agents/.codex/memories ~/Vault/Agents/Memory/Codex
```

Add this to `/etc/fstab` with `doas vi /etc/fstab`; replace `bren` for another user.
Use a bind mount, not a symlink:

```fstab
/home/bren/Vault/Agents/.codex/memories /home/bren/Vault/Agents/Memory/Codex none bind,nofail 0 0
```
Run `doas findmnt --verify --verbose`, then `doas mount ~/Vault/Agents/Memory/Codex`.
Confirm it with `findmnt --mountpoint ~/Vault/Agents/Memory/Codex`.

## Desktop files and Windows
Restore `~/Pictures/Screensaver/Screensaver` and
`~/Pictures/Lockscreen/Lockscreen.jpg`; create your Pictures/Videos directories.
Check `swaylock` before relying on hibernation.

Restore a shut-down `~/VM/Windows/disk.qcow2` with its matching `OVMF_VARS.fd`.
Copy `templates/windows-rdp.env.example` to `~/.config/windows-rdp.env`, edit it
locally and chmod it 600. Supply WINPASS there; never pass it on the command line.
Adjust WINUSER, PIN_CPUS, RAM and SMP for your guest and hardware. Windows/Office
licensing, drivers and RDP enablement are manual. Restore other app logins normally.
