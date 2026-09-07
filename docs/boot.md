# Framework disk, boot and hibernation

## Expected layout

The reference uses an unencrypted GPT disk, direct EFISTUB boot, and no bootloader
manager. Partition numbers are examples of the reference, not portable identifiers.

| Partition | Reference size | Format | Mount/use |
| --- | --- | --- | --- |
| 1 | 512 MiB | FAT32, ESP partition type | `/boot` |
| 2 | approximately 899 GiB on a 1 TB disk | Btrfs | `@` at `/`, `@snapshots` at `/.snapshots` |
| 3 | 32 GiB | Linux swap | Dedicated swap and hibernation resume |

`/home` is inside `@`; there is no separately mounted `@home`. Existing snapshots
are recovery state, not configuration to recreate. An empty `@snapshots` subvolume
is sufficient. The reference Btrfs allocation policy is SINGLE data/DUP metadata.
Keep a separate backup: a snapshot on this disk is not protection against disk loss.

Have the clean Artix installer create/format the partitions deliberately. No
partitioning or formatting command is automated here. On a newly created Btrfs
filesystem, mount its top level in the installer, create `@` and `@snapshots`
with `btrfs subvolume create`, then mount `@` as the installation root and
`@snapshots` at its `/.snapshots`. Mount the FAT ESP at that root's `/boot` **before**
installing `linux`, `booster` or `intel-ucode`. Enable the swap partition with
`swapon`. See the [Artix installation guide](https://wiki.artixlinux.org/Main/Installation)
for the live-media/chroot procedure; use the layout above instead of guessing
from old filesystem UUIDs.

For a reasonably clean, already running Artix installation, retain its filesystems
and verify that this layout was chosen. If its layout differs, adapt the rendered
fstab/kernel arguments explicitly. Do not create another root subvolume underneath
the currently mounted `@`, or rerun formatting commands on existing data.

## Render and apply machine values

Run `lsblk -f`, `findmnt /`, `findmnt /boot`, and `doas blkid` on the new machine.
Record filesystem UUIDs for Btrfs root, the FAT ESP, and swap. They are **not**
partition GUIDs/PARTUUIDs. Replace the three placeholders in this command:

```sh
cd ~/Projects/artix-bootstrap
scripts/boot-plan \
    --root-uuid NEW_BTRFS_FILESYSTEM_UUID \
    --esp-uuid NEW_FAT_FILESYSTEM_UUID \
    --swap-uuid NEW_SWAP_FILESYSTEM_UUID
cat local/boot/fstab
cat local/boot/cmdline
doas findmnt --verify --verbose --tab-file local/boot/fstab
```

The placeholder command intentionally fails validation until real UUIDs are
supplied. It only renders files under ignored `local/boot`. Confirm these UUIDs
resolve to the intended partitions and that mountpoints/subvolumes exist. The
rendered options match the reference: noatime, zstd:3 compression, SSD/discard,
space_cache=v2 and the normal 30-second Btrfs commit interval. Swap uses
`discard=once,pri=100`; no swapfile resume offset is used.

On the fresh target, back up and install the reviewed fstab:

```sh
doas cp -an /etc/fstab /etc/fstab.before-bootstrap
doas install -m644 local/boot/fstab /etc/fstab
doas findmnt --verify --verbose
```

Check/mount `/.snapshots`, `/boot`, and swap as needed with ordinary `mount` and
`swapon` commands. An fstab edit does not remount the running root. Use the next
boot to apply the new root mount options after boot configuration is ready.

## Kernel and initramfs

The framework file stage supplies `/etc/booster.yaml`: host-specific image,
zstd, vconsole, Btrfs/NVMe modules, forced early i915, and busybox for recovery.
Build on the Framework rather than a different laptop whose hardware detection
could produce a different host-specific image.

```sh
scripts/initramfs
doas scripts/initramfs --apply
doas booster ls /boot/booster-linux.img
ls -lh /boot/vmlinuz-linux /boot/intel-ucode.img /boot/booster-linux.img
```

This stage uses the **installed** kernel's `/usr/lib/modules/*/pkgbase`, not
`uname -r` (which may describe the older running kernel). It builds and inspects
the image before replacing either boot file, stages both on the mounted FAT ESP,
and keeps previous files under `/var/lib/artix-bootstrap/boot/`. There is still
an unavoidable interval between the two file renames; do not power off mid-update.

Normal kernel/Booster package upgrades use the packaged libalpm hooks. There are
no custom boot hooks on the reference. Keep `/boot` mounted during upgrades and
check errors. The packaged `/usr/lib/booster/regenerate_images` is also available;
the explicit stage here builds synchronously so build failure is reported before
changing the boot files. [Booster upstream documentation](https://github.com/anatol/booster)

## EFI registration

The loader is `\vmlinuz-linux`. Its exact argument structure is:

```text
initrd=\intel-ucode.img initrd=\booster-linux.img root=UUID=<root> rootflags=subvol=@ rootfstype=btrfs rw rootwait init=/sbin/init resume=UUID=<swap> quiet loglevel=4
```

`local/boot/cmdline` contains this with the new UUIDs. Microcode must precede the
Booster image. The reference has one Artix entry and ordinary firmware USB/DVD/
network fallbacks. Firmware-assigned entry numbers and old partition GUIDs are
not copied. Check UEFI variables are accessible from UEFI-booted installation media
or the installed system, then inspect existing entries:

```sh
doas efibootmgr -v
lsblk -o NAME,PKNAME,PARTN,FSTYPE,MOUNTPOINTS
```

If an Artix entry already loads the kernel on the correct ESP with the rendered
arguments, reuse it. Do not blindly create a second entry. Otherwise, explicitly
set the **new disk** and its ESP partition number; the example below is correct
only when `/boot` is `/dev/nvme0n1p1`:

```sh
efi_disk=/dev/nvme0n1
efi_esp_part=1
doas efibootmgr --create-only --disk "$efi_disk" --part "$efi_esp_part" \
    --label Artix --loader '\vmlinuz-linux' --unicode "$(cat local/boot/cmdline)"
doas efibootmgr -v
```

`--create-only` preserves the current BootOrder. Identify the newly assigned Artix
number from the output and request it for the next boot, for example
`doas efibootmgr --bootnext 0007` **only if 0007 is the new Artix entry**.
After a successful boot, place that entry first in BootOrder while retaining the
existing firmware fallbacks, using `efibootmgr --bootorder` with the actual comma
separated numbers from this firmware. Do not copy `0000,2001,2002,2003` blindly.
See [efibootmgr's options](https://github.com/rhboot/efibootmgr).

EFI registration is a deliberate manual step. Rendering, file deployment and
image generation are rerunnable; an unconditional `--create` is not. Keep the
previous working boot path until the new one has succeeded.

## Swap, suspend and hibernation

The dedicated 32 GiB swap partition must be active and large enough for the new
machine's hibernation image. Reconsider sizing if RAM changes. Resume uses its
filesystem UUID, not a byte offset. Check `swapon --show`, `/sys/power/resume`,
and `/proc/cmdline` after boot. The reference reports `[s2idle] deep` for suspend
and `[platform]` for hibernation; there is no custom sleep-mode override.

The existing `hibernate` wrapper requires a normal Wayland session, locks with
`swaylock -f`, then uses the captured doas rule to write `disk` to
`/sys/power/state` without a hidden authentication prompt. Fingerprint enrollments
and the account password are separate inputs. Test ordinary lock/unlock first,
then save work and test hibernate/resume physically. This repository does not
hibernate the reference or promise resume will work on changed firmware/hardware.

## Recovery

If EFI cannot find the kernel, use UEFI Artix live media. Mount the correct `@`
root at `/mnt`, its ESP at `/mnt/boot`, and `@snapshots` at `/mnt/.snapshots`,
then `artix-chroot /mnt`. Confirm UUIDs, the mounted ESP and boot file names;
reinstall `linux`, `intel-ucode`, `booster` together with the ESP mounted if needed.
Rebuild the image for the installed kernel and repair the EFI entry as above.

For an initramfs/root failure, temporarily remove `quiet` and add
`booster.log=debug,console` to a recovery entry. Busybox is included in the image.
If a new image fails, restore the matching backed-up kernel/image pair from
`/var/lib/artix-bootstrap/boot/` or reinstall the packaged kernel and rebuild.
Do not point `rootflags` at an arbitrary snapshot without understanding its
fstab, boot artifacts, read-only status and recovery purpose.

Hibernation failure: compare resume UUID, active swap, kernel resume device and
swap capacity first. Ordinary suspend is a separate path. Avoid changing unrelated
power policies as a workaround before identifying the failure.
