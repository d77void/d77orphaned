# TEST_REPORT — Phase 5 (prototype)

- **Date:** 2026-11-07
- **Commit tested:** `30c5b50d` (later commits only touch `.gitignore` and documentation)
- **ISO:** `d77orphaned-live-x86_64-20261107.iso`, 1,664,143,360 bytes (1.6 GiB), sha256 `37b324352fd8f65fdca499e9d193b9b1917af7d36a0b22bd5fa2de4ad9a3f79d`
- **Build:** Ubuntu 24.04 host with static xbps 0.60, as root. The host kernel cannot mount vfat, so the EFI image was written with mtools (see commit `34c90c87`). Repositories: Void current and nonfree, plus d77void (SourceForge).
- **VM:** QEMU 8, **no KVM** (pure emulation), 2 vCPUs, 3 GiB, std VGA, user networking (SLIRP). Boot to login: about 150 s.
- **Tools:** `tests/qemu-harness.py`, `tests/check-tools.sh`, `tests/integrity-prepare.sh`, `tests/integrity-check.sh`.
- **Not tested:** real hardware (T12) and persistence (outside the base PoC).

## Results

| # | Test | Result | Evidence |
|---|---|---|---|
| T1 | Manifest | **PASS** | 450 packages installed; none of `udisks2 udiskie gvfs NetworkManager ollama calamares pipewire sddm pulseaudio zfs hashcat d77run plymouth`; no `autoinstaller` dracut module |
| T2 | BIOS boot | **PASS** | isolinux menu with normal, RAM, *graphics disabled*, *console only* and Memtest86+ entries; the default entry boots to the pwm session |
| T3 | UEFI boot | **PASS (partial)** | With OVMF it boots to the pwm session, which is only possible through `EFI/BOOT/BOOTX64.EFI`. The GRUB menu screenshot at 60 s came out black: the menu was not visually confirmed |
| T4 | `d77.nogui` | **PASS** | `sv status greetd` → `down`; the other services run; TTY and serial console usable |
| T5 | `nomodeset` + pwm | **FAIL** | Xorg loads `fbdev`/`vesa` but pwm does not stay running and the screen is black (720×400 text mode). **Not investigated** |
| T6 | pwm autologin → greeter → wasp + Utumno | **PASS, with one unexplained failure** | pwm autologin works (pwm bar). Kantele opens on X11 with `~/.config/pwm/config.toml`. wasp + Utumno starts from the greeter, with "weather unavailable" (D1), in 2 of 3 attempts; in the other one the wasp login ended in the pwm session, cause not identified. Kantele on Wayland was not tested: the test command used a wrong `WAYLAND_DISPLAY` |
| T7 | Libraries and commands | **PASS** | 1499 ELF executables with no missing libraries; every promised command is present |
| T8 | Target disk integrity | **PASS** | Test disks: ext4 and XFS with unclean journals, NTFS, LUKS2, MD RAID1, LVM, swap. After a full boot with a graphical session: no MD assembled, no device-mapper device, nothing mounted, swap off, ext4 journal still unclean; **SHA-256 of all 8 disks identical before and after** |
| T9 | Safe mounting | **PASS** | `blockdev --setro` + `mount -o ro,noload` (ext4) and `ro,norecovery` (XFS); the journal stays unclean; hashes unchanged |
| T10 | Network | **PASS (VM)** | Automatic DHCP (`10.0.2.15/24`, route and DNS), gateway ping OK, no TCP port listening (sshd inactive). chrony did not sync: SLIRP does not pass NTP. Wi-Fi not tested |
| T11 | No persistence | **PASS** | All boots above were done without a data partition |
| T12 | Real hardware | **TO DO** | On the user's side (T480s/Libreboot) |

## Defects found by the tests and fixed

1. **LVM activated at boot** (T8, first run: LV `tvg-tlv` active). runit-void's `03-filesystems.sh` runs `vgchange --sysinit -a ay` on every boot, outside udev. Fix: `postsetup.sh` sets `auto_activation_volume_list = []` and `event_activation = 0` in `lvm.conf`. In the same script, `mdadm -As` did not assemble the RAID thanks to `AUTO -all`.
2. **pwm exited after ~2 s** (T6: autologin ended and the greeter appeared). pwm runs `xmodmap -pke` at startup and exits with `Io(NotFound)` without it. The `pwm` package does not declare `xmodmap` and `xorg-minimal` does not pull it in. Fix: `xmodmap` in the manifest. **Suggestion outside this repository:** add `xmodmap` to the `depends` of the pwm template in srcpkgs-d77.
3. **wasp did not start without a GPU** (T6: `Software rendering detected … couldn't create renderer`). scenefx needs EGL/GLES and refuses llvmpipe. Fix: `WLR_RENDERER_ALLOW_SOFTWARE=1` in `/etc/profile.d/`, which greetd sources before each session.
4. **Empty EFI image without an error** (build). The inherited `mklive.sh` mounted `efiboot.img` with errors discarded. Fix: the mount is checked, there is an mtools fallback, and the build fails if `BOOTX64.EFI` is missing.

## Open

- **T5 `nomodeset`:** black screen and pwm does not stay running. Possible causes, none verified: without KMS Xorg picks a driver that fails on QEMU's std VGA, or the greeter (dwl) fails again without `/dev/dri` and greetd loops.
- **Intermittent T6:** one of three wasp login attempts from the greeter ended in pwm. greetd logs to syslog and the ISO has no syslog daemon; in a second round greetd should log via `svlogd` to catch this.
- **Cosmetic:**
  - on wasp with software rendering, the background shows leftovers of the greeter, and there is a black block left of Utumno's bar;
  - Utumno's network widget says "offline" because it reads NetworkManager state, which the ISO does not have; DHCP works.
- **Size:** the ISO is 1.6 GiB, above the gate's 0.9–1.1 GiB estimate.
