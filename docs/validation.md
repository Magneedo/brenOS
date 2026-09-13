# Validation of this capture

Initial audit: 2026-09-06. Authenticated completion: 2026-09-07.
The reference laptop remained running and its
installed configuration, packages, services, boot entries and storage were not
modified. Builds, temporary roots, downloads and reports stayed in the new
repository's ignored work area or temporary directories.

## Popup and restoration completion, 2026-09-12

- dwl and dwlb build cleanly without compiler warnings. Bootstrap stages their
  completed source commits directly, including `dwl-codex`; the duplicated dwl
  patch is removed. GitHub fetches resolve the new pins. The remaining dotfiles
  patch is checked in reverse after preparation, guarding against silently
  skipped patches beneath the bootstrap checkout.
- Real headless dwl/foot/tmux tests reproduce the wheel-to-arrow failure, then
  verify mouse scrollback, return to the prompt by scrolling down or Escape,
  and ordinary typing/arrow input. Before/after screenshots also confirmed that
  earlier output becomes visible. Codex itself is represented by a busy process
  recording raw input; no model requests are sent. The live Codex pane's terminal
  modes confirmed the same cause, and mouse reporting was enabled on its existing
  dedicated server without changing its Codex PID.
- Full popup tests pass at 100% and 80%, plus out-of-range percentages (0/200)
  clamped to valid geometry. Tests include centered coordinates, a reserved bar
  area, two monitors, tags, monitor removal, rapid toggles, hidden background
  work, fullscreen stacking, swallowing exclusion, terminal close/detach/crash,
  server/session recovery, fresh graphical sessions and normal/crash cleanup.
  A standalone foot shutdown hang under load prompted a bounded child wait.
  The tracked configuration remains 100% by 100%.
- Actual wlogout launches through the configured binding survive repeated
  bursts of 100 keypresses with one process, then launch again after exit.
  No power action or swaylock setting is changed. The nonblocking lock uses the
  already-required util-linux package and is not inherited by action children.
- All 36 bootstrap tests pass: 11 rehearsals, 12 installer tests and 13 phase-0
  tests. Rehearsals cover literal WPA quoting, meaningful shell changes,
  dhcpcd trailing blank lines, inaccessible files, runit down versus unreadable
  status, idempotent temporary-root deployment and protected-policy integrity.
  Syntax, manifest coverage, obvious-secret scanning and diff whitespace checks
  pass for 66 destinations and 128 explicit packages. ShellCheck is unavailable.
- T3 Code is removed from the AUR manifest and the captured explicit/all/foreign
  inventories and AUR provenance. The AUR preview selects only the six remaining
  packages. dwl's manpage is retained as upstream source documentation but is
  not deployed or compared; unused man/data installation variables are removed.
- dwl's GPL and dwm/sway/TinyWL attribution remain, and distribution archives
  include them. dwlb's removed license and UTF-8/protocol notices are restored
  from its history. Generated protocol bindings are rebuilt from XML rather
  than tracked, preserving generated attribution without duplicate source state.
- With explicit authorization and fingerprint authentication, the validated dwl
  binary and Codex helper were installed and checked byte-for-byte with root:root
  ownership and 0755 modes. The running graphical session was preserved; the
  new geometry and wlogout binding require the next graphical login. The host
  audit reports 269 passes, zero mismatches, 12 unverified privileged checks and
  four equivalent-representation notices. Historical protected reports no longer
  count as current verification. Privileged policy/runit state was not re-audited.

No package transaction, boot change, reboot or physical multi-monitor test was
performed. The unrelated dotfiles Windows-launcher deletion remains unstaged.

## Fresh-base phase 0 validation — 2026-09-08

- Added `./bootstrap` (Bash, Framework default) and `scripts/phase0.py`. `install`,
  repository pins, source patches, file/package manifests, and staged safety
  gates are unchanged. Existing prepared-machine invocation remains valid.
- All 31 tests pass: 13 phase-0 tests, 12 installer tests and six rehearsals.
  Phase-0 tests cover wrong distro/init/account, root/effective-root rejection,
  missing/present prerequisites, ESP type/options, dry-run, noninteractive refusal,
  retry after a package transaction, review decline/failure, source pin selection,
  policy quoting, unsafe paths, atomic private policy creation, existing/symlink
  destinations, publication races, and unprivileged installer handoff/status.
- Test package/privilege/installer commands are stubbed. Files, Git fixtures and
  simulated policy publication use temporary directories only. No live OS
  package transaction, doas policy write, account change or mount was performed.
