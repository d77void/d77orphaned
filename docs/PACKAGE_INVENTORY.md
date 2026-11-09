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
| CLI traffic capture | `wireshark` (Void, CLI package; **there is no `tshark`**) | +41·206M | FOUND | DEFER; `tcpdump` covers the PoC *(D25: documented, installed when needed)* |
| TUI capture | `termshark` | +42·223M | FOUND | DEFER *(D25: documented, installed when needed)* |
| Wireshark GUI | `wireshark-qt` | **+225·649M** | FOUND | EXCLUDE in the PoC |
| Advanced metadata | `bulk_extractor` | — | **MISSING** | DEFER (would be a port) *(D25: rejected)* |
| Integrity/AFF | `afflib` `yara` `binwalk` | ≤ +15·10M | FOUND | DEFER *(`afflib`, `binwalk`: D18; `yara`: D25, in the image)* |
| Web auditing | `nikto` `sqlmap` | +7·77M / +5·37M | FOUND | DEFER |
| Passwords | `john` / `hashcat` | +51M / **+149M** | FOUND | `john` DEFER *(D25: documented, installed when needed)*; `hashcat` EXCLUDE (no GPU in the live system) |
| Service brute force | `thc-hydra` (**not `hydra`**) | +6·30M | FOUND | DEFER |
| Host auditing | `lynis` `rkhunter` `chkrootkit` | +1·2M / +17·83M / +19·49M | FOUND | `lynis` INCLUDE [PROP]; the others DEFER |
| TLS / SSH | `testssl.sh` `ssh-audit` | +16·17M / +5·25M | FOUND | DEFER *(D25: in the image)* |
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
- Size: estimate core+pwm+wasp ≈ 2.4 GiB installed → ISO ≈ 0.9–1.2 GiB; **measured in phase 5: ISO 1.6 GiB**, 450 packages. **2026-11-08, after D17/D18:** ISO 2.06 GB (2,062,133,248 bytes), 711 binary packages from 615 source packages.

**Sustainability gate:** with **5** new essential ports, stop and review the scope with the user; near **30**, the design is infeasible. A missing package does not force a port.

## Review after the first real-hardware use (2026-11-08)

The user found the image hard to use day to day: no battery in Utumno, no wallpapers, missing desktop basics and tools. Two comparisons, both **verified by command** on 2026-11-08 (x86_64 glibc; repositories Void `current`, `current/nonfree` and d77void on SourceForge):

- **Grml:** `grml-live` @ `6d729f0` (2026-11-06), lists `GRMLBASE`, `GRML_FULL` and `XORG` (amd64). 383 entries: 100 already in the ISO, 149 available in Void (after mapping Debian names, e.g. `gddrescue`→`ddrescue`, `lm-sensors`→`lm_sensors`, `bind9-dnsutils`→`bind-utils`), 46 not found in Void under that name, 67 Debian/Grml-specific (apt, grml-*, firmware-*, systemd, …).
- **d77void desktop:** the packages of d77void's `wasp` and `pwm` variants (`mkd77.sh` @ `c567d0cf`, glibc) that the ISO lacks: 76.

Already decided (D17): `mullvad-browser` `NetworkManager` `font-hack-ttf` `feh` `conky` `papirus-icon-theme` `ranger`.

Root causes found while comparing: Utumno reads the battery through **UPower** (`upower` missing) and pwm's volume keys run `pactl` (no audio stack: `pipewire`, `wireplumber`, `pulseaudio-utils` missing).

Sizes are installed sizes of the package alone, not counting dependencies.

### A. Desktop: needed for the sessions to work as in d77void (proposed: include)

