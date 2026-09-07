# Artix bootstrap

Restore the intentional configuration of bren's Artix/runit system from a clean
Artix installation. The complete reference profile is **Framework Laptop 13,
Intel i5-1240P**, x86_64, with `/home/bren` and UID 1000.

Start with [the installation sequence](docs/install.md). It links the disk,
package, boot, secret and verification instructions at the point they are needed.
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
| `manifests/` | Packages, services, groups, capabilities, directory permissions, Wi-Fi methods, pinned repositories, file allowlist |
| `files/portable`, `files/framework` | Missing reviewed configuration and scripts |
| `patches/` | Reviewed live/uncommitted differences from the pinned repositories |
| `templates/` | Pacman configuration and secret-free examples |
| `scripts/` | Independent restoration, inspection and verification stages |
| `tests/rehearsal.py` | Temporary-root deployment and failure/retry tests |
| `.work/`, `local/` | Ignored builds, rehearsals, local reports and machine inputs |

Mutating system scripts preview by default and require `--apply` to write.
`scripts/sources` and `scripts/desktop` only prepare/build inside `.work/`.
`scripts/files` refuses conflicting files unless `--replace` is given; replaced
files are backed up. No script formats disks, deletes snapshots, creates a VM,
reboots, hibernates or registers an EFI entry.

Passwords, Wi-Fi identities/credentials, keys, certificates, VPN accounts, browser
profiles, application history, recordings, wallpapers, game data and VM images
belong in a separate backup. See [manual inputs](docs/secrets.md). Never use
`git add -f` on `local/` or `.work/`.

To maintain this capture: edit the specific manifest/file, prepare sources and
build the desktop, run `scripts/check`, `python3 tests/rehearsal.py`, and the
read-only `scripts/verify --profile framework`, then review and commit. Update a
repository pin and its patch together. Once a patch is incorporated into its
original repository, advance the pin and remove the redundant patch.
