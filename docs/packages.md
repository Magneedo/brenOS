# Package restoration

`packages-portable.txt` + `packages-framework.txt` exactly cover the 122 native
explicit packages. `packages-aur.txt` covers seven AUR packages.
`packages-local.txt` covers `mullvad-vpn-cli`. Together these equal the 130-name
audit snapshot, enforced by `scripts/check`.

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
mkdir -p .work/aur
if [ ! -d .work/aur/yay ]; then
    git clone https://aur.archlinux.org/yay.git .work/aur/yay
fi
git -C .work/aur/yay checkout --detach cb43f84828ab4f9700f7c6f9c6d7a923d4cfaff0
less .work/aur/yay/PKGBUILD
less .work/aur/yay/.SRCINFO
printf 'source /etc/makepkg.conf\nPACMAN_AUTH=(doas)\n' > .work/makepkg.conf
bootstrap_repo=$PWD
cd .work/aur/yay
makepkg --config "$bootstrap_repo/.work/makepkg.conf" -si --needed
cd "$bootstrap_repo"
scripts/aur
scripts/aur --apply
```

makepkg's authentication command is explicitly set to doas; no sudo installation
is needed. The Artix base-devel meta-package would pull in sudo, so the manifest
retains the already installed individual build tools instead. Review dependency
and signing-key prompts. yay is called with its recipe diff/edit menus enabled
and an explicit doas/makepkg configuration, without saving global yay settings.

Current AUR recipes are used for the seven application packages. Cached recipe
commits/versions are recorded in [aur-provenance.tsv](aur-provenance.tsv) to help
diagnose changes; they are not all known build inputs for the original installs.
`localsend` requires a substantial Flutter/Rust build toolchain when built from
source. `tofi` needs Meson/scdoc. Let recipe dependencies install as required;
do not silently substitute differently named binary packages.

If a package moves to a native repository, Pacman/yay can obtain it there. If a
package disappears, stop, inspect the recorded source/recipe and update the
manifest deliberately. Do not ignore a missing browser, launcher, VPN or desktop
dependency to make an install command succeed.

## Recovered Mullvad CLI package

The installed `mullvad-vpn-cli 2025.14-1` comes from the source-build AUR recipe.
It is absent from AUR's RPC listing on the audit date, while its Git history still
exists. The exact recipe at `1f542474a3e05301c3025a46f54ac8c1234c8ed0` is retained
under `packages/mullvad-vpn-cli`, with its install script, `.SRCINFO` and license.
Its install script matches the installed package database. This is the only
vendored package recipe; it avoids depending on a removed AUR listing.

Review it, then copy just the recipe inputs to an ignored build directory:

```sh
cd ~/Projects/artix-bootstrap
less packages/mullvad-vpn-cli/PKGBUILD
less packages/mullvad-vpn-cli/mullvad-vpn.install
mkdir -p .work/local-packages/mullvad-vpn-cli
cp packages/mullvad-vpn-cli/PKGBUILD packages/mullvad-vpn-cli/mullvad-vpn.install \
   packages/mullvad-vpn-cli/LICENSE .work/local-packages/mullvad-vpn-cli/
bootstrap_repo=$PWD
printf 'source /etc/makepkg.conf\nPACMAN_AUTH=(doas)\n' > .work/makepkg.conf
cd .work/local-packages/mullvad-vpn-cli
makepkg --config "$bootstrap_repo/.work/makepkg.conf" -si --needed
cd "$bootstrap_repo"
pacman -Q mullvad-vpn-cli
```

This builds Rust/Go source and needs cargo (usually provided by rust), git, go,
protobuf, working Internet and disk space. Upstream Cargo.lock is used with locked
fetch/frozen release build; submodule commits come from the release tree. It also
fetches the current relay list while building. This is functional reproducibility,
not identical package bytes. The full source build was not repeated on the
reference; its absent toolchains were left absent.

If signed-tag verification reports a missing key, use the full signing fingerprint
reported by GnuPG, confirm it is one of `validpgpkeys` in the reviewed recipe and
verify it against Mullvad's upstream signing information. Fetch that public key
into your normal build user's keyring, for example with
`gpg --keyserver hkps://keys.openpgp.org --recv-keys FULL_FINGERPRINT`, then rerun
makepkg. Do not use `--skippgpcheck`. Build/signature/upstream failures remain
visible rather than being hidden by automatic package substitution.

The package supplies `/usr/bin/mullvad`, `mullvad-daemon`, setuid `mullvad-exclude`,
and resources including the public upstream trust certificate and Maybenot data.
Those resources are fetched by the package recipe, never stored in this repository.
The upstream package includes inert systemd units; the bootstrap uses the captured
runit service instead. Its original removal hook can remove the registered VPN
device and reset firewall state, so review it before uninstalling the package.

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
