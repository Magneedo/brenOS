# Phase 0: fresh-install boundary and security

Start with [Fresh Framework restore](../README.md#fresh-framework-restore) for the
single command sequence. This document explains its decisions and recovery.

## Design and minimum base

Phase 0 is a Bash launcher plus a small Python policy/handoff helper. It does not
replace `install`. The default of `./bootstrap` is **framework**; the existing
installer and stage scripts keep their **portable** defaults. Select portable
explicitly when appropriate. All source revisions in `repositories.tsv`, patches,
package manifests, normal installer prompts and boot gates remain unchanged.

Artix's `base` dependencies, inspected in the Artix sync metadata on 2026-09-08,
include Bash, coreutils, shadow, util-linux, pacman, Artix signing keys, iproute2
and iputils. `su` and `findmnt` come from util-linux. Base does **not** promise
Git, Python, opendoas, github-cli, a DHCP client, firmware for every adapter, or a
desktop credential store. Git and github-cli are available from Artix world;
Python and util-linux are in system. Arch repositories are unnecessary for phase
0. These are package-name/dependency observations, not a version lock or assurance
that an old installation's mirrors/signing keys still work.
[Artix base package](https://packages.artixlinux.org/packages/system/any/base/),
[Artix installation guide](https://wiki.artixlinux.org/Main/Installation)

| Assumption | Phase 0 | Existing installer |
| --- | --- | --- |
| Artix, x86_64, runit actually running | Refuse another OS/init/chroot | Keeps its own Artix/runit preflight |
| bren, UID/primary GID 1000, /home/bren, Bash | Validate only; require active wheel membership | Keeps exact account and stage-specific group checks |
| Local console, trusted checkout | Reject root, SSH/GUI, unsafe ownership/permissions | Keeps local-console and unprivileged orchestration gates |
| Bash/core tools, pacman, su, working network/clock | Required base; do not try to repair an OS or network blindly | Ordinary package/repository handling |
| Python, Git, doas, findmnt, CA bundle | Install only missing prerequisites | Keep preflight; normal package manifest later |
| Framework ESP at /boot, FAT, rw | Check before any phase-0 package transaction | Repeat findmnt check before workstation upgrades |
| doas policy | Keep existing safe policy; otherwise review/install exact final pinned policy | Full backed-up configuration and policy checks remain |
| UUIDs, layout, EFI, private inputs, physical tests | No guessing or automation | Existing explicit manual gates |

The account should be created **during Artix installation**, not transformed by
bootstrap. If installation did not create it, use a root console first. Inspect
`getent passwd bren`, `getent passwd 1000`, `getent group bren`, and
`getent group 1000`. Only when those names/IDs are unused and `/home/bren` does
not already contain data:

```sh
groupadd -g 1000 bren
useradd -m -u 1000 -g bren -G wheel -s /bin/bash bren
passwd bren
```

For an already correct installer-created account, add wheel only if missing with
`usermod -aG wheel bren`, then log out and back in. Do not run useradd/groupadd
again, rename users, change populated account IDs, or recursively chown a home.
Keep a working root password and recovery console until login/lock are tested.

## Obtaining the private repository

The recommended GitHub CLI HTTPS device/browser flow avoids manually transporting
a token or private key. Install `git github-cli ca-certificates` from the root
console after networking and `/boot` are ready, as shown in README. Run gh as
**bren**, with `umask 077`. Complete the displayed one-time code on another trusted
device if no browser is installed on the fresh console. Authentication is needed
to obtain this repository; bootstrap cannot install its own downloader before
its files exist. It never calls `gh auth token`, records credentials, changes the
checkout revision, or pulls a branch during restoration.

On a minimal console, gh may lack a working system credential store and fall back
to an unencrypted private file under `~/.config/gh`. The private umask protects
new files, but this is not encryption at rest. Keep that directory out of Git and
public backups; don't use `--insecure-storage` or enable shell tracing. Use
`gh auth status` without token-display flags to inspect storage. Prefer the
non-persistent Git alternative below if you do not want a stored token.
[GitHub CLI authentication](https://cli.github.com/manual/gh_auth_login)

| Alternative | Initial packages and tradeoff |
| --- | --- |
| SSH | `git openssh ca-certificates`; useful with an existing authorized key, but a new machine needs a passphrase-protected key, public-key registration and host-key verification |
| Ordinary Git HTTPS | `git ca-certificates`; use a short-lived fine-grained PAT for only this repository, Contents read access, entered at Git's hidden password prompt; no gh or credential storage needed |

For SSH, generate a new passphrase-protected key with `ssh-keygen -t ed25519`
only if needed; never overwrite an existing key. Register only the public `.pub`
key on GitHub. Verify the server fingerprint against
[GitHub's published fingerprints](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints),
then `git clone git@github.com:Magneedo/artix-bootstrap.git ~/Projects/artix-bootstrap`.
Do not disable host-key checking or put private keys in this repository.

For ordinary HTTPS, create the scoped token in GitHub's settings on your trusted
device, then as bren:

```sh
mkdir -p ~/Projects
git -c credential.helper= clone https://github.com/Magneedo/artix-bootstrap.git ~/Projects/artix-bootstrap
```

Enter your GitHub username and the token when prompted; GitHub account passwords
do not authenticate Git HTTPS. Never insert the token in that command or URL.
An empty helper disables configured credential storage for this invocation on a
fresh shell. Avoid credential-store, askpass scripts and tracing; revoke the
token when no longer needed. See [Git's credential behavior](https://git-scm.com/docs/gitcredentials).
An independently authenticated archive is also usable: phase 0 can install Git
before reading the pinned public policy. Keep an archive in a private trusted
directory just like a clone.

## Privilege transition

`bootstrap` runs as bren. Bash's privileged startup mode suppresses BASH_ENV and
imported shell functions; phase 0 uses `/usr/bin:/bin`. It invokes `su --login`
only for a fixed prerequisite package command or the reviewed policy installation,
and announces the root-password prompt. Pacman retains ordinary confirmation and
signature checks. Missing prerequisites use `-Syu --needed`, never a partial
upgrade or a full workstation manifest. A full transaction can still update
installed base/kernel packages and run package hooks, which is why `/boot` must
be ready even before downloading this repository.

If `/etc/doas.conf` exists, it must be a root-owned regular file that is not
group/world writable; phase 0 never overwrites or broadens it. Interactive
`doas /usr/bin/true` checks access. A policy that allows only some commands can
still fail at the corresponding installer stage; resolve that policy deliberately
from the retained root console, never append a blanket fallback rule.

If policy is absent, an unprivileged temporary bare Git repository reads only
`etc/doas.conf` at dotfiles' exact manifest commit. It does not execute source
scripts or prepare/build the workstation. A patch that changes doas policy stops
for manual review. After displaying the final policy and explicit `policy`
confirmation, su runs a fixed isolated Python program with policy text as data.
It creates a private root-owned temporary directory inside `/etc`, validates the
candidate with `doas -C`, and atomically hard-links it into place without replacing
any existing path, including dangling symlinks. Root never reads a user-writable
temporary policy or imports checkout code for this operation.

This installs the **intended final** wheel administration policy and its existing
specific passwordless power commands early, not a temporary privilege exception.
PAM stays at the package default until the normal reviewed configuration stage.
The final policy's existing privileges are a deliberate security tradeoff; inspect
the displayed rules before accepting. No account/group changes happen in phase 0.

## Failure, rerun and security boundaries

- Already present tools skip the entire phase-0 package transaction. A failed or
  declined transaction stops before policy/handoff. Inspect Pacman errors and
  rerun `./bootstrap`; a damaged package whose binary is missing may need an
  explicit reinstall from the root console because `--needed` will not repair it.
- Packages can have completed even when a later step failed. There is no hidden
  phase-completion flag. Existing policy is preserved on reruns; a policy-review
  decline makes no system-policy change. Invalid candidates are never published.
- Use the printed `./install --profile framework --from STAGE` after an intentional
  gate, logout or reboot. `./bootstrap --from STAGE` repeats prerequisite checks
  before the same handoff on a local text console. After graphical login use the
  existing `./install --profile framework --from verify` directly.
- For an absent/read-only ESP, inspect `lsblk -f`, `/etc/fstab` and `findmnt`.
  If fstab already names the reviewed ESP, `su -c 'mount /boot'` can mount it.
  Otherwise use the root console to mount the device you identified. Phase 0
  neither guesses an ESP nor silently remounts/edits fstab.
- Working network, clock and signing keys are external inputs. If a minimal base
  has no DHCP client, install `dhcpcd` and required NIC firmware from live media
  into the installed target before rebooting. Package downloads cannot bootstrap
  an absent network. No Wi-Fi credentials are accepted by the bootstrap.
- Use a checkout you trust under `/home/bren`, with no group/world-writable input
  files or parent directories. No ownership repairs are automatic. Python runs
  isolated, commands use argument arrays or shell-quoted data, and no curl-to-shell
  flow is used. Normal source/AUR/desktop stages remain unprivileged.
- This is a single-user restore, not a security boundary against compromise of
  bren's account or malicious changes to a trusted checkout. The later existing
  stages deliberately run reviewed repository code through doas. Protect the
  checkout and review changes before running it; local path checks are not
  cryptographic source attestation.

Tests use temporary roots/Git repositories, mocked privilege/package commands,
and pseudo-terminals. They do not install packages, alter doas, create accounts,
mount disks or execute the real installer on the reference host. A physical fresh
restore and real interactive su/doas authentication remain acceptance tests.
