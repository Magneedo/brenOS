# Validation of this capture

Initial audit: 2026-09-06. Authenticated completion: 2026-09-07.
The reference laptop remained running and its
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
  modes. Repeated application made zero changes. Six integration tests passed,
  including conflict preflight, backup, symlink escape and malformed boot inputs.
  The additional regression verifies that the captured polkit directory-group
  exception cannot hide changed rule contents or other integrity warnings.
- Checked Python/Bash/PKGBUILD syntax, manifest coverage and an obvious-secret
  scan. Sources are selected individually; existing OBS state and gh credentials
  are not copied into the repository or deployment allowlist.
- Generated a Booster image in `.work/` using the captured Framework configuration
  and installed kernel. Inspected init, busybox, i915 and NVMe support. Btrfs is
  built into this reference kernel (`modinfo` confirms `(builtin)`), so no separate
  btrfs module is expected in that image. Generation warned that the protected
  crypttab could not be read: this unprivileged test is not a substitute for the
  authenticated target build. No `/boot` files were changed.
- The authenticated read-only host verifier outside the sandbox reported
  **317 passed checks, zero failures, zero incomplete checks, one informational review and one physical
  test reminder**. The review is an older installed dwl manpage; restore uses the
  pinned source's documentation. Package, policy, group, capability, boot, service
  and session comparisons matched the captured intent. Raw reports remain ignored
  in `local/`; no private profile values or raw reports were committed.

## Completed protected audit

Fingerprint authentication through an interactive doas terminal succeeded.
The protected audit and full verifier completed without changing installed
configuration. The earlier thirteen permission-related blind spots are resolved.

- Live doas policy matches the pinned dotfiles source; its mode is 0600.
- All eleven supervised services are running.
- Crypttab, default/useradd, libaudit.conf and sshd_config match package defaults.
- Polkit/SSH include files are unchanged package files or package symlinks.
  Pacman's full checks passed for elogind and openssh. Polkit's only mismatch is
  the rules-directory group: the reference uses root:polkitd/0750 while the
  archive records root:root. The permission manifest restores that difference;
  verification checks it separately and rejects any additional Pacman warning.
- No extra local polkit rules, SSH includes or cron entries were found; crontab
  is not installed. Historical Btrfs snapshots/old roots remain excluded state.
- The three private Wi-Fi profiles have the expected root ownership and 0600
  modes. Non-secret control, regulatory, hotspot scan and school PEAP/MSCHAPV2
  settings are captured and verified. SSIDs, identities and credentials are
  excluded; absent institutional trust directives are documented in secrets.md.

See [verify.md](verify.md) for the repeatable commands, including optional private
report capture after visible authentication. Fresh hardware, credentials and
physical behavior still require the acceptance tests below.

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
