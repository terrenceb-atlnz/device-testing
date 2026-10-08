# T22652 process review -- modbus-2026-10-08T1131
Reviewed 2026-10-08 by /create-logs from `agent-a819940a509fabe68.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 6 | 12 | 11,805 | 1,420,968 | 3,703 | 6 | 113 s | 10,430 chars |

## Process taken
1. #1 built `22652.sh` by `sed` from T22651's script (ID, title, then the reads).
2. #2 patched a quoting bug in the cloned script (`show interface status | include ...`) and ran it (7,954 chars back).
3. #3 `grep` for the Link-down alarm reads; #4 working log; #5 fixed the script's usage line + queue + commit; #6 RESULT.

## Wasted input
- none significant.

## Repetition
- **The driver was cloned from the previous case's script and patched twice** (#1, #2, and a
  leftover "Usage: bash 22651.sh" fixed in #5). A plan-driven runner removes the clone-and-patch
  step and its bugs (`tools/mbplan.py`, ../REVIEW.md).

## Accuracy risks
- The case's addresses 0x3600-0x3602 are the older map and answer an exception. The steps were
  graded at MV5 0x3000/0x3001/0x3005. That this DUT is MV5 is sourced from T22650's read of 0x0000, not
  from a read in this case: read 0x0000 in every case that grades at MV5 addresses.
- Step 2 only saw config 0x0000. A live config word (0x8000 = LED) is covered by T22654.
- Status semantics: 0x3005 is the inverse of the CLI's "Power Input 1" (alarm present where the
  input is absent). The working log's reading, consistent on all three members.

## Next run: expected outputs (this bench)
| step | register (unit = member) | member 1 / 3 / 4 |
| --- | --- | --- |
| case literal | 0x3600 / 0x3601 / 0x3602 | exception |
| 1 #1 Alarm Type | 0x3000 ENUM | 1 / 1 / 1 (External PSU) |
| 2 #1 Alarm Configuration | 0x3001 HEX | `0000` (CLI Outputs "-") |
| 3 #1 Alarm Status | 0x3005 BOOL | False / True / False (= Power Input 1 Yes / No / Yes) |

## Next run: scripts
- `tools/mbplan.py` (proposed) -- `22652.plan`; no `sed` cloning.

## Next run: references
- `platforms/IE520.md` §3 Modbus row (6-word alarm entries, status at +5).
