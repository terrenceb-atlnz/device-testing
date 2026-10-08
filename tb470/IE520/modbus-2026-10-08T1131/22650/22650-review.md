# T22650 process review -- modbus-2026-10-08T1131
Reviewed 2026-10-08 by /create-logs from `agent-a819940a509fabe68.jsonl` and the working files.
Group-wide findings (overhead, `mb.py` exception codes, driver per case, eth1 MAC): [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 20 | 27,397 | 2,047,760 | 6,152 | 10 | 172 s | 33,688 chars |

## Process taken
1. #1 created all six case folders and wrote `22650.sh` (setup | reads | teardown).
2. #2 copied the new `rc2cfg.py` to the box. #3 ran setup (baseline, enable server).
3. #4 one ssh: `rc2cfg.py` -> `stk_a.cfg`, the CLI reference block, all 40 Modbus reads, statistics.
4. #5 teardown + `rcdiff.py`. #6 copied the outputs into the case folder.
5. #7 wrote the working log; #8-#9 added `rc2cfg.py` to tools/README.md; #10 RESULT.

## Wasted input
- #4 printed its whole run back into the context: 28,967 chars (full `show system`, environment,
  alarm settings, 40 reads with 32-word lists). It was already tee'd to `22650.out`. Printing a
  summary (`grep -a -E 'READ|EXCEPTION|Number|Alarms'` plus the four CLI lines graded) would have
  cost ~3k.

## Repetition
- none found within the case (one driver, one run).

## Accuracy risks
- The case text's addresses are the version-1 map. Each item was graded at its MV5 address, by
  item name. The case's own expected values are not in the working log, only the item names.
- What 0x0065 and 0x0085 hold under MV5 is not recorded (read, exception / `000000050000`, not explained).
- Step 5's FAIL rests on the CLI count of 31 alarms per member (93) vs 0x0049 = 124. Solid
  evidence; whether a provisioned slot SHOULD count is the case owner's question.

## Next run: expected outputs (this bench, main-calanm)
| step | register (MV5, unit 0) | expected |
| --- | --- | --- |
| 1 Mapping Version | 0x0000 x1 | 5 |
| 2 Board Name | unit 1/3/4 0x0202 x32 ASCII | `AT-IE520-28GSX` |
| 3 Serial Number | unit 1/3/4 0x0222 x32 ASCII | 264A23061 / 264A23066 / 264A23052 |
| 4 Number of Sensors | 0x0047 | 15 (3 x 5) |
| 5 Number of Alarms | 0x0048 / 0x0049 | 4 / **124 while member 2 is provisioned** (CLI 93); 93 if `no switch 2 provision` |
| 6 Number of Ports | 0x0045 | 84 (3 x 28) |
| 7 Number of Faults | 0x0046 | 0 |
| 8 Software Version | 0x0021 x32 ASCII | `main-calanm` (whatever `show system` says) |
| 9 System Name | 0x0001 x32 ASCII | `IE520-stk` |
| 10 HW MAC | 0x0041 x3 HEX | `0000cd370d6f` (the virtual MAC) |
| - | unit 2 anything | exception |

## Next run: scripts
- `tools/mbplan.py` (proposed, ../REVIEW.md) with the table above as `22650.plan`.

## Next run: references
- `platforms/IE520.md` §3 Modbus row; `../REVIEW.md` register map notes. Ask the Test Engineer
  first whether member 2's provisioning is to stay (it decides step 5).
