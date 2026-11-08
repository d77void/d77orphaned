# APPROVAL_GATE — Phase 4: PoC approval gate

- **Date:** 2026-11-07
- **Based on:** `BASELINE_AUDIT.md` (decisions D1–D7) and `PACKAGE_INVENTORY.md`.
- **Status:** **APPROVED on 2026-11-07** (D10); P1 = `dhcpcd` enabled, P2 = `chronyd` enabled. At approval time nothing had been built or tested; all packages had been *found in the indexes* (x86_64 glibc, 2026-11-07). Phase 5 results: `TEST_REPORT.md`.

Approving this document authorizes **phase 5 — prototype**: create the local `d77orphaned` repository, copy the builder, write the manifest and overlay, build the ISO on a Void host and test it in a VM. It does **not** include creating or publishing the remote repository, publishing packages, or changing d77void, Utumno or any other project. *(The remote was later authorized separately — D11.)*

Notes in *italics* record how phase 5 actually implemented or changed an item.

---

## 1. Summary

| | |
|---|---|
| Architecture | x86_64 glibc (D2) |
| Builder | own copy of `mklive.sh` and the files it depends on (D3) *(implemented as a full clone of d77void, then pruned)* |
| Login | greetd + quickshell-d77 greeter, with autologin into pwm (D4–D6) |
| Console-only boot | dedicated entry with `d77.nogui` (D7) |
| New ports | **0** |
| Packages in the PoC closure | 456: Void 446, nonfree 1 (`nmap`), d77void 9 *(measured: 450 installed)* |
| Installed size (estimate) | ≈ 2.2 GiB → ISO ≈ 0.9–1.1 GiB (**not measured**) *(measured: ISO 1.6 GiB)* |
| Unwanted packages in the closure | none: verified that `udisks2`, `udiskie`, `gvfs`, `NetworkManager`, `ollama`, `calamares`, `pipewire`, `sddm` and `pulseaudio` do **not** get in |

## 2. Proposed manifest

*Since 2026-11-08 the manifest is larger than this section: see `PACKAGE_INVENTORY.md`, "Review after the first real-hardware use", and decisions D17–D19.*

### 2.1 Included automatically by `mklive.sh` (not listed)
`base-system` (kernel 6.18, linux-firmware), `syslinux`, `grub-i386-efi`, `grub-x86_64-efi`, `memtest86+` and the initramfs packages (`dracut-network`, `device-mapper`…).

### 2.2 Core — console (66, all Void except `nmap`)

| Group | Packages |
|---|---|
| Disks and storage hardware | `util-linux` `parted` `gptfdisk` `smartmontools` `nvme-cli` `hdparm` `sdparm` `sg3_utils` `lsscsi` |
| Recovery and cloning | `ddrescue` `testdisk` `partclone` `fsarchiver` |
| Filesystems | `e2fsprogs` `xfsprogs` `btrfs-progs` `dosfstools` `exfatprogs` `ntfs-3g` `f2fs-tools` `mtools` |
| Volumes and encryption | `cryptsetup` `lvm2` `mdadm` (with auto-activation disabled, §4) |
| Boot / EFI | `efibootmgr` `efivar` `os-prober` |
| Network | `iproute2` `iputils` `dhcpcd` `wpa_supplicant` `openssh` `curl` `rsync` |
| Network diagnostics | `tcpdump` `nmap`* `traceroute` `mtr` `ldns` `openbsd-netcat` `socat` `arp-scan` |
| Forensics | `dcfldd` `libewf` `sleuthkit` `foremost` |
| Hardware and system | `dmidecode` `pciutils` `usbutils` `hwinfo` `chntpw` `f3` `lynis` *(+ `acpid`)* |
| Operations | `tmux` `vim` `less` `man-db` `lsof` `strace` `pv` `zstd` `p7zip` `squashfs-tools` `dialog` `chrony` `xtools-minimal` |

\* `nmap` comes from the **nonfree** repository (NPSL license). The build must add `-r https://repo-default.voidlinux.org/current/nonfree`, because `mklive.sh` does not include nonfree by default. NPSL allows redistribution in a free ISO; reviewed on 2026-11-07, see §9.

