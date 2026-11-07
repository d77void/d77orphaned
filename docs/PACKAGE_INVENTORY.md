# Package inventory — PHASE 0/1: FOUND IN INDEXES (phase 5 test status at the end)

**Note:** "FOUND" means the package is in the repository index. Package in index ≠ package installed ≠ working tool in the live system. Do not copy this table into any build script; the build manifest is in `mkorphaned.sh`. Phase 5 test results are in `TEST_REPORT.md`.

- **Date:** 2026-11-07
- **Method:** reading `index.plist` from the `repo-default.voidlinux.org/current` (+`nonfree`) and d77void (SourceForge) repositories, x86_64 and x86_64-musl. The dependency closure was computed from `run_depends` and is an estimate. Details and reproduction commands in `BASELINE_AUDIT.md`.
- **"+deps"** = packages/MiB the package adds to the `base-system` closure (x86_64). musl values identical unless noted.
- **Decision** = phase 3 proposal, later approved in `APPROVAL_GATE.md`.

## Core (console)

| Capability | Exact package (origin) | Version | +deps | Status | Proposed decision / notes |
|---|---|---|---|---|---|
| Identification/partitions | `util-linux` `parted` `gptfdisk` (Void) | 2.41.4 / 3.8 / 1.0.10 | 0 / +2·3M / +2·1M | FOUND | INCLUDE |
| SMART / NVMe / ATA / SCSI | `smartmontools` `nvme-cli` `hdparm` `sdparm` `sg3_utils` `lsscsi` (Void) | 7.5 / 2.16 / 9.65 … | ≤ +3·3M each | FOUND | INCLUDE |
| Imaging / block recovery | `ddrescue` (Void; **`gddrescue` does not exist**) | 1.29.1 | +1·0M | FOUND | INCLUDE |
| Partition/file recovery | `testdisk` (Void; includes photorec — confirmed in T7) | 7.2 | +16·21M | FOUND | INCLUDE |
| FS cloning/backup | `partclone` `fsarchiver` (Void) | 0.3.47 / 0.8.6 | +17·20M / +3·3M | FOUND | INCLUDE |
| Filesystems | `e2fsprogs` `xfsprogs` `btrfs-progs` `dosfstools` `exfatprogs` `ntfs-3g` `f2fs-tools` `mtools` | — | ntfs-3g +14·18M; rest ≈0 | FOUND | INCLUDE |
| Encryption/volumes | `cryptsetup` `lvm2` `mdadm` (Void) | 2.8.8 / 2.03.29 / 4.4 | ≤ +5·6M | FOUND | INCLUDE; **disable auto-activation** (see audit §5) |
| ZFS | `zfs` (Void, DKMS) | 2.4.4 | **+39·559M** | FOUND | **EXCLUDE** in the PoC (DKMS + compiler) |
| EFI / boot | `efibootmgr` `efivar` `os-prober` `grub-x86_64-efi` `grub-i386-efi` (Void) | 18 / 39 / 1.84 / 2.12 | grub-efi +7·33M | FOUND | INCLUDE (grub comes via mklive) |
| Memory | `memtest86+` (Void) | 9.00 | — | FOUND | Already included by `mklive.sh` on x86 |
| Base network | `iproute2` `iputils` `dhcpcd` `iwd` **or** `wpa_supplicant` `openssh` `curl` `rsync` | — | NetworkManager +31·61M | FOUND | INCLUDE without NetworkManager [PROP]; **sshd off by default** |
| Network diagnostics | `tcpdump` `traceroute` `mtr` `ldns` (drill) `openbsd-netcat` `socat` `nmap` (**nonfree**) | — | nmap +3·29M; bind-utils +15·14M | FOUND | INCLUDE; `ldns` instead of `bind-utils` |
| Hashing / forensic imaging | `coreutils` `dcfldd` (Void; **`dc3dd` does not exist**) `libewf` | 9.4 / 1.3.4 / 2026-09-24 | libewf +2·10M | FOUND | INCLUDE |
| Forensic analysis | `sleuthkit` `foremost` `exiftool` (Void; **`perl-Image-ExifTool` → `exiftool`**) | 4.13 / 1.5.7 / 13.57 | sleuthkit +6·85M; exiftool +4·96M | FOUND | INCLUDE sleuthkit+foremost; exiftool deferred (size) |
| Hardware | `dmidecode` `pciutils` `usbutils` `hwinfo` `lshw` | — | lshw +1·8M | FOUND | INCLUDE (lshw optional) |
| Firmware | `linux-firmware` (Void, already in `base-system`) | 20260810 | network = 442 MiB | FOUND | INCLUDE (needed for Wi-Fi) |
| Offline Windows | `chntpw` (Void) | 140201 | +1·0M | FOUND | INCLUDE [PROP] |
| USB sticks / fakes | `f3` (Void) | 9.0 | +2·1M | FOUND | INCLUDE [PROP] |
| Console / maintenance | `tmux` `vim` `less` `man-db` `lsof` `strace` `pv` `zstd` `p7zip` `squashfs-tools` | — | vim +5·44M; neovim +15·36M | FOUND | INCLUDE; a single editor |

## Optional / phase 2

