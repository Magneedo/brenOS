# Artix bootstrap

Restore the intentional configuration of bren's Artix/runit system from a clean
Artix installation. The complete reference profile is **Framework Laptop 13,
Intel i5-1240P**, x86_64, with `/home/bren` and UID 1000.

## Fresh Framework restore

Start from a booted x86_64 Artix **runit** installation, using a local text console
such as tty2. During OS installation, create `bren` with UID **1000**, primary
group `bren`/GID **1000**, home `/home/bren`, shell `/bin/bash`, and wheel membership.
Set bren's and root's passwords. If the account is absent or differs, follow the
[account checks](docs/bootstrap.md#design-and-minimum-base); bootstrap never renames
users or changes IDs. Choose the [reviewed disk/boot layout](docs/boot.md) during
installation, with the existing FAT ESP mounted read-write at `/boot`.

For the temporary network, use wired Ethernet or USB tethering. Include `dhcpcd`
and the needed NIC firmware during the Artix install: base alone does not supply
a DHCP client. If you already have Internet, skip the DHCP command below. If the
fresh machine lacks networking tools, use live media to install them into the
target first; bootstrap cannot download through an absent network.

In the **fresh machine's root console**, check the clock, select the interface
shown by `ip` (do not assume eth0), and install only the repository-access tools:

```sh
date -u
ip -br link
read -r -p 'Temporary wired/USB network interface: ' bootstrap_iface
dhcpcd -w "$bootstrap_iface"
findmnt --mountpoint /boot -o SOURCE,FSTYPE,OPTIONS
# Continue only after the reviewed ESP is mounted as vfat,rw.
# If /etc/fstab already names the correct ESP and it is unmounted: mount /boot
pacman -Syu --needed git github-cli ca-certificates
```

Keep working Artix mirrors and signature checks. Correct a wrong clock before
TLS/package operations. This full base upgrade can run kernel hooks, so `/boot`
must be mounted **before** this first Pacman transaction too.

Log in as **bren on tty2**. Authenticate using gh's displayed browser/device code;
you can complete it on another trusted device without installing a local browser:

```sh
umask 077
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git --hostname github.com
mkdir -p ~/Projects
gh repo clone Magneedo/artix-bootstrap ~/Projects/artix-bootstrap
cd ~/Projects/artix-bootstrap
./bootstrap
```

`./bootstrap` defaults to Framework. It validates the base/account/checkout and
ESP, offers to install only missing launcher prerequisites (Python, Git, doas,
findmnt and CA trust), then invokes the existing installer as bren. Expect `su`
to request the **root password** for prerequisite installation and, only when
doas policy is absent, installation of the displayed **pinned final policy**.
No temporary broad rule is created. Later doas prompts use bren's password.

Minimal consoles may lack a credential store; gh can fall back to an unencrypted
file under `~/.config/gh`, protected by the private umask above. Keep it out of
Git/backups you share. [Authentication alternatives and security details](docs/bootstrap.md#obtaining-the-private-repository)
cover SSH and non-persistent ordinary Git HTTPS. Never put a token in a command,
URL, environment variable or repository file.

At an intentional gate/failure, use the printed resume command after completing
the requested work. For example, after configuration and a fresh tty2 login:

```sh
cd ~/Projects/artix-bootstrap
./install --profile framework --from services
# After completing boot/EFI work and rebooting deliberately:
./install --profile framework --from verify
```

`./bootstrap --dry-run` prints phase 0 without executing commands or writing files;
`./bootstrap --from STAGE` rechecks prerequisites and resumes on a local console.
Restore Wi-Fi credentials and other secrets manually at the existing services
gate; stop/reconcile temporary networking before enabling the final services.
Disk/UUID/EFI decisions, reboot and hardware tests remain manual. See
[the full staged installation sequence](docs/install.md) for those reviews.

A machine that already meets the prerequisites can still run directly:

```sh
./install --profile framework
```

The guided installer calls the existing stages, shows previews and pauses for
policy/file review, private inputs, group activation and boot/EFI decisions.
Use `./install --profile framework --dry-run` to print the whole plan without
running commands. At a pause or failure it prints a command to resume with
`--from STAGE`; no hidden completion files skip work automatically.

Read [the reference audit](docs/audit.md) and [validation results](docs/validation.md)
for coverage and test limits. The authenticated policy audit is complete;
physical restore/boot tests have not been performed.

This repository supplies manifests, selected missing files, small scripts and
reviewed patches. The existing repositories remain the sources of truth:

- [dotfiles](https://github.com/Magneedo/dotfiles): shell, desktop/session scripts,
  application configuration and existing system overrides.
- [dwl](https://github.com/Magneedo/dwl): compositor code and configuration.
- [dwlb](https://github.com/Magneedo/dwlb): bar code and configuration.

`manifests/repositories.tsv` pins their reviewed commits. `scripts/sources`
prepares those commits plus `patches/` in ignored `.work/` directories. It never
changes the original checkouts. The additional Windows launcher/helper preserve
the working live versions without resurrecting the deleted, older dotfiles copy.

## What is reproduced

The restore includes 129 explicit packages: 122 native packages and seven AUR
packages. Direct runtime/build dependencies are listed separately. Ten runit
services, system policy,
desktop builds, groups/capabilities, networking, audio startup and Framework boot
configuration are covered. `manifests/files.tsv` is the complete deployment
allowlist; no directory-wide home or `/etc` copy is used.

The dwl build includes the persistent `Mod+c` Codex popup and its
`/usr/local/libexec/dwl-codex` helper. `tmux` is an additional direct runtime
dependency; `foot` and `openai-codex` are already included. Each graphical session
starts a fresh chat, and hiding the popup keeps Codex working. Restore Codex
authentication separately through its normal login flow.

The pinned personal dwl `config.h` uses a centered `70` percent popup and 3px
borders; `config.def.h` retains `100` percent defaults. Wheel input scrolls the dedicated
tmux history. `Mod+Escape` uses util-linux's existing `flock` to keep wlogout
single-instance. Bootstrap does not install the dwl manpage.

Pacman and AUR stay rolling release. Package-version inventories record the audit
baseline; they are not instructions to downgrade individual packages. Source
configuration is pinned. Restoration may need explicit maintenance if repositories,
ABIs, signing keys or upstream downloads change; missing packages fail visibly.
There is no claim of identical binaries or an indefinitely frozen package archive.

The `portable` profile contains this user's software and non-hardware policy.
`framework` adds the Intel drivers, fingerprint PAM configuration, hardware
workarounds, Wi-Fi service and boot/hibernate configuration. See
[profile boundaries](docs/hardware.md). Portable does not mean arbitrary username:
existing dwl commands use `/home/bren`. Adapt those sources deliberately for another
account rather than relying on a hidden username substitution.

## Repository map

| Path | Purpose |
| --- | --- |
| `bootstrap`, `scripts/phase0.py` | Minimal fresh-base checks, prerequisite/pinned-policy preparation and unprivileged handoff |
| `install` | Interactive orchestration, read-only plan and explicit stage resume |
| `manifests/` | Packages, services, groups, capabilities, directory permissions, Wi-Fi methods, pinned repositories, file allowlist |
| `files/portable`, `files/framework` | Missing reviewed configuration and scripts |
| `patches/` | Reviewed live/uncommitted differences from the pinned repositories |
| `templates/` | Pacman configuration and secret-free examples |
| `scripts/` | Independent restoration, inspection and verification stages |
| `tests/rehearsal.py` | Temporary-root deployment and failure/retry tests |
| `tests/installer.py` | Installer stop/resume, privilege boundaries and offline helper-bootstrap tests |
| `tests/bootstrap.py` | Fresh-base, privilege, policy, retry and handoff tests without host changes |
| `.work/`, `local/` | Ignored builds, rehearsals, local reports and machine inputs |

Individual mutating stage scripts preview by default and require `--apply` to write.
The top-level `install` is interactive: it confirms installation intent, calls
those previews and explicitly applies the reviewed stages. It has no unattended
yes/force mode, and never supplies `--noconfirm` to package tools.
`scripts/sources` and `scripts/desktop` only prepare/build inside `.work/`.
`scripts/files` refuses conflicting files unless `--replace` is given; replaced
files are backed up. No script formats disks, deletes snapshots, creates a VM,
reboots, hibernates or registers an EFI entry.

Passwords, Wi-Fi identities/credentials, keys, certificates, VPN accounts, browser
profiles, application history, recordings, wallpapers, game data and VM images
belong in a separate backup. See [manual inputs](docs/secrets.md). Never use
`git add -f` on `local/` or `.work/`.

To maintain this capture: edit the specific manifest/file, prepare sources and
build the desktop, run `scripts/check`, `python3 tests/rehearsal.py`,
`python3 tests/installer.py`, `python3 tests/bootstrap.py`, and the
read-only `scripts/verify --profile framework`, then review and commit. Update a
repository pin and its patch together. Once a patch is incorporated into its
original repository, advance the pin and remove the redundant patch.
