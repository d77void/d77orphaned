# DESCARTAVEL — disposable handoff for CLI testing

> **Disposable.** Handoff from a cloud session (no KVM, no GPU) to a Claude Code
> CLI session on the user's own Void machine. Delete this file once the items
> below are closed or moved into `docs/TEST_REPORT.md`. It is not
> documentation.

## Read first

- `AGENTS.md` — rules (no edits to sibling repos, disposable environments only for installs, communicate tersely, never claim success without a test).
- `docs/TEST_REPORT.md` — what passed, what failed, what was fixed.
- `docs/BASELINE_AUDIT.md` §9 — user decisions D1–D13.

## Ground rules on this machine

- Build and VM tests are fine here. **No destructive tests on the user's personal machines.** The integrity tests (`tests/integrity-*.sh`) only ever run inside QEMU against disposable images in the working directory — never against real disks.
- The Acer is the user's main development machine: VM tests yes, nothing that writes to its disks outside the work dir.
- Nothing is pushed or published without the user saying so.

## State at handoff (2026-11-07, `main` @ 299671a6)

- ISO builds (`./mkorphaned.sh`, ~1.6 GiB). Tested in QEMU/TCG: T1–T4, T7–T11 pass; T6 passes with one unexplained failure; **T5 (`nomodeset`) fails**; T12 (real hardware) not done.
- Fixed during testing: LVM auto-activation by runit `vgchange -a ay` (postsetup.sh), pwm needing `xmodmap`, wasp needing `WLR_RENDERER_ALLOW_SOFTWARE=1` without a GPU, unchecked EFI image write in `mklive.sh`.

## Setup

```sh
# as root, from the repo root
xbps-install -S qemu qemu-system-amd64 edk2-ovmf xorriso ImageMagick python3 mtools
# Reuse the package cache from the user's d77void builds instead of
# downloading again (ask the user for the d77void checkout path). Copying keeps
# the d77void cache untouched; pointing -c/-H at it directly also works but
# adds the extra packages to it.
cp -a /path/to/d77void/xbps-cachedir-x86_64 ./xbps-cachedir-x86_64

# The user also has the d77 packages compiled locally with xbps-src (ask for the
# void-packages checkout path; binaries are in hostdir/binpkgs). Prefer that
# local repository over SourceForge: -n drops the default extra repositories
# (d77void SourceForge + Void nonfree), so add the local one and nonfree back.
# Repositories given first take precedence in XBPS.
./mkorphaned.sh -n \
  -r /path/to/void-packages/hostdir/binpkgs \
  -r https://repo-default.voidlinux.org/current/nonfree \
  -- -k pt-latin1                       # extra mklive.sh options, if wanted
# Check the build log ("install x86_64 <repo>" lines) that pwm, wasp, utumno,
# qsd77, dwl, d77-st, scenefx0.5 and kantele came from the local repository.
# If any d77 package is missing locally, re-run without -n (SourceForge fills
# the gap) or build it with xbps-src first.
export OVMF_CODE=/usr/share/edk2/x64/OVMF_CODE.4m.fd
export OVMF_VARS=/usr/share/edk2/x64/OVMF_VARS.4m.fd
ISO=$PWD/d77orphaned-live-x86_64-$(date -u +%Y%m%d).iso
```

`tests/qemu-harness.py` uses KVM automatically when `/dev/kvm` is usable (`D77_NO_KVM=1` to disable). Scenarios: `bios-menu`, `uefi-menu`, `serial`, `sessions`, `integrity` — see its docstring. The VM is driven over a serial console; screenshots go to `--workdir` as PNG. Log in on the serial console as `root` / `voidlinux`.

## Open items, in order

### 1. T5 — `nomodeset` gives a black screen (FAIL)

Observed in QEMU (std VGA, no KVM): Xorg loads `modesetting`, `fbdev`, `vesa`; pwm is not running; screen black in 720×400 text mode. Not investigated yet.

Hypotheses (unverified):
- without KMS there is no `/dev/dri`; the autologin X session fails, then greetd falls back to the greeter, which runs **dwl** (wlroots) and cannot start without DRM → greetd keeps respawning it;
- or Xorg picks a driver that fails on this display.

How to look: boot with `nomodeset d77.nogui`, switch greetd's log to a file, start it, wait, inspect:

```sh
python3 tests/qemu-harness.py serial --iso "$ISO" --workdir vmtest --wait 5 \
  --extra "nomodeset d77.nogui" --cmd "\
mkdir -p /var/log/greetd; printf '#!/bin/sh\nexec svlogd -tt /var/log/greetd\n' > /etc/sv/greetd/log/run; \
rm -f /etc/sv/greetd/down; sv restart greetd/log; sv up greetd; sleep 120; \
ls -la /dev/dri /dev/fb0; ps -eo pid,user,args | grep -E 'pwm|Xorg|xinit|dwl|qs|greetd' | grep -v grep; \
tail -n 30 /var/log/greetd/current; grep -E '\(EE\)|Fatal|no screens' /var/log/Xorg.0.log"
```

Likely fix directions (decide with the user): make the `nomodeset` entry console-only, or have `dracut/vmklive/nomodeset.sh` keep greetd down like it already does for lightdm/sddm/gdm, and start X by hand (`startx /usr/bin/env dbus-launch pwm`). Also test on real hardware — QEMU's std VGA under `nomodeset` is a special case.

### 2. T6 — wasp login from the greeter once ended in pwm (intermittent)

2 of 3 attempts fine; one ended with the pwm bar on screen, no wasp process and no `~/.local/state/wasp/wasp.log`. Cause unknown. Re-run with greetd logging to a file (same `svlogd` trick as above) and the `sessions` scenario until it reproduces:

```sh
python3 tests/qemu-harness.py sessions --iso "$ISO" --workdir vmtest --wait 120 --downs 1
```

Also fix the scenario's Kantele-on-Wayland step: it hardcodes `WAYLAND_DISPLAY=wayland-0` and `XDG_RUNTIME_DIR=/run/user/1000`, which did not exist; read them from the running `wasp` process' environment instead (`/proc/<pid>/environ`).

### 3. T3 — GRUB menu not visually confirmed

UEFI boot reaches pwm (so the EFI loader works), but the menu screenshot at 60 s was black. With KVM, retake it earlier (`uefi-menu` scenario; adjust the 60 s sleep).

### 4. T12 — real hardware (user)

T480s (Libreboot): boot, pwm, wasp + Utumno with a real GPU, Wi-Fi via `wpa_supplicant`, Kantele keyboard layout, `nomodeset` and "console only" entries. **No disks with data the user cares about attached during these tests.**

### 5. Cosmetic / known

- wasp with software rendering: greeter leftovers in the background, black block left of Utumno's bar.
- Utumno's network widget shows "offline" (no NetworkManager); DHCP works.
- ISO is 1.6 GiB vs the 0.9–1.1 GiB estimate.

## When done

Update `docs/TEST_REPORT.md` with results (date, commit, KVM/GPU details), commit, ask the user before pushing, and delete this file.
