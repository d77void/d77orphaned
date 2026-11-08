# BASELINE_AUDIT — Phase 0 (read-only)

- **Date:** 2026-11-07
- **Audited repository:** `https://github.com/d77void/d77void`, branch `main`, commit `c567d0cf` (2026-11-05), version `0.26`. Clean clone, no local changes. 1 submodule (`common/.bash_it`, Bash-it), not initialized.
- **Indexes consulted (downloaded and read, nothing installed):**
  - Void `current/x86_64-repodata`, `current/nonfree/x86_64-repodata`, and the `musl` equivalents
  - d77void `sourceforge.net/projects/d77void/files/d77void-repo/x86_64-repodata` and `d77void-musl/x86_64-musl-repodata`
- **d77 packages opened for inspection (ELF/files):** `qsd77-1.3.3_1`, `utumno-0.2.0_1`, `wasp-0.10.1_1`, `pwm-0.6.7_1` (x86_64).
- **Audit environment:** Ubuntu 24.04 host (not Void). **Nothing was built, installed or booted.** No d77void file was modified.

Legend: **[OBS]** observed in the code · **[VER]** verified by command · **[INF]** inferred · **[PROP]** proposed · **[UNK]** unknown

---

## 1. What `mkd77.sh` is

- [OBS] The repository is a **fork of `void-mklive`** (README). Licenses: `COPYING` BSD-2 (void-mklive, Juan RP / Dave Elusive) and `LICENSE` MIT (Daniel Azevedo, 2025).
- [OBS] `mkd77.sh` is a **wrapper around `mklive.sh`**, adapted from `mkiso.sh`. It does not build the ISO itself: it assembles `PKGS`, `SERVICES` and a temporary `INCLUDEDIR`, and finally calls:
  ```
  ./mklive.sh -a "$TARGET_ARCH" -o "$IMG" -p "$PKGS" -S "$SERVICES" -I "$INCLUDEDIR" [-v kernel] [-r repo…] "$@"
  ```
- [OBS] Entry points: `d77` → `mkd77.sh`; `d77nc` → `--nc`; `musl-d77` → `--musl`; `musl-d77nc` → `--musl --nc`.
- [OBS] CLI: `-a arch`, `-b variant` (repeatable), `-d date`, `-t arch-date-variant`, `-r repo`, `--musl`, `--nc`, `-h`, `-V`; everything after `--` goes to `mklive.sh`.
- [OBS] **Variants are hardcoded** in a `case $variant in … esac` (~30 entries: base, pwm, wasp, qsd77, spitfire, hyprland…). **There is no way to define a new variant without editing `mkd77.sh`.** → d77orphaned cannot use `mkd77.sh` without modifying it.
- [OBS] Each variant combines shared lists (`D77_CORE`, `XORG_PKGS`, `WAYLAND_PKGS`, `$CALAMARES`) and `include_*` functions that copy `common/` and `<variant>/skel` into `INCLUDEDIR/etc/skel`.
- [OBS] The installer (`d77void-installer`, from `installer.sh`) is only included with `--nc` on x86_64/i686; otherwise it is a stub.

### `mklive.sh` (the actual builder)
- [OBS] Useful options: `-p` packages, `-S` services, `-I` include directory (repeatable), `-C` kernel cmdline, `-T` title, `-k` keymap, `-l` locale, `-x` post-setup script, `-c/-H` caches, `-s/-i` compression, `-v` kernel.
- [OBS] Must be run **from the repository root** (`. ./lib.sh`, `keys/`, `dracut/`, `grub/`, `isolinux/` by relative path).
- [OBS] Writes `xbps-cachedir-*` and `mklive-build.*` into the current directory, unless `-c`/`-H` and the `ROOTDIR` variable are used.
- [OBS] **Always** appends the official Void repositories (`current`, `current/musl`, `current/aarch64`) to the given `-r`.
- [OBS] Hybrid ISO (isolinux BIOS + GRUB EFI in an appended GPT partition), xz squashfs, **overlayfs** overlay, fixed label `VOID_LIVE`. On x86 it always includes `syslinux grub-i386-efi grub-x86_64-efi memtest86+` → **memtest86+ is already in the boot menu**.
- [OBS] Cmdline of every GRUB/isolinux entry: `root=live:CDLABEL=VOID_LIVE ro … rd.luks=0 rd.md=0 rd.dm=0 …`. **The initramfs already does not auto-mount LUKS, MD or DM.** See §5 for what happens after the pivot.
- [OBS] Entries: normal, RAM (`rd.live.ram`), no graphics (`nomodeset`), and three with speech synthesis.

