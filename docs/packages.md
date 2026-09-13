# Package restoration

`packages-portable.txt` + `packages-framework.txt` exactly cover the 122 native
explicit packages. `packages-aur.txt` covers six AUR packages. Together these
equal the 128-name restoration inventory, enforced by `scripts/check`.
No local package recipes are required.

`packages-runtime.txt` promotes installed dependencies that are directly required
by the environment: dbus/runit integration, elogind/rtkit/polkit, compositor
libraries, fonts, Python, Java, Deno and tools invoked by scripts. It prevents
their accidental omission as dependency graphs change. C build utilities already
appear in the explicit manifest. The reference had no orphan dependency packages.
`packages-all.tsv` records dependency versions for diagnosis, not forced restore.

Use `scripts/packages --profile framework` to preview and
`doas scripts/packages --profile framework --apply` to install. It uses
`pacman -Syu --needed` followed by `pacman -D --asexplicit` for desired packages;
it does not remove extra packages. There is no `pacman -Sy` partial upgrade and
no `--noconfirm` or disabled signature verification.

## AUR helper and packages

Use the installed yay if present. On a fresh system without yay, review and build
the audited helper version as bren. Native build tools must already be restored.
Go is a build dependency, even though it was no longer installed on the reference.
This is expected; build-only dependencies are not a request to add new development
workflows. Do not run makepkg as root.

```sh
cd ~/Projects/artix-bootstrap
scripts/yay
scripts/yay --apply
scripts/aur
scripts/aur --apply
```

`scripts/yay` moves the previously manual helper bootstrap into one small stage.
It reuses an existing yay executable; otherwise it clones the AUR recipe into
`.work/aur/yay`, verifies the origin, selects the audited commit recorded in the
script, and displays every tracked recipe input. Type `build` only after review.
It refuses tracked local recipe edits and symlink build paths. Building uses
`makepkg -si --needed` as your user; signature/provider/dependency errors stop the
stage for review. No keys are imported automatically and no checks are bypassed.
The guided installer calls this stage before `scripts/aur`.

makepkg's authentication command is explicitly set to doas; no sudo installation
is needed. The Artix base-devel meta-package would pull in sudo, so the manifest
retains the already installed individual build tools instead. Review dependency
and signing-key prompts. yay is called with its recipe diff/edit menus enabled
and an explicit doas/makepkg configuration, without saving global yay settings.

Current AUR recipes are used for the six application packages. Cached recipe
commits/versions are recorded in [aur-provenance.tsv](aur-provenance.tsv) to help
diagnose changes; they are not all known build inputs for the original installs.
`localsend` requires a substantial Flutter/Rust build toolchain when built from
source. `tofi` needs Meson/scdoc. Let recipe dependencies install as required;
do not silently substitute differently named binary packages.

If a package moves to a native repository, Pacman/yay can obtain it there. If a
package disappears, stop, inspect the recorded source/recipe and update the
manifest deliberately. Do not ignore a missing browser, launcher, VPN or desktop
dependency to make an install command succeed.

## Maintenance and recovery

Keep Artix repositories first: system, world, galaxy, lib32, then Arch extra and
multilib. The installed Artix support package provides compatibility for dependencies
named systemd/systemd-libs without installing systemd. Do not replace runit to
satisfy an AUR dependency; inspect provider choices if packaging changes.

For trust failures, first correct the clock and update Artix/Arch keyrings with
the distribution-supported recovery procedure. On a fresh install, initialize and
populate the Artix keyring as needed with `pacman-key --init` and
`pacman-key --populate artix`; install artix-archlinux-support before enabling Arch
repositories. Do not trust random package signatures or disable SigLevel.

The current environment intentionally includes QEMU/OVMF, FreeRDP, Steam/Prism,
OBS, media tools, Python/pip, C toolchain, Java and Deno. Old Flutter/Dart/pnpm
caches are excluded; none of those executable environments existed at the audit.
Git identity, SSH access, language project dependencies and cloud/tool logins are
supplied separately. Do not copy whole tool configuration directories containing
authentication or history.
