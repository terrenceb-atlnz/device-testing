# T47192 process review -- mgmt-2026-10-21T1159
Reviewed 2026-10-22 by /create-logs from the tester's transcript and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 15 | 30 | 33,714 | **3,605,031** | 137 | 15 | 596 s | 15,873 |

The reboot-persistence limb was measured in a second run, in a different tester's segment:

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 15 | 30 | 24,016 | **5,700,261** | 185 | 15 | 638 s | 9,770 |

**Combined cache-read for this case: 9,305,292.**

## Process taken

15 tool calls over 596 s.

## Wasted input

Tool output read back off disk: 15,873 characters. Low against this case's own context cost.

## Repetition

See the group [REVIEW.md](../REVIEW.md) for what every case in this group repeated.

## Accuracy risks

- The per-address-family filters (`service telnet ip|ipv6`, `service ssh ip|ipv6`) are cited to another case's evidence, so the log only states they exist and were not exercised here.
- The mid-flow frames-lost timing number is **NOT MEASURED** — no `tools/` helper drives a continuous stream from the same process as a console write. The bound that was measured is stated and no precision is claimed.

## Next run: expected outputs

The final log's STEP blocks hold this bench's measured value for every step. Compare against `T47192.log`; do not rediscover.

## Next run: scripts

Every helper this case used is in `tools/` with a `tools/README.md` entry. Nothing was left uncatalogued.

## Next run: references

- `platforms/x960.md` -- this family's measured behaviour, including the sections this campaign added.
- The campaign queue's `## Issues` -- the findings and method rules this campaign produced.
- [REVIEW.md](../REVIEW.md) -- this group's shared findings.
