#!/usr/bin/env python3
"""VM test of d77-persist: a simulated USB stick (the ISO written to an image)
and a "target" disk that must stay untouched, although it also has a partition
named d77-data. Everything is created in the workdir; nothing else is written.

    persist-test.py --iso ISO [--workdir DIR] [--tool common/d77orphaned/d77-persist]

--tool pastes that script into the VM, to test it without rebuilding the ISO.
Prints PASS or FAIL per check and exits non-zero on any FAIL.
"""
import argparse, atexit, hashlib, importlib.util, os, re, shutil, subprocess, sys, time

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("h", os.path.join(here, "qemu-harness.py"))
h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)

PASS = "correct horse battery"
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""), flush=True)


def sha(path):
    d = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            d.update(chunk)
    return d.hexdigest()


def clean(text):
    return re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", text)


def boot(wd, name, iso, stick, target, tool=None, extra="d77.nogui"):
    k, i = h.extract_boot(iso, wd)
    args = ["-kernel", k, "-initrd", i, "-append", f"{h.BASE_CMDLINE} {extra}",
            "-device", "qemu-xhci",
            "-drive", f"if=none,id=stick,file={stick},format=raw",
            "-device", "usb-storage,drive=stick",
            "-drive", f"file={target},format=raw,if=virtio"]
    vm = h.VM(wd, name, args)
    atexit.register(vm.proc.kill)  # never leave a VM holding the images
    vm.login()
    vm.run("sleep 5; udevadm settle", 60)
    if tool:
        h.copy_in(vm, tool, "/usr/bin/d77-persist")
    return vm


def sh(vm, cmd, timeout=120):
    """Run a command in the VM; returns (output, rc)."""
    vm.send(f"{cmd}; echo __RC__=$?")
    out = clean(vm.wait_for(r"__RC__=\d+\s", timeout))
    m = re.search(r"__RC__=(\d+)\s*$", out)
    body = out[:m.start()]
    # Drop the echoed command line.
    body = body.split("\n", 1)[1] if "\n" in body else ""
    return body, int(m.group(1))


def answer(vm, prompt, text, timeout=180):
    """Wait for a passphrase prompt and answer it. cryptsetup flushes pending
    input when it turns echo off, right after printing the prompt."""
    vm.wait_for(prompt, timeout)
    time.sleep(1.5)
    vm.send(text)


