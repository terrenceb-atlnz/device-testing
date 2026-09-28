---
name: no-power-cycle-between-testcases
description: "Terrence 2026-09-29: never power-cycle or adjust the setup between TestCases of one TestSet. The framework does it BY DEFAULT after any failed case (ATTestCase.powerCycleOnFail=True, no run flag disables it) — generated scripts must turn it off; bench setup is set once before and restored once after."
metadata:
  type: feedback
---

**Terrence, 2026-09-29** (watching T33234 run 2 power-cycle all six tb470 units after
TestCase 1 failed): *"we should not be cycling power or adjusting the setup between test Cases
in the same test set. thats really really inefficient from all perspectives."*

**What the framework does:** `ATTestCase._power_cycle()` (`ATTestCase.py:~1020`) reboots every
control device via the PDU when a TestCase's result is FAIL, UNSUPPORTED or ERROR, then waits
for all ports. `powerCycleOnFail` is True per TestCase by default (`ATTestCase.py:116`) and is
only skipped when a case has `quitOnFail`, or lacks one of doConf/doMain/doTear. `--nopower`
is NOT it — that flag only skips the initial power cycle at TestSet setup. So a script with a
systematic defect (T33234's `no polarity`) turns into N failed cases × a ~4 min bench reboot.

**Why:** a power cycle costs ~4 min of six units, re-arms every "unexpected reboot" trap, and
resets nothing a properly torn-down case needs. Setup changes between cases make later cases
depend on earlier ones. Both waste bench time and blur the evidence.

**How to apply:**
- Generated scripts (Test-cases frame) must disable power-cycle-on-fail in every TestCase; the
  bench-runner checks for it before launch and refuses a script that would cycle the bench.
- Set the bench up ONCE before the TestSet (aggregator/VLAN isolation, boot pointers) and
  restore ONCE after; between cases only the case's own steps and its `tear_down()` run.
- Recorded as STANDING-ORDERS.md §6. Related: [[tester-full-authority-within-tests]],
  [[campaign-measurement-discipline]].
