# ports-2026-10-22T1320 process review
Reviewed 2026-10-22 by /create-logs. One attempted case (T47209); T44179 was NOT TESTED (blocked at triage).

## Token usage
| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T47209, first tester (died ~14:00) | 39 | 78 | 120,574 | 3,299,702 | 6,798 | 39 | 945 s | 82,815 |
| T47209, resuming tester | 37 | 74 | 118,213 | 3,176,230 | 1,674 | 39 | 1,127 s | 64,837 |
| overhead (hand-back) | 1 | 2 | 334 | 118,213 | 24 | 2 | 16 s | 143 |
| **total** | **77** | **154** | **239,121** | **6,594,145** | **8,496** | **80** | **2,088 s** | **147,795** |

## Overhead findings
- **The session cut cost about half of this group.** The first tester's sentinel session (device-testing-43) exited ~14:00,
  and its bench-runner subagent died with it after R6. A fresh tester had to re-gate, re-read the brief, transcribe R2-R6
  and re-run R6. About 3.3 M of the 6.6 M cache-read tokens are the first tester's. The fix is the one /test-mode §1
  step 3 already gives: run a multi-row campaign from a tmux session, not from an editor window.
- **Pre-flight reading.** The first tester read 12.2 k of the queue and 26 k of tools/README.md + logged-output.md before
  touching the bench. The resuming tester, given named line ranges (`sed -n '14,52p;83,101p'`), read 6.0 k and lost
  nothing. Dispatch every tester with named line ranges.

## Findings that recur across cases
- Per-port counter deltas were computed by hand-built scripts twice (see 47209-review.md "Next run: scripts":
  proposed tools/portdelta.py).
- The working log must be written per row, not per batch: here it survived a cut only because the row script wrote into
  the repo (47209-review.md "Accuracy risks").
