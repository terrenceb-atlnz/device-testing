# atmf-2026-10-27T0855 process review
Reviewed 2026-10-27 by /create-logs from agent-ac199d3fbcfdc217f.jsonl (group 3 tester, T28218).

## Token usage
| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T28218 | 40 | 80 | 76,787 | 4,250,373 | 35,639 | 40 | 1,664 s | 67,193 |
| overhead | 6 | 12 | 67,312 | 374,595 | 3,071 | 6 | 34 s | 37,419 |
| **total** | 46 | 92 | 144,099 | 4,624,968 | 38,710 | 46 | 1,698 s | 104,612 |

Wall time includes a 90 s wait on a marker file and the restore reload (169 s).

## Overhead findings
- 37 KB of overhead: this campaign's queue file read in two slices (24 KB) and the 2026-10-21 queue's T28218 section (11 KB). The queue file had grown past 20 KB by group 3, with the earlier groups' recipes in it. A dispatch that names line ranges (test-mode §6 step 1) would cut this to under 10 KB.

## Findings for the group
- The one-pass steps run (`ckcon --stop-on-error` with CKTO=600 for all five steps) worked well: 2 minutes, one call, every prompt captured. Keep it.
- The occupancy check found a minicom on u2, outside the session's consoles. The tester correctly held and asked. The Test Engineer's answer ("dont touch u2, its irrelevant") suggests that a holder on a console OUTSIDE the session's list need not stop a run; whether to make that a standing order is the Test Engineer's call.
