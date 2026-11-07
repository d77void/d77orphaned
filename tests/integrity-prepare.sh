#!/bin/sh
# T8, step 1 — run as root inside a DISPOSABLE VM booted from the ISO, with
# 9 extra virtio disks vdb..vdj that hold nothing of value. Creates the
# "target disk" fixtures, then crashes the VM (sysrq b) so the ext4 and XFS
# journals stay dirty. NEVER run this on real hardware.
set -eu

for d in vdb vdc vdd vde vdf vdg vdh vdi; do
	[ -b /dev/$d ] || { echo "missing /dev/$d — refusing to run"; exit 1; }
	[ "$(cat /sys/block/$d/size)" -le 2097152 ] || { echo "/dev/$d bigger than 1 GiB — refusing"; exit 1; }
done

mkfs.ext4 -q -F -L T_EXT4 /dev/vdb
mkfs.xfs -q -f -L T_XFS /dev/vdc
mkfs.ntfs -q -F -f -L T_NTFS /dev/vdd
printf 'test\n' | cryptsetup luksFormat --type luks2 -q --pbkdf pbkdf2 --pbkdf-force-iterations 1000 /dev/vde -
mdadm --create /dev/md0 --run --level=1 --raid-devices=2 --metadata=1.2 /dev/vdf /dev/vdg
mkfs.ext4 -q -F -L T_MD /dev/md0
pvcreate -q /dev/vdh
vgcreate -q tvg /dev/vdh
lvcreate -q -y -L 64M -n tlv tvg
mkfs.ext4 -q -F -L T_LV /dev/tvg/tlv
mkswap -L T_SWAP /dev/vdi >/dev/null

mkdir -p /mnt/e /mnt/x
mount /dev/vdb /mnt/e
mount /dev/vdc /mnt/x
for m in /mnt/e /mnt/x; do
	dd if=/dev/urandom of=$m/data bs=1M count=8 status=none
	echo "fixture $(date -u)" > $m/note
done
# Push data blocks out but leave the journals un-checkpointed, then crash.
sync -f /mnt/e/data /mnt/x/data
echo "PREPARE-DONE"
echo 1 > /proc/sys/kernel/sysrq
echo b > /proc/sysrq-trigger
