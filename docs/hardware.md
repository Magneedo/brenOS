# Portable configuration and Framework-specific intent

`--profile portable` selects the user's software/session policy; `--profile
framework` includes it plus the Intel Framework layer. The default is portable
to avoid silently applying laptop workarounds elsewhere. The full reference
installation uses framework consistently for packages, files, services and checks.

| Portable/user intent | Framework or installation-specific |
| --- | --- |
| runit, Bash/Vim, dwl/dwlb builds, PipeWire, portals, Noto fonts | Intel microcode, graphics/media/Vulkan, Intel/Realtek firmware |
| User scripts, application packages, power wrappers | Fingerprint PAM hooks and new local fingerprint enrollment |
| User bren/UID 1000, groups, limits, capabilities | i915/NVMe/Btrfs Booster image and dedicated swap resume |
| DHCP preference for Ethernet over Wi-Fi, named profile workflow | wlan0 check/service, new wireless credentials, device-name adaptations |
| Chrony, SSH, Mullvad service definitions | Framework USB power driver blacklist and webcam access rule |
| Locale en_US.UTF-8, America/New_York, hostname artix | Disk UUIDs, ESP partition number, firmware boot entry number |
| Normal package/mirror mechanisms | VM CPU affinity, laptop-sized OBS recording defaults |

The portable layer is a **personal** configuration, not a generic multi-user
distribution. Changing the account/home requires updating the original dwl command
paths, tty1 autologin, doas rules, resource limits and user-script defaults. No
templating engine obscures those dependencies.

Captured hardware policies, without new tuning:

- `blacklist cros_usbpd_charger` in modprobe.d preserves the existing Framework
  USB power workaround. Early graphics is forced through Booster's i915 setting.
- `options kvm ignore_msrs=1` supports the existing Windows guest workload.
- The USB webcam rule matches vendor/product `0bda:5634`, uses `TAG+="uaccess"`
  and mode 0666. This broad local device access is the existing policy, retained
  deliberately; no additional device rules are inferred.
- bren belongs to audio, input, kvm, network, seat, storage, video and wheel.
  The reference seat socket is root:seat 0770, KVM is root:kvm 0666 and the
  render device is root:render 0666 through normal device provisioning.
- btop has `cap_dac_read_search,cap_perfmon=ep`; newuidmap/newgidmap have their
  setuid/setgid capabilities. doas and mullvad-exclude are setuid root; swaylock
  uses PAM without a setuid bit. These are verified, not generalized into blanket
  capabilities for arbitrary binaries.
- `/usr/bin/sh` selects dash. bren's login shell remains Bash. The PAM resource
  limit raises bren's hard nofile limit to 524288; no unrelated system-wide
  sysctl/tuning is introduced.
- The recorded subordinate UID and GID ranges are `100000:65536` for bren.
  Installation refuses collisions rather than overwriting other users' mappings.

Firmware settings, enrolled fingerprints and device pairing are not files to
version. Enable virtualization for KVM and verify the firmware permits direct
unsigned EFISTUB boot. The initial audit did not export a full firmware-variable
dump or assume a BIOS version can be restored safely with a script.

For another machine, use the portable layer as a starting point, choose appropriate
kernel/firmware/drivers and disk configuration, then add only required hardware
policy. The existing dwl configuration also carries this laptop's monitor and
input preferences; inspect `config.h` before reusing them on different displays.