### `vmklive` dracut module (live behaviour)
- [OBS] `adduser.sh`:
  - creates user `anon` in groups `audio,video,wheel`;
  - **sets the password `voidlinux` for root and anon**;
  - grants `NOPASSWD: ALL` in sudo;
  - writes a polkit rule that **authorizes everything for group `wheel` without asking**.
- [OBS] Inherited from void-mklive, but relevant: `mkd77.sh` enables **`sshd` in every variant** (`SERVICES="sshd chronyd"`). See §5.

## 2. d77void binary repository

- [VER] x86_64: **74 packages**; x86_64-musl: **38 packages**. Signed with RSA-4096, `signature-by: Daniel Azevedo <daniazevedo77@posteo.net>`.
- [VER] The public key in `index-meta.plist` is **byte-for-byte identical** to `keys/2b:d7:d1:cf:67:ab:53:3a:56:03:f5:f0:c2:de:a6:1a.plist` in the repository. The other two keys in `keys/` are Void Linux's. **There are no private keys in the repository.**
- [OBS] URL documented in INSTALL.md: `https://sourceforge.net/projects/d77void/files/d77void-repo` (and `d77void-musl`).
- [VER] Relevant glibc vs musl differences:

| Package | x86_64 | x86_64-musl |
|---|---|---|
| `pwm` | 0.6.7_1 | 0.6.7_1 |
| `wasp` | 0.10.1_1 | **MISSING** |
| `scenefx0.5` (wasp dependency) | 0.5_1 | **MISSING** |
| `utumno` | 0.2.0_1 | 0.2.0_1 |
| `qsd77` | 1.3.3_1 | 1.3.3_1 |
| `fresh-editor`, `joshuto`, `ollama` | present | missing |

→ **[VER] The wasp + Utumno environment currently exists only on x86_64 glibc.** musl would require porting `wasp` and `scenefx0.5`.

## 3. Graphical components — what they actually need

### pwm (X11)
- [VER] Rust binary; `NEEDED`: libX11, libXft, fontconfig, libgcc_s, libc. Depends on `dmenu`, `d77-st`, `wireless_tools`, `font-JetBrainsMono`.
- [VER] The package ships `/etc/xdg/pwm/startup.sh`, which starts **`udiskie -a` (automounting)**, plus conky, feh, dunst, xcompmgr, xautolock+slock, redshift and sxhkd.
- [OBS] `config.toml.example` documents `startup_script = "/etc/xdg/pwm/startup.sh"`. **[INF]** This can be overridden in the user's config without touching the package. Still to be tested.
- [OBS] The session (`pwm.desktop`) is `dbus-launch pwm`. In the d77void variant, login is handled by SDDM.

### wasp + Utumno (Wayland)
- [VER] `wasp`: C binary (dwl) linked against libwlroots-0.20, libscenefx-0.5, lua5.4, fcft, libinput and xkbcommon. `wasp-session` runs `dbus-run-session -- sh -c 'wasp-statusbar | wasp'` and logs to `~/.local/state/wasp/`.
- [VER] **`utumno` is QML only** (`/usr/share/quickshell/utumno/…`) and runs under **Quickshell** (`qs -c utumno`). The package **does not declare** `quickshell` or `qsd77` as dependencies; it only declares power-profiles-daemon, alsa-utils, alsa-tools, brightnessctl, wireless_tools and matugen.
- [VER] **`qsd77` is a Go CLI**, linked only to libc/libresolv, that sends IPC calls to Quickshell (`qsd77 -c utumno launcher`).
- [OBS] In the d77void `wasp` variant, `quickshell` only gets in by accident, through `include_greetd` (`dwl greetd quickshell`). **→ d77orphaned must list `quickshell` and `qsd77` explicitly.**
- [OBS] The wasp skel (`wasp/skel/.config/wasp/config.lua`) autostarts:
  - awww-daemon, Utumno's wallpaper script, dunst;
  - **`udiskie -a`**;
  - pipewire, `qsd77 run -c utumno`, swayidle, polkit-mate, xdg-user-dirs and `~/.auto.sh`.
