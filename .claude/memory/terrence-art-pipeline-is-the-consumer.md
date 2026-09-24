---
name: terrence-art-pipeline-is-the-consumer
description: "Terrence runs his OWN ART (st-art framework) tests on tb470 built from this repo's methodology; everything here feeds that pipeline. A framework run renames the stack (hostname stk_a_<test>_<run>, saved) — that is his, not drift"
metadata:
  node_type: memory
  type: project
  originSessionId: 41cd590a-840f-44c2-ac1d-f420ac15666e
  modified: 2026-09-24T21:55:22.079Z
---

2026-09-25: Terrence is running his own ART tests on the tb470 bench, written with the methodology developed in this repo (bench-state.md, the per-case logs, the orient-dt mechanics). In his words, "everything we do feeds THAT pipeline". The bench is shared with those runs.

A framework run leaves recognisable traces on the stack:
- **Hostname:** `stk_a_<testid>_<run>` (e.g. `stk_a_9001_33235`), written to startup-config.
- **Log lines:** `[SCRIPT]aaa-configure …` entries.
- **tb470 used as the TFTP server:** e.g. `copy tftp://10.38.215.65/IE520-tb470.rel flash:/IE520-tb470_<epoch>.rel`, plus debug `.tgz` uploads.

**Why:** on 2026-09-25 I found the renamed stack and stopped, assuming a stranger's run. It was Terrence's.

**How to apply:**
- A framework hostname or `[SCRIPT]` lines are Terrence's ART work, not drift and not an intruder. Don't "restore" the hostname.
- Still check that no run is live before sending traffic: `fuser` on the consoles, and the time of the last `[SCRIPT]` entry. His runs and mine can corrupt each other.
- Shape results so they can become ART tests. That means exact console strings from real captures (see [[legacy-scripts-vs-framework]]), explicit expected values, and a gate for each step.

Related: [[tb470-topology-and-setup]], [[bench-scripts-stop-on-cli-errors]].
