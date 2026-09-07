# Installation sequence

These commands target a **fresh installation**, not the running reference laptop.
Work from tty2 (Ctrl-Alt-F2) or a recovery shell so tty1's desktop autostart does
not interrupt setup. Keep that console available until login/lock are tested.

## 1. Clean-install prerequisites

Install x86_64 Artix using **runit** and a normal user `bren`, UID 1000, primary
group `bren`, home `/home/bren`, shell `/bin/bash`. Use the disk layout in
[boot.md](boot.md) if reproducing the Framework. Mount the ESP at `/boot` before
installing the kernel or microcode. Choose `linux`, `booster`, `intel-ucode`,
`btrfs-progs`, `runit`, `runit-rc`, and `elogind` during the base install. Booster
is the intended initramfs provider; review Pacman's provider/conflict prompts if
the clean installation selected a different generator. Confirm `/sbin/init`
resolves to `runit-init`.

Prerequisites also include working Internet, a correct clock (TLS/signatures),
root access, enabled firmware virtualization, UEFI mode with Secure Boot disabled,
and separate backups of the manual inputs. Networking used for installation may
be temporary; the final configuration is applied later.

From the fresh installation's root shell, install the tools needed to get this
private repository and run its scripts:

```sh
pacman -Syu --needed git github-cli python opendoas
```

If the installer did not create the account, create it now, then set its password:

```sh
useradd -m -u 1000 -s /bin/bash bren
passwd bren
```

For an existing installer-created account, check `getent passwd bren` and skip
`useradd`. Add it to wheel. If no doas policy exists yet, create the temporary
password-authenticated policy below; keep an existing working policy otherwise:

```sh
usermod -aG wheel bren
if [ ! -e /etc/doas.conf ]; then
    printf 'permit persist :wheel\n' > /etc/doas.conf
    chmod 0600 /etc/doas.conf
fi
```

Log in as bren on tty2. Authenticate GitHub interactively; do not paste tokens
into commands, files in the repository, or clone URLs:

```sh
gh auth login --hostname github.com --git-protocol https
mkdir -p ~/Projects
gh repo clone Magneedo/artix-bootstrap ~/Projects/artix-bootstrap
cd ~/Projects/artix-bootstrap
```

## 2. Configure repositories and restore packages

Install Artix's compatibility package while using the installation's working
Artix repositories; it supplies the Arch keyring/mirrorlist and compatibility
providers. Never place Arch repositories ahead of Artix.

```sh
doas pacman -Syu --needed artix-archlinux-support
doas cp -an /etc/pacman.conf /etc/pacman.conf.before-bootstrap
diff -u /etc/pacman.conf templates/pacman.conf
```

`diff` exits 1 when files differ; this is a review step. Check mirror files
`/etc/pacman.d/mirrorlist` and `/etc/pacman.d/mirrorlist-arch` contain reachable
servers for their respective distributions. The reference used RIT, Clarkson and
Waterloo mirrors, in that order; current working mirrors are preferable to copying
a stale list. Keep package signature checking enabled.

```sh
doas install -m644 templates/pacman.conf /etc/pacman.conf
pacman-conf --repo-list
scripts/packages --profile framework
doas scripts/packages --profile framework --apply
```

The first command sequence is intentionally visible: replacing Pacman policy is
not hidden inside a later stage. The saved original is not overwritten on reruns.
Review `packages.md` for keyring recovery and package-movement handling.

Next follow [packages.md](packages.md) to bootstrap yay, restore the seven AUR
packages. Return here once
all package commands succeed. No service is enabled by these bootstrap scripts
at this stage. Upstream package install hooks retain their normal behavior.

## 3. Restore sources and build the desktop

```sh
cd ~/Projects/artix-bootstrap
scripts/sources
scripts/desktop
```

`sources` downloads the three public repositories at recorded commits and applies
the local patches. It can reuse existing repositories read-only with
`scripts/sources --local ~/Projects`; this reads committed objects and still
applies the captured patch, rather than trusting unstaged files. Prepared source
checksums make unexpected edits fail visibly. If intentionally changing sources,
update the original repository/pin/patch and prepare again.

The desktop stage builds from fresh copies, runs dwl's swallowing regression
tests and stages both executables plus the session file/manpage. It uses the
existing Makefiles, including dwl's `-march=native`, and requires wlroots 0.19.
Build on the target hardware. Do not substitute wlroots 0.18 or a future major ABI.

## 4. Deploy configuration and permissions

Review both previews, then apply. `--replace` means differing **regular files**
may be backed up and replaced; symlinks and symlink parents are refused. If you
already manage a destination with a symlink, resolve that layout manually first.

```sh
scripts/files --profile framework --scope home
doas scripts/files --profile framework --scope system
scripts/files --profile framework --scope home --replace --apply
doas scripts/files --profile framework --scope system --replace --apply
scripts/permissions
doas scripts/permissions --apply
doas doas -C /etc/doas.conf
```

Home files are installed as bren; system files and desktop binaries as root.
Backups go under `~/.local/state/artix-bootstrap/backups/` for home scope and
`/var/lib/artix-bootstrap/backups/` for system scope. A conflicting file causes
preflight to fail before writing any files unless replacement was requested.
Individual replacements use a temporary file and rename. A whole stage is not
a transaction; failures after successful writes can be resolved and rerun.

Permissions restore the reference supplemental groups, subordinate ID range,
capabilities, polkit rules-directory ownership, `/usr/bin/sh -> dash`, timezone
and locale. It does not remove any
existing group memberships. A conflicting subordinate ID allocation fails for
manual resolution. Log out and back into tty2 to pick up groups.

## 5. Supply manual inputs, then enable services

Follow [secrets.md](secrets.md), especially the root-owned `home.conf` Wi-Fi
profile, personal images and VM backup. Then:

```sh
cd ~/Projects/artix-bootstrap
scripts/services --profile framework
doas scripts/services --profile framework --apply
doas sv status /run/runit/service/*
```

The service stage verifies definitions, current runlevel, private Wi-Fi file
permissions, `wlan0` and SSH configuration before linking
services. It creates missing host keys with `ssh-keygen -A`; keys never enter Git.
Enabling a link in the current default runlevel can start that service immediately.
Existing services are not restarted by the script. If existing processes predate
the restored configuration, restart them deliberately from a local console or
let the next boot start them. Restarting networking can interrupt the connection.

Use [networking/audio instructions](network-audio.md) to check networking,
pair Bluetooth devices, and check audio.

## 6. Complete boot and hibernation configuration

Follow [boot.md](boot.md) in full: verify subvolumes/mounts, render fstab with
**new** filesystem UUIDs, inspect/apply it, build the Booster image and create or
verify the EFISTUB entry. Boot setup requires a few explicit firmware commands;
it is not a side effect of package or file restoration.

## 7. Verify, boot and test

```sh
scripts/check
python3 tests/rehearsal.py
doas scripts/verify --profile framework
```

Before graphical login, missing session processes are expected findings. Read
[verify.md](verify.md), correct every important failure, and retain recovery
media before your first boot. After a successful boot, tty1 autologin starts the
desktop; rerun verification there, then perform the documented hardware tests.
Confirm tty2 password login and screen unlock before testing hibernation.
The root verifier includes the protected audit; see verify.md to save private
reports without hiding the interactive authentication prompt.

Re-running stages normally skips installed packages, unchanged files and existing
service links. Package restore performs a normal full rolling-release upgrade.
Do not rerun account creation, replace private profiles, format disks, or create
duplicate EFI entries. EFI numbers and hardware/manual state are deliberately
not guessed by an installer script.
