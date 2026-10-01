# platforms/ — one file of platform facts per product family

`/orient-dt` holds what is true of any AlliedWare Plus product and any bench. What is true of
one **product family** lives here, as `platforms/<FAMILY>.md`, for example
[IE520.md](IE520.md):
- its hardware limits;
- its boot and bootloader behaviour;
- its build naming;
- CLI forms that differ from other AW+ products;
- measured quirks.

Every session whose DUT is that family reads the file (`/orient-dt` §2). It lives at the repo
root, not in the product's campaign directory, because that directory is archived into
`old test runs/` when the product's testing ends.

## Rules

- **Product facts only.** A fact about what a bench *is* (cabling, boot source today, which
  unit is master) goes in the box's generated `bench-state.md`, never here.
- **Date every claim and say where it was measured**: the box, the build, and the case that
  showed it. Mark *observed* vs *cause inferred*.
- **A counter-observation is added beside the claim, dated.** Never silently overwrite a claim.
- **The structure is free, but keep the IE520 file's shape** where it fits:
  1. boot, builds and the stack;
  2. the boot menu;
  3. the platform-facts table (Fact | Consequence);
  4. where the rest lives.

## Starting a new product's file

With no `platforms/<FAMILY>.md` for your DUT, `/orient-dt` says so in its brief, and the
session works from the general traps alone.
- **Create the file the first time you measure something that would have cost the next session
  time.** Use the header block of `IE520.md`, with its `verified:` date, and list what the
  product lacks or does differently.
- **Check the IE520 file for cousins.** Some of its rows are really AW+-wide, for example
  service-gated daemons or polarity on aggregators. If you confirm one on your product too,
  say so in both files, or propose moving it into `/orient-dt` §2's general list.
