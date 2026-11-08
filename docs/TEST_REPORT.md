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

## Second round (2026-11-07, Void host with KVM)

- **Host:** the user's Acer, Void Linux x86_64 glibc, QEMU 11.1.3 with **KVM**, OVMF from `edk2-ovmf` (`/usr/share/edk2/x64/OVMF_*.4m.fd`). Boot to login: about 15 s.
- **Build:** `sudo ./mkorphaned.sh -n -r ~/d77void-pkgs/hostdir/binpkgs/d77 -r https://repo-default.voidlinux.org/current/nonfree`. The d77 packages came from the local xbps-src repository (build log: pwm 0.6.7_1, wasp 0.10.1_1, utumno 0.2.0_1, qsd77 1.3.3_1, dwl 0.9_1, d77-st 0.9.3_1, scenefx0.5 0.5_1, kantele 0.3.0_1). The package cache was copied from d77void's `xbps-cachedir-x86_64` (btrfs reflink).
- **ISO:** `d77orphaned-live-x86_64-20261107.iso`, 1,698,652,160 bytes, sha256 `80420001c7c99b8f5e925988d5acf7fbcba55cd32c3f5e45981ad218bc220c83`, kernel 6.18.62_1. Built from this round's working tree (the build guard and the `nomodeset.sh` change below).

### Results

