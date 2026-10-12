# T33235 repairs -- Ask-CK validation run 2026-10-13T0626-val-fbe9 (/test-mode §11)

Copy under repair: tb470/IE520/port-2026-10-13T0626/33235/work/test-9001.33235.py
(fresh copy of claude/Test-cases/ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py, sha1 b044d695...,
taken 2026-10-13 ~06:38 NZDT; NOT yesterday's copy). library_9001.py sha1 943e11a6..., ck_media.py = Test-cases
ask-ck/tools/pt_media (sha1 8d042bad...).

## R1 -- bench state, NOT a script edit (carried from port-2026-10-12T1537/33235/work/repairs.md R1)
- **What:** before each launch, read `show exception log` on every bound device (stack master u5 shows all members; u0, u1, u3)
  and save it to `work/pre-run<N>-<uN>-exc.out`. If any entry exists and every entry predates the run, `clear exception log` on
  that device, then re-read it (`None` for every member). An entry from during a run is a DUT finding: record it, never clear it.
- **Why:** under `--nodefaultcfg` the framework skips its own TestSet-start "Clear exception log for all devices", while
  ATTestCase.check_exceptions() fails a TestCase on ANY entry. On 2026-10-12 run 1, stale Oct 04/07 entries on stk_a member 3
  failed TestCase_1 after its own checks had PASSed and cost a six-unit PDU cycle.
- **Expected today:** no-op (triage 2026-10-13 06:30: every log `None`).
- **Script copy:** unchanged. No check removed, loosened or overridden; powerCycleOnFail untouched.