| Packages | Size | Why |
|---|---|---|
| `upower` | 0.6 MB | battery in Utumno (and pwm's bar) |
| `pipewire` `wireplumber` `alsa-pipewire` `pulseaudio-utils` `pavucontrol` | 8 MB | sound; pwm/Utumno volume keys and widgets (`pactl`) |
| `mate-polkit` | 0.3 MB | password prompts for graphical programs (e.g. NetworkManager) |
| `nerd-fonts-symbols-ttf` `noto-fonts-emoji` `font-awesome6` | 17 MB | icons in the bars and Kantele |
| `xdg-desktop-portal` `xdg-desktop-portal-gtk` `xdg-desktop-portal-wlr` `qt5-wayland` | 7 MB | file dialogs, screen sharing, Qt5 programs on Wayland |
| `xdg-utils` `xdg-user-dirs` | 0.5 MB | opening links/files with the right program |
| `arc-theme` `qt6ct` `nwg-look` | 13 MB | the same look as d77void |
| `htop` `inxi` `bash-completion` `nano` `unzip` `wget` `bc` | 11 MB | everyday basics |
| `zathura` `zathura-pdf-poppler` | 2 MB | reading PDFs (manuals, reports) |

### B. Tools from Grml, small and useful for recovery (proposed: include)

| Area | Packages | Size |
|---|---|---|
| Console | `mc` `ncdu` `tree` `screen` `psmisc` `sysstat` `iotop` `moreutils` `mbuffer` | 13 MB |
| Hardware | `lshw` `lm_sensors` `memtester` `stress` `fio` `cpuid` `cpupower` `acpi` | 19 MB |
| Disks/filesystems | `dmraid` `dislocker` (BitLocker) `xmount` `afflib` `extundelete` `gpart` `jfsutils` `xfsdump` `bcache-tools` `fuse-exfat` | 4 MB |
| Network | `bind-utils` `whois` `ipcalc` `iftop` `nethogs` `iperf3` `net-tools` `wireguard-tools` `openvpn` `lftp` `links` | 13 MB |
| Network filesystems | `fuse-sshfs` `nfs-utils` `cifs-utils` | 2 MB |
| Analysis | `hexedit` `ltrace` `binwalk` | 4 MB |
| Archives | `zip` `cabextract` `lz4` `lzop` `unp` | 1 MB |
| Serial consoles | `minicom` `tio` | 1 MB |
| Other | `kexec-tools` `gnupg` | 13 MB |

### C. Only on request (useful, but large, niche or services)

`git` (47 MB), `samba` (22 MB), `restic` (41 MB), `borg`, `duplicity`, `gparted` (GUI that writes partitions), `pcmanfm`, `mpv`, `stress-ng` (15 MB), `ipmitool`, iSCSI (`open-iscsi` `tgt` `targetcli-fb`), network services (`dnsmasq` `hostapd` `radvd` `avahi`), `netsniff-ng`, `iptraf-ng`, `mosh`, `irssi`, accessibility (`brltty` `espeakup`, deferred since phase 1), `zsh`.

### D. Excluded (with reason)

| Packages | Reason |
|---|---|
| `srm` `wipe` | destructive by nature (`nwipe` joined by D24) |
| `udisks2` `udiskie` `gvfs` | automounting (integrity policy) |
| `fwupd` | writes device firmware; not a default in a forensic ISO; requires `udisks2` (checked for D25) |
| `gcc` (234 MB), `edk2-ovmf` (154 MB), `qemu` | size / out of scope |
| `debootstrap` `rinse` `mmdebstrap` | install Debian/RPM systems |
| `open-vm-tools` `qemu-ga` | guest agents, not for a rescue system |
| `cups` `system-config-printer` `plymouth` `ollama` `brave-bin` `octoxbps` `transmission-qt` `uget` `yt-dlp` `geary` `cmus` `d77run` | no role in the PoC (d77void desktop extras) |
| `fluxbox` `xterm` `x11vnc` | Grml's own X session; d77orphaned has pwm and wasp |

Not in Void under any name found: `partimage`, `clonezilla`, `hping3`, `autopsy`, `recoverjpeg`, `myrescue`, `disktype`, `dump`, `udpcast`, `ipxe` (as a package), and others in the 46 above. None is essential; porting is not proposed (AGENTS.md: priority 4, exclude/defer).

**Estimate:** A ≈ 60 MB, B ≈ 70 MB of the packages themselves, plus dependencies; to be measured by a build.

**Decided (D18, 2026-11-08):** A and B approved by the user, `mc` kept although `ranger` is in. Removed from B on review: `dmraid` (runit's `03-filesystems.sh` runs `dmraid -i -ay` at boot whenever it is installed) and `bcache-tools` (its udev rule and dracut module register bcache devices on their own). Added for the pwm session: `d77-slock`, `xautolock`, `xcompmgr` (D19). Measured: ISO 2.06 GB (from 1.9 GB with D17 only, 1.7 GB before).

## Decided for D25 (2026-11-09)

Checked read-only against `current`, `current/nonfree` and the d77void repository, x86_64; sizes installed, with new dependencies, against the ISO of 2026-11-08.

| Package | Size | Decision |
|---|---|---|
| `grub` + `grub-x86_64-efi` | 29 MB + 4 MB | image: boot repair |
| `restic` / `borg` | 41 MB / 11 MB (10 new `python3-*`) | image |
| `exiftool` / `yara` | 23 MB / 1 MB | image |
| `gparted` | 16 MB (6 new, gtkmm) | image |
| `testssl.sh` / `ssh-audit` | 4 MB / 1 MB | image |
| `flashrom` / `i2c-tools` | 3 MB / 0.3 MB | image |
| `rclone` | 106 MB | documented; installed when needed |
| `wireshark` + `termshark` | 158 MB + 17 MB | documented; installed when needed |
| `john` | 51 MB | documented; installed when needed |
| `clamav` | 182 MB + signatures | documented; installed when needed |
| `fwupd` | 24 MB, pulls `udisks2` | rejected |
| `bulk_extractor`, `clonezilla` | not in Void | rejected; no ports |

New packages in the image: 31, of which 0 are ports. The five left out were installed in a live VM and took about 770 MB of RAM together, signatures included.
