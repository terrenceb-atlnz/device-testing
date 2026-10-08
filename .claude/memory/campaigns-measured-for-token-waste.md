---
name: campaigns-measured-for-token-waste
description: Terrence 2026-10-08 wants every campaign's per-case token use measured and the tester's process reviewed for waste; up-front reading is the dominant cost
metadata:
  type: feedback
---

Terrence (2026-10-08) asked for `/create-logs` to measure token usage per case, review the tester's
process for wasted input, repetition and accuracy risk, and leave an `<id>-review.md` per case plus a
group `REVIEW.md` with expected outputs, scripts and references for a faster next run. Then he had
the suggestions implemented (`tools/mbplan.py` + `tb470/IE520/plans/modbus/`, `mb.py` exception
codes, `bench_probe.py --baud`, bench-runner "Keep the context small").

**Why:** on the 10-08 Modbus group, 98% of tokens were cache reads: every API call re-reads the whole
context, and ~300k chars read before the first case (whole skill/rules files, all of the previous
run's final logs) were carried by ~80 later calls. The cases themselves were cheap (5–10 calls).

**How to apply:**
- Read by section (`grep -n '^#'`, then `sed -n`), never `cat` a skill or rules file whole; don't
  re-read a spilled tool result in full.
- For a repeat of earlier cases, start from the group's `REVIEW.md` / `<id>-review.md` and any plan
  under `<TB>/<FAMILY>/plans/`, not the old final logs.
- Send step output to files and bring back a grep summary.
- The lab-home CLAUDE.md still requires TESTBOX-ACCESS.md in full; only Terrence can relax that.
- Measure with `tools/case_tokens.py`; the rules are logged-output.md §5.

Related: [[sentinel-session-keeps-long-runs-moving]], [[log-is-the-deliverable]].
