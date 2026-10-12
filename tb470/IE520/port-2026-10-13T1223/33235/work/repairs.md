# T33235 repairs -- Ask-CK validation run 2026-10-13T1223-val-3ede (/test-mode §11)

Copy under repair: tb470/IE520/port-2026-10-13T1223/33235/work/test-9001.33235.py
(fresh copy of claude/Test-cases/ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py, sha1 f04ea359...,
Test-cases ef53cea, taken 2026-10-13 12:37 NZDT). library_9001.py sha1 943e11a6..., ck_media.py = Test-cases
ask-ck/tools/pt_media.py (sha1 8d042bad...).

## R1 -- bench state, NOT a script edit (carried from port-2026-10-12T1537 and port-2026-10-13T0626 R1)
- **What:** before each launch, read `show exception log` on every bound device (stack master u5 shows all members; IE520-sa u3)
  and keep it in `work/pre-run<N>-<uN>.out`. If any entry exists and every entry predates the run, `clear exception log` there and
  re-read it. An entry from during a run is a DUT finding: record it, never clear it.
- **Why:** under `--nodefaultcfg` the framework skips its own TestSet-start "Clear exception log for all devices", while
  ATTestCase.check_exceptions() fails a TestCase on ANY entry (2026-10-12 run 1 cost a PDU cycle that way).
- **Run 1 (12:39 NZDT):** no-op -- `None` on stack members 1/3/4 and on the IE520-sa.
- **Script copy:** unchanged. No check removed, loosened or overridden; powerCycleOnFail untouched.
