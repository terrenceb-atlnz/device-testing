# T33412 process review -- tacacs-2026-10-20T0825
Reviewed 2026-10-20 by /create-logs from the tester's transcript and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 28 | 56 | 48,456 | **9,409,040** | 257 | 28 | 1278 s | 20,107 |

## Process taken

28 tool calls in 1278 s. The largest single reads were:

- `3020 chars: cd /media/bidhanc/mnt/testbox_home/claude/device-testing D=tb277/x960/tacacs-2026-10-20T0825/T33412/work date '+BOX %Y-%m-%d %H:%M:%S %Z' > $D/clock.t`
- `1912 chars: cd /media/bidhanc/mnt/testbox_home/claude/device-testing D=tb277/x960/tacacs-2026-10-20T0825/T33412/work tools/tb cfg tb277 cktac u2 115200 'configure`
- `1835 chars: cd /media/bidhanc/mnt/testbox_home/claude/device-testing D=tb277/x960/tacacs-2026-10-20T0825/T33412/work MARK=9002 tools/tb conlogin tb277 cktac u2 11`
- `1727 chars: tools/tb grep tb277 'awplus login:|Last login|AlliedWare Plus' /tmp/cktac/console-u2.log 2>&1 | tail -30`
- `1509 chars: cd /media/bidhanc/mnt/testbox_home/claude/device-testing D=tb277/x960/tacacs-2026-10-20T0825/T33412/work echo '=== baseline: any tacacs line in the wh`

## Wasted input

Tool output read back off disk in this case: 20,107 characters. That is low against the case's own context cost.

## Repetition

None found in this case's own segment.

## Accuracy risks

- Five rows of the STEP 8 facility/severity table were built from **another case's** output and were dropped. The seven rows this case's own output supports are kept.
- The working log's verdict sentence ("five of the seven ... two of the five reveal gaps") does not parse: of five driven specs, three are satisfied and two are gaps. The count sentence was corrected; no verdict changed.
- STEP 5 carries a step verdict of `PARTIAL`, which is not in `logged-output.md` §4's step vocabulary (`done`, `PASS`, `FAIL`, `UNSUPPORTED`, `NOT RUN`). Preserved verbatim rather than re-graded.
- STEP 8 had no step verdict at all in the working log; it was graded `done` as a non-measurement step.

## Next run: expected outputs

The final log's STEP blocks hold this bench's measured value for every step. Compare against `T33412.log`, do not rediscover.

## Next run: scripts

Every helper this case used is already in `tools/` with a `tools/README.md` entry. Nothing was hand-built that is not catalogued.

## Next run: references

- `platforms/x960.md` -- this DUT family's measured behaviour, including the sections this campaign added.
- See [REVIEW.md](../REVIEW.md) for the findings that apply to the whole group.
