# T31866 process review -- platform-2026-10-27T0855
Reviewed 2026-10-27 by /create-logs from agent-a512b95ab36fe7ece.jsonl (group 1 tester) and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 18 | 36 | 20,201 | 2,452,336 | 14,683 | 18 | 985 s | 9,820 chars |

## Process taken
1. Baseline `show platform prbs` while still logged in from T31863.
2. Reload 1, 168 s; `exec-timeout 0`; `exit`; health before (fresh login).
3. Setup reads in one ckcon; swi_f.cfg via rc2cfg.py.
4. qmark for `platform prbs` help; `ckyn "YN?:platform prbs all-fabric duration 20"`; one ckcon with the other forms, `show platform prbs`, `show exception log`; then the case's literal `platform prbs all duration 20`.
5. Health after (tool exit 4, DIRTY on the boot-time `HTTP server restarted` line); two greps to show the line was already in the before sample.
6. Reload 2, 168 s; start-job comparison; post reads; rcdiff.
7. Group close-out: post probe, u0 boot read, both consoles logged out.
8. RESULT to the sentinel.

## Wasted input
- none found. This case reused T31863's method and stayed under 10 KB of tool output.

## Repetition
- The start-job extraction was repeated per reload (as in T31863). See ../REVIEW.md.
- The DIRTY-flag investigation (calls 118-119) repeats a check the health tool should do itself (below).

## Accuracy risks
- `tools/health.py` flags lines in the log tail that the before sample already held, so a boot-time line reads as DIRTY. Here the tester checked by hand and the Test Engineer confirmed "clean". Fixing the tool removes the manual step and the risk of a real line being waved through the same way.

## Next run: expected outputs
- `show platform prbs` -> "Unable to open results file. No previous PRBS run?" before and after.
- `platform prbs all-fabric duration 20`, `internal-fabric duration 20`, `all-fabric`, `all duration 20` -> `% PRBS not supported on this platform` (no warning, no y/n).
- Help: `platform prbs ?` -> all-fabric / internal-fabric; `all` is accepted as a short form of all-fabric.

## Next run: scripts
- Fix `tools/health.py`: subtract the before sample's filtered lines from the tail's flagged lines before calling DIRTY.
- Proposed `tools/startjobs.py` (see 31863-review.md).

## Next run: references
- platforms/x230v2-28GS.md §2 (PRBS row).
- This case's final log for the command forms.
