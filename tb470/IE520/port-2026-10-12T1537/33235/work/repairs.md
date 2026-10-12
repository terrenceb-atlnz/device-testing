# T33235 repairs -- Ask-CK validation run 2026-10-12T1537-val-9f45 (/test-mode §11)

Copy under repair: tb470/IE520/port-2026-10-12T1537/33235/work/test-9001.33235.py
(source claude/Test-cases/ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py, sha1 b044d695...).

## R1 -- bench state, NOT a script edit (shown by run 1, 2026-10-12 15:57:48)
- **What:** before launch, read `show exception log` on every bound device (stack master u5 shows all members) and save it to
  `work/pre-run<N>-<uN>-exc.out`. If any entry exists and every entry predates the run, `clear exception log` on that device, then
  re-read it (`None` for every member). An entry from during a run is a DUT finding: record it, never clear it.
- **Why:** under `--nodefaultcfg` the framework skips its own TestSet-start "Clear exception log for all devices" (ATTestSet,
  default-config path), while ATTestCase.check_exceptions() fails a TestCase on ANY entry in the log. In run 1 the five stale entries
  on stk_a member 3 (Oct 04 vcs-l2-err snapshot; Oct 07 tpm_server/tpm2-abrmd cores, builds 20260923-20 and main-calanm) failed
  TestCase_1 after its own checks had all PASSed, and cost a six-unit PDU cycle. check_exceptions() then cleared them itself.
- **Script copy:** unchanged (sha1 b044d695...). No check removed, loosened or overridden; powerCycleOnFail untouched.
- **Status after run 1:** every log already reads `None` (the framework's clear, verified 16:03:48-16:04:26), so R1 is a check at run 2
  setup; a clear is sent only if new stale entries appear before then.
