#!/usr/bin/env python3
"""Host-side QEMU harness for the D77orphaned PoC tests (docs/APPROVAL_GATE.md §6).

Drives a VM through its serial console (for commands) and the QEMU monitor
(for screenshots and power-off). Works without KVM (pure TCG), just slower.

    qemu-harness.py <scenario> --iso ISO [--workdir DIR]

Scenarios:
  bios-menu    T2: SeaBIOS, ISO as CD, screenshot of the isolinux menu and of the default boot
  uefi-menu    T3: OVMF, idem with the GRUB menu
  serial       direct kernel boot with console=ttyS0 (+ extra cmdline), log in as root,
               run one command and print its output (used for T4, T7, T10, T11)
  integrity    T8/T9: prepare fixture disks, hash them, boot again normally, check, hash again

Fixture disks are created in the workdir; nothing outside it is written.
"""
import argparse, hashlib, os, re, shutil, socket, subprocess, sys, time

OVMF_CODE = "/usr/share/OVMF/OVMF_CODE_4M.fd"
OVMF_VARS = "/usr/share/OVMF/OVMF_VARS_4M.fd"
BASE_CMDLINE = ("root=live:CDLABEL=D77ORPHANED ro init=/sbin/init rd.luks=0 rd.md=0 rd.dm=0 "
                "rd.lvm=0 loglevel=4 rd.live.overlay.overlayfs=1 console=tty0 console=ttyS0,115200")


class VM:
    def __init__(self, workdir, name, args, mem=3072):
        self.workdir, self.name = workdir, name
        self.ser_path = os.path.join(workdir, f"{name}.serial.sock")
        self.mon_path = os.path.join(workdir, f"{name}.monitor.sock")
        self.log_path = os.path.join(workdir, f"{name}.serial.log")
        for p in (self.ser_path, self.mon_path):
            if os.path.exists(p):
                os.unlink(p)
        cmd = ["qemu-system-x86_64", "-m", str(mem), "-smp", "2", "-display", "none",
               "-vga", "std", "-no-reboot",
               "-chardev", f"socket,id=ser0,path={self.ser_path},server=on,wait=off",
               "-serial", "chardev:ser0",
               "-monitor", f"unix:{self.mon_path},server,nowait"] + args
        self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=open(
            os.path.join(workdir, f"{name}.qemu.err"), "w"))
        for _ in range(100):
            if os.path.exists(self.ser_path) and os.path.exists(self.mon_path):
                break
            time.sleep(0.1)
        self.ser = socket.socket(socket.AF_UNIX); self.ser.connect(self.ser_path)
        self.ser.settimeout(1)
        self.buf = ""
        self.log = open(self.log_path, "w")

    def _read(self):
        try:
            data = self.ser.recv(65536).decode("utf-8", "replace")
        except socket.timeout:
            return False
        if not data:
            return False
        self.buf += data; self.log.write(data); self.log.flush()
        return True

    def wait_for(self, pattern, timeout):
        rx = re.compile(pattern)
        end = time.time() + timeout
        while time.time() < end:
            m = rx.search(self.buf)
            if m:
                out = self.buf[:m.end()]; self.buf = self.buf[m.end():]
                return out
            if self.proc.poll() is not None:
                self._read()
                m = rx.search(self.buf)
                if m:
                    return self.buf[:m.end()]
                raise RuntimeError(f"{self.name}: QEMU exited while waiting for {pattern!r}")
            self._read()
        raise TimeoutError(f"{self.name}: timeout waiting for {pattern!r}; tail:\n{self.buf[-800:]}")

    def send(self, line):
        self.ser.sendall((line + "\n").encode())

    def run(self, command, timeout=600, marker="__D77_DONE__"):
        self.send(f"{command}; echo {marker} rc=$?")
        out = self.wait_for(rf"{marker} rc=\d+", timeout)
        return out

    def login(self, timeout=1800):
        self.wait_for(r"login:", timeout)
        self.send("root"); self.wait_for(r"Password:", 60)
        self.send("voidlinux"); self.wait_for(r"#\s*$|# ", 120)
        self.send("export PS1='# '; stty cols 200; dmesg -n 1")
        time.sleep(1)

    def monitor(self, command):
        s = socket.socket(socket.AF_UNIX); s.connect(self.mon_path); s.settimeout(5)
        try:
            s.recv(4096)
        except socket.timeout:
            pass
        s.sendall((command + "\n").encode()); time.sleep(1.5)
        try:
            s.recv(65536)
        except socket.timeout:
            pass
        s.close()

    def screenshot(self, name):
        ppm = os.path.join(self.workdir, f"{name}.ppm")
        png = os.path.join(self.workdir, f"{name}.png")
        self.monitor(f"screendump {ppm}")
        time.sleep(1)
        if shutil.which("convert"):
            subprocess.run(["convert", ppm, png], check=False)
            return png
        return ppm

    def quit(self):
        try:
            self.monitor("quit")
        except OSError:
            pass
        try:
            self.proc.wait(30)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.log.close()