### 2.3 X11 graphics — pwm (16)
`xorg-minimal` `xorg-input-drivers` `xorg-video-drivers` `xinit` `setxkbmap` `xauth` `dejavu-fonts-ttf` `terminus-font` `font-misc-misc` `pwm`† `d77-st`† `dmenu` `sxhkd` `dbus` `elogind` `polkit` *(implemented: `sxhkd` dropped — no sxhkdrc in the overlay; `dbus-x11` added for `dbus-launch`; `xmodmap` added — pwm needs it, see `TEST_REPORT.md`)*

### 2.4 Wayland graphics — wasp + Utumno (10)
`mesa-dri` `wasp`† `utumno`† `qsd77`† `quickshell` `matugen` `wmenu` `alacritty` `dunst` `awww`

### 2.5 Login (2 + overlay)
`greetd` `dwl`† and the greeter copied from `d77void/common/quickshell-d77/greeter` (§3).

† Packages from the d77void repository (signature verified, `keys/2b:d7:…`). The closure also pulls `d77-st-terminfo`, `font-JetBrainsMono` and `scenefx0.5`, also from d77void.

### 2.5b d77 tools (added at the user's request, 2026-11-07)
`kantele`† (settings GUI for pwm and wasp): +7 packages / ≈19 MiB on top of the rest of the manifest (Qt6/Python already present).

### 2.6 runit services
| Service | State | Note |
|---|---|---|
| `dbus` `elogind` `polkitd` `acpid` | enabled | needed by the graphical sessions and ACPI *(elogind is D-Bus activated, not a runit service)* |
| `greetd` | enabled, except with `d77.nogui` | D5–D7 |
| `dhcpcd` | enabled | D8 *(replaced by NetworkManager at boot, D17; dhcpcd stays installed)* |
| `chronyd` | enabled | D9 |
| `sshd` | **disabled** | installed; after changing the passwords, enable it with `ln -s /etc/sv/sshd /var/service/` (`sv up sshd` fails: the service is not linked) |
| `wpa_supplicant` | disabled | used manually or via dhcpcd *(NetworkManager uses it on its own, D17)* |

## 3. Optional — phase 2 (not in the PoC)
`exiftool`, `wireshark` (tshark CLI), `termshark`, `afflib`, `yara`, `binwalk`, `nikto`, `sqlmap`, `john`, `thc-hydra`, `testssl.sh`, `ssh-audit`, `fuse-sshfs`, `nfs-utils`, `cifs-utils`, `wireguard-tools`, `iperf3`, `rkhunter`, `chkrootkit`, `lshw`, console accessibility (`espeakup`, `brltty`, `void-live-audio`). With all of these the image would grow to ≈ 2.6 GiB installed.

## 4. Out
| Package | Reason |
|---|---|
| `zfs` | DKMS + compiler, +559 MiB |
| `hashcat` | no GPU in the live system; `john` covers the function |
| `wireshark-qt` | +649 MiB |
| `nwipe` | destructive by nature |
| `udiskie` `udisks2` `gvfs` | automounting, incompatible with the integrity policy |
| `NetworkManager` | +61 MiB; dhcpcd/wpa_supplicant are enough *(brought in by D17 after real-hardware use)* |
| `d77run` | GTK4, +369 MiB; `dmenu`/`wmenu`/Utumno's launcher are enough |
| `ollama`, `calamares`, `sddm`, `plymouth`, `pipewire` | no role in the PoC |
| `orca` | +373 MiB; graphical accessibility deferred |
| `bulk_extractor`, `dc3dd` | not in Void; not porting |

## 5. What is reused from d77void and how

