# T22651 process review -- modbus-2026-10-08T1131
Reviewed 2026-10-08 by /create-logs from `agent-a819940a509fabe68.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 10 | 11,784 | 1,127,864 | 3,667 | 5 | 103 s | 9,797 chars |

The leanest case of the group: one call wrote and ran the whole driver.

## Process taken
1. #1 wrote `22651.sh` and ran setup + reads + teardown in one ssh (8,983 chars back).
2. #2 pulled the statistics lines from `22651.out` with `awk`/`grep` (506 chars).
3. #3 working log; #4 queue update + commit; #5 RESULT.

## Wasted input
- #1's 8,983 chars of output could have been a summary; small. none otherwise.

## Repetition
- none found.

## Accuracy risks
- **Only status 0 ("Ok") was seen.** No sensor was in fault, so the fault-status encoding for a
  real fault is unverified. A Power Input that reads "No" is still status Ok.
- The case's own step text is not in the working log (item names only), so the final log could
  not quote it.

## Next run: expected outputs (this bench)
| step | register (unit = member) | member 1 / 3 / 4 |
| --- | --- | --- |
| 1 #1 Sensor Type | 0x1000 ENUM | 2 / 2 / 2 (temperature) |
| 2 #1 Sensor Reading | 0x1001 x2 FLOAT (big-endian) | ~48.0 / ~42.0 / ~44.0 = `show system environment` Temp |
| 3 #1 Sensor Units | 0x1003 ENUM | 2 (Degrees C) |
| 4 #1 Fault Status | 0x1004 | 0 (Ok) |
| 5 #2 sensor | 0x1005-0x1009 | type 11 (LED Output), 0.0, units 0, status 0 |
| - | 0x1019 (sensor 6) | exception (5 sensors per member) |

Temperatures drift; grade against the CLI read in the same minute, not these numbers.

## Next run: scripts
- `tools/mbplan.py` (proposed) with a `cli-regex` column pulling the Temp line per member.

## Next run: references
- `platforms/IE520.md` §3 Modbus row. To exercise a real fault status, the Test Engineer would need
  to pull a power input or force a temperature threshold; ask, don't improvise.
