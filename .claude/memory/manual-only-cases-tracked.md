---
name: manual-only-cases-tracked
description: Cases/steps needing a person (fan magnet, LEDs, browser GUI, accounts/internet) are tracked in MANUAL-ONLY.md at the repo root; triage reads it, never schedules them unattended, adds new ones
metadata:
  type: feedback
---

Test cases, or single steps, that need a person are listed in **`MANUAL-ONLY.md`** at the repo root,
with the manual part, why, and what an agent can still automate. Examples: a magnet on the fan, watching
LEDs, a browser GUI, an idevid account or internet access.

**Why:** Terrence, 2026-10-13, after the x230 campaign re-triaged the same person-needed cases
(T45543 step 3, T47214, T31854, T31859, T47120 GUI) again: *"Mark this as a MANUAL-ONLY test case …
We will encounter many, and i want them clearly tracked (so we dont have this issue down the road)"*.

**How to apply:**
- At `/test-mode` triage, check every queued case against MANUAL-ONLY.md first. Report a listed case
  as MANUAL-ONLY with its reason. Never put it in an unattended or after-hours run.
  - Still run the automatable part if the row gives one. The unrun manual part goes under `NOT RUN:`.
- When triage finds a new person-needed case or step, add a dated row to MANUAL-ONLY.md in the same
  commit as the queue, and say so in the triage report.
- Remove a row only on the Test Engineer's word.

Related: [[reboot-heavy-runs-after-hours]], [[restate-topology-gaps-before-dispatch]].