- [OBS] `~/.auto.sh` (from `common/`) automatically opens `calamares` (via `sudo -E`) if installed, then `d77-welcome`.
- [VER] **Utumno makes network requests on its own**: `modules/Weather.qml` runs `curl https://wttr.in/…`. There is no configuration option to turn it off (`config/` only has `Colors.qml`). **[INF]** This exposes the public IP and approximate geolocation to an external service every time the graphical session starts. Relevant for an incident-response ISO.
- [User, 2026-11-07] Without network, Utumno works normally: the widget shows an unavailable/no-network indication. This matches the code (`"weather unavailable"`). The failure is benign; the open question is only the outgoing request **when there is a network**. [PROP] Block `wttr.in` in the d77orphaned overlay (e.g. `0.0.0.0 wttr.in` in `/etc/hosts`), without touching Utumno.
- [OBS] Utumno also has the Ollama chat popup. The d77void variant includes `ollama` (72 MiB) with the service enabled. **[UNK]** How Utumno behaves without Ollama installed.
- [OBS] Utumno's README says it was tested with niri and Hyprland. d77void uses it with wasp and spitfire; the workspaces module has Hyprland and Sway versions. **[UNK]** Which widgets work on wasp.

### Launcher
- [OBS] pwm: `rofi` (via sxhkd/skel) and `dmenu` (pwm dependency). wasp: `wmenu-run` (`wasp.menu`), Utumno's launcher (`super+space`) and `d77run` (`super+r`).
- [VER] `d77run` is GTK4: it adds 182 packages / 369 MiB on top of `base-system`. **[PROP]** Not needed in the PoC: `wmenu` and `dmenu` are enough.

## 4. What can be reused **without modification**

| Item | Reuse | Notes |
|---|---|---|
| `mklive.sh`, `lib.sh`, `dracut/`, `grub/`, `isolinux/`, `keys/` | **Yes**, if called as they are from a pinned checkout (e.g. a read-only submodule at a fixed commit), with `-I <d77orphaned overlay>`, `-c/-H` and `ROOTDIR` pointing outside the checkout | Requires no edits. `mklive.sh` accepts multiple `-I`, `-x` (post-setup) and `-C`. |
| `mkd77.sh` | **No** | Hardcoded variants; the `include_*` logic brings udiskie, permissive polkit, Calamares, plymouth, etc. |
| `common/` and pwm/wasp skels | **Partial / not advised** | They contain automounting and `.auto.sh`. Better to have our own overlay, inspired by them. |
| `common/os-release`, branding | No | d77void identity; d77orphaned should have its own. |
| d77void binary repository | **Yes**, as an extra `-r` | pwm, wasp, utumno, qsd77 and d77-st; signature verified. |

**[PROP] Build strategy:** a wrapper of our own in `d77orphaned` (package manifest + overlay + cmdline) that calls d77void's `mklive.sh` at a **pinned commit**, without copying. The alternative is to copy `mklive.sh` and its files (BSD-2, keep `COPYING` and the origin), for full independence from future d77void changes. To be decided. *(Decided in D3, §9.)*

## 5. Inherited integrity and security risks

