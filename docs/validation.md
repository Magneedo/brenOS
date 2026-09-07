# Validation of this capture

Audit/validation date: 2026-09-06. The reference laptop remained running and its
installed configuration, packages, services, boot entries and storage were not
modified. Builds, temporary roots, downloads and reports stayed in the new
repository's ignored work area or temporary directories.

## Completed

- Verified the published GitHub main commits match the three recorded pins.
  Also fetched all three sources through the normal fresh GitHub download path,
  independently of the existing local repositories.
  Original worktrees retained their initial state: deleted Windows file in
  dotfiles, modified dwl config.h, clean dwlb. No reset/commit/push was made there.
- Captured every explicit installed package; all 122 native names resolve in
  the current Pacman sync databases. AUR RPC resolves seven names. Recovered the
  missing Mullvad package's original 2025.14 recipe from its Git history, with
  its original install script and license.
- Ran Pacman's dependency resolver against an empty local package database and
  the reference sync databases, requesting the native manifests plus the foreign
  packages' declared native runtime dependencies. The 755-package solution
  resolved successfully and covered every currently installed native package.
  No packages were downloaded or installed by that simulation.
- Prepared pinned sources plus reviewed deltas; rebuilt both dwl and dwlb on
  the laptop. dwl's existing swallowing regression tests passed. No installed
  desktop executable was replaced.
- Applied all 68 managed files to a temporary root and verified their content/
  modes. Repeated application made zero changes. Five integration tests passed,
  including conflict preflight, backup, symlink escape and malformed boot inputs.
- Checked Python/Bash/PKGBUILD syntax, manifest coverage and an obvious-secret
  scan. Sources are selected individually; existing OBS state and gh credentials
  are not copied into the repository or deployment allowlist.
- Generated a Booster image in `.work/` using the captured Framework configuration
  and installed kernel. Inspected init, busybox, i915 and NVMe support. Btrfs is
  built into this reference kernel (`modinfo` confirms `(builtin)`), so no separate
  btrfs module is expected in that image. Generation warned that the protected
  crypttab could not be read: this unprivileged test is not a substitute for the
  authenticated target build. No `/boot` files were changed.
- The read-only host verifier outside the sandbox reported **275 passed checks,
  zero failures, 13 incomplete checks, one informational review and one physical
  test reminder**. The review is an older installed dwl manpage; restore uses the
  pinned source's documentation. Package/group/capability/boot/session comparisons
  that were readable matched the captured intent.

## Required protected audit

`doas -n` returned `Authentication required`. Local authentication is needed to
finish protected configuration review and supervisor status checks. The 13
incomplete comparisons are the unreadable live doas policy, eleven supervisor
status files and the not-yet-supplied protected audit report. They are not treated
as passing checks.

Run in a local terminal on the reference:

```sh
cd ~/Projects/artix-bootstrap
mkdir -p local
doas python3 scripts/audit-privileged > local/privileged-audit.json
doas scripts/verify --profile framework
```

Review the protected report against the capture before declaring restoration
coverage complete. In particular: confirm the live doas policy equals its
existing dotfiles source; confirm protected SSH/polkit and cron configuration;
check the protected package-backup checksums for crypttab/default-user/libaudit
policy; inspect the non-secret enterprise Wi-Fi method requirements. Copy only
reviewed configuration or secret-free templates if something additional is
required. Keep identities, certificates, passwords and raw report contents local.

Unprivileged inspection already verified the real host group list, capabilities,
EFI entry, mount/boot arguments, service links, root process names, device modes
and private Wi-Fi file metadata. Those observations do not replace the protected
checks above. The existing doas configuration is reused as a known repository
source, with its live equivalence explicitly unconfirmed.

## Not claimed/tested

- No reinstall, new EFI registration, reboot, fresh boot, suspend, hibernation,
  fingerprint enrollment, Wi-Fi reassociation or account/device re-registration
  was performed. Previous dotfiles audit notes documented successful hibernation;
  a newly restored target still needs the physical tests in verify.md.
- No live package transaction or AUR build toolchain installation was performed.
  The full recovered Mullvad Rust/Go build and the other AUR source builds were
  not rerun. Their dependencies and restoration commands are documented; a
  staging file test does not prove their future upstream availability.
- The safe Booster install stage was syntax checked and its input workflow
  reviewed against the installed tool/hook implementations. Image generation and
  inspection were exercised separately in the workspace; --apply was not run.
  EFI creation remains a visible manual operation with actual target values.
- This is a configuration restore, not a backup of personal data or an immutable
  archive of every package version. Disappearing upstream sources, future library
  ABI changes, missing private backups or changed hardware need explicit handling.
