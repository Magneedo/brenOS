# Recovered Mullvad CLI recipe

Exact AUR recipe at `1f542474a3e05301c3025a46f54ac8c1234c8ed0`, recovered on 2026-09-06 from
https://aur.archlinux.org/mullvad-vpn-cli.git. The package is absent from the
AUR RPC listing, but its Git history remains accessible. Vendoring these four
small recipe/license files makes restoration independent of that listing.

It builds the reference version 2025.14-1 from signed upstream source and pinned
submodules. Its installed package metadata and install script match the reference.
No binary, certificate, relay list or account state is stored here. The upstream
recipe includes inert systemd units; runit service definitions are in files/.
The original install script is retained, including the setuid bit on
mullvad-exclude. It does not enable systemd units when systemctl is absent.

The full Rust/Go source build was not run on the reference because its build
toolchains are absent. See docs/packages.md for the exact build and key setup.
The official .deb has different binaries and omits maybenot_machines, so it is
not substituted for this source recipe.
