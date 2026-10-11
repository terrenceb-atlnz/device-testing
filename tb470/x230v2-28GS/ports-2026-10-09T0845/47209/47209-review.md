# T47209 process review -- ports-2026-10-09T0845
Reviewed 2026-10-12 by /create-logs from `agent-a4163fdf23e120522.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 20 | 22,012 | 2,558,937 | 81 | 10 | 352 s | 17,804 chars |

The highest context per call of the group (~256k): the last case pays for everything read before it.

## Process taken
1. #1 step 1 on u0: pluggable detail + diagnostics, `show interface port1.0.4`, then `speed 100`, `speed 10`,
   `speed auto 100`, `speed 2500`, `speed 10000`, `duplex half`, `duplex full` (poll), `duplex auto` + `speed 1000`
   (poll), port detail and running-config.
2. #2 read back the pluggable block, diagnostics and status lines (2.1k).
3. #3 step 2: `speed 100` held; x230 and stack counters at t0 and t0+40 s, LLDP both ends, stack loop-protection.
4. #4 read back the LLDP and log lines.
5. #5 step 3: x230 back to auto + `show log`; control on the stack (`speed 100` on its SX port, back to auto).
6. #6 grep of the x230 log, 60 lines (5.8k).
7. #7 teardown reads + diffs. #8 `.cfg` + working log. #9 commit. #10 RESULT.

## Wasted input
- #6: 5.8k of `show log` lines (60 lines cut at 140 chars) for the window 19:19-19:23. The final log needs ~14 lines:
  `grep -E 'IMISH.*\](speed|duplex)|EXFX|NSM.*port1\.0\.4'` limited to 19:20:00-19:20:40 and 19:21:1x.
- #2: 2.1k read back of `show system pluggable detail` for one port; `show system pluggable` gives its row.

## Repetition
- none found (one call per step, files reused).

## Accuracy risks
- **The control is narrower than the Results reason.** The Results row says "the IE520 does the same (control)". The
  control (#5, 19:23:17) shows the IE520's SX port accepts `speed 100` and reads `connected 104 a-full 100`; it was
  reverted within 3 s, so whether frames stop on the IE520 was not measured. The final log says exactly that.
- **Frames at fixed 1000** rest on counters: input 2703 (auto, 19:19:59) -> 2707 (fixed 1000, 19:20:42) -> 2740
  (19:21:22, 8 s after `speed 100`, then flat). The +4 spans the 100 Mb/s window at 19:20:02-19:20:40, so the
  2707 -> 2740 rise is the clean proof. A 30 s hold at fixed 1000 with a counter read either side would be cleaner.
- run1.log's "probably shared AW+ code" is the tester's speculation; left out of the final log.
- The frames on the link are the stack's loop-detect frames and LLDP only (no traffic generator); enough to show
  "nothing received", but a known-rate stream (`tools/linerate.py` from eth1 through the stack) would quantify it.
- Unsourced claims left out of the final log: none (the post-restore counter 2835 and LLDP are in the teardown
  capture `td-u0.out`, quoted in STEP 1D as the control).

## Next run: expected outputs
| command on x230 port1.0.4 (AT-SPSX) | expected on this build |
| --- | --- |
| `speed 10`, `speed 2500`, `speed 10000` | `% port1.0.4: Unsupported speed/duplex combination port1.0.4`; log EXFX "Invalid request vs capabilities" for 10 |
| `duplex half` | `% Duplex set failed port1.0.4`; log EXFX "Failed to set the duplex mode on ifx 5004, rc 16" |
| `speed 100` / `speed auto 100` | accepted (the FAIL): `connected 104 a-full 100` / `a-full a-100`; input flat both ends; LLDP empty both ends; stack `a-full a-1000` |
| `speed 1000` | `connected 104 a-full 1000`, input rising |
| `speed auto` + `duplex auto` | `connected 104 a-full a-1000` in 1 read |
| `show system pluggable diagnostics` | "Diagnostics information is not supported by device" |

## Next run: scripts
- Proposed `tools/portmatrix.py` (../REVIEW.md) with `--counters 40` to read both ends' input/output counters before
  and after a hold; it would have made #3 one argument.

## Next run: references
- `platforms/x230v2-28GS.md` §2, the 1000BASE-SX `speed 100` row (this finding). A re-run on a new build should
  start from the expected-output table above.