| Capability | Exact package (origin) | +deps | Status | Proposed decision / notes |
|---|---|---|---|---|
| CLI traffic capture | `wireshark` (Void, CLI package; **there is no `tshark`**) | +41·206M | FOUND | DEFER; `tcpdump` covers the PoC |
| TUI capture | `termshark` | +42·223M | FOUND | DEFER |
| Wireshark GUI | `wireshark-qt` | **+225·649M** | FOUND | EXCLUDE in the PoC |
| Advanced metadata | `bulk_extractor` | — | **MISSING** | DEFER (would be a port) |
| Integrity/AFF | `afflib` `yara` `binwalk` | ≤ +15·10M | FOUND | DEFER |
| Web auditing | `nikto` `sqlmap` | +7·77M / +5·37M | FOUND | DEFER |
| Passwords | `john` / `hashcat` | +51M / **+149M** | FOUND | `john` DEFER; `hashcat` EXCLUDE (no GPU in the live system) |
| Service brute force | `thc-hydra` (**not `hydra`**) | +6·30M | FOUND | DEFER |
| Host auditing | `lynis` `rkhunter` `chkrootkit` | +1·2M / +17·83M / +19·49M | FOUND | `lynis` INCLUDE [PROP]; the others DEFER |
| TLS / SSH | `testssl.sh` `ssh-audit` | +16·17M / +5·25M | FOUND | DEFER |
| L2 discovery | `arp-scan` | +1·2M | FOUND | INCLUDE [PROP] |
| Shares | `fuse-sshfs` (**not `sshfs`**) `nfs-utils` `cifs-utils` | +4·15M / +7·5M / +27·63M | FOUND | DEFER |
| VPN | `wireguard-tools` | +2·0M | FOUND | DEFER |
| Network performance | `iperf3` | +1·0M | FOUND | DEFER |
| Secure erase | `nwipe` | +6·4M | FOUND | **EXCLUDE** in the PoC (destructive by nature) |

## d77 graphics

| Component | Exact package (origin) | +deps | Status | Notes |
|---|---|---|---|---|
| X11 base | `xorg-minimal` `xorg-input-drivers` `xorg-video-drivers` `xinit` + fonts (Void) | full pwm set: 183 pkgs / 751 MiB installed | FOUND | no SDDM [PROP] |
| pwm | `pwm` 0.6.7_1 (**d77void**, glibc and musl) | +19·249M (incl. X) | FOUND | the package's startup runs `udiskie -a`; override `startup_script` [INF]. **Phase 5:** needs `xmodmap`, undeclared |
| X11 terminal | `d77-st` (d77void, pwm dependency) | +13·11M | FOUND | — |
| X11 launcher | `dmenu` (Void, pwm dependency) | +14·11M | FOUND | `rofi` (+42·58M) optional |
| Wayland base | `mesa-dri` `dbus` `elogind` `polkit` | — | FOUND | — |
| wasp | `wasp` 0.10.1_1 (**d77void, glibc only**) + `scenefx0.5` (d77void) + `wlroots0.20` (Void) | +99·149M | FOUND | **MISSING on musl**. **Phase 5:** needs `WLR_RENDERER_ALLOW_SOFTWARE=1` without a GPU |
| Utumno | `utumno` 0.2.0_1 (d77void) | +92·195M | FOUND | **does not declare `quickshell` or `qsd77`**: list them explicitly; queries wttr.in |
| Utumno runtime | `quickshell` 0.3.2 (Void) + `qsd77` 1.3.3 (d77void, Go CLI) | quickshell +143·291M | FOUND | required by Utumno |
| Wayland launcher | `wmenu` (Void) | +27·44M | FOUND | `d77run` (GTK4, +182·369M) EXCLUDE [PROP] |
| Wayland terminal | `alacritty` (Void) | +23·31M | FOUND | — |
| d77 tools | `kantele` 0.3.0_1 (d77void) | +7·19M on top of the rest | FOUND | added at the user's request (D12) |
| Automounting | `udiskie` `udisks2` `gvfs` | — | FOUND | **EXCLUDE** (conflicts with the integrity policy) |

## Required record per approved package

Copy this template for **each package** during research:

```text
Function:
Exact name / origin (official Void, d77void, new port):
Architecture / libc / version / date:
Search command + relevant output:
New dependencies and size:
Install test (disposable environment):
Functional test + result:
Risks (kernel, firmware, licenses, privileges):
Alternatives:
Maintenance effort:
Decision: INCLUDE / DEFER / EXCLUDE / PORT PROPOSED
Rationale:
```

## Counters

- Core packages **found**: ~65 names, all in official Void/nonfree. **Phase 5:** all promised commands present and 1499 ELF executables with no missing libraries (T7).
- Optional packages found: ~20; none in the PoC image except `lynis` and `arp-scan`.
- d77 packages reused unchanged: `pwm`, `d77-st`, `wasp`, `scenefx0.5`, `utumno`, `qsd77`, `dwl`, `kantele` (wasp/scenefx0.5/dwl glibc only).
- New essential ports: **0** (x86_64 glibc).
- New optional ports: `bulk_extractor` (1); on musl, +2 (`wasp`, `scenefx0.5`).
- Size: estimate core+pwm+wasp ≈ 2.4 GiB installed → ISO ≈ 0.9–1.2 GiB; **measured in phase 5: ISO 1.6 GiB**, 450 packages.

**Sustainability gate:** with **5** new essential ports, stop and review the scope with the user; near **30**, the design is infeasible. A missing package does not force a port.
