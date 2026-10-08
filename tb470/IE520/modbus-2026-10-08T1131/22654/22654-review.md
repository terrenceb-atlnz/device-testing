# T22654 process review -- modbus-2026-10-08T1131
Reviewed 2026-10-08 by /create-logs from `agent-a819940a509fabe68.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 9 | 18 | 29,455 | 2,426,928 | 6,264 | 9 | 298 s | 31,726 chars |

The most expensive case after T22650: three separate step runs, each echoing ~8-10k chars.

## Process taken
1. #1 wrote `22654.sh` (setup | s1..s5 | teardown).
2. #2 setup + s1 (10,550 chars back); #3 s2 + s3 (8,789); #4 s4 + s5 (7,897).
3. #5 `grep` of the DUT log lines for the step times (3,174); #6 teardown + `rcdiff.py`.
4. #7 working log; #8 `.cfg` check + queue + commit; #9 RESULT.

## Wasted input
- #2-#4 printed every step's full output back (27k chars together), and #5 then grepped the same
  file for the log lines. One run of all steps to `22654.out`, then one `grep` for the RESULT
  lines and the modbusd/NSM log lines, would have cost ~5k and two calls fewer.

## Repetition
- The step split (s1 / s2+s3 / s4+s5) made three round trips where one would do. Splitting is
  only worth it when a later step depends on reading an earlier one, which none did here.

## Accuracy risks
- **The case's "bit 0 = LED" is the MSB (0x8000) on this DUT.** 0x0001 is acknowledged (FC06
  echo) and logged "Performed write request" yet changes nothing. A client cannot tell. Recorded
  for the case owner.
- Steps 2, 4 and 5 vary only the enabled nibble, on port1.0.1 (an empty cage). Duplex, polarity
  and speed were always written as auto.
- The DUT clock is ~50 s ahead of tb470; DUT log times and host times differ by that (recorded).
- Step 3's exception type was inferred from counters (../REVIEW.md, `mb.py`).

## Next run: expected outputs (this bench)
| step | write | expected |
| --- | --- | --- |
| 1 alarm config | unit 1 0x3001 = 0x8000 | read-back `8000`; `show alarm facility settings` External PSU 1 `L` on member 1; running-config `alarm facility power-supply 1 input-member 1 led`; log "Performed write request ... data 0x8000". Then 0x0000 clears it |
| 1 (literal) | 0x3001 = 0x0001 | ok echo, read-back `0000`, no CLI change |
| 2 port state | unit 1 0x5001 = 0x0000 / 0xf000 | read-back follows; CLI "administrative state is DOWN"/"UP"; log `NSM ... port1.0.1 user shutdown` / `no shutdown` |
| 3 PoE | 0x5002 = 0xff00 | exception; `show power-inline` = `% Invalid input` -> UNSUPPORTED |
| 4 global IPv6 | as step 2 via `fd32:b1f0:dff8:d701::10` (temporary vlan1 address) | ok; log source `fd32:b1f0:dff8:d701::1` |
| 5 link-local | as step 2 via `fe80::200:cdff:fe37:d6f%eth1` | ok; log source `fe80::f667:7041:7dff:3cfc` |

## Next run: scripts
- `tools/mbplan.py` (proposed) with `write` lines and a `log-regex` column, so "relevant log
  generated" is checked by the script against `show log`.

## Next run: references
- `platforms/IE520.md` §3 Modbus row (LED = 0x8000, unmapped bit acknowledged, no PoE).
