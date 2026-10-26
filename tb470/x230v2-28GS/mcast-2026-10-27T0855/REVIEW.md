# mcast-2026-10-27T0855 process review
Reviewed 2026-10-27 by /create-logs from agent-a4a7a65c22a5db4d1.jsonl (group 2 tester, T30403).

## Token usage
| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T30403 | 66 | 132 | 98,997 | 7,217,480 | 41,470 | 67 | 932 s | 108,126 |
| overhead | 4 | 8 | 31,939 | 293,999 | 2,703 | 4 | 26 s | 21,466 |
| **total** | 70 | 140 | 130,936 | 7,511,479 | 44,173 | 71 | 958 s | 129,592 |

## Overhead findings
- 21 KB of overhead was the queue file read in two slices (`sed -n 1,125p` 12 KB, `sed -n 126,200p` 7.7 KB). The tester needed the Session facts, Rules, the 09:10 Triage section and one row. A dispatch that names those line ranges (test-mode §6 step 1, "a short brief") would cut this to ~6 KB.

## Findings for the group
- The case cost 108 KB of tool output for a verdict decided by the parser in step 1 and the TPS. Half of it was rule and catalogue reading inside the case segment, and documentation searches that could not decide the verdict (CLI wiki, ck.db command tables). For a support question, the order that worked was: licence read -> qmark -> step commands -> TPS / build-target page.
- The missing `Feature Overview Guides/` directory cost three calls. The memory `review-feature-docs-before-testing` still points at it; it should be corrected once the Test Engineer says where the guides live now.