| Origin (commit `c567d0cf`) | How | Planned local changes in `d77orphaned` |
|---|---|---|
| `mklive.sh`, `lib.sh`, `version` | **copy** + `COPYING` (BSD-2) + provenance record | own label (`D77ORPHANED`) instead of `VOID_LIVE`; autoinstaller removed (row below) *(also: EFI image write checked, with mtools fallback)* |
| `dracut/vmklive/` | copy | `adduser.sh`: no `sshd` enabled; new `nogui.sh` hook (D7); polkit kept (the live user already has passwordless `sudo`; the real risk was automounting, which loses its tools) |
| `dracut/autoinstaller/` | **do not copy** | `mklive.sh` references it in 3 places (`copy_autoinstaller_files`, `--force-add`, `rm -r`) → remove those references in the copy. It only triggers with `root=vai`, but it is a **destructive** installer inside the initramfs; it must not exist in a forensic ISO |
| `dracut/netmenu/` | do not copy | not used by `mklive.sh` |
| `grub/`, `isolinux/` | copy | title `d77orphaned`; "console only" entry with `d77.nogui`; speech entries removed (phase 2); `rd.lvm=0` added to the cmdline |
| `keys/` (3 public keys) | copy | — |
| `data/splash.png` | copy, or our own splash | own branding when it exists |
| `common/quickshell-d77/greeter/` | copy into the overlay `/etc/greetd/…` | `config.toml` with `[initial_session]` (pwm) |
| d77void binary repository | `-r` at build time | — |

**What does not change:** d77void's `mkd77.sh`, skels and `common/`, the pwm/wasp/Utumno/qsd77/dwl packages, the binary repository and Utumno. Utumno's weather is handled via `/etc/hosts` in the overlay (D1).

### Own overlay (`includedir/`)
- `/etc/hosts` with `0.0.0.0 wttr.in` (D1).
- `/etc/greetd/config.toml` + greeter + `greet-dwl.sh` (D4–D6).
- `/etc/skel/.config/pwm/config.toml` with its own `startup_script` **without `udiskie`** (pwm without automounting).
- Own `/etc/skel/.config/wasp/config.lua`: autostart without `udiskie`, `pipewire` and `ollama`; keeps `qsd77 run -c utumno`, `dunst`, `awww`.
- `/etc/lvm/lvm.conf` with `event_activation = 0` and `auto_activation_volume_list = []`; `/etc/mdadm.conf` with `AUTO -all` (to test, §6). *(Implemented: `lvm.conf` is edited by `postsetup.sh`; the udev rules `64-md-raid-assembly.rules` and `69-dm-lvm.rules` are also masked.)*
- Own `/etc/os-release` (`ID_LIKE=void`).
- Do **not** bring `.auto.sh`, `d77-welcome`, `50-udisks.rules` or the plymouth rules.

## 6. Test plan

**Where:** build on a Void host. Integrity tests run **only in a VM with disposable disks**. Real hardware is only for boot, graphics and network: the T480s (Libreboot) and a legacy-BIOS machine if available. No destructive tests on personal machines.

| # | Test | Environment | Success criterion |
|---|---|---|---|
| T1 | Reproducible build | Void host | ISO produced; the log lists the manifest packages; no §4 package in the rootfs (`xbps-query -r`) |
| T2 | BIOS boot | QEMU SeaBIOS | isolinux menu; boots to the TTY and greetd |
| T3 | UEFI boot | QEMU OVMF | GRUB menu; same |
| T4 | `d77.nogui` | QEMU | greetd does not start; TTY1 usable |
| T5 | `nomodeset` + pwm | QEMU (VGA std) | pwm autologin starts with fbdev/vesa |
| T6 | Autologin pwm → log out → greeter → wasp+Utumno | QEMU virtio-gpu | both sessions start; the bar shows "weather unavailable" with networking up (D1) |
| T7 | Core tools | QEMU | every §2.2 binary runs `--version`/`-h` without missing libraries (check script) |
| T8 | Integrity: target disks | QEMU with test disks: ext4 with an unclean journal, XFS, NTFS, LUKS2, MD RAID1, LVM, swap | after boot and after graphical login: no `md*` assembled, no LV active, no LUKS open, nothing mounted, swap inactive (`/proc/mdstat`, `lvs`, `lsblk`, `/proc/swaps`, `mount`); disk SHA-256 hashes identical before and after |
| T9 | Safe mounting | QEMU | `blockdev --setro` + `mount -o ro,noload` (ext4) / `ro,norecovery` (XFS) do not change the hash |
| T10 | Network | QEMU + hardware | wired DHCP (per P1); Wi-Fi via wpa_supplicant on the T480s; `sshd` off (`ss -tln`) |
| T11 | No persistence | QEMU | booting without a data partition neither blocks nor delays |
| T12 | Real hardware | T480s (Libreboot) | UEFI/payload boot, X11, Wayland, Wi-Fi |

LUKS2 persistence comes after the base PoC, as the RESEARCH_PLAN says (phase 5, last step).