| Risk | Origin | Status |
|---|---|---|
| Automounting of target disks | `udiskie -a` in pwm's startup (in the package) and in the wasp skel; polkit rule `50-udisks.rules` grants mount/unlock without authentication to group `storage`; `adduser.sh` grants everything to `wheel` | [OBS] **Blocking**: the d77orphaned overlay must not autostart udiskie/gvfs/udisks2. |
| `sshd` enabled with a known password (`anon:voidlinux`) | `mkd77.sh` (`SERVICES="sshd …"`) + `adduser.sh` | [OBS] On a compromised network this is an open door. [PROP] Do not enable sshd by default in the PoC. |
| Automatic RAID/LVM assembly **after** the initramfs | `mdadm`/`lvm2` udev rules in the real system; `rd.md=0 rd.dm=0` only cover the initramfs | [UNK] Test in a VM with test RAID/LVM. Options to evaluate: `rd.md=0`, `rd.lvm=0`, `lvm.conf` with `event_activation=0`/`auto_activation_volume_list = []`, `/etc/mdadm.conf` with `AUTO -all`. *(Tested in phase 5: see `TEST_REPORT.md`, T8.)* |
| Activation of swap found on disks | Void runit `core-services` (fstab/swap) | [INF] The live fstab must not list swap. [UNK] To confirm. |
| Journal replay when mounting `ro` | ext4/XFS kernel behaviour | Use `-o ro,noload` (ext4) / `ro,norecovery` (XFS); for forensic work, `blockdev --setro` before mounting. |
| Automatic network request (wttr.in) | Utumno `Weather.qml` | [VER] Cannot be turned off by configuration; changing Utumno is out of scope. User decision. |
| Calamares opening automatically | `.auto.sh` | Not applicable if Calamares is not included and `.auto.sh` is not copied. |
| Fixed `VOID_LIVE` label | `mklive.sh` | [INF] Conflict if another Void live stick is plugged in. Minor. |

## 6. Footprint estimate (installed, uncompressed)

[VER] Dependency closure computed from the `run_depends` of the x86_64 indexes (the method does not follow `shlib-requires` or complex virtual packages; treat as an **estimate**):

| Set | Packages | Installed |
|---|---|---|
| `base-system` (includes kernel 6.18 and linux-firmware) | 136 | 1118 MiB |
| Proposed console core (inventory §core) | 249 | 1465 MiB |
| + optional | 299 | 1805 MiB |
| Core + pwm | 373 | 2090 MiB |
| Core + pwm + wasp/Utumno | 479 | 2371 MiB |
| Everything (core + optional + pwm + wasp) | 512 | 2660 MiB |

[INF] With xz squashfs, the ISO should be around **≈0.9–1.2 GiB**. Not measured. The largest consumer is `linux-firmware-network` (442 MiB), essential for Wi-Fi. *(Measured in phase 5: 1.6 GiB.)*

## 7. New ports

[VER] **Essential: 0.** All core capabilities exist in official Void or nonfree (nmap) for glibc and musl. The d77 graphical tools exist in the d77void repository for glibc. Missing without needing a port: `dc3dd` (alternative `dcfldd`), `bulk_extractor` (defer), `tshark` as a separate package (`wireshark` is the CLI package; `wireshark-qt` is the GUI).

## 8. Unknowns that require testing

1. BIOS/UEFI boot of the resulting ISO in a VM and on hardware (including the T480s with Libreboot).
2. Utumno on wasp: widgets, IPC, behaviour without Ollama.
3. Whether pwm accepts `startup_script` in the user's file as the documentation suggests.
4. udev automounting of MD/LVM in the live system.
5. Graphical session from a TTY without a display manager (`startx`/`wasp-session`), if SDDM/greetd were left out.
6. A stick-writing workflow that preserves a data partition (`mklive.sh` produces a hybrid ISO with an appended EFI partition; adding a partition after a `dd` is possible in theory but untested).

## Reproducing on a Void host

```sh
xbps-query -R -p pkgver,installed_size <package>
xbps-query -R -x <package>                      # direct dependencies
xbps-install -n -R -r /tmp/dryroot <list>       # closure and size, without installing
xbps-query --repository=https://sourceforge.net/projects/d77void/files/d77void-repo -Rs .
```

## 9. User decisions

