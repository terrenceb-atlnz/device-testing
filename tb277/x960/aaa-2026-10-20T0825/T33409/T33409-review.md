# T33409 process review -- aaa-2026-10-20T0825
Reviewed 2026-10-20 by /create-logs from the tester's transcript and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 36 | 72 | 45,148 | **11,272,631** | 415 | 36 | 774 s | 30,281 |

## Process taken

36 tool calls in 774 s. The largest single reads were:

- `2855 chars: D=tb277/x960/aaa-2026-10-20T0825/T33409/work && echo "=== upstream leg (ports 11812/11813), secret testing456 ===" && tools/tb tool tb277 ckaaa radwir`
- `2598 chars: D=tb277/x960/aaa-2026-10-20T0825/T33409/work && sed -n '/>>> show log tail 150/,/>>> show boot/p' $D/post-u2.log | command grep -aE '2026 Oct 19 (20:3`
- `2525 chars: D=tb277/x960/aaa-2026-10-20T0825/T33409/work && echo "=== NAS leg (ports 1812/1813), secret testing123 ===" && tools/tb tool tb277 ckaaa radwire /tmp/`
- `2128 chars: D=tb277/x960/aaa-2026-10-20T0825/T33409/work && { echo "=== P1: matching realm -- must be proxied to the upstream and Accepted ==="; tools/tb tool tb2`
- `1711 chars: D=tb277/x960/aaa-2026-10-20T0825/T33409/work && tools/tb qmark tb277 ckaaa u2 115200 --mode "configure terminal" "radius-server proxy-server" -- "rule`

## Wasted input

Tool output read back off disk in this case: 30,281 characters. **This is high.** Extract what the step needs when the result first arrives, rather than re-reading the saved file.

## Repetition

None found in this case's own segment.

## Accuracy risks

- Step 6's A/B pair (`id=213 Proxy-State='209'` and `id=40 user='radclient1@example.com' Proxy-State='108'`) carries the `nostrip` conclusion and exists **only in `run1.log`** — the saved server tail stops at 09:42:36.
- Step 4's cross-check (`valid=0 invalid=5 unpaired=0` under the wrong secret) is the single most load-bearing measurement in the case and has no saved artefact; the two `wire-*.txt` files hold the other two decodes.
- `.cfg` captured at 09:45, after step 6's rule restore rather than after setup. Contents are correct for the configured state.

## Next run: expected outputs

The final log's STEP blocks hold this bench's measured value for every step. Compare against `T33409.log`, do not rediscover.

## Next run: scripts

Every helper this case used is already in `tools/` with a `tools/README.md` entry. Nothing was hand-built that is not catalogued.

## Next run: references

- `platforms/x960.md` -- this DUT family's measured behaviour, including the sections this campaign added.
- See [REVIEW.md](../REVIEW.md) for the findings that apply to the whole group.
