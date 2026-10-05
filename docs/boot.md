# Optional Framework boot setup

Partitioning and the Artix runit base install are your job. `brenos` assumes
an already bootable system; it does not format disks, write fstab or register EFI.
This guide recommends an unencrypted GPT layout and optional direct-kernel boot.

## Layout

| Partition | Size | Use |
| --- | --- | --- |
| ESP | 512 MiB | FAT32, mounted at `/boot` |
| Root | Remaining space | Btrfs `@` at `/`, `@snapshots` at `/.snapshots` |
| Swap | 32 GiB or enough for hibernation | Dedicated swap partition |

During the Artix install, create `@` and `@snapshots` from the Btrfs top level.
Keep `/home` inside `@`; no separate `@home`. SINGLE data/DUP metadata is suitable.
The Framework `weekly-snapshot` job expects these mounts and 20 GiB free;
it keeps four weekly snapshots, including home and a copy of `/boot`.
Keep an independent backup; choose sizes for your disk.

Inspect `lsblk -f` and `doas blkid`. Edit `/etc/fstab` with your filesystem UUIDs;
these are examples to merge with existing entries, including the [Vault bind](secrets.md#vault-and-agents):

```fstab
UUID=ROOT_UUID / btrfs subvol=@,noatime,compress=zstd:3 0 0
UUID=ROOT_UUID /.snapshots btrfs subvol=@snapshots,noatime,compress=zstd:3 0 0
UUID=ESP_UUID /boot vfat defaults 0 2
UUID=SWAP_UUID none swap defaults,pri=100 0 0
```

Run `doas findmnt --verify --verbose`, mount `/boot` and `/.snapshots`, then
`doas swapon -a`. `brenos` regenerates Booster when Framework extras are selected.
Keep `/boot` mounted for kernel upgrades. Check the files before changing EFI:

```sh
ls -lh /boot/vmlinuz-linux /boot/intel-ucode.img /boot/booster-linux.img
doas booster ls /boot/booster-linux.img
```
## Direct-kernel EFI entry

Boot in UEFI mode. Use `doas efibootmgr -v` to check existing entries first.
Reuse a correct entry, or adapt this example to the actual disk and ESP number.
Replace ROOT_UUID and SWAP_UUID; microcode must precede Booster:

```sh
efi_disk=/dev/nvme0n1
efi_esp_part=1
cmdline='initrd=\intel-ucode.img initrd=\booster-linux.img root=UUID=ROOT_UUID rootflags=subvol=@ rootfstype=btrfs rw rootwait init=/sbin/init resume=UUID=SWAP_UUID quiet loglevel=4'
doas efibootmgr --create-only --disk "$efi_disk" --part "$efi_esp_part" \
    --label Artix --loader '\vmlinuz-linux' --unicode "$cmdline"
doas efibootmgr -v
```
Keep the working boot path. Test the new entry with `doas efibootmgr --bootnext NNNN`,
using its actual number. After a successful boot, set `--bootorder` with your
actual entry numbers and retain fallbacks. Do not create duplicates on reruns.

## Hibernation and recovery
Check `swapon --show`, `/proc/cmdline` and `/sys/power/resume` after reboot.
`resume=UUID=SWAP_UUID` uses the active swap partition; no swapfile offset is needed.
Size swap for the hibernation image. Test `swaylock` first, save work, then run
`hibernate` from the Wayland session. Test suspend and hibernate/resume separately.

For recovery, boot Artix live media in UEFI mode. Mount `@` at `/mnt`, the ESP at
`/mnt/boot` and `@snapshots` at `/mnt/.snapshots`, then run `artix-chroot /mnt`.
Check UUIDs and fstab; with the ESP mounted, repair the installed kernel/images:

```sh
pacman -S linux intel-ucode booster
/usr/lib/booster/regenerate_images
```
Repair EFI as above. For early boot errors, remove `quiet` and add
`booster.log=debug,console`; [Booster](https://github.com/anatol/booster) includes
Busybox recovery with this configuration. For resume errors, check swap UUID,
capacity and the resume device. Do not boot a snapshot without reviewing its
fstab, read-only status and matching kernel/image files.
