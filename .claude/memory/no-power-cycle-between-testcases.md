---
name: no-power-cycle-between-testcases
description: "Terrence 2026-09-29: the framework's PDU restart of every device after a FAILED TestCase is ACCEPTED (\"I dont mind that restart\") — do not engineer around it; what he objects to is a tester adjusting the bench setup between cases, and a script whose systematic defect makes every case fail and pay that restart."
metadata:
  type: feedback
---

**Terrence, 2026-09-29.** Watching T33234 run 2 power-cycle all six tb470 units after
TestCase 1 failed: *"we should not be cycling power or adjusting the setup between test Cases in
the same test set."* Told that the cycle is the framework's own design
(`ATTestCase._power_cycle()` after any FAIL/UNSUPPORTED/ERROR case; `powerCycleOnFail` re-armed
True per case, no run flag): *"ok, thats not the worst type of behavior. I dont mind that
restart."* An override I had already sent to Test-cases was withdrawn the same morning.

**Why:** the restart guarantees a clean state after a failure and he accepts its cost. The real
waste was a script defect (`no polarity`) that failed EVERY case at its defaulting step — two
bench cycles with nothing measured — and any tester-side setup change between cases, which
makes later cases depend on earlier ones.

**How to apply:**
- Leave `powerCycleOnFail` alone in generated scripts and the frame.
- Before launching, check the script's defaulting commands against the platform; stop a run
  whose failures are systematic instead of letting N cases pay N restarts.
- Bench setup ONCE before the TestSet, restore ONCE after; nothing in between but the case's
  own steps and `tear_down()`. STANDING-ORDERS.md §6. Related: [[tester-full-authority-within-tests]].
