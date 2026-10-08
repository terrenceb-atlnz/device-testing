# T22655 process review -- modbus-2026-10-08T1131
Reviewed 2026-10-08 by /create-logs from `agent-a819940a509fabe68.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 6 | 12 | 20,126 | 1,766,795 | 4,866 | 6 | 285 s | 17,650 chars |

Wall time is mostly deliberate waits (5-10 s after each port change for link and register to settle).

## Process taken
1. #1 wrote `22655.sh` and ran the precondition + steps 1-2 (3,357 chars back).
2. #2 steps 3-4 (12,345 chars back); #3 teardown + `rcdiff.py`.
3. #4 working log; #5 queue + commit; #6 RESULT.

## Wasted input
- #2 printed 12k chars, including the full `show log` tail twice. Grep the run file for the
  `NSM`/`modbusd` lines and the READ/WRITE results instead (~3k).

## Repetition
- none found within the case.

## Accuracy risks
- **"Exception 4" is inferred**, from the server's slave-device-failure counter (+2 over the two
  port1.0.2 writes). The client printed only `Exception response 134 / 0`. The final log says so.
  `mb.py` printing the exception code would make this direct (../REVIEW.md).
- **Every linked stack port reachable here is an aggregator member** (port1.0.2 in sa2;
  port3.0.13 is the client's own link and cannot be shut). So step 3's change is applied but
  answered with an exception, and three `Failed to set Auto duplex/polarity/speed` lines are
  logged. The control on port1.0.1 answers ok but has no link. A linked, non-LAG port would make
  step 3 clean. That is a bench change (cable, or `no static-channel-group` on port1.0.2 for the case), so
  it is the Test Engineer's call.

## Next run: expected outputs (this bench)
| step | action | expected |
| --- | --- | --- |
| precondition | enable + `access read-write`; unit 0 0x0000 | 5 |
| 1 port change | `scada modbus tcp server port 5020` | :502 refused, :5020 ok (0x0000 = 5); log "Modbus server TCP Port changed to 5020."; `no ... port` restores 502 |
| 2 disable/enable | `no scada modbus tcp server` / `scada modbus tcp server` | refused / ok; `access read-write` kept |
| 3 API port | unit 1 0x500e = 0x0000 then 0xf000 (port1.0.2) | exception (code 4) BUT applied: 0x500d `0000` -> `f103`, CLI DOWN/UP, NSM user shutdown / no shutdown, 3x "Failed to set Auto ..." |
| 3 control | unit 1 0x5001 on port1.0.1 | ok echo, applied |
| 4 CLI port | `shutdown` / `no shutdown` on port1.0.2 | 0x500d/0x500e `0000`/`0000` then `f103`/`f000` within 10 s |

## Next run: scripts
- `tools/mbplan.py` (proposed) with `cli` and `sleep` lines so the waits and the CLI actions are in the plan.

## Next run: references
- `platforms/IE520.md` §3 rows: Modbus (exception 4 on aggregator members) and `polarity` refused
  on aggregator members (the same LAG constraint).