- The actual pinned-policy fetch also succeeded against GitHub, reading the
  250-byte doas blob at the exact dotfiles manifest revision into a temporary
  bare repository. It did not execute fetched code or install the policy.
- The read-only phase-0 platform, account, checkout and ESP guards passed on the
  real Framework host as bren; prerequisite detection correctly reported nothing
  missing. Only those inspection functions ran, not the installer or su/policy steps.
- Artix sync metadata confirms base includes Bash/coreutils/shadow/util-linux,
  pacman/keyring and iproute2/iputils; Git, github-cli, Python, opendoas and dhcpcd
  cannot all be assumed on a minimal base. The installed opendoas file list
  includes its PAM policy and executable but does not supply `/etc/doas.conf`.
- `scripts/check` covers the new entrypoint and passes syntax, all 66 allowlisted
  destinations, all 129 explicit packages and the obvious-secret scan. Python
  AST/compile checks, Bash syntax, documentation links and `git diff --check`
  pass. ShellCheck and Ruff are unavailable; no host packages were installed just
  to obtain linters. Bash's syntax checker is the available shell check.
- Security review: no credential handling or curl-pipe-shell; fixed prerequisite
  names, quoted policy data, isolated Python, no temporary broad doas rule, no
  automatic ownership/account repair, and no root execution of downloaded source.
  Existing final wheel/power permissions are explicitly reviewed before being
  installed early. The main installer retains its original privilege boundaries.

A sandbox remaps `/home` ownership and PID 1, so the new preflight correctly
refuses that artificial environment. Read-only host inspection also confirmed
that `/proc/1/exe` is not readable by bren; the running-init check uses the
unprivileged `/proc/1/comm` interface instead. The read-only network fetch was
verified outside the sandbox. Full fresh installation, interactive su/doas authentication, package
upgrades, boot and physical hardware acceptance remain target-machine tests;
these automated results do not claim an end-to-end physical restore.

## Guided installer validation — 2026-09-07

- Current restore scope is 129 explicit packages, ten services and 66 managed
  files. The removed VPN has no package recipe, service definition, resource
  preflight or setuid requirement in the bootstrap.
- Exercised `./install --profile framework --dry-run`: it prints the ordered
  stages and manual gates without executing child commands or writing files.
  Portable boot orchestration leaves hardware-specific image generation manual.
- All twelve tests in `tests/installer.py` passed. They cover no-command previews,
  refusal without a terminal, stopping on package failure, review before file or
  service writes, user/root separation, group activation, boot/EFI gates, explicit
  verification resume and propagation of verifier failures/incomplete results.
- Tested Pacman policy replacement against temporary files using the actual
  copy/install commands without doas: declining makes no change, reruns preserve
  the first backup, and matching policy is left alone.
- Exercised the fresh yay bootstrap against a temporary local Git repository,
  with makepkg stubbed out. Declining recipe review stops before the build;
  tracked edits are preserved, accepting resumes successfully, and an available
  helper is reused. No network package source was built or installed by this test.
- All six existing rehearsal tests still pass, including temporary-root file
  deployment/idempotency and the protected-policy integrity regression. Syntax,
  manifest coverage, obvious-secret scanning and local documentation links pass.

The live installer was not applied to the reference laptop. These tests validate
sequencing and safety boundaries; full AUR builds, fresh installation and physical
boot/hibernate acceptance remain the documented target-machine tests.

## Original capture validation

These results describe the initial capture before the user removed the VPN from
restore scope. Current manifests select 129 explicit packages, ten services and
66 files; the original validation counts are retained as historical evidence.

- Verified the published GitHub main commits match the three recorded pins.
  Also fetched all three sources through the normal fresh GitHub download path,
  independently of the existing local repositories.
  Original worktrees retained their initial state: deleted Windows file in
  dotfiles, modified dwl config.h, clean dwlb. No reset/commit/push was made there.
- Captured the explicit package inventory; all 122 native names resolve in
  the reference Pacman sync databases. AUR RPC resolves the seven retained names.
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
  The AUR source builds were not rerun. Their dependencies and restoration
  commands are documented; a
  staging file test does not prove their future upstream availability.
- The safe Booster install stage was syntax checked and its input workflow
  reviewed against the installed tool/hook implementations. Image generation and
  inspection were exercised separately in the workspace; --apply was not run.
  EFI creation remains a visible manual operation with actual target values.
- This is a configuration restore, not a backup of personal data or an immutable
  archive of every package version. Disappearing upstream sources, future library
  ABI changes, missing private backups or changed hardware need explicit handling.
