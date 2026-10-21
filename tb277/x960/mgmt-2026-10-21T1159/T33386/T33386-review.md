# T33386 process review -- mgmt-2026-10-21T1159
Reviewed 2026-10-22 by /create-logs from the tester's transcript and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 16 | 32 | 36,375 | **3,123,648** | 147 | 16 | 618 s | 11,159 |

The reboot-persistence limb was measured in a second run, in a different tester's segment:

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 18 | 36 | 26,286 | **6,357,050** | 208 | 18 | 487 s | 17,521 |

**Combined cache-read for this case: 9,480,698.**

## Process taken

16 tool calls over 618 s.

## Wasted input

Tool output read back off disk: 11,159 characters. Low against this case's own context cost.

## Repetition

See the group [REVIEW.md](../REVIEW.md) for what every case in this group repeated.

## Accuracy risks

- **The `EXFX` driver-error contrast is a cross-case claim.** Run 1 captured `exfx_cExt_dxch_rules_pclIdActionUpdate` when the NUMBERED form lost a rule; T47192 later showed the NAMED form editing cleanly. That pairing is what makes it a reportable defect, and it cannot live in either case's own log. It is in the campaign queue instead.

## Next run: expected outputs

The final log's STEP blocks hold this bench's measured value for every step. Compare against `T33386.log`; do not rediscover.

## Next run: scripts

Every helper this case used is in `tools/` with a `tools/README.md` entry. Nothing was left uncatalogued.

## Next run: references

- `platforms/x960.md` -- this family's measured behaviour, including the sections this campaign added.
- The campaign queue's `## Issues` -- the findings and method rules this campaign produced.
- [REVIEW.md](../REVIEW.md) -- this group's shared findings.
