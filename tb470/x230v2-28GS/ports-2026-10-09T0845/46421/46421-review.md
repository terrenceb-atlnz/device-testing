# T46421 process review -- ports-2026-10-09T0845
Reviewed 2026-10-12 by /create-logs from `agent-a4163fdf23e120522.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 27 | 54 | 51,079 | 4,057,339 | 784 | 29 | 502 s | 36,383 chars |

The most expensive case of the group, but about a third of it is group work counted here (#1-#10, below).

## Process taken
1. #1-#6 group setup inside this segment: create all five cases' `work/`, edit the queue's run row and NOT TESTED
   titles, `git diff` check, commit (queue + bench-state).
2. #7-#10 read `tools/ckcon.py` and `tools/console.py` source (2.6k + 10.2k), add the `@sleep` / `@poll` directives,
   add the README entry.
3. #11 step A attempt 1: stopped at its 4th command, `show log tail 5` ("% Invalid input"); nothing changed.
   #12 `tail` of the output to see why.
4. #13 step A: 12 local flaps (u0), stdout `stepA-u0.out`.
5. #14-#16 read back poll results, status lines, NSM log lines, counts per port, LLDP (6.5k + 1.3k + 0.2k).
6. #17 step B: 9 remote flaps from the stack (u5). #18 x230 status/log/LLDP/running-config. #19 grep step B's log
   lines and `rcdiff.py` both units.
7. #20-#23 read bench-state + another group's `.cfg` header for the header format, `rc2cfg.py` both `.cfg`s, fix
   the capture time.
8. #24-#26 working log (heredoc), #27 commit, #28-#29 RESULT.

## Wasted input
- #8: 10.2k of ckcon.py / console.py source to add the `@poll` directive. A one-off tool change, worth it (every
  later case used `@poll`), but it belongs to group overhead, not this case.
- #14: 6.5k read back from `stepA-u0.out` (every @poll line, status lines and the whole log window) when #15's
  per-port down/up counts (1.3k) carried the verdict. One `grep -c` per port plus the four final status lines would
  have done.
- #20: 1.7k of bench-state and another group's `.cfg` header, to copy the `.cfg` header format; the format is in
  logged-output.md §2.

## Repetition
- #11/#13: step A sent twice because attempt 1 used `show log tail 5`, which the x230 lacks. Recorded below.

## Accuracy risks
- The `show log` quotes are filtered to port lines; the log also prints "Port down/up notification received for
  vlanN" lines for each flap (seen in step B). The per-port counts (3 down / 3 up each) are from the port lines only.
- Convergence times are poll-granular (each read ~1.2 s), so "4.5 s (3 reads)" means 3.3-4.5 s, not a measurement.
- port1.0.5 was flapped locally only (its partner is a host NIC); the case's "supported speed" was 1000 only.
- Unsourced claims left out of the final log: none.

## Next run: expected outputs
| step | expected on this bench |
| --- | --- |
| baseline | port1.0.2/1.0.3/1.0.4/1.0.5 `connected` `a-full a-1000` in VLAN 1/103/104/105; LLDP 3 neighbours, chassis 0000.cd37.0d6f on 1.0.2/1.0.3/1.0.4 |
| `shutdown` | status `disabled ... auto auto` at the first read (1.2 s); log `Port down notification received for portX` + `portX user shutdown` |
| `no shutdown` | copper back at `connected a-full a-1000` in 3 reads (4.5 s), SX in 1 read; log `portX user no shutdown` then `Port up notification received for portX` 3-5 s later (copper), <=1 s (SX) |
| remote flap (stack shut) | x230 log `Port down` / `Port up notification` only (no "user shutdown" line); stack port back `a-full a-1000` |

## Next run: scripts
- `tools/ckcon.py` `@poll` (now in tools/) for the flap loop; a counter such as the proposed `tools/flapcount.py`
  (../REVIEW.md, Next run: scripts) would replace #14-#16 and #19.

## Next run: references
- `show log`, never `show log tail` (x230). ../REVIEW.md "Next run: references" for the bench link map and clocks.
