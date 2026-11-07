# Integration contract with d77void, and persistence

## Mandatory Git topology

```text
d77void/                    # GitHub organization
├── d77void                  # existing repository; read-only for this work
├── d77-immutable            # sibling repository; read-only for this work
└── d77orphaned              # NEW standalone repository; the only place to work
```

The organization name and the sibling repositories are architectural context, not authorization to edit, create remotes or publish. Creating the remote requires explicit authorization.

## Main rule

**D77orphaned consumes the d77void ecosystem; it does not own it.** d77void's code, configuration, packages and current users take precedence over this PoC's convenience.

## Explicitly preserve

1. **d77void binary repository:** URL, structure, metadata, signatures/public keys, publishing policy, versions and compatibility. Do not duplicate or replace the repository; do not publish experimental builds without separate authorization.
2. **`mkd77.sh`:** locate and document before using. Preserve the CLI, arguments, defaults, paths, package selection, build flow, boot logic, overlays, hooks, signing and behaviour for the existing ISOs, **to the extent they actually exist**. Do not assume all of these capabilities exist.
3. **Graphical projects:** pwm/X11; wasp/Wayland with Utumno; the existing launcher and qsd77. Do not insert D77orphaned-specific code into shared components.
4. **Configs and branding:** do not replace d77void's global files. Exclusive branding and presets live in D77orphaned overlays/configuration.
5. **Security and secrets:** never copy private signing keys, tokens, passwords or personal data from previous builds.
6. **Regression:** if a shared change ever becomes essential, create a separate proposal, rollback plan and tests of the existing variants before approval.

## Preferred build strategy — to be verified

- Independent source repository with a package manifest, overlays and, if needed, a wrapper **of its own**.
- Reuse `void-mklive`/existing infrastructure **if** the audit confirms it fits.
- Consume the d77void repository as an additional source of compatible packages, keeping normal signatures and checks.
- **In-place changes to `mkd77.sh` or any sibling repository are forbidden.** After research and approval, reuse code by copying/adapting it **inside `d77orphaned`**, if licenses and dependencies allow, or write a builder of our own. Do not propose changes to d77void as a shortcut for the PoC.

## Data persistence (optional)

Goal: keep documentation, scripts, configuration, personal tools and possibly protected credentials **without** persisting the system, packages or `/`.

### Principles

- The ISO/live environment works without a data partition.
- Separate partition identified by a known, validated UUID/PARTUUID; a human-readable label only as a convenience.
- Prefer LUKS2 + a supported filesystem; explicit unlocking with no embedded credentials.
- Mounted at a stable mount point, e.g. `/mnt/d77-data`, initially by user action.
- Do not automatically bind `/home` or `/etc` to the persistent volume; import configs selectively only in a later phase.
- The system must not block boot because of a missing, encrypted, corrupted or incompatible volume.
- Rewriting/updating the live image must preserve the partition **only if the writing method guarantees it and this has been tested**. A `dd` of the ISO to the whole device can destroy the partition table and the data; do not promise safe updates without a dedicated workflow.
- A persistent volume **is not a backup**; advise external copies.

### Open questions

- How to prepare the stick (hybrid image, own installer, copying files to a boot partition, etc.).
- BIOS/UEFI compatibility and GPT/MBR layout.
- Ability to reserve/grow a data partition and update the image without wiping it.
- ext4 vs another filesystem, size, mount policy and unlocking tool.

These questions require testing; **do not design a final layout or formatting tool during the research phase**.

## Separation of responsibilities

| Location | May contain | Must not contain |
|---|---|---|
| Existing d77void | General-purpose packages and tools, already-validated infrastructure | D77orphaned-only logic imposed on the other remasters |
| D77orphaned | Manifest, overlay, branding, tests, documentation, future specific scripts | A permanent fork of the whole d77void infrastructure |
| User's persistent partition | Personal data, scripts and configs, optionally encrypted | A replacement of the live root or a mandatory boot assumption |

## Change gate

**All D77orphaned commits are made only in the `d77orphaned` repository.** If a need to change `d77void`, `d77-immutable` or another project ever arises, it is a separate request, outside the scope of this plan, subject to explicit authorization. Never make that change as a side effect of the PoC.
