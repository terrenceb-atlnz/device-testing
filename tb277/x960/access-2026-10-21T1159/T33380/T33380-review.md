# T33380 process review -- access-2026-10-21T1159
Reviewed 2026-10-22 by /create-logs from the tester's transcript and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 36 | 72 | 45,602 | **9,994,410** | 683 | 36 | 790 s | 15,931 |

The reboot-persistence limb was measured in a second run, in a different tester's segment:

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 13 | 26 | 19,308 | **4,309,284** | 134 | 13 | 427 s | 8,322 |

**Combined cache-read for this case: 14,303,694.**

## Process taken

36 tool calls over 790 s.

## Wasted input

Tool output read back off disk: 15,931 characters. Low against this case's own context cost.

## Repetition

See the group [REVIEW.md](../REVIEW.md) for what every case in this group repeated.

## Accuracy risks

- Four capture file names were not recorded, so four decode lines in the final log name the capture by description rather than by file. The measurements themselves are all verbatim.

## Next run: expected outputs

The final log's STEP blocks hold this bench's measured value for every step. Compare against `T33380.log`; do not rediscover.

## Next run: scripts

Every helper this case used is in `tools/` with a `tools/README.md` entry. Nothing was left uncatalogued.

## Next run: references

- `platforms/x960.md` -- this family's measured behaviour, including the sections this campaign added.
- The campaign queue's `## Issues` -- the findings and method rules this campaign produced.
- [REVIEW.md](../REVIEW.md) -- this group's shared findings.
