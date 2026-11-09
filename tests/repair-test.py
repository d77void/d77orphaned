#!/usr/bin/env python3
"""VM test of the boot repair procedure in the documentation: install Void on a
disposable disk from the live ISO, destroy its boot loader on purpose, repair
it from the ISO with xchroot, and boot the repaired disk with BIOS and UEFI.
Everything is created in the workdir; needs network in the VM (SLIRP).

    repair-test.py --iso ISO [--workdir DIR] [--luks] [--cache DIR]

--luks puts the system on LUKS2 + LVM. --cache takes a directory of .xbps packages,
such as the build's xbps-cachedir, to avoid downloading what it already has.
Prints PASS or FAIL per check.
"""
import argparse, atexit, importlib.util, os, re, shutil, subprocess, sys, time

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("h", os.path.join(here, "qemu-harness.py"))
h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)

PASS = "repair test passphrase"
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail[-400:]}]" if detail and not ok else ""), flush=True)


def clean(text):
    return re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", text)


def sh(vm, cmd, timeout=300):
    vm.send(f"{cmd}; echo __RC__=$?")
    out = clean(vm.wait_for(r"__RC__=\d+\s", timeout))
    m = re.search(r"__RC__=(\d+)\s*$", out)
    return out[:m.start()], int(m.group(1))


def live(wd, name, iso, disk, extra=()):
    k, i = h.extract_boot(iso, wd)
    vm = h.VM(wd, name, ["-cdrom", iso, "-kernel", k, "-initrd", i,
                         "-append", f"{h.BASE_CMDLINE} d77.nogui",
                         "-drive", f"file={disk},format=raw,if=virtio"] + list(extra), mem=4096)
    atexit.register(vm.proc.kill)
    vm.login()
    sh(vm, "sleep 5; udevadm settle")
    return vm


def off(vm):
    vm.send("poweroff")
    try:
        vm.proc.wait(120)
    except subprocess.TimeoutExpired:
        vm.proc.kill()
    vm.log.close()


def boot_disk(wd, name, disk, uefi, luks):
    """Boot the installed system from the firmware; True if it reaches a root shell."""
    args = ["-drive", f"file={disk},format=raw,if=virtio"]
    if uefi:
        v = os.path.join(wd, "VARS.fd")
        shutil.copy(h.OVMF_VARS, v)
        args += ["-drive", f"if=pflash,format=raw,readonly=on,file={h.OVMF_CODE}",
                 "-drive", f"if=pflash,format=raw,file={v}"]
    vm = h.VM(wd, name, args, mem=2048)
    atexit.register(vm.proc.kill)
    try:
        if luks:
            vm.wait_for(r"[Pp]assphrase|[Pp]assword for", 240)
            time.sleep(2)
            vm.send(PASS)
        # The installed system's password, not the ISO's.
        vm.wait_for(r"login:", 300)
        vm.send("root"); vm.wait_for(r"Password:", 60)
        vm.send("repair"); vm.wait_for(r"#\s*$|# ", 60)
        vm.send("export PS1='# '; stty cols 200; dmesg -n 1")
        time.sleep(1)
        out, _ = sh(vm, "cat /etc/hostname; uname -r; findmnt -no SOURCE /", 60)
        ok = "repairtest" in out
        vm.screenshot(name)
        vm.send("poweroff")
        try:
            vm.proc.wait(60)
        except subprocess.TimeoutExpired:
            vm.proc.kill()
        return ok, out
    except Exception as e:
        vm.screenshot(name)
        vm.proc.kill()
        return False, f"{e}\n{clean(vm.buf)[-300:]}"


