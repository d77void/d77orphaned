#!/usr/bin/env python3
"""VM test of the emergency procedures in the documentation, on disposable disks
in the workdir: a failing disk (device-mapper error sectors) copied with ddrescue,
a deleted partition found with testdisk, and a move to a bigger disk.

    emergency-test.py --iso ISO [--workdir DIR] [--bootable DISK]

--bootable DISK also moves that installed system (from repair-test.py) to a bigger
disk, and boots the result with BIOS and UEFI. DISK is only read.
"""
import argparse, atexit, importlib.util, os, re, shutil, subprocess, sys

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("h", os.path.join(here, "qemu-harness.py"))
h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
spec = importlib.util.spec_from_file_location("r", os.path.join(here, "repair-test.py"))
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)

# Drives testdisk's real menus with the keys the documentation describes.
TESTDISK = r"""
import os, pty, re, select, sys, time
img, kind = sys.argv[1:3]
DOWN, RIGHT, ENTER = "\x1b[B", "\x1b[C", "\r"
pid, fd = pty.fork()
if pid == 0:
    os.environ["TERM"] = "vt100"
    os.execvp("testdisk", ["testdisk", "/log", img])
def read(t):
    out = b""
    end = time.time() + t
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.2)
        if r:
            try:
                out += os.read(fd, 65536)
            except OSError:
                break
    return out.decode("latin1")
def key(k, t=3):
    os.write(fd, k.encode())
    return read(t)
read(3)
key(ENTER)                                   # Proceed
key(DOWN if kind == "gpt" else "", 1)        # the proposed type is Intel: GPT is next
key(ENTER)                                   # the partition table type
key(ENTER)                                   # Analyse
screen = key(ENTER, 12)                      # Quick Search
if "Vista" in screen:
    screen = key("y", 12)
screen += key(RIGHT, 2) if kind == "gpt" else key(RIGHT * 2, 2)   # D -> P, deleted to primary
s2 = key(ENTER, 3)                           # Continue to the Write menu
s3 = key("w", 3)                             # Write
s4 = key("y", 4)                             # confirm
key(ENTER, 2)
for t in (screen, s2, s3, s4):
    pass
txt = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b[()][A-Z0-9]", " ", s4)
print("      after write:", " ".join(txt.split())[:160])
os.close(fd)
"""

