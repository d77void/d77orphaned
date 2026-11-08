# Research plan — gate before building

> **Where the project is (2026-11-08):** phases 0–4 are done (inventory, matrix, triage, gate approved on 2026-11-07). Phase 5, the prototype, is in progress: three rounds of tests (`TEST_REPORT.md`), first use on real hardware by the user, and the package set extended after that use (`PACKAGE_INVENTORY.md`, "Review after the first real-hardware use"; decisions D17–D21 in `BASELINE_AUDIT.md` §9). Optional persistence (LUKS2) has not been started.

## Phase 0 — Reconnaissance (read-only)

- **First question:** x86_64 glibc or musl. It determines whether pwm, wasp and Utumno already exist as binaries in the d77void repository for that variant (phase 0 result: wasp and scenefx0.5 exist only for glibc — see `BASELINE_AUDIT.md` §2).
- Identify the distribution, target architecture(s), Void version, init system and intended live method.
- Inspect the d77void repository and locate the real `mkd77.sh`. Determine whether it is an ISO generator, a `void-mklive` wrapper, a remaster script or something else. **Do not assume.**
- Gather origin, licenses, dependencies and build status of pwm, wasp, Utumno, qsd77 and the other packaged components.
- Check that `void-mklive` (or the existing mechanism) works in the intended version, including BIOS/UEFI boot and USB-stick install/boot options.
- Identify how the d77void binary repositories are configured: priorities, signing/keys and compatibility. Never embed private keys.

**Output:** `docs/BASELINE_AUDIT.md` with facts, references, unknowns and risks. If the repositories are not available, ask for paths/URLs instead of inventing.

## Phase 1 — Capability matrix (no installing)

Research by **capability**, not popularity:

1. Disks: SMART/NVMe, identification, partition tables, cloning and file recovery.
2. Filesystems and volumes: ext4, XFS, Btrfs, FAT/exFAT, NTFS, LUKS, LVM, RAID; ZFS **only if feasible**, with a dedicated kernel/module analysis.
3. Boot: EFI, GRUB, chroot, initramfs, bootloader identification and controlled recovery.
4. Network: wired and wireless connectivity, DNS, SSH, secure transfer, capture and diagnostics.
5. Forensics: disk imaging, hashing, metadata, timeline/analysis **where justified**, preservation and logging.
6. Limited security/pentesting: network discovery and auditing, traffic capture/analysis and service checks on own/authorized systems.
7. Operations: terminal, editor, pager, man pages, required firmware and drivers, logs, compression, USB tools.
8. Graphics: minimal dependencies for pwm/X11 and wasp/Wayland + Utumno, existing terminal and launcher.

**Output:** `docs/PACKAGE_INVENTORY.md` filled in with evidence per candidate, including alternatives and redundancies.

## Phase 2 — Per-package verification

For each candidate:

- **Exact** name in XBPS or in the d77void repository; architecture and libc variant.
- Origin and verification command (`xbps-query`, `xbps-install -n` where applicable, repository index lookup, Void template, etc.).
- Dependencies, installed size and estimated ISO impact (distinguish estimates from measurements).
- Binary presence, runtime compatibility and a functional test in a VM/disposable environment where possible.
- Constraints: permissions, kernel, modules, firmware, network, GUI, privileges, licenses.
- Status: `NOT RESEARCHED`, `FOUND`, `TESTED`, `INCOMPATIBLE`, `TO PORT`, `DEFERRED`, `REJECTED`.

**Important:** listed in an index ≠ installed ≠ a working tool in the live system.

## Phase 3 — Triage and feasibility

Build three lists:

- **Core PoC**: essential, available and testable with low risk.
- **Optional/phase 2**: useful but not needed to demonstrate value.
- **Out**: redundant, heavy, risky, unmaintainable or without clear benefit.

Estimate the number of new ports of our own. For each proposed port, justify why no sufficient alternative exists and estimate the version/dependency maintenance. If the total reaches **5**, stop and review the scope with the user; if it approaches **30**, the design is infeasible — no "port everything".

## Phase 4 — Approval gate

Present to the user:

- Final minimal list, optional tools and exclusions.
- Actual availability and evidence that things work.
- Required ports and expected effort.
- Exactly what is reused from d77void and the changes that will **not** be made.
- Test plan and known risks.
- Open questions (for example x86_64 glibc vs musl, USB-stick writing method, ISO size, firmware, persistence).

**Do not move to implementation without explicit approval.**

## Phase 5 — Future implementation (not authorized by this document)

Only after the gate: console-first prototype; boot in a VM and on hardware; then graphical sessions; then the optional data partition. No `forensics.qml` in the PoC.

## Minimal future functional checks

- UEFI and BIOS boot under supported conditions; TTY fallback without GUI.
- Network and storage detected; core tools run without missing libraries.
- pwm on X11; wasp + Utumno on Wayland, without trying Utumno on X11.
- Target disk not mounted read-write automatically; no destructive commands run at boot.
- With test disks holding MD RAID, LVM, LUKS, swap and unclean ext4/XFS journals: nothing is assembled, activated, unlocked, mounted or journal-replayed without explicit action.
- Live system works without a data partition; optional LUKS2 unlockable only by user action.
- Repeat tests with the data stick absent, locked, damaged and with a mismatching UUID.
- Regression: the d77void repo, scripts and shared packages keep their original behaviour.
