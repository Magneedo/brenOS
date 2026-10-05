# brenOS

bren's Artix Linux desktop in one script, in the spirit of
[LARBS](https://larbs.xyz): install a bare Artix system, run `brenos` as root,
answer a few questions, and get the dwl desktop with all its programs,
configuration and services. Made for a Framework Laptop 13 (Intel), and
usable without the Framework extras on other x86_64 machines.

## Installation

1. Install Artix Linux with **runit** from the Artix ISO. Partition, install the
   base system and a bootloader, set the root password, and include `dhcpcd`
   for the network. Don't create a user: brenos does. On the Framework, use
   [the reference layout](docs/boot.md) while partitioning.
2. Boot into the new system and log in as root.
3. Connect to the Internet. Ethernet or USB tethering is easiest:
   `ip -br link` shows the interface, then `dhcpcd -w <interface>`.
4. Run:

   ```sh
   curl -LO https://raw.githubusercontent.com/Magneedo/brenOS/main/brenos
   sh brenos
   ```

5. Answer the questions: username (default `bren`), password, and whether this
   is the Framework. Then it runs on its own; it takes a while.
6. Do the [manual steps](#after-installing), then `reboot`. The user is logged
   in on tty1 and dwl starts.

## What it does

- Adds the Arch repositories (`templates/pacman.conf`) and installs every
  package in `manifests/`, plus the AUR ones through yay.
- Creates the user in `wheel`, and clones this repo,
  [dotfiles](https://github.com/Magneedo/dotfiles), [dwl](https://github.com/Magneedo/dwl)
  and [dwlb](https://github.com/Magneedo/dwlb) into `~/Projects`.
- Builds and installs dwl and dwlb.
- Copies dotfiles' `home/` into the user's home and its `etc/` and `usr/` into
  `/`, then does the same with `files/portable` (and `files/framework`).
- Sets the groups, subordinate IDs, capabilities, dash as `sh`, the time zone
  (America/New_York) and the locale, and enables the runit services.

For a username other than `bren`, it builds and copies from a copy of the
sources in which every `bren` becomes that name; the clones in `~/Projects`
stay as they are. Running brenos again brings the system back in line with the
repos, overwriting local edits to the files it copies.

It never partitions, formats, changes the bootloader or reboots.

## After installing

These need private data or the hardware, so they stay manual:

- Wi-Fi profiles in `/etc/wpa_supplicant`: [secrets](docs/secrets.md).
- `gh auth login`, then clone the private Vault and log in to Codex and Claude:
  [secrets](docs/secrets.md).
- Framework: `fprintd-enroll`, and hibernation with the direct EFI boot entry:
  [boot](docs/boot.md).
- Pictures, the Windows VM and other personal files from backup:
  [secrets](docs/secrets.md).

## Changing what gets installed

| Path | What it holds |
| --- | --- |
| `brenos` | The installer |
| `manifests/packages-*.txt` | Packages: `portable`, `framework`, `aur`, and `runtime` (installed as dependencies) |
| `manifests/services-*.txt` | runit services to enable |
| `manifests/groups.txt`, `capabilities.tsv`, `directories.tsv` | Groups, file capabilities, directory owners and modes |
| `files/portable`, `files/framework` | System files that aren't in dotfiles, laid out like dotfiles |
| `templates/` | `pacman.conf` and secret-free examples |
| `docs/` | [Framework boot](docs/boot.md) and [private inputs](docs/secrets.md) |

Configuration lives in dotfiles, dwl and dwlb. brenos clones their `main`; on
a rerun it fast-forwards the clones in `~/Projects`, and keeps a clone with
local changes as it is. To add a package, add its name to a manifest. To test a
change, run brenos on a fresh install, in a VM or in a chroot.