| # | Date | Question | Decision |
|---|---|---|---|
| D1 | 2026-11-07 | Utumno's automatic request to `wttr.in` | **PoC:** block it in the d77orphaned overlay (`0.0.0.0 wttr.in` in `/etc/hosts`), without touching Utumno; seeing "weather unavailable" in the bar is accepted during the PoC. **If the project goes beyond the PoC:** an option in Utumno itself (e.g. `UTUMNO_WEATHER=0`, which hides the widget **and** stops the `Timer`), made as a separate change in the Utumno repository, with its own authorization and a new package version; d77orphaned then exports the variable and drops the `/etc/hosts` entry. |
| D2 | 2026-11-07 | Architecture | **x86_64 glibc.** wasp and scenefx0.5 exist only for glibc; new essential ports = 0. musl out of the PoC. |
| D3 | 2026-11-07 | Build strategy | **Revised by the user (2026-11-07):** `d77orphaned` starts as a **full clone of d77void @ `c567d0cf`, with history**, and is then pruned; `git diff c567d0cf` shows everything that diverged. No bash-it (no submodules or external dependencies in the build). Original wording: **copy into `d77orphaned`** `mklive.sh`, `lib.sh`, `dracut/`, `grub/`, `isolinux/` and `keys/` from d77void at commit `c567d0cf`; keep `COPYING` (BSD-2, void-mklive) and record the origin; the original stays untouched; the copy may be adapted **locally** (e.g. sshd off, own label), with every deviation documented. |
| D4 | 2026-11-07 | Graphical login | **greetd with the quickshell-d77 greeter** (`common/quickshell-d77/greeter` in d77void; Daniel, MIT), copied into the d77orphaned overlay. See the note below. |
| D5 | 2026-11-07 | Live login | **Autologin** via greetd's `[initial_session]`, as `anon`. Only applies on greetd's first start. Leaving that session brings up the greeter (`default_session`), where the other session can be chosen. |
| D6 | 2026-11-07 | Autologin session | **pwm (X11)**, as the most compatible with varied hardware. `initial_session` = `startx /usr/bin/env dbus-launch pwm` (the same the greeter uses for xsessions); wasp + Utumno available from the greeter after logging out. Requires `xinit`. [INF] Fits the `nomodeset` entry: X11 has fbdev/vesa via `xorg-video-drivers`. *(Second round: `nomodeset` works with vesa; the failures came from a pwm startup race, see `TEST_REPORT.md` T5 and D15–D16.)* |
| D7 | 2026-11-07 | Console-only boot | **Dedicated GRUB/isolinux entry** with a parameter (`d77.nogui`) that keeps greetd from starting; the TTYs are the only environment. Implemented as a pre-pivot hook in the copied `dracut/vmklive` (same pattern as `nomodeset.sh`): creates `etc/sv/greetd/down` in the new root. |
| D8 | 2026-11-07 | Network at boot | **`dhcpcd` enabled by default** (network ready, Grml-style). *(Superseded by D17: NetworkManager.)* |
| D9 | 2026-11-07 | Clock | **`chronyd` enabled by default** (automatic NTP sync). |
| D10 | 2026-11-07 | Phase 4 gate | **Approved** (`APPROVAL_GATE.md`): move to phase 5 — local repository, copied builder, manifest, overlay, build and VM tests. No publishing, no changes to other projects. dracut autoinstaller removed from the copied `mklive.sh`. |
| D11 | 2026-11-07 | Remote repository | **Authorized by the user ahead of schedule.** The user created `d77void/d77orphaned` (empty) and the local history was pushed to it. |
| D12 | 2026-11-07 | Kantele | **Added at the user's request** (settings GUI for pwm and wasp, incl. keyboard): +7 packages / ≈19 MiB. |
| D13 | 2026-11-07 | Language | **All repository documentation in English**, for universality. |
| D14 | 2026-11-07 | Build touched the host's `/boot/grub/grub.cfg` | **Guard in `mkorphaned.sh`:** build in a private mount namespace with a tmpfs over `/boot`, and fail if the host's `grub.cfg` changes. Root cause (memtest86+'s post-install run on the host) reproduced in a disposable VM first. See `TEST_REPORT.md`, defect 5. |
| D15 | 2026-11-07 | pwm startup race (`BadDrawable`) | **Fix it in pwm itself**, as a separate change with its own authorization and a new package version, rather than a restart wrapper in d77orphaned. Released as pwm 0.6.8 (approved by the user) and published to the d77void repositories. |
| D16 | 2026-11-07 | Greeter under `nomodeset` | **Text greeter:** with `nomodeset`, greetd's `default_session` becomes `agreety --cmd /bin/bash` (set in `dracut/vmklive/nomodeset.sh`); the pwm autologin stays. |
| D17 | 2026-11-08 | Desktop basics after the first real-hardware use | **NetworkManager** replaces `dhcpcd` at boot (nmtui/nmcli for Wi-Fi; `dhcpcd` and `wpa_supplicant` stay installed, not started). Browser: **Mullvad Browser** (d77void repo; chosen over Firefox/LibreWolf). Also `font-hack-ttf`, `feh`, `conky`, `papirus-icon-theme`, `ranger`. `xbps` was reported broken; it works (the user's network was not connected). |
| D18 | 2026-11-08 | Grml comparison | Groups **A** (desktop: `upower` for Utumno's battery, PipeWire sound, polkit agent, fonts, portals, theme, everyday basics) and **B** (Grml-like tools) of `PACKAGE_INVENTORY.md` approved; `mc` kept. `dmraid` and `bcache-tools` dropped on review (they activate volumes at boot). |
| D19 | 2026-11-08 | pwm session | `pwm-startup.sh` restored to what d77void's pwm does, minus udiskie, redshift and sxhkd: theme wallpaper with `feh`, own `~/.conkyrc1` (dark panel, bottom left, keys that exist here), `d77-slock` + `xautolock` (5 min), `xcompmgr`, touchpad tap, PipeWire and the polkit agent. Each program starts only once, because pwm re-runs the script on every theme change (Kantele sends SIGHUP). |
| D20 | 2026-11-08 | wasp wallpaper | Six `d77void_*` wallpapers in `~/Wallpaper` (d77void's `wall_macos*` left out: likely Apple's, not redistributable). `wasp-wallpaper.sh` sets the wallpaper **before** Utumno starts, so Utumno's backdrop hides; choosing with `super+y` works on real hardware. |
| D21 | 2026-11-08 | Documentation | User documentation in `d77void/orphaned-docs` (mdBook site + SourceForge wiki), with one page per tool in seven chapters. It is built into the ISO (`/usr/share/doc/d77orphaned`, `d77-docs` opens it in Mullvad Browser or `links`), readable without a network. |
| D22 | 2026-11-08 | Persistence | **Implemented with `d77-persist`:** data plus selected settings (Wi-Fi, pwm, wasp, Kantele, Utumno's theme and wallpaper, SSH keys), never the system or packages. **LUKS2 is mandatory for whoever creates it**; the system works as before without it. The partition takes the free space on the boot device only, and is opened by hand. **A new ISO means new data:** preserving it across ISO writes is not a requirement. |

**Note on D4 — what the greeter implies** [OBS/VER]:
- Startup: greetd → `/etc/greetd/greet-dwl.sh` → `dwl -s "qs -p <greeter>"`, as user `_greeter`, on VT 7. TTYs 1–6 stay free for the console.
- Packages: `greetd` (Void), `dwl` 0.9_1 (**d77void**, glibc only, depends on wlroots0.20), `quickshell` (Void), `xinit` (for X11 sessions). Closure of `greetd dwl quickshell xinit`: 161 packages / ≈298 MiB beyond `base-system`, largely shared with the wasp/Utumno set.
- Sessions: the greeter reads `/usr/share/wayland-sessions` and `/usr/share/xsessions`. It shows **wasp** (`wasp-session`) and **pwm** (`dbus-launch pwm`, launched as `startx /usr/bin/env dbus-launch pwm`), and skips `dwl.desktop` (the greeter's own compositor).
- [OBS] In d77void, greetd is only used by the Wayland variants (`include_greetd`); the X11 ones, including `pwm`, use SDDM. [User, 2026-11-07] Daily use of the greeter with X11 sessions on the laptop: works well. → X11 support confirmed in real use. *(Phase 5: greetd + pwm autologin works in the live ISO, see T6.)*
- Authentication goes through greetd's PAM. The live user (`anon`) has the password `voidlinux`, set by `adduser.sh`.