def firmware_boot(wd, name, stick, uefi=False):
    args = ["-device", "qemu-xhci",
            "-drive", f"if=none,id=stick,file={stick},format=raw",
            "-device", "usb-storage,drive=stick,bootindex=1"]
    if uefi:
        vars_copy = os.path.join(wd, "OVMF_VARS.fd")
        shutil.copy(h.OVMF_VARS, vars_copy)
        args += ["-drive", f"if=pflash,format=raw,readonly=on,file={h.OVMF_CODE}",
                 "-drive", f"if=pflash,format=raw,file={vars_copy}"]
    vm = h.VM(wd, name, args)
    atexit.register(vm.proc.kill)
    time.sleep(12)
    menu = vm.screenshot(f"{name}-menu")
    time.sleep(70)
    booted = vm.screenshot(f"{name}-booted")
    vm.quit()
    return menu, booted


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", required=True)
    ap.add_argument("--workdir", default="vmtest/persist")
    ap.add_argument("--tool")
    a = ap.parse_args()
    wd = a.workdir
    os.makedirs(wd, exist_ok=True)
    for f in ("vmlinuz", "initrd"):
        if os.path.exists(os.path.join(wd, f)):
            os.unlink(os.path.join(wd, f))

    stick = os.path.join(wd, "stick.img")
    with open(stick, "wb") as f:
        f.truncate(4 << 30)
    subprocess.run(["dd", f"if={a.iso}", f"of={stick}", "bs=4M", "conv=notrunc", "status=none"], check=True)
    target = os.path.join(wd, "target.img")
    with open(target, "wb") as f:
        f.truncate(64 << 20)
    subprocess.run(["sgdisk", "-n", "0:0:0", "-t", "0:8309", "-c", "0:d77-data", target],
                   check=True, stdout=subprocess.DEVNULL)
    target_hash = sha(target)
    stick_hash = sha(stick)

    vm = boot(wd, "p1", a.iso, stick, target, a.tool)
    out, rc = sh(vm, "d77-persist status")
    check("status: no persistence yet", "Persistence: none" in out and rc == 0, out)
    boot_line = re.search(r"Boot device: (\S+)", out)
    check("boot device is the USB stick, not the target disk",
          bool(boot_line) and "vd" not in boot_line.group(1), out)

    # Cancelling writes nothing.
    vm.send("d77-persist create; echo __RC__=$?")
    vm.wait_for(r"type the device name", 60)
    vm.send("no")
    out = clean(vm.wait_for(r"__RC__=\d+\s", 60))
    check("create: a wrong answer cancels", "nothing was written" in out and "__RC__=1" in out, out)
    vm.run("sync", 30)

    # Create.
    vm.send("d77-persist create; echo __RC__=$?")
    out = clean(vm.wait_for(r"type the device name \((\w+)\)", 60))
    dev = re.search(r"type the device name \((\w+)\)", out).group(1)
    vm.send(dev)
    answer(vm, r"Enter passphrase", PASS)
    answer(vm, r"Verify passphrase", PASS)
    answer(vm, r"Enter passphrase for", PASS)
    out = clean(vm.wait_for(r"__RC__=\d+\s", 180))
    check("create: succeeds", "__RC__=0" in out and "Done." in out, out)

    out, _ = sh(vm, "lsblk -rno NAME,PARTLABEL,FSTYPE; sgdisk -v /dev/%s | tail -n 2" % dev)
    check("create: LUKS partition on the stick", re.search(rf"{dev}\d+ d77-data crypto_LUKS", out) is not None, out)
    check("create: GPT is valid", "No problems found" in out, out)
    out, _ = sh(vm, "cryptsetup luksDump /dev/%s4 | grep -E '^Version'" % dev)
    check("create: LUKS version 2", "2" in out, out)

    # Keep data and settings.
    sh(vm, "echo keep > /mnt/d77-data/file.txt; "
           "echo marker > /home/anon/.config/pwm/marker; "
           "echo '[connection]' > /etc/NetworkManager/system-connections/test.nmconnection; "
           "chmod 600 /etc/NetworkManager/system-connections/test.nmconnection; sync")
    out, rc = sh(vm, "d77-persist close")
    check("close: succeeds", rc == 0, out)
    _, mapped = sh(vm, "test -e /dev/mapper/d77-data")
    out, _ = sh(vm, "findmnt -rno TARGET | grep -c d77-data; ls /home/anon/.config/pwm/marker 2>&1")
    check("close: locked and settings put back", mapped == 1 and "No such file" in out, out)

    # Wrong passphrase.
    vm.send("d77-persist open; echo __RC__=$?")
    for _ in range(3):
        answer(vm, r"Enter passphrase", "wrong passphrase")
    out = clean(vm.wait_for(r"__RC__=\d+\s", 180))
    check("open: a wrong passphrase is refused", "__RC__=1" in out, out)
    vm.send("poweroff")
    try:
        vm.proc.wait(120)
    except subprocess.TimeoutExpired:
        pass
    vm.quit()

    # New boot: everything locked until asked for.
    vm = boot(wd, "p2", a.iso, stick, target, a.tool)
    out, _ = sh(vm, "d77-persist status; ls /dev/mapper; findmnt -rno TARGET | grep -c d77-data; ls /home/anon/.config/pwm/marker 2>&1")
    check("new boot: locked, nothing mounted", "State:       locked" in out and "No such file" in out, out)

    vm.send("d77-persist open; echo __RC__=$?")
    answer(vm, r"Enter passphrase", PASS)
    out = clean(vm.wait_for(r"__RC__=\d+\s", 180))
    check("open: succeeds", "__RC__=0" in out, out)
    out, _ = sh(vm, "cat /mnt/d77-data/file.txt; cat /home/anon/.config/pwm/marker; "
                    "ls /etc/NetworkManager/system-connections/; stat -c '%U' /home/anon/.config/pwm/marker /mnt/d77-data; "
                    "nmcli -t -f NAME connection show | grep -c test")
    check("open: files are back", "keep" in out, out)
    check("open: settings are back", "marker" in out and "test.nmconnection" in out, out)
    out, rc = sh(vm, "d77-persist open")
    check("open: twice is refused", rc == 1 and "already open" in out, out)
    out, rc = sh(vm, "su - anon -c 'echo userwrite > /mnt/d77-data/user.txt; d77-persist status'")
    check("the live user can write and use it (sudo)", rc == 0 and "open at" in out, out)
    out, rc = sh(vm, "d77-persist close")
    check("close: succeeds again", rc == 0, out)
    vm.send("d77-persist open --data-only; echo __RC__=$?")
    answer(vm, r"Enter passphrase", PASS)
    out = clean(vm.wait_for(r"__RC__=\d+\s", 180))
    check("open --data-only: succeeds", "__RC__=0" in out, out)
    out, _ = sh(vm, "cat /mnt/d77-data/file.txt; ls /home/anon/.config/pwm/marker 2>&1")
    check("open --data-only: settings not touched", "keep" in out and "No such file" in out, out)
    sh(vm, "d77-persist close")
    vm.send("poweroff")
    try:
        vm.proc.wait(120)
    except subprocess.TimeoutExpired:
        pass
    vm.quit()

    check("the target disk is unchanged", sha(target) == target_hash)
    check("the stick did change (sanity)", sha(stick) != stick_hash)

    # The firmware must still boot the stick with the new table.
    print("bios:", *firmware_boot(wd, "bios", stick), flush=True)
    print("uefi:", *firmware_boot(wd, "uefi", stick, uefi=True), flush=True)

    print(f"{sum(results)}/{len(results)} checks passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