SCRIPT = r"""
ok() { echo "PASS  $1"; }
no() { echo "FAIL  $1: $2"; }
t() { n=$1; shift; if "$@" >/tmp/o 2>&1; then ok "$n"; else no "$n" "rc=$? $(tail -n 4 /tmp/o | tr '\n' ' ' | cut -c1-260)"; fi; }
udevadm settle

# Source: GPT, one ext4 partition with known files.
sgdisk -Z /dev/vdb >/dev/null; sgdisk -n 1:0:0 -t 1:8300 /dev/vdb >/dev/null; partprobe /dev/vdb; udevadm settle
mkfs.ext4 -q -L data /dev/vdb1
mkdir -p /src /t /m; mount /dev/vdb1 /src
head -c 20000000 /dev/urandom > /src/photo.bin; echo keep > /src/note.txt
SUM=$(cd /src && sha256sum photo.bin note.txt); umount /src
mkfs.ext4 -q -L backup /dev/vdd; mount /dev/vdd /t

# 1. A failing disk: 64 unreadable sectors far from the files.
S=$(blockdev --getsz /dev/vdb); B=$((S-204800))
printf '0 %s linear /dev/vdb 0\n%s 64 error\n%s %s linear /dev/vdb %s\n' $B $B $((B+64)) $((S-B-64)) $((B+64)) > /tmp/table
t "dying: simulated disk with bad sectors" dmsetup create --noudevsync flaky /tmp/table
dd if=/dev/mapper/flaky of=/dev/null bs=4k 2>/dev/null && no "dying: disk really fails to read" "dd succeeded" || ok "dying: disk really fails to read"
t "dying: ddrescue first pass" ddrescue -n /dev/mapper/flaky /t/disk.img /t/disk.map
t "dying: ddrescue retry pass" ddrescue -d -r3 /dev/mapper/flaky /t/disk.img /t/disk.map
BAD=$(ddrescuelog -t /t/disk.map | awk '/bad-sector|bad areas/ {print}' | head -3 | tr '\n' ' ')
echo "      map: $BAD"
ddrescuelog --list-blocks=- /t/disk.map | grep -q . && ok "dying: map records the bad blocks" || no "dying: map records the bad blocks" "$BAD"
L=$(losetup -rPf --show /t/disk.img); udevadm settle
t "dying: image partition mounts read-only" mount -o ro,noload ${L}p1 /m
[ "$(cd /m && sha256sum photo.bin note.txt)" = "$SUM" ] && ok "dying: files identical from the image" || no "dying: files identical from the image" "hash"
umount /m; losetup -d $L; dmsetup remove flaky

# 2. A deleted partition, repaired on a copy of the disk.
dd if=/dev/vdb of=/t/lost.img bs=1M status=none
sgdisk -d 1 /t/lost.img >/dev/null
[ "$(sgdisk -p /t/lost.img | grep -c '^ *1 ')" = 0 ] && ok "deleted: partition gone from the table" || no "deleted: partition gone from the table" "still there"
cd /t; python3 /root/td.py /t/lost.img gpt; cd /
grep -qE 'ext4' /t/testdisk.log && ok "deleted: testdisk finds the partition" || no "deleted: testdisk finds the partition" "$(tail -n 4 /t/testdisk.log | tr '\n' ' ' | cut -c1-200)"
sgdisk -p /t/lost.img | tail -n 1 | cut -c1-70 | sed 's/^/      /'
back() {
  L=$(losetup -Pf --show $1); udevadm settle
  if mount -o ro,noload ${L}p1 /m 2>/tmp/o; then
    [ "$(cd /m && sha256sum $3)" = "$4" ] && ok "$2: partition back with its files" || no "$2: partition back with its files" "hash"
    umount /m
  else no "$2: partition back with its files" "$(cut -c1-200 /tmp/o)"; fi
  losetup -d $L
}
back /t/lost.img deleted "photo.bin note.txt" "$SUM"

# The same on an MBR disk.
truncate -s 300M /t/mbr.img; printf 'label: dos\nstart=2048, type=83\n' | sfdisk -q /t/mbr.img
L=$(losetup -Pf --show /t/mbr.img); udevadm settle; mkfs.ext4 -q ${L}p1; mount ${L}p1 /m; echo mbr > /m/mbr.txt; MSUM=$(cd /m && sha256sum mbr.txt); umount /m; losetup -d $L
sfdisk -q --delete /t/mbr.img 1
[ -z "$(sfdisk -d /t/mbr.img | grep start=)" ] && ok "deleted-mbr: partition gone from the table" || no "deleted-mbr: partition gone from the table" there
rm -f /t/testdisk.log; cd /t; python3 /root/td.py /t/mbr.img mbr; cd /
sfdisk -d /t/mbr.img | grep start= | cut -c1-70 | sed 's/^/      /'
back /t/mbr.img deleted-mbr mbr.txt "$MSUM"

# 3. Move to a bigger disk.
t "migrate: copy to the bigger disk" ddrescue -f /dev/vdb /dev/vdc /t/move.map
t "migrate: move the GPT backup to the disk's end" sgdisk -e /dev/vdc
t "migrate: grow the partition" parted -s /dev/vdc resizepart 1 100%
partprobe /dev/vdc; udevadm settle
e2fsck -fy /dev/vdc1 >/tmp/o 2>&1; rc=$?; [ $rc -le 1 ] && ok "migrate: check before growing (rc=$rc)" || no "migrate: check before growing" "rc=$rc $(tail -n 3 /tmp/o | cut -c1-200)"
t "migrate: grow the file system" resize2fs /dev/vdc1
t "migrate: new partition GUIDs" sgdisk -G /dev/vdc
t "migrate: new file system UUID" tune2fs -U random /dev/vdc1
partprobe /dev/vdc; udevadm settle
[ "$(blkid -s UUID -o value /dev/vdb1)" != "$(blkid -s UUID -o value /dev/vdc1)" ] && ok "migrate: UUIDs differ from the old disk" || no "migrate: UUIDs differ from the old disk" same
t "migrate: mount" mount /dev/vdc1 /m
[ "$(cd /m && sha256sum photo.bin note.txt)" = "$SUM" ] && ok "migrate: files identical" || no "migrate: files identical" hash
df -BM --output=size /m | tail -1 | sed 's/^/      size: /'
[ "$(df -BM --output=size /m | tail -1 | tr -dc 0-9)" -gt 1500 ] && ok "migrate: file system uses the new space" || no "migrate: file system uses the new space" small
umount /m; umount /t; sync
"""

