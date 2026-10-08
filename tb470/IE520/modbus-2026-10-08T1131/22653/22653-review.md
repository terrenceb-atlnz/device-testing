# T22653 process review -- modbus-2026-10-08T1131
Reviewed 2026-10-08 by /create-logs from `agent-a819940a509fabe68.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 6 | 12 | 12,443 | 1,492,871 | 4,360 | 6 | 139 s | 8,486 chars |

## Process taken
1. #1 cloned `22653.sh` from T22651's by `sed`; #2 ran setup + steps + teardown in one ssh (6,748 chars back).
2. #3 `awk` for the port1.0.1 CLI block; #4 working log; #5 queue + commit; #6 RESULT.

## Wasted input
- none significant.

## Repetition
- The driver was cloned by `sed` again (see T22652's review and ../REVIEW.md).

## Accuracy risks
- **The case's port #1 (port1.0.1) is an empty SFP cage**, so steps 1, 6 and 7 can only read
  zero/down. The tester added linked ports port1.0.2 and port3.0.13 as a control, which is what
  makes the PASS meaningful. Next time make the control part of the plan, not an extra.
- Step 7's text says "Input Bytes" at 0x5009, which is the output counter. Graded as output; a
  case-text error for the owner.
- Exception types for the PoE registers were inferred from the server counters (`mb.py` does not
  print the code; ../REVIEW.md).
- The working log explains port1.0.2's +500 output bytes as LACP/LLDP. That is unsourced (the port is in a static
  channel group), and the final log left it out.
- Step 2 only ever read `f000`: every port is configured auto/auto/auto. A non-default configured
  state (e.g. a fixed speed) was never read back.

## Next run: expected outputs (this bench; port N of member M at unit M, 0x5000 + 13*(N-1))
| step | port1.0.1 (unit 1 0x5000..) | port1.0.2 (0x500d..) | port3.0.13 (unit 3 0x509c..) |
| --- | --- | --- | --- |
| 1 current state | `0000` | `f103` (up, full, auto, 1000) | `f103` |
| 2 configured state | `f000` | `f000` | `f000` |
| 3-5 PoE | exception | exception | exception |
| 6 input bytes (4 words) | 0 | = CLI input bytes | = CLI (grows: carries the Modbus traffic) |
| 7 output bytes (4 words) | 0 | = CLI output bytes | = CLI |
| - whole 13-word block read | exception (spans the PoE words) | | |

## Next run: scripts
- `tools/mbplan.py` (proposed) with a port-index helper (`--port 1.0.2` -> unit 1, 0x500d).

## Next run: references
- `platforms/IE520.md`: "first copper port is x.0.2" and the Modbus row (no PoE).
