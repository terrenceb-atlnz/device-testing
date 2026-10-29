# dot1x-2026-10-29T1528 process review
Reviewed 2026-10-30 by /create-logs from agent-a703cc5195e03bfaa.jsonl.

| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T44277 | 47 | 96 | 173,288 | 3,541,041 | 32,170 | 46 | 10,071 s | 64,283 |
| overhead | 2 | 4 | 10,388 | 145,495 | 1,820 | 2 | 15 s | 9,334 |
| **total** | 49 | 100 | 183,676 | 3,686,536 | 33,990 | 48 | 10,086 s | 73,617 |

T44277's wall time includes a usage-limit cut of about 2 h 27 min (17:02-19:29); active time was about 15 min.

## Overhead
- The dispatch's queue line ranges kept the queue read to 9,191 chars. That worked.
- The case read two platform files and another case's working log for recipes it could have taken from the queue's group A recipe (see T44277-review.md, Wasted input).

## Cross-case findings
- The group has one case, so none.
- T33355 (in this group's README) was not run here: the Test Engineer recorded it as already tested and finished.
