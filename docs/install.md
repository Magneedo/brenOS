# Installation sequence

These commands target a **fresh installation**, not the running reference laptop.
Work from tty2 (Ctrl-Alt-F2) or a recovery shell so tty1's desktop autostart does
not interrupt setup. Keep that console available until login/lock are tested.

## 1. Fresh-base preparation

Use [Fresh Framework restore in README](../README.md#fresh-framework-restore)
for the complete root-console → temporary network → authentication → clone →
`./bootstrap` sequence. It is the canonical entry path; do not create a temporary
wheel-wide doas rule. Phase 0 validates the existing account, installs missing
launcher tools, and, only if policy is absent, reviews/installs the exact pinned
final doas policy before handing off to `install` as bren.

Choose x86_64 Artix with runit/runit-rc, a bootable kernel, and a normal bren
account (UID and primary GID 1000, /home/bren, /bin/bash, active wheel membership).
The Framework restore expects UEFI with Secure Boot disabled and the reviewed
[boot layout](boot.md). Mount the ESP at /boot before kernel/microcode or any full
package upgrade. The intended kernel/initramfs setup uses linux, booster,
intel-ucode and btrfs-progs; review provider conflicts if the base selected another
initramfs generator. Keep root access, working networking/mirrors/signatures,
a correct clock and separate private backups. Select dhcpcd and the required NIC
firmware during installation so temporary networking works at the first login.

See [phase-0 boundaries and recovery](bootstrap.md) for exact minimum assumptions,
account creation checks, authentication alternatives and privilege/security review.

## Guided installation

Phase 0 automatically runs the command below. A prepared machine can run it
directly from the cloned repository, as bren on tty2:

```sh
./install --profile framework
```

The prerequisites above still apply, including Python, doas, the bren account,
working Internet, a correct clock and the intended disk layout. The orchestrator
requires an interactive terminal and refuses installation from an active graphical
session or SSH. Framework package upgrades require a FAT ESP mounted read-write
at `/boot`. Run the installer as your ordinary user; it invokes doas for system
operations and keeps source/AUR/desktop builds and home deployment unprivileged.

It asks for installation intent once, preserves Pacman/makepkg/yay prompts, and
pauses for the reviews below. Type the requested word to continue, or press Enter
to stop. Supply credentials using private editors or the application's own login
commands in another console, never in an installer confirmation prompt.

| Stage | Actions and review boundaries |
| --- | --- |
| `repositories` | Install Artix compatibility support, show the Pacman diff, require `replace` before installing the policy with its original backup; preserve mirror files |
| `packages` | Preview and apply the existing native package stage, including a normal full upgrade |
| `aur` | Bootstrap the pinned yay recipe if needed after explicit review, then run the existing AUR stage with its diff/edit menus |
| `desktop` | Prepare the pinned repositories, build/test dwl and dwlb, and check manifest/source inputs |
| `configuration` | Preview home/system files, require `replace` for backed-up replacements, then apply permissions and check doas policy |
| `services` | Stop for a new login if group changes are not active; pause for private inputs and review before enabling the listed services |
| `boot` | Pause for manually reviewed UUIDs/fstab/layout, run the existing initramfs stage with backups, then pause for explicit EFI decisions |
| `verify` | Run the protected verifier and report physical acceptance tests; retain its failure/incomplete exit status |

Inspect the sequence without running commands or writing any files:

```sh
./install --profile framework --dry-run
```

A pause or error names the stage and prints a resume command. For example, after
applying configuration, log out and back into tty2 to activate new groups, then:

```sh
cd ~/Projects/artix-bootstrap
./install --profile framework --from services
```

There is no saved completion state. `--from` deliberately skips earlier stages;
use it only after those stages succeeded and keep the same profile. Stage-level
checks still run, so absent packages/sources/private inputs or conflicting files
fail visibly. Resuming at `configuration` repeats both file previews and the
replacement review. Resuming at `boot` repeats its reviews and initramfs build;
after completing that stage's manual EFI work, `--from verify` is sufficient.

Exit status 3 means paused for review/manual work, 1 means a stage/preflight failed
(or verification found drift), 2 from verification means incomplete checks, and
130 means interrupted. The failing command is shown; inspect package transactions
or other partial work before retrying. No whole-install rollback is implied:
existing file/image backups and each stage's normal rerun behavior are preserved.

The first verification runs before reboot; session processes and the running
kernel's old arguments can still differ. Review every finding and finish the
boot guide, then reboot deliberately and run from the restored desktop:

```sh
./install --profile framework --from verify
```

Follow [verify.md](verify.md) for physical acceptance tests. Disk formatting,
partitioning, fstab/EFI decisions, reboot and suspend/hibernate testing remain
manual. `portable` uses the same sequence but leaves the hardware-specific
initramfs/boot setup to you. The numbered sections below remain the full review
instructions and standalone commands for each stage.

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
python3 tests/installer.py
python3 tests/bootstrap.py
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