def extract_boot(iso, workdir):
    k, i = os.path.join(workdir, "vmlinuz"), os.path.join(workdir, "initrd")
    if not (os.path.exists(k) and os.path.exists(i)):
        subprocess.run(["xorriso", "-osirrox", "on", "-indev", iso,
                        "-extract", "/boot/vmlinuz", k, "-extract", "/boot/initrd", i],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return k, i


def direct(iso, workdir, extra=""):
    k, i = extract_boot(iso, workdir)
    return ["-cdrom", iso, "-kernel", k, "-initrd", i, "-append", f"{BASE_CMDLINE} {extra}".strip()]


FIXTURES = ["vdb", "vdc", "vdd", "vde", "vdf", "vdg", "vdh", "vdi"]


def fixture_args(workdir, readonly=False):
    # The first virtio disk is vda: occupy it with an empty placeholder so the
    # fixtures are vdb..vdi, the names the in-VM scripts expect.
    pad = os.path.join(workdir, "fixture-vda-placeholder.img")
    with open(pad, "wb") as f:
        f.truncate(1 << 20)
    args = ["-drive", f"file={pad},format=raw,if=virtio"]
    for d in FIXTURES:
        p = os.path.join(workdir, f"fixture-{d}.img")
        args += ["-drive", f"file={p},format=raw,if=virtio"]
    return args


def hashes(workdir):
    out = {}
    for d in FIXTURES:
        h = hashlib.sha256()
        with open(os.path.join(workdir, f"fixture-{d}.img"), "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        out[d] = h.hexdigest()
    return out


def copy_in(vm, local, remote):
    """Paste a small text file into the VM over the serial console."""
    data = open(local).read()
    vm.send(f"cat > {remote} <<'__D77_EOF__'")
    for line in data.splitlines():
        vm.send(line); time.sleep(0.02)
    vm.send("__D77_EOF__")
    vm.run(f"chmod 755 {remote}", 60)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario")
    ap.add_argument("--iso", required=True)
    ap.add_argument("--workdir", default="vmtest")
    ap.add_argument("--cmd", default="true")
    ap.add_argument("--extra", default="")
    ap.add_argument("--wait", type=int, default=300, help="seconds before the 'booted' screenshot")
    a = ap.parse_args()
    os.makedirs(a.workdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))

    if a.scenario in ("bios-menu", "uefi-menu"):
        args = ["-cdrom", a.iso, "-boot", "d"]
        if a.scenario == "uefi-menu":
            vars_copy = os.path.join(a.workdir, "OVMF_VARS.fd")
            shutil.copy(OVMF_VARS, vars_copy)
            args += ["-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
                     "-drive", f"if=pflash,format=raw,file={vars_copy}"]
        vm = VM(a.workdir, a.scenario, args)
        time.sleep(25 if a.scenario == "bios-menu" else 60)
        print("menu:", vm.screenshot(f"{a.scenario}-menu"))
        time.sleep(a.wait)
        print("booted:", vm.screenshot(f"{a.scenario}-booted"))
        vm.quit()

    elif a.scenario == "serial":
        vm = VM(a.workdir, "serial", direct(a.iso, a.workdir, a.extra))
        vm.login()
        print(vm.run(a.cmd, timeout=1800))
        if a.wait:
            time.sleep(a.wait)
            print("screen:", vm.screenshot("serial-screen"))
        vm.quit()

    elif a.scenario == "integrity":
        for d in FIXTURES:
            p = os.path.join(a.workdir, f"fixture-{d}.img")
            with open(p, "wb") as f:
                f.truncate(512 << 20)
        vm = VM(a.workdir, "prepare", direct(a.iso, a.workdir, "d77.nogui") + fixture_args(a.workdir))
        vm.login()
        copy_in(vm, os.path.join(here, "integrity-prepare.sh"), "/root/prepare.sh")
        vm.send("/root/prepare.sh")
        vm.wait_for(r"PREPARE-DONE", 900)
        vm.proc.wait(300)  # sysrq b + -no-reboot => QEMU exits
        vm.log.close()
        before = hashes(a.workdir)
        print("hashes before:", before)

        # Normal boot (greetd autologin into pwm), then check over serial.
        vm = VM(a.workdir, "check", direct(a.iso, a.workdir) + fixture_args(a.workdir))
        vm.login()
        print("waiting for the graphical session to settle...")
        time.sleep(a.wait)
        print("screen:", vm.screenshot("integrity-session"))
        copy_in(vm, os.path.join(here, "integrity-check.sh"), "/root/check.sh")
        print(vm.run("/root/check.sh", 900))
        vm.send("poweroff")
        try:
            vm.proc.wait(600)
        except subprocess.TimeoutExpired:
            vm.quit()
        after = hashes(a.workdir)
        same = before == after
        for d in FIXTURES:
            print(f"{d}: {'unchanged' if before[d] == after[d] else 'CHANGED'}")
        print("T8 disk hashes:", "PASS" if same else "FAIL")
        sys.exit(0 if same else 1)
    else:
        ap.error("unknown scenario")


if __name__ == "__main__":
    main()
