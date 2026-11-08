# d77orphaned — Proof of Concept

> **Status: PROTOTYPE (phase 5).** Gate approved on 2026-11-07 (`docs/APPROVAL_GATE.md`). Tested in QEMU in three rounds and, since 2026-11-08, used on real hardware by the user; results in `docs/TEST_REPORT.md`, nothing beyond what is listed there has been tested. User documentation: <https://d77void.github.io/orphaned-docs/> (also inside the ISO: `d77-docs`).

## Download

Prototype. ISO, hash and source list: [ISO-x86_64 on SourceForge](https://sourceforge.net/projects/d77void/files/ISO-x86_64/); how to check it and write it to a USB stick: [Download](https://d77void.github.io/orphaned-docs/getting-started/download.html).

## Vision

d77orphaned is a **live recovery, diagnostics and analysis system** based on **Void Linux**, with a small, justified selection of security/pentesting tools for authorized use. Conceptual reference: **more Grml than Kali**. It is not an independent distribution, a general-purpose d77void variant, or a replacement for Kali/Parrot/BlackArch.

## Repository identity and boundaries

- **New standalone Git repository `d77void/d77orphaned`**, in the same organization as `d77-immutable` and the other projects. It is not a subdirectory, branch or development workspace of the `d77void` repository.
- **All d77orphaned experimentation and commits live exclusively in its own repository.** Sibling repositories are external dependencies, not places to work.
- Auditing `d77void`, `mkd77.sh` and the binary repository is **read-only**. If reusing code is useful, propose a local copy/adaptation in this repository, respecting provenance and license; never edit the original.
- No agent may create or publish the remote repository without authorization; initially it may prepare the local Git directory and documentation, if asked.

## Architecture decisions already made

- Void Linux base and XBPS package management; **do not** create a package manager, init system or binary repository of our own.
- A single ISO initially; console/TTY fully usable without a graphical session.
- Two optional environments on the same ISO: **pwm (X11)** and **wasp (Wayland) + Utumno**. Utumno is Wayland-only and must not be proposed for pwm/X11.
- Reuse **existing** shells, compositors, tools and packages from the d77 ecosystem, without changing the general-purpose projects to serve this ISO.
- Existing launcher to open applications. **No** `forensics.qml` dashboard, new qsd77 integrations or special panels in the first proof of concept.
- **Optional** persistence of data and selected settings on a separate LUKS2 partition (`d77-persist`, D22); no persistent overlay of `/`, no full package persistence.
- No destructive operation on target disks without explicit choice and confirmation; reading is not automatically the same as forensic preservation.

## Mandatory work order

1. Read `AGENTS.md`, `docs/RESEARCH_PLAN.md`, `docs/PACKAGE_INVENTORY.md` and `docs/INTEGRATION_CONTRACT.md`.
2. Inventory the **actual** state of the d77void repository, its own packages and `mkd77.sh` — read-only.
3. Research Void packages and recovery/security tools with reproducible evidence.
4. Classify the packages, estimate maintenance effort and **present decisions to the user**.
5. Only after approval, prepare an implementation plan and a minimal prototype.

**Gate:** during the research phase, no implementation or changes to build scripts. **In no phase is there implicit authorization to edit sibling repositories**, including `d77void` and `d77-immutable`. The original `mkd77.sh` is always read-only; future adaptations, if approved, live in `d77orphaned`.

## Initial scope

Data recovery, disk and filesystem diagnostics, boot/EFI inspection, emergency networking and a limited set of analysis and authorized security-testing tools. The final list depends on the research; names suggested in the documents are **candidates, not confirmed packages**.

## Out of scope for the PoC

A new independent distro, a custom kernel, a new graphical environment, a forensic QML interface, changes to Utumno/qsd77/pwm/wasp, a catalogue of hundreds of offensive tools, credential syncing, root persistence, destructive automation and duplicated package infrastructure.

## Success criterion

An image that boots on real hardware and in a VM, provides a useful console, offers **verified** tools, lets each graphical session be started in a controlled way, does not modify target disks by default and keeps working without a persistent partition. Do not promise untested capabilities.

## Code origin

This repository started as a **full clone of `d77void/d77void` at commit `c567d0cf`** (with history) and was then pruned for the PoC. `git diff c567d0cf` shows everything that was removed or changed. The builder (`mklive.sh`, `lib.sh`, `dracut/`, `grub/`, `isolinux/`) derives from void-mklive — BSD-2-Clause, see `COPYING`; the rest is MIT (`LICENSE`).

## Building

On a Void Linux x86_64 host, as root, from the repository root:

```sh
./mkorphaned.sh                                   # d77orphaned-live-x86_64-YYYYMMDD.iso
./mkorphaned.sh -- -k pt-latin1 -l pt_PT.UTF-8    # extra options for mklive.sh
```

By default it uses the d77void (SourceForge) and Void nonfree (`nmap`) repositories in addition to the official ones; `-n` drops them and `-r <repo>` adds one (repositories given first take precedence). Host tools: xbps, `mkfs.vfat`, `losetup`, `unshare`, and `mtools` if the host kernel cannot mount vfat.

What a build produces and needs:

- `d77orphaned-live-x86_64-YYYYMMDD.iso` and `d77orphaned-live-x86_64-YYYYMMDD.SOURCES.txt` in the repository root. The SOURCES file (also inside the image, `/usr/share/doc/d77orphaned/SOURCES.txt`) lists every package with its license and source, and carries the written offer for the GPL software; publish it with the ISO (`docs/APPROVAL_GATE.md` §9).
- The user documentation goes into the image (`/usr/share/doc/d77orphaned`, opened with `d77-docs`) when a checkout of [d77void/orphaned-docs](https://github.com/d77void/orphaned-docs) sits next to this repository (or `D77_DOCS_DIR` points to one) and `mdbook` is installed on the build host. Without them the build warns and goes on.
- The build runs in a private mount namespace with an empty `/boot`, because `mklive.sh` would otherwise regenerate the **host's** `/boot/grub/grub.cfg` (memtest86+'s post-install script); it fails if the host's `grub.cfg` changes anyway (`docs/TEST_REPORT.md`, defect 5).

### ⚠️ IMPORTANT — Offline documentation

The d77orphaned ISO includes a complete offline mdBook manual, but **the documentation is not bundled in this repository**.

To include it in the ISO, **both requirements must be met before building**:

1. Install `mdBook` on the build host.
2. Clone [d77void/orphaned-docs](https://github.com/d77void/orphaned-docs) alongside the `d77orphaned` repository.

```sh
sudo xbps-install -S mdBook
git clone https://github.com/d77void/orphaned-docs.git ../orphaned-docs
sudo ./mkorphaned.sh
```

If the documentation is stored elsewhere, set `D77_DOCS_DIR` to its location.

**WARNING:** If either requirement is missing, the build will continue, but the resulting ISO **will not contain the offline documentation**.

Check the build output for the documentation inclusion confirmation before distributing the ISO.

## Testing

`tests/qemu-harness.py` (host, QEMU; KVM optional) runs the test plan scenarios; `tests/check-tools.sh` and `tests/integrity-*.sh` run inside the VM. The integrity tests create and destroy **disposable** disks in the working directory; never run `integrity-prepare.sh` on real hardware.
