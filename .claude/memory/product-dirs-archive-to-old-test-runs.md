---
name: product-dirs-archive-to-old-test-runs
description: A finished product campaign's top-level dir is archived (IE520/ was, 2026-10-30) into "old test runs/" and a new product dir takes its place; "old test runs/" is Terrence's history — leave it alone, never sweep or tidy it
metadata:
  type: project
  verified: 2026-10-30
---

Terrence, 2026-10-02: *"leave the old test runs/ directory. its fine. after the IE520 platform
testing is done, it will go to that directory as well, and a new one will take its place."*

- **`old test runs/` is the archive of finished product campaigns.** It is history, so it is never
  cleaned up, generalised or moved, even when it holds scripts or duplicates. It was left out of
  the 2026-10-02 script sweep for that reason.
- **A product directory (`IE520/` today) is live only while that platform is under test.** When
  IE520 testing finishes, `IE520/` moves into `old test runs/` and the next product's directory
  takes its place.

**Why:** the repo is shared by Test Engineers across testboxes and products. Product-specific
material must not be load-bearing for the shared tooling, because it will move.

**How to apply:**
- Keep reusable things out of product directories: helpers go in `tools/` and logging rules in
  `logged-output.md`.
- Never make a skill, agent or tool depend on a path under `IE520/`. Name it by `<FAMILY>`, or
  move what it needs into `tools/` first.
- Links from live documents into a product directory will go stale at the archive. That is
  accepted, as for any historical record.

**DONE 2026-10-30:** Terrence moved `IE520/` to `old test runs/IE520/` on the share; commit
`35baaf7` records it (2424 pure renames, blobs verified identical; two `.gitignore` lines for the
>10 MB random-reboot transcripts repointed). Live IE520 work is under `<TB>/IE520/` (tb470, tb101),
which did NOT move. Text references to `IE520/…` remain in orient-dt (§0 table, §0b rule 2
globs), test-mode, bench-runner, tools/README.md, logged-output.md and platforms/IE520.md;
repointing them was put to Terrence and is unanswered.

Related: [[no-stray-scripts]], [[tb470-topology-and-setup]].
