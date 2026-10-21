# T33400 process review -- ntp-2026-10-21T1159
Reviewed 2026-10-22 by /create-logs from the tester's transcript and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 12 | 24 | 27,754 | **3,074,551** | 126 | 12 | 1040 s | 6,342 |

## Process taken

12 tool calls over 1040 s.

## Wasted input

Tool output read back off disk: 6,342 characters. Low against this case's own context cost.

## Repetition

See the group [REVIEW.md](../REVIEW.md) for what every case in this group repeated.

## Accuracy risks

- No CPU load averages recorded — percentages only.
- The `clock set` recovery is explicitly **NOT MEASURED**: not recovered in 90 s at a 3523 s offset nor 75 s at 2.12 s, and nothing in the run separates "the daemon refuses" from "the daemon is slewing too slowly to see".

## Next run: expected outputs

The final log's STEP blocks hold this bench's measured value for every step. Compare against `T33400.log`; do not rediscover.

## Next run: scripts

Every helper this case used is in `tools/` with a `tools/README.md` entry. Nothing was left uncatalogued.

## Next run: references

- `platforms/x960.md` -- this family's measured behaviour, including the sections this campaign added.
- The campaign queue's `## Issues` -- the findings and method rules this campaign produced.
- [REVIEW.md](../REVIEW.md) -- this group's shared findings.
