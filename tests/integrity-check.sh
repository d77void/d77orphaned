#!/bin/sh
# T8/T9, step 2 — run as root inside the VM booted normally (autologin into
# the graphical session has already happened) with the fixture disks
# attached. Checks that nothing on them was assembled, activated, unlocked,
# mounted or swapped on, then exercises the safe read-only mounts (T9).
# The host compares SHA-256 of every disk image before and after this boot.
fail=0
ok()  { echo "OK   $*"; }
bad() { echo "FAIL $*"; fail=$((fail+1)); }

grep -q '^md' /proc/mdstat && bad "MD array assembled: $(grep '^md' /proc/mdstat)" || ok "no MD array assembled"
dm=$(dmsetup ls 2>/dev/null | grep -v 'No devices found')
[ -n "$dm" ] && bad "device-mapper devices present: $dm" || ok "no device-mapper devices (LVM/LUKS inactive)"
mnt=$(grep -E '^/dev/(vd|md|dm-|mapper)' /proc/mounts)
[ -n "$mnt" ] && bad "target disks mounted: $mnt" || ok "no target disk mounted"
sw=$(tail -n +2 /proc/swaps)
[ -n "$sw" ] && bad "swap active: $sw" || ok "no swap active"
dumpe2fs -h /dev/vdb 2>/dev/null | grep -q needs_recovery && ok "ext4 journal still dirty (no replay)" || bad "ext4 journal was replayed or fixture not dirty"

echo "--- state ---"
lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,MOUNTPOINTS
cat /proc/mdstat

echo "--- T9: safe read-only mounts ---"
mkdir -p /mnt/t9
blockdev --setro /dev/vdb && mount -o ro,noload /dev/vdb /mnt/t9 && ls /mnt/t9 && umount /mnt/t9 && ok "ext4 ro,noload" || bad "ext4 ro,noload"
blockdev --setro /dev/vdc && mount -t xfs -o ro,norecovery /dev/vdc /mnt/t9 && ls /mnt/t9 && umount /mnt/t9 && ok "xfs ro,norecovery" || bad "xfs ro,norecovery"
dumpe2fs -h /dev/vdb 2>/dev/null | grep -q needs_recovery && ok "ext4 journal still dirty after T9" || bad "ext4 journal replayed by T9"

echo "T8/T9 failures: $fail"
echo "CHECK-DONE"
