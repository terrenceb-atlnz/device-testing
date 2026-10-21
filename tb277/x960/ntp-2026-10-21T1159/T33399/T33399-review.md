# T33399 process review -- ntp-2026-10-21T1159
Reviewed 2026-10-22 by /create-logs from the tester's transcript and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 45 | 90 | 57,224 | **8,257,143** | 503 | 45 | 1116 s | 21,862 |

## Process taken

45 tool calls over 1116 s.

## Wasted input

Tool output read back off disk: 21,862 characters. Low against this case's own context cost.

## Repetition

See the group [REVIEW.md](../REVIEW.md) for what every case in this group repeated.

## Accuracy risks

- 🔴 **Finding 3 — `ntp rate-limit` holds exactly one keyword — has NO sourced before/after pair.** The tester reports measuring it three times and says the wire agreed with running-config each time, but quotes no `show running-config | include ntp` output. **It could not go in the deliverable.** It is in the campaign queue beside the numbered-ACL defect and needs a re-run with a quoted pair before it can face a developer.
- Findings 4-7 (the `ntp restrict` / `ntp rate-limit` syntax rejections) have no command-plus-output blocks, so no step could carry its own proof.
- "After sixty client requests all three counters still read 0" has no post-serving counter read; only the all-zero read taken right after configuration is quoted.

## Next run: expected outputs

The final log's STEP blocks hold this bench's measured value for every step. Compare against `T33399.log`; do not rediscover.

## Next run: scripts

Every helper this case used is in `tools/` with a `tools/README.md` entry. Nothing was left uncatalogued.

## Next run: references

- `platforms/x960.md` -- this family's measured behaviour, including the sections this campaign added.
- The campaign queue's `## Issues` -- the findings and method rules this campaign produced.
- [REVIEW.md](../REVIEW.md) -- this group's shared findings.