| # | Test | Result | Evidence |
|---|---|---|---|
| T3 | UEFI GRUB menu | **PASS** | Screenshot at 12 s: GRUB 2.12 menu with the normal, RAM, *graphics disabled* and *console only* entries, Memtest86+, UEFI firmware settings, restart and shutdown |
| T5 | `nomodeset` | **PASS** | No `/dev/dri` or `/dev/fb0`. Xorg falls back to `vesa` (VBE 3.0, 1920×1080) and the pwm session comes up. After `pkill pwm`, greetd shows `agreety` on VT 7 and `anon`/`voidlinux` logs into a shell |
| T6 | autologin pwm → greeter → wasp + Utumno | **PASS (6/6), but autologin failed once** | wasp, qsd77 and Utumno came up from the greeter in all 6 runs. Kantele ran on X11 and on Wayland (`WAYLAND_DISPLAY=wayland-0`, `XDG_RUNTIME_DIR=/run/user/1000`, read from Utumno's `qs`). The phase-5 case (a wasp login ending in pwm) did not reproduce. In 1 of 6 runs the pwm autologin had already died before the first check; this is the pwm race below |

### Defects found and fixed in this round

5. **The build rewrote the host's GRUB configuration.** During the first build on the Acer, the host's `/boot/grub/grub.cfg` was regenerated (os-prober included, which also touched `/var/lib/os-prober/labels`). No other host files changed, and the user found the boot menu unchanged after a reboot. Cause, reproduced in a disposable VM with a stub `grub-mkconfig`: `mklive.sh` installs `memtest86+` into the helper root `void-target`, which has no `/bin/sh`. XBPS then runs the package's post-install script **on the host** (working directory `void-target`), and that script runs `grub-mkconfig -o /boot/grub/grub.cfg` whenever `/boot/grub` exists. Fix: `mkorphaned.sh` now runs the whole build in a private mount namespace with an empty tmpfs over `/boot`, so the script finds no `/boot/grub` and does nothing. It also fails the build if the host's `grub.cfg` changes. Verified by a rebuild: `grub-mkconfig` did not run, and the host's `grub.cfg` (mtime and size) and all other files under `/` were unchanged, with no build mounts left behind. **The same `mklive.sh` is inherited from d77void, so its builds very likely do the same (not verified there).**
6. **pwm dies at startup about 5% of the time** (T5, and the T6 autologin failures). The error is `BadDrawable` on `X_CopyArea` while creating the status bar. penrose_ui creates the bar's window on its x11rb connection and draws to it through a separate Xlib connection. The X server orders requests only within one connection, so the first copy can arrive before the window exists, and Xlib's default handler exits the process. In the same VM, the pwm 0.6.7 binary failed 6 of 120 starts (3/60 with KMS, 3/60 with `nomodeset`). The rate does not depend on `nomodeset`; in phase 5 it only looked that way. Fix, outside this repository (D15): pwm branch `fix-bar-window-race` (commit `4ce82db`, not pushed) vendors penrose_ui 0.4.0 with one round trip after creating the window. That binary failed 0 of 120 starts in the same test. Released as **pwm 0.6.8** (see below).
7. **No way out under `nomodeset` once the first session ends.** The greeter runs under dwl (wlroots), which cannot start without DRM, so greetd kept restarting it every ~10 s on a black screen. Fix (D16): with `nomodeset`, `dracut/vmklive/nomodeset.sh` switches greetd's `default_session` to `agreety --cmd /bin/bash`.

### pwm 0.6.8 in the ISO

- **pwm 0.6.8** (tag `0.6.8`, pwm `1aa0e8e`) built with xbps-src for x86_64 and x86_64-musl, signed and published to the d77void repositories on SourceForge. The published glibc and musl packages verified against the repository key, and the glibc one is identical to the local build.
- **ISO:** rebuilt with the default repositories (SourceForge) under the build guard; pwm-0.6.8_1 came from SourceForge. 1,699,414,016 bytes, sha256 `ee49cd748b82306ad6c648872dfe935923c3ad5d43feffbf3d02e31e3612077e`. The host's `grub.cfg` was unchanged.

| # | Test | Result | Evidence |
|---|---|---|---|
| — | pwm startup race | **PASS** | 0 of 120 starts failed (60 with KMS, 60 with `nomodeset`), against 6 of 120 with pwm 0.6.7 |
| T5 | `nomodeset` | **PASS** | pwm up on vesa; after it ends, `agreety` on VT 7 and a shell after logging in |
| T6 | autologin pwm → greeter → wasp + Utumno | **PASS (3/3)** | pwm running after autologin in all 3 runs; wasp, qsd77 and Utumno from the greeter in all 3 |

### Corrections found while writing the user documentation

8. **Read-only LVM advice was wrong.** The comments in the masked udev rules suggested `vgchange -ay --readonly` and `lvchange -ay -pr`. Tested in a disposable VM with an LVM volume group on a loop file: `vgchange --readonly` activates nothing, and `lvchange -pr` **changed the disk's hash** (it writes the permission into the metadata). `vgchange -ay --config 'activation { read_only_volume_list = [ "<vg>" ] }' <vg>` activated the LV read-only (`-Ri-a-`), writes failed, a `ro,noload` mount worked and the hash did not change. The comments now give that command. `cryptsetup open --readonly` on a LUKS2 container behaved the same way (read-only mapping, hash unchanged).
9. **`sv up sshd` does not work** in the ISO (`unable to change to service directory`): `sshd` is not linked into `/var/service`. `APPROVAL_GATE.md` now says to enable it with `ln -s /etc/sv/sshd /var/service/` after changing the passwords.

The user documentation is in [d77void/orphaned-docs](https://github.com/d77void/orphaned-docs) (site and SourceForge wiki).

## Third round (2026-11-08): first real-hardware use, desktop and tools

The user booted the ISO on real hardware and reported: missing desktop basics (browser, file manager, icons, fonts, NetworkManager), no battery in Utumno, no wallpapers in pwm or wasp, no conky, no screen lock, and `xbps` not working. Fixes are decisions D17–D21 (`BASELINE_AUDIT.md` §9); the package review is in `PACKAGE_INVENTORY.md`.

- **ISO:** `d77orphaned-live-x86_64-20261108.iso`, 2,062,133,248 bytes, sha256 `67d3f024bf126b69170531da8bf68dec4b18d2c060f89c421b4c294f0a8af92d`, 711 binary packages. Built from SourceForge under the build guard (host `grub.cfg` unchanged). Written to the user's USB stick, verified by hash.
- **VM:** QEMU 11.1.3 with KVM, as in the second round.

| # | Test | Result | Evidence |
|---|---|---|---|
| — | `xbps` | **PASS** | `xbps-install -S` and `xbps-install -y tree` work as root; the reported failure was the user's network not being connected |
| — | pwm session | **PASS** | theme wallpaper (feh), conky, xautolock, xcompmgr, dunst, PipeWire + WirePlumber and the polkit agent running; `slock` present |
| — | Theme change (Kantele) | **PASS** | `[theme] active = "dracula"` + SIGHUP: pwm re-execs, the Dracula wallpaper is applied, and no background program is started twice |
| — | Leaving pwm after a theme change | **PASS** | `pkill pwm` ends the session and the greeter appears |
| — | Sound | **PASS (VM)** | `pactl info`: "PulseAudio (on PipeWire 1.6.10)" in both sessions (no sound card in the VM) |
| — | Battery (UPower) | **PASS (VM)** | `upower` daemon answers (`on-battery: no`, no battery in the VM) |
| — | NetworkManager | **PASS** | starts at boot, wired connected by itself; Utumno shows "wired"; Wi-Fi works on the user's hardware |
| — | wasp wallpaper | **PASS** | the default wallpaper is applied before Utumno starts (its backdrop hides). Switching with `set-wallpaper.sh apply` (what `super+y` runs) works on real hardware; in the VM (software rendering) the new image appears only with a transition, a wasp repaint quirk not seen with a GPU |
| T6 | autologin pwm → greeter → wasp | **PASS (2/2)** | wasp, qsd77 and Utumno; Kantele on Wayland |
| T7 | Libraries and commands | **PASS** | 2006 ELF executables, 0 missing libraries |
| T8 | Target disk integrity | **PASS** | 8 test disks unchanged after a full boot with a graphical session |

### Defects found and fixed in this round

10. **No wallpaper in wasp on a live system.** Utumno hides its backdrop only when `~/.cache/quickshell/wallpaper/current` exists when it starts; a fresh live home has none, so every wallpaper picked stayed under the backdrop. Fix (D20): `wasp-wallpaper.sh` applies a wallpaper before Utumno starts.
11. **pwm's startup script lost the wallpaper, conky and lock.** The minimal script written to avoid `udiskie` kept only `dunst`. Fix (D19), including starting each program once, since pwm re-runs the script on every theme change.
12. **Conky unreadable** (white text on pwm's light default wallpaper) and covering the wallpaper's kitten. Dark panel, bottom left.

**Rebuilt the same day** with conky on the left and the documentation inside the image: `d77orphaned-live-x86_64-20261108.iso`, 2,063,036,416 bytes, sha256 `1d45daf915a1793b985dbeecffa7c73173ebef7858f680f8ee21c33c4d7602bf`, documentation from orphaned-docs `69574e7`; host `grub.cfg` unchanged. In a VM: `/usr/share/doc/d77orphaned/{html,md,SOURCES.txt}` present, `links -dump` reads the pages on the console, and `d77-docs` in the pwm session opens the local site in Mullvad Browser without a network (**PASS**). Written to the user's USB stick for real-hardware testing.

## Persistence (2026-11-08, D22)

`d77-persist`, tested with `tests/persist-test.py`: QEMU with KVM, the ISO written to a 4 GiB image attached as a USB stick, and a second disk that also has a partition named `d77-data`.

- **ISO:** `d77orphaned-live-x86_64-20261108.iso`, 2,062,475,264 bytes, sha256 `ad5bcff3bbbba3f94cfb1fb4f4945741664a8f3e917c694603e95a1a8874d600`, documentation from orphaned-docs `f18221f`; host `grub.cfg` unchanged. Written to the user's USB stick, verified by hash.
- **Result: 21/21 checks passed.** A wrong answer at the confirmation writes nothing; `create` makes a LUKS2 partition on the boot device only, with a valid GPT; `close` locks it and puts the settings back; a wrong passphrase is refused; after a reboot it stays locked and unmounted; `open` brings back the files and settings (including a NetworkManager connection, which `nmcli` lists); `--data-only` leaves the settings alone; the live user can use it through `sudo`; **the second disk's hash did not change**.
- **Boot with the new partition table: PASS (VM).** SeaBIOS and OVMF both boot the stick to the pwm session after `create` (screenshots).
- **Power cut with the partition open (VM):** existing files and a file written with `sync` survive; a file written without `sync`, though listed by `ls`, is lost; the file system mounts normally. On real hardware (the Toshiba, forced power-off during the black screen below) nothing already saved was lost.
- **Real hardware:** works, according to the user, including reopening after a deliberately failed close. After `open`, pwm's theme and the Wi-Fi come back at once, and wasp and Utumno pick up their settings at the next login (user, normal boot).

## `nomodeset`: black screen on a legacy BIOS machine (2026-11-08, D23)

On a Toshiba with Intel HD 4000 and legacy BIOS, Xorg runs on the `vesa` driver (VBE 3.0). Leaving pwm **and** switching to a TTY with `Ctrl+Alt+F2` from inside pwm both left a black screen that only the power button got out of: the video BIOS apparently cannot switch modes back. QEMU's video BIOS does not reproduce this.

Fix: with `nomodeset`, X no longer ends on its own (`pwm-session.sh` restarts pwm, and gives up after 5 quick failures) and `DontVTSwitch` turns `Ctrl+Alt+Fn` off. Power off with pwm's menu.

- **ISO:** `d77orphaned-live-x86_64-20261108.iso`, 2,063,034,368 bytes, sha256 `98b05ca43a8661c01d2125c547aa58947f6c12863a4877578f26ab91f1549b7d`; host `grub.cfg` unchanged.
- **VM, `nomodeset`: PASS.** Killing pwm starts a new pwm under the same Xorg, with no background program started twice; `Ctrl+Alt+F2` stays on VT 7; `loginctl poweroff` (what the menu runs) powers off. It refuses while another user is logged in (root on the test's serial console), and pwm's menu shows no message when that happens.
- **VM, normal boot: unchanged.** `Ctrl+Alt+F2` switches, and leaving pwm brings up the greeter.
- **Real hardware (the Toshiba, user, 2026-11-08): PASS.** No more black screen: `logout` in pwm's menu appears to do nothing (pwm restarts at once under the same X, and windows stay), `Ctrl+Alt+F2` does nothing, and `reboot` and `shutdown` work.

## Published ISO (2026-11-08)

Published to the `ISO-x86_64` folder on SourceForge as a prototype, with its `.iso.sha256` and `.SOURCES.txt`; `iso.sh` confirmed the copies match. It replaces an upload from earlier the same day with the same name (sha256 `13afb7b1…931a`, without `nwipe` and `parallel`).

- **ISO:** `d77orphaned-live-x86_64-20261108.iso`, 2,063,949,824 bytes, sha256 `c84d919eedc5e12deb8c835c18f60be62a51710d60ae8bd64cc0605e31b3c09f`. Built from d77orphaned `b747ec42` and orphaned-docs `307bce4`, from the SourceForge d77void repository; host `grub.cfg` unchanged.
- **Tests on this exact ISO (VM):** T7 (2007 executables, 0 failures). The previous build, with the same packages and older documentation, passed T8 and the `nwipe` tests; persistence passed 21/21 on the one before, without `nwipe` and `parallel`. Real-hardware tests were on those previous builds.

## Secure erasure (2026-11-08, D24)

`nwipe` 0.41 and `parallel` added. Tested in a VM on a build of `d77orphaned-live-x86_64-20261108.iso`, 2,063,185,920 bytes, sha256 `e9eb6cf4404f55db00a8c1bdb6a4bfc3066f7563fb68d37329323a9f42cd9e1c`, not published yet; host `grub.cfg` unchanged.

- **Wipe: PASS.** `--method=zero --verify=last` on a virtual disk: it reads back as all zeros, and the log says "Erased".
- **`--autonuke` with no device: PASS.** It wiped none of these: the boot stick (hash unchanged; "IN USE"; also with the RAM boot entry, where it stays mounted), a disk given to `--exclude` (hash unchanged) and a mounted disk (read-only mount, hash unchanged while mounted and after, file still readable). A first run reported the mounted disk as changed: that test mounted it read-write, and `umount` itself writes to ext4.
- **`parallel`: PASS**, including `--dry-run`.
- **T7: PASS** (2007 executables, 0 failures). **T8: PASS** (8 disks unchanged).
- **Real hardware (user):** `nwipe` works on the Toshiba with a disposable stick. Its screen is unreadable in pwm's `st` (Dracula colours and transparency compiled into `d77-st`) and readable in wasp's `alacritty`.
- **Not tested:** `hdparm` security erase, `nvme sanitize`/`format` and `sg_sanitize` on real drives (only their options were checked against the tools in the ISO).

## Open

- **T12 real hardware:** done by the user (2026-11-08), with no open failures: boot, both sessions, Wi-Fi with NetworkManager, wallpaper switching, offline documentation, battery, sound, conky, screen lock, theme and keyboard in Kantele, the console-only entry, `nomodeset` (after D23), TTY switching and logout on a normal boot, and persistence. **Machines:** a Toshiba with legacy BIOS and a T480s with Libreboot. On the T480s the stick boots with both the SeaBIOS and the GRUB payloads, with the persistence partition added, and persistence works in both (user).
- **`nomodeset` under UEFI:** untested. A VM with OVMF and a direct kernel boot did not reach the login.
- **Sony Vaio (Core 2 Duo P8400, old nVidia):** intermittent segmentation faults in `su` and `sudo nwipe`, then `SQUASHFS error: Unable to read page` and `exec: dwl: Input/output error`: the system is failing to read the stick, which works on the Toshiba and was verified by hash. The USB port, power or memory on that laptop are suspected; not confirmed. Not an ISO defect as far as is known. Another port was being tried.
- **ThinkPad X61:** planned by the user, not tested yet.
- **MD RAID read-only assembly** (`mdadm --assemble --readonly`): documented but not tested.
- **Phase-5 T6 case** (wasp login ending in pwm): not reproduced in 9 runs with greetd logging to `/var/log/greetd` (the harness now sets that up). Treated as unexplained, not fixed.
- **Cosmetic:**
  - on wasp with software rendering, the background shows leftovers of the greeter, and there is a black block left of Utumno's bar;
- **Size:** the ISO is 2.06 GB (1.6 GiB before D17/D18), well above the gate's 0.9–1.1 GiB estimate; Mullvad Browser (350 MB installed) and Papirus (117 MB) are the largest additions.
