# atmf-2026-10-21T0835 -- process review (group)
Reviewed 2026-10-21 by /create-logs from `agent-a1531ba7f0ac26939.jsonl` (the bench-runner subagent that ran TRIAGE, then RUN, then the resumed restore) and the working files. Measured with `tools/case_tokens.py --find ~/.claude/projects/-media-terrenceb-mnt-testbox-home-claude-device-testing --cases 46810,28218`.

## Token usage
| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T46810 | 17 | 544 | 28,640 | 2,613,763 | 1,327 | 17 | 7.7 min | 9,846 |
| T28218 | 7 | 224 | 10,506 | 1,218,412 | 74 | 7 | 3.3 min | 3,806 |
| overhead (triage, gates, recipe, restore, hand-backs) | 47 | 1,416 | 287,130 | 5,675,928 | 446 | 47 | 49.8 min | 114,988 |
| **total** | **71** | **2,184** | **326,276** | **9,508,103** | **1,847** | **71** | **60.8 min** | **128,640** |

The two cases together are 24 of 71 calls, 11% of the tool output read back and 40% of the cache reads. The overhead segment holds the triage (read-only reads of the rules, the platform file, two memories, the prior ATMF logs and the probe captures), the recipe, the group restore and both hand-backs. Its wall time includes two idle gaps that are not the tester's: 08:47-09:19 waiting for the Test Engineer's triage answers, and the 09:33 session restart. Each gap cost a full cache re-write on resume (the 287 K cache-write tokens sit almost entirely in this segment).

## Overhead findings
1. **One 18 KB read at triage** (`sed STANDING-ORDERS §3 && cat MANUAL-ONLY.md && sed platforms/x230v2-28GS.md 1-75 && cat two memories && grep tools/README.md`, 18,120 chars) and **three 7-8.5 KB reads** (the queue file + section headings; the probe captures filtered; the health-check section + console.py prompt regexes + the recipe). Together 42 KB of the 115 KB overhead. The narrower reads: the queue file was already in the dispatch prompt's facts (read only its Session facts and Queue sections); the platform file's §2 table rows on boot/config were not needed for an AMF case on the master; the probe captures were read to confirm a cabling fact (one link) that `bench-state.md`'s Links table already stated in 4 lines.
2. **The triage-to-RUN hand-back.** The tester handed back its triage with three questions, waited 32 min for the answers, and resumed. Where the defaults are safe (as they were here: the master's own file-set, Enterprise-AMF, no `device`), the dispatch can say "run with these defaults unless the Test Engineer objects within the triage report", and the tester continues straight into RUN. The queue file already carries the answers; the stall was the only cost.
3. **The session restart.** The sentinel's process died during the group restore; the tester was resumed by name and re-verified the restore in 12 calls (211,673 subagent tokens for that segment per the harness usage line). The device had taken every restore command, so nothing was lost on the bench, but the restore echo now exists only in the box's tmpfs transcript. Writing `work/restore-u0.out` from the ckyn call itself (tee) rather than from a later verification read would have kept it in the repo.

## Findings that recur across cases
- **Health reads are the bulk of each case's console traffic** (reboot history + exception log + filtered log + `show log tail 150` + `show cpu` + `show memory` on both units, before and after). The tester read back only awk-filtered summaries, which is the right pattern; keep it. The full `show cpu` and `show memory` process tables (about 240 lines each) go into the working log four times per case. A `tools/health.py` that keeps the header lines (averages, totals, free) and drops the per-process tables unless `--full` is given would cut each working log by about 1,000 lines with no loss for the HEALTH block.
- **`show cpu` on the x230 gives busy averages, not idle.** Both HEALTH blocks say so. Add the fact to `platforms/x230v2-28GS.md` so the next log does not have to explain it.
- **One console pass per case works for AMF CLI cases.** T28218 ran all five steps, the proof reads and the dir in one `ckcon --stop-on-error` call. T46810 needed two (setup via `cfg`, step via `ckcon` with `@poll`). Keep this shape; it is why the two cases cost 24 calls.

## The three biggest savings
1. Read the triage inputs by section, not whole files: about 35 KB less tool output at triage (30% of the overhead's read-back).
2. Let the tester run on safe defaults instead of handing back for answers: removes the 32 min stall and one cache re-write (about 150-250 K cache-write tokens).
3. Keep the sentinel session alive through the restore, or write restore captures with tee at send time: removes the 12-call re-verification and keeps the restore echo in the repo.

## Accuracy risks carried from the cases
- T46810 is graded under an assumed definition (no steps in ck.db). Only the Test Engineer's definition of the case closes it.
- The restore commands' device responses are not in the repo (see T28218's review); the verification reads are.
