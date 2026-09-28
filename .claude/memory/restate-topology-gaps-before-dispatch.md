---
name: restate-topology-gaps-before-dispatch
description: "Terrence 2026-09-29: before dispatching (or resuming) a run, RESTATE the triage's topology gaps as a heads-up with the exact fix — 'you don't have the topology to do this test properly: cases X need Y; fit Z first or accept UNSUPPORTED'. A gap named at triage gets buried by later derails (script defects, rulings) and must be re-surfaced at the go/no-go moment."
metadata:
  type: feedback
---

**Terrence, 2026-09-29 (T33235):** *"i'd have appreciated a reminder 'heads-up, you dont have
the topology to do the test properly' for this test set, because we identified that lacking
criteria at the outset but then immediately got derailed by the script defects and the MDI/X
test case."*

**What happened:** the 07:56 triage said T33235's fibre sweep (cases 8–12) needed a fibre
link the stack lacks, with the exact remedy (an SR module in stack port1.0.25 + LC fibre to
IE520-sa port1.0.25). Four hours of script defects, a stopped run and the MDI/MDI-X ruling
followed; when he said "ready to run tests" the sentinel resumed the queue and mentioned only
"five power cycles" before his go — not that the fibre could still be fitted first. The run
then paid five full-bench power cycles for cases known unsupported at triage.

**How to apply (sentinel, at every dispatch/resume of a row):**
- Re-read that row's triage line and restate, in one sentence each, every topology gap it
  carries and the exact change that removes it — before asking "proceed or reconfigure?".
- Frame the choice as: fit <exact change> now (cost: N minutes of hands) vs run now and take
  UNSUPPORTED on cases <list> (cost: what the framework charges for them).
- A gap surfaced hours earlier does not count as surfaced; the go/no-go moment is where he
  decides. Related: [[no-power-cycle-between-testcases]], [[campaign-measurement-discipline]].