BOOTABLE = r"""
ok() { echo "PASS  $1"; }
no() { echo "FAIL  $1: $2"; }
t() { n=$1; shift; if "$@" >/tmp/o 2>&1; then ok "$n"; else no "$n" "rc=$? $(tail -n 4 /tmp/o | tr '\n' ' ' | cut -c1-260)"; fi; }
udevadm settle
t "bootable: copy to the bigger disk" ddrescue -f /dev/vda /dev/vdb /tmp/m.map
t "bootable: move the GPT backup" sgdisk -e /dev/vdb
t "bootable: grow the partition" parted -s /dev/vdb resizepart 3 100%
partprobe /dev/vdb; udevadm settle
e2fsck -fy /dev/vdb3 >/tmp/o 2>&1; rc=$?; [ $rc -le 1 ] && ok "bootable: check (rc=$rc)" || no "bootable: check" "rc=$rc $(tail -n 3 /tmp/o | cut -c1-200)"
t "bootable: grow the file system" resize2fs /dev/vdb3
sync
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", required=True)
    ap.add_argument("--workdir", default="vmtest/emergency")
    ap.add_argument("--bootable")
    a = ap.parse_args()
    wd = a.workdir
    os.makedirs(wd, exist_ok=True)
    fails = 0

    def live(name, script, disks, timeout):
        nonlocal fails
        k, i = h.extract_boot(a.iso, wd)
        args = ["-cdrom", a.iso, "-kernel", k, "-initrd", i, "-append", f"{h.BASE_CMDLINE} d77.nogui"]
        for d in disks:
            args += ["-drive", f"file={d[0]},format=raw,if=virtio" + (",readonly=on" if d[1] else "")]
        vm = h.VM(wd, name, args, mem=3000)
        atexit.register(vm.proc.kill)
        vm.login()
        path = os.path.join(wd, name + ".sh")
        with open(path, "w") as f:
            f.write(script)
        h.copy_in(vm, path, "/root/t.sh")
        tdp = os.path.join(wd, "td.py")
        with open(tdp, "w") as f:
            f.write(TESTDISK)
        h.copy_in(vm, tdp, "/root/td.py")
        out = r.clean(vm.run("sleep 5; sh /root/t.sh 2>&1", timeout))
        for line in out.splitlines():
            if re.match(r"(PASS|FAIL|      )", line):
                print(line, flush=True)
        fails += len(re.findall(r"^FAIL", out, re.M))
        vm.quit()

    def blank(name, size):
        p = os.path.join(wd, name)
        with open(p, "wb") as f:
            f.truncate(0); f.truncate(size)
        return p

    live("procedures", SCRIPT, [(blank("pad.img", 1 << 20), False), (blank("src.img", 400 << 20), False),
                                (blank("big.img", 2 << 30), False), (blank("bak.img", 2 << 30), False)], 900)
    if a.bootable:
        big = blank("moved.img", 8 << 30)
        live("bootable", BOOTABLE, [(a.bootable, True), (big, False)], 900)
        for uefi, name in ((False, "bios"), (True, "uefi")):
            ok, out = r.boot_disk(wd, f"moved-{name}", big, uefi, False)
            print(f"{'PASS' if ok else 'FAIL'}  bootable: the moved system boots with {name.upper()}", flush=True)
            fails += not ok
    print(f"{fails} failures")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
