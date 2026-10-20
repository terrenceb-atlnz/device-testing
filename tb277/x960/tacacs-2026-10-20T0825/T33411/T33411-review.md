# T33411 process review -- tacacs-2026-10-20T0825
Reviewed 2026-10-20 by /create-logs from the tester's transcript and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 59 | 118 | 100,760 | **11,138,633** | 644 | 59 | 1898 s | 54,993 |

## Process taken

59 tool calls in 1898 s. The largest single reads were:

- `3633 chars: sed -n '93,180p' tools/conlogin.py`
- `3332 chars: cd /media/bidhanc/mnt/testbox_home/claude/device-testing D=tb277/x960/tacacs-2026-10-20T0825/T33411/work tools/tb ckcon tb277 cktac u2 115200 'show re`
- `3264 chars: head -40 tools/conlogin.py && echo '...' && command grep -n 'settle\|restore\|enable\|Last login\|def ' tools/conlogin.py | head -40`
- `3051 chars: wc -l tb277/x960/aaa-2026-10-20T0825/T33408/swi_d.cfg && sed -n '141,200p' tools/README.md`
- `2484 chars: D=tb277/x960/tacacs-2026-10-20T0825/T33411/work && tools/tb qmark tb277 cktac u2 115200 --mode 'configure terminal' -- 'tacacs-server ' 'tacacs-server`

## Wasted input

Tool output read back off disk in this case: 54,993 characters. **This is high.** Extract what the step needs when the result first arrives, rather than re-reading the saved file.

## Repetition

None found in this case's own segment.

## Accuracy risks

- The stale `Last login:` mechanism (AW+ lastlog keyed on a recycled UID) is sourced only through **another campaign's** working log, so the final log keeps the measurement and drops the mechanism. **The conclusion is weaker in the deliverable than in the evidence — worth re-sourcing in a future case.**
- The idle control (40 s, 0 packets) was measured by accident through a shell-variable mistake. The measurement is kept; the accident is not.

## Next run: expected outputs

The final log's STEP blocks hold this bench's measured value for every step. Compare against `T33411.log`, do not rediscover.

## Next run: scripts

Every helper this case used is already in `tools/` with a `tools/README.md` entry. Nothing was hand-built that is not catalogued.

## Next run: references

- `platforms/x960.md` -- this DUT family's measured behaviour, including the sections this campaign added.
- See [REVIEW.md](../REVIEW.md) for the findings that apply to the whole group.