INSTALL = r"""
set -e
sgdisk -Z /dev/vda >/dev/null
sgdisk -n 1:0:+1M -t 1:ef02 -n 2:0:+256M -t 2:ef00 -n 3:0:0 -t 3:8300 /dev/vda >/dev/null
partprobe /dev/vda; udevadm settle
mkfs.vfat -F32 -n EFI /dev/vda2 >/dev/null
"""
PLAIN = r"""
mkfs.ext4 -q -L root /dev/vda3
mount /dev/vda3 /mnt
ROOTDEV=/dev/vda3
"""
LUKS = r"""
printf '%s' 'repair test passphrase' > /tmp/key
cryptsetup luksFormat -q --type luks2 --pbkdf pbkdf2 --pbkdf-force-iterations 1000 /dev/vda3 /tmp/key
cryptsetup open --key-file /tmp/key /dev/vda3 cr
pvcreate -q /dev/mapper/cr >/dev/null; vgcreate -q vg0 /dev/mapper/cr >/dev/null
lvcreate -q -y -l 100%FREE -n root vg0 >/dev/null; vgchange -q -ay vg0 >/dev/null; udevadm settle
mkfs.ext4 -q -L root /dev/vg0/root
mount /dev/vg0/root /mnt
"""
SYSTEM = r"""
mkdir -p /mnt/boot/efi /mnt/var/db/xbps/keys; mount /dev/vda2 /mnt/boot/efi
cp -a /var/db/xbps/keys/. /mnt/var/db/xbps/keys/
mkdir -p /cache; mount /dev/vdb /cache 2>/dev/null || true
XBPS_ARCH=x86_64 xbps-install -Sy -r /mnt -c /cache -R https://repo-default.voidlinux.org/current base-minimal linux grub grub-x86_64-efi dracut PKGS_EXTRA
echo repairtest > /mnt/etc/hostname
echo 'root:repair' | chroot /mnt chpasswd -c SHA512
sed -i 's/^GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="loglevel=4 console=tty0 console=ttyS0,115200 CMDLINE_EXTRA"/' /mnt/etc/default/grub
mkdir -p /mnt/etc/runit/runsvdir/default
ln -sf /etc/sv/agetty-ttyS0 /mnt/etc/runit/runsvdir/default/agetty-ttyS0
"""
PROCEDURE = r"""
set -e
UNLOCK
mkdir -p /mnt; mount ROOTDEV /mnt; mkdir -p /mnt/boot/efi; mount /dev/vda2 /mnt/boot/efi
xchroot /mnt /bin/sh -e -c '
  grub-install --target=i386-pc /dev/vda
  grub-install --target=x86_64-efi --efi-directory=/boot/efi --removable --no-nvram
  grub-mkconfig -o /boot/grub/grub.cfg
  xbps-reconfigure -f $(xbps-query -l | awk "{print \$2}" | xargs -n1 xbps-uhelper getpkgname | grep -E "^linux[0-9]")
'
sync; umount -R /mnt
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", required=True)
    ap.add_argument("--workdir", default="vmtest/repair")
    ap.add_argument("--luks", action="store_true")
    ap.add_argument("--cache")
    a = ap.parse_args()
    wd = a.workdir
    os.makedirs(wd, exist_ok=True)
    for f in ("vmlinuz", "initrd"):
        p = os.path.join(wd, f)
        if os.path.exists(p):
            os.unlink(p)
    disk = os.path.join(wd, "disk.img")
    with open(disk, "wb") as f:
        f.truncate(6 << 30)

    def script(name, text):
        p = os.path.join(wd, name)
        with open(p, "w") as f:
            f.write(text)
        return p

    # 1. Install.
    extra_disk = []
    if a.cache:
        img = os.path.join(wd, "cache.img")
        subprocess.run(["mke2fs", "-q", "-t", "ext4", "-d", a.cache, img, "12G"], check=True)
        extra_disk = ["-drive", f"file={img},format=raw,if=virtio"]
    vm = live(wd, "install", a.iso, disk, extra_disk)
    extra = "cryptsetup lvm2" if a.luks else ""
    system = SYSTEM.replace("PKGS_EXTRA", extra)
    if a.luks:
        uuid_cmd = r"""
U=$(blkid -s UUID -o value /dev/vda3)
sed -i "s|CMDLINE_EXTRA|rd.luks.uuid=$U rd.lvm.vg=vg0|" /mnt/etc/default/grub
printf 'GRUB_ENABLE_CRYPTODISK=n\n' >> /mnt/etc/default/grub
echo "/dev/vg0/root / ext4 defaults 0 1" > /mnt/etc/fstab
"""
        # /boot lives on the ESP-less encrypted root otherwise: keep it on a plain partition.
        body = INSTALL.replace("-n 3:0:0 -t 3:8300", "-n 4:0:+512M -t 4:8300 -n 3:0:0 -t 3:8300") + \
            "mkfs.ext4 -q -L boot /dev/vda4\n" + LUKS + "mkdir -p /mnt/boot; mount /dev/vda4 /mnt/boot\n" + system + uuid_cmd + \
            'echo "/dev/vda4 /boot ext4 defaults 0 2" >> /mnt/etc/fstab\n'
    else:
        body = INSTALL + PLAIN + system.replace(" CMDLINE_EXTRA", "") + \
            'echo "/dev/vda3 / ext4 defaults 0 1" > /mnt/etc/fstab\n'
    body += 'echo "/dev/vda2 /boot/efi vfat defaults 0 2" >> /mnt/etc/fstab\n'
    body += r"""
xchroot /mnt /bin/sh -e -c '
  grub-install --target=i386-pc /dev/vda
  grub-install --target=x86_64-efi --efi-directory=/boot/efi --removable --no-nvram
  grub-mkconfig -o /boot/grub/grub.cfg
  xbps-reconfigure -f $(xbps-query -l | awk "{print \$2}" | xargs -n1 xbps-uhelper getpkgname | grep -E "^linux[0-9]")
