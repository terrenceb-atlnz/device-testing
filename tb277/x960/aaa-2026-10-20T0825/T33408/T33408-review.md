# T33408 process review -- aaa-2026-10-20T0825
Reviewed 2026-10-20 by /create-logs from the tester's transcript and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 55 | 110 | 76,604 | **13,738,358** | 3622 | 55 | 1236 s | 33,905 |

## Process taken

55 tool calls in 1236 s. The largest single reads were:

- `5187 chars: D=tb277/x960/aaa-2026-10-20T0825/T33408/work && tools/tb tool tb277 ckaaa radwire /tmp/ckaaa/t33408-on2.pcap --secret testing123 2>&1 | tee $D/wire-on`
- `3738 chars: D=tb277/x960/aaa-2026-10-20T0825/T33408/work && sed -n '/>>> show log tail 200/,/>>> show boot/p' $D/post-u2.log | command grep -aE '2026 Oct 19 (20:[`
- `2460 chars: D=tb277/x960/aaa-2026-10-20T0825/T33408/work && tools/tb cfg tb277 ckaaa u2 115200 "configure terminal" "radius-server host 10.38.22.33 auth-port 1181`
- `2080 chars: D=tb277/x960/aaa-2026-10-20T0825/T33408/work && tools/tb tail tb277 /tmp/ckaaa/radsrv4.log 30 | tee $D/radsrv4-tail.log`
- `1654 chars: D=tb277/x960/aaa-2026-10-20T0825/T33408/work && tools/tb qmark tb277 ckaaa u2 115200 --mode "configure terminal" -- "aaa authentication login default"`

## Wasted input

Tool output read back off disk in this case: 33,905 characters. **This is high.** Extract what the step needs when the result first arrives, rather than re-reading the saved file.

## Repetition

None found in this case's own segment.

## Accuracy risks

- The `09:22:50 id=195` Access-Request/Accept pair and the `09:22:57 id=134 user='manager'` Reject pair exist **only in `run1.log`**. The saved server tails start at 09:26:02 and 09:27:16, so neither pair has a second copy.
- `show privilege -> "Current privilege level is 15"` and the post-removal `show radius -> "No RADIUS servers currently defined"` are prose in the working log with no transcript file behind them.
- The Message-Authenticator is abbreviated as `0x451a...` in the working log, so the final log carries the abbreviation. The full value is unrecoverable.
- `.cfg` capture time reads `09:31`, which is immediately before the step 9 removal batch, not after setup as `logged-output.md` §2 requires. The file's **contents** are correct for the configured state.

## Next run: expected outputs

The final log's STEP blocks hold this bench's measured value for every step. Compare against `T33408.log`, do not rediscover.

## Next run: scripts

Every helper this case used is already in `tools/` with a `tools/README.md` entry. Nothing was hand-built that is not catalogued.

## Next run: references

- `platforms/x960.md` -- this DUT family's measured behaviour, including the sections this campaign added.
- See [REVIEW.md](../REVIEW.md) for the findings that apply to the whole group.