## 7. Known risks
- **MD/LVM auto-activation after the initramfs:** the mitigation (§5) is untested. If T8 fails, consider local udev rules in the overlay. *(T8 initially failed on LVM because of runit's `vgchange -a ay`; fixed and passing.)*
- **Utumno on wasp:** the workspace widgets target Hyprland/Sway/niri, so on wasp they may stay empty. Cosmetic, not blocking.
- **greetd + pwm in live:** confirmed in real use on the laptop, never exercised in an ISO. *(Works in phase 5.)*
- **`dwl` and `scenefx0.5` only exist in the d77void repository:** the ISO depends on SourceForge being available at build time.
- **ISO label:** keeping `VOID_LIVE` would conflict with other Void sticks, hence the own label.
- **Size estimates:** computed from `run_depends`; T1 measures the real value.

## 8. Open questions (answered)
- **P1 — Network at boot:** `dhcpcd` enabled by default (Grml-style, network ready, but announces itself on the network at boot) or manual (`sv up dhcpcd`)? → **Enabled (D8).**
- **P2 — Clock:** `chronyd` enabled (correct time in logs and hashes, but contacts NTP servers) or manual? → **Enabled (D9).**
- **P3 — Approval:** do you approve the manifest (§2), exclusions (§3–4), reuse (§5) and test plan (§6) to move to phase 5? → **Approved (D10).**

## 9. License review: `nmap` (NPSL 0.95)

Reviewed 2026-11-07 against the license text shipped in the package (`nmap-7.99_1`, Void `nonfree`, `license="custom:nmap"`, `/usr/share/licenses/nmap/LICENSE`, "Nmap Public Source License Version 0.95"). This is a reading of the license, not legal advice.

- **What NPSL is:** GPLv2 (Exhibit A) plus extra terms that take precedence where they conflict (§2). The extra terms mean Nmap cannot be redistributed under plain GPL, and the license is not OSI-approved. Void ships it in `nonfree`, and Debian and Fedora also treat it as non-free. So the ISO is not "100% free software", and the documentation must not claim that.
- **Redistributing the unmodified binary in the ISO is allowed.** The GPL part permits it, and the NPSL adds no restriction on plain redistribution.
- **The ISO is not a "derivative work" under NPSL §3.** §3 says that "including Nmap with other software in compressed or archival form does not trigger this provision", provided open decompression tools are widely available, which is the case for squashfs and ISO 9660. Nothing in d77orphaned integrates Nmap source, reads its data files (`nmap-os-db`, `nmap-service-probes`), parses its output, or ships it in a proprietary installer. Utumno, Kantele and the menus only launch programs the user picks.
- **§6 (External Deployment)** applies only to services that run Nmap for other people, which the ISO does not do. **§7:** the name may be used to describe the origin ("includes Nmap"), not as branding. **§10 (Npcap)** concerns the Windows builds only.
- **Obligations when the ISO is published:**
  1. Keep the license text with the binary. **Done:** it is in the image (verified in a VM).
  2. Make the corresponding source available (GPLv2 §3), for example by offering it from the same place as the ISO. The source of the binary is the upstream tarball `https://nmap.org/dist/nmap-7.99.tar.bz2` (sha256 `df512492…d51b2`, from Void's template) built with Void's `srcpkgs/nmap/template`, with no patches. Not specific to Nmap: every GPL program in the ISO (kernel, coreutils, …) has the same requirement. **Done (2026-11-07):** each build writes `d77orphaned-live-x86_64-<date>.SOURCES.txt` next to the ISO and `/usr/share/doc/d77orphaned/SOURCES.txt` in it (`mksources.sh`). It lists every installed package with its license and source (`sources.voidlinux.org/<package>-<version>/` for Void packages, `srcpkgs-d77` and the homepage for d77void ones) and carries a written offer, valid for three years, with requests through the d77orphaned GitHub issues. Checked: 383 of the 386 Void source links answer; the three missing archives (`sof-firmware`, `xf86-input-vmmouse`, `xf86-video-vesa`) are BSD/MIT, and their entries also give the homepage.
- **Conclusion:** `nmap` can stay in a published ISO. Publish the `SOURCES.txt` file together with each ISO (point 2), and describe the image as containing non-free software (`nmap`).
