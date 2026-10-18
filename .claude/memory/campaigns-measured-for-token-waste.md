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

**Measured again 2026-10-16, tb277 x960, 10 cases: 126.0 M cache-read, 599 calls, overhead down
to 9% from 46%.** What moved it, and three new levers:

- **What worked:** one `bench-runner` per group rather than per case, and each tester reading the
  *previous* campaign's `REVIEW.md` before starting. The review loop paid for itself.
- **🔥 An idle gap longer than the prompt cache's lifetime costs a FULL context re-write.** One
  call showed `cache_read = 0, cache_write = 327,405` after a 339 s gap with no API call — 78% of
  that case's cache write, paid a second time for material already held. Bench work is full of
  long waits (reloads, convergence timers, 60 s captures): **poll them in sub-lifetime chunks so
  a call lands every couple of minutes**, rather than sleeping through them.
- **Position is a ~4.9× lever.** Cache-read per tool call rose from ~74 k in a group's overhead
  segment to ~362 k in its last case. The same read costs five times more late. Front-load specs,
  platform sections, `tools/README.md` and CLI-surface probes; order the reading-heavy case
  first; and never judge one group's case cost against another's.
- **A group brief must be readable alone.** ~115 kB of overhead across two groups went on slicing
  the campaign-wide queue to reconstruct rows and a session block the dispatch already carried —
  37% and 42% of those groups' overhead output respectively. Either put a readable-alone
  `## Group <X>` section in the queue, or give line ranges in the dispatch.
- **Cost tracks accumulated context × API calls, not volume of output.** The case that read back
  the third-most tool output was the second cheapest, because it ran as one near-linear pass
  writing full output to `work/` and reading back only a grepped slice. Reading a lot once in
  small slices is cheap; re-reading a little many times is not.

**`tools/case_tokens.py` gotchas, measured 2026-10-16.** `--find <projects dir>` finds nothing
when the testers were **subagents** — their transcripts are the task `.output` files under the
session scratchpad, so use `--transcript <that file>` per tester. It matches `RESULT <id> ` as a
literal, so pass the ids **exactly as the RESULT lines write them** (`T43870`, not `43870`). Run
it per group. Its per-case split keys on main-chain calls into the case directory, so pointing it
at a *sentinel's* transcript attributes everything to overhead and reports the sentinel's own
watch loop, not the test work.

**How to apply:**
- Read by section (`grep -n '^#'`, then `sed -n`), never `cat` a skill or rules file whole; don't
  re-read a spilled tool result in full.
- For a repeat of earlier cases, start from the group's `REVIEW.md` / `<id>-review.md` and any plan
  under `<TB>/<FAMILY>/plans/`, not the old final logs.
- Send step output to files and bring back a grep summary.
- The lab-home CLAUDE.md still requires TESTBOX-ACCESS.md in full; only Terrence can relax that.
- Measure with `tools/case_tokens.py`; the rules are logged-output.md §5.

Related: [[sentinel-session-keeps-long-runs-moving]], [[log-is-the-deliverable]].