' >/dev/null 2>&1
sync; umount -R /mnt; umount /cache 2>/dev/null || true
"""
    if a.luks:
        body += "vgchange -q -an vg0 >/dev/null; cryptsetup close cr\n"
    h.copy_in(vm, script("install.sh", body), "/root/install.sh")
    sh(vm, "(sh -ex /root/install.sh > /tmp/i.log 2>&1; echo $? > /tmp/i.rc) & sleep 1", 30)
    # Installing downloads a whole system: slow on a slow network, so show progress.
    deadline = time.time() + 3000
    rc = None
    while time.time() < deadline:
        time.sleep(60)
        out, _ = sh(vm, "cat /tmp/i.rc 2>/dev/null; tail -n 1 /tmp/i.log | cut -c1-100; "
                        "ps -eo etimes,comm --sort=-etimes | grep -E 'xbps|dracut|grub|chroot|depmod' | tail -n 3 | tr '\\n' ' '", 60)
        print("  " + " | ".join(l.strip() for l in out.splitlines()[1:])[:160], flush=True)
        m = re.search(r"^\s*(\d+)\s*$", out, re.M)
        if m:
            rc = int(m.group(1))
            break
    if rc is None:
        print(sh(vm, "tail -n 25 /tmp/i.log | cut -c1-150; ps -ef | tail -n 20 | cut -c1-120", 60)[0])
        raise TimeoutError("install did not finish")
    log, _ = sh(vm, "tail -n 12 /tmp/i.log | cut -c1-120", 30)
    check("install: system written to the disk", rc == 0, log)
    if rc != 0:
        sys.exit(1)
    off(vm)

    ok, out = boot_disk(wd, "before-bios", disk, False, a.luks)
    check("before: boots with BIOS", ok, out)
    ok, out = boot_disk(wd, "before-uefi", disk, True, a.luks)
    check("before: boots with UEFI", ok, out)

    # 2. Break it: boot loader and its configuration gone.
    vm = live(wd, "break", a.iso, disk)
    rootdev = "/dev/vda3"
    unlock = ""
    bootm = ""
    if a.luks:
        rootdev = "/dev/vg0/root"
        unlock = ("printf '%s' 'repair test passphrase' > /tmp/key; cryptsetup open --key-file /tmp/key /dev/vda3 cr; "
                  "vgchange -q -ay vg0 >/dev/null; udevadm settle")
        bootm = "mkdir -p /mnt/boot; mount /dev/vda4 /mnt/boot; "
    brk = f"""set -e
{unlock}
mount {rootdev} /mnt; {bootm}mount /dev/vda2 /mnt/boot/efi
rm -rf /mnt/boot/grub /mnt/boot/efi/EFI
sync; umount -R /mnt
dd if=/dev/zero of=/dev/vda bs=440 count=1 conv=notrunc status=none
dd if=/dev/zero of=/dev/vda1 bs=1M count=1 status=none 2>/dev/null || true
sync
"""
    if a.luks:
        brk += "vgchange -q -an vg0 >/dev/null; cryptsetup close cr\n"
    h.copy_in(vm, script("break.sh", brk), "/root/break.sh")
    out, rc = sh(vm, "sh -e /root/break.sh 2>&1 | tail -n 8", 120)
    check("break: boot loader removed", rc == 0, out)
    off(vm)

    v = h.VM(wd, "broken", ["-drive", f"file={disk},format=raw,if=virtio"], mem=1024)
    atexit.register(v.proc.kill)
    time.sleep(25)
    v.screenshot("broken-bios")
    got = False
    try:
        v.wait_for(r"login:", 10)
        got = True
    except Exception:
        pass
    v.proc.kill(); v.proc.wait()
    check("broken: the disk no longer boots", not got)

    # 3. Repair from the ISO, following the documented procedure.
    vm = live(wd, "repair", a.iso, disk)
    proc = PROCEDURE.replace("UNLOCK", unlock).replace("ROOTDEV", rootdev)
    if a.luks:
        proc = proc.replace("mkdir -p /mnt/boot/efi; mount /dev/vda2", "mkdir -p /mnt/boot; mount /dev/vda4 /mnt/boot; mkdir -p /mnt/boot/efi; mount /dev/vda2")
        proc += "vgchange -q -an vg0 >/dev/null; cryptsetup close cr\n"
    h.copy_in(vm, script("repair.sh", proc), "/root/repair.sh")
    out, rc = sh(vm, "sh -e /root/repair.sh > /tmp/r.log 2>&1; echo rc=$? ; tail -n 12 /tmp/r.log | cut -c1-120", 600)
    check("repair: the procedure succeeds", "rc=0" in out, out)
    off(vm)

    ok, out = boot_disk(wd, "after-bios", disk, False, a.luks)
    check("after: boots with BIOS", ok, out)
    ok, out = boot_disk(wd, "after-uefi", disk, True, a.luks)
    check("after: boots with UEFI", ok, out)

    print(f"{sum(results)}/{len(results)} checks passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
