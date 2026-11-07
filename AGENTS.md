# AGENTS.md — Rules for 1100, 1200 and other agents

## Mission

Plan and, **only after authorization**, implement the d77orphaned PoC: a Void Linux live system aimed at recovery, diagnostics, careful forensic analysis and a limited selection of authorized pentesting.

## Rule zero: PLAN FIRST

The initial task is to **research and document**. Do not write build code, do not install packages on the host, do not modify the d77void repository, do not port software and do not run `mkd77.sh` until there is a reviewed inventory and an explicit decision from the user. If execution is requested later, keep that authorization separate from any authorization to change shared projects.

**Exception (phase 2):** from phase 2 on, installing packages is allowed **only in a disposable environment** (a VM, chroot or container created for the purpose and destroyed afterwards) to check dependencies and behaviour. Never on the host, never on the user's personal machines and never in sibling repositories.

## Before proposing changes

1. Locate and read the relevant files; **do not assume** the structure, paths, syntax or semantics of `mkd77.sh`.
2. Identify the branch, Git state, local changes, remotes, submodules and the origin of the d77 packages. Do not modify files with unrelated changes.
3. Distinguish: **observed**, **verified by command**, **inferred**, **proposed** and **unknown**.
4. Do not invent Void package availability, dependencies, versions, architecture compatibility or real-world behaviour.
5. Record verification commands, date, architecture, repository and results in `docs/PACKAGE_INVENTORY.md` or an equivalent report.

## Package policy

Priority: (1) official, working Void package; (2) existing, usable binary from the d77void repository; (3) our own build/packaging only when essential and sustainable; (4) exclude/defer. **Never** turn a wish list into an install list without validation.

Classify porting effort per package: trivial, low, medium, high, infeasible/not advised. Count new dependencies and ongoing maintenance, not just the time to compile once. Thresholds for new essential ports:

- **≥ 5:** stop and present a scope review to the user before continuing.
- **≈ 30:** the design is infeasible; propose a drastic scope reduction.

In both cases, **do not start the ports**. These numbers are warning signs, not a work budget.

## Project boundaries

- The source repository **`d77void/d77orphaned` is new and independent**, a sibling of `d77-immutable` in the `d77void` GitHub organization. Never work inside `d77void`, on a branch of that project, or inside `d77-immutable`.
- The d77void **binary** repository is shared/reused, not copied or reorganized for the PoC's convenience.
- **Never modify the original `mkd77.sh` or any files in sibling repositories as part of this project.** Investigate read-only. If needed, propose a local copy/adaptation or a builder of our own in `d77orphaned`, subject to approval, license and traceable origin.
- Do not change global Utumno, qsd77, pwm or wasp configuration to accommodate a need exclusive to d77orphaned.
- Prefer overlays and configuration **local to d77orphaned**; avoid hardcoding and circular dependencies.
- Do not publish packages to the d77void repository without a separate review of security, licenses, maintenance and impact on current users.

## Security and integrity

- Do not mount target disks read-write automatically; any write requires a conscious action and confirmation.
- Distinguish `mount -o ro` from real forensic preservation guarantees (journaling, replay, swap, automount, device changes, chain of custody). Concrete risks to handle and test:
  - automatic MD RAID assembly and LVM activation by udev rules, including **after** the initramfs;
  - automatic unlocking of LUKS volumes by dracut (`rd.luks=0`, `rd.md=0`, `rd.lvm=0`, `rd.dm=0` as a requirement to test);
  - udisks2/udiskie/gvfs mounting disks in graphical sessions (do not include them in autostart);
  - ext4 and XFS replay the journal even with `ro`: use `noload` (ext4) / `norecovery` (XFS) and `blockdev --setro` before mounting;
  - automatic activation of swap found on target disks.
- Pentesting tools are for authorized environments only; do not include covert persistence, credential harvesting or automated exploitation as default behaviour.
- Persistent data is optional and independent from the image; LUKS2 recommended; never unlock secrets automatically.
- USB-stick installation scripts must not reformat devices without unambiguous confirmation of the device, partitions and data loss.

## First-phase deliverables

- Verified inventory with sources/commands and gaps.
- Matrix of essential functions and alternatives.
- Audit of `mkd77.sh` and of what can be **reused without modification**.
- Estimate of effort, footprint and risks, including GUI and architecture dependencies.
- **Minimal** proposed list for the PoC, deferred list and rejected list.
- Decision questions for the user, including any blockers.

## How to communicate

Be direct, technical and concise. Do not claim success without testing. Do not do extra "while I'm at it" work. Do not create unnecessary auxiliary files. When an idea comes up, ask: **what problem does it solve in the PoC?** If there is no concrete answer, record it as optional future work.
