# T31858 process review -- platform-2026-10-09T0845
Reviewed 2026-10-12 by /create-logs from `agent-a591963d08f049547.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 9 | 18 | 13,405 | 1,271,564 | 70 | 9 | 299 s | 7,352 chars |

Segment #41-#49 (18:05:42-18:10:41), bounded by the T47226-batch and T31858 RESULT messages.
`case_tokens.py` gave it 3 calls (it started the case at #47, the first call naming `31858/`).
Of the 299 s, 163 s was the reload.

## Process taken
1. #41 set value computed on the host (true UTC, +10 s), then one ckcon call: show clock, show
   running-config, show boot, `clock set 05:05:52 9 Oct 2026`, show clock (`clk1.out`).
2. #42 `tools/tb ckreload tb470 x230plat-1800 u0 115200 720` (163 s to login).
3. #43 show clock, show system, show reboot history, then the VLAN 103-105 isolation, show vlan brief.
4. #44 clock restored to NZ wall time + `rcdiff.py` -> `-lldp run`; #45 `lldp run` re-added, diff empty.
5. #46-#47 `.cfg`, work files, working log written then spliced with the step-1 sequence (awk + python).
6. #48 `lldp run` added to the queue's restore recipe; #49 RESULT.

## Wasted input
none found (largest read 2,614 chars, #43).

## Repetition
- #46 then #47: the working log was written, then re-opened to splice the step-1 command sequence in.
  One pass with a block extractor (proposed `tools/wlog.py`, ../REVIEW.md) would do.

## Accuracy risks
- The verdict rests on printed output: set 05:05:52 at tb470 18:05:52, read 05:09:01 at tb470
  18:09:02 after the reload (3 m 09 s on the DUT, 3 m 10 s on tb470), uptime 0:02:36, reboot history
  `2026-10-09 05:06:04 Expected CLI(user request)`. A strong positive proof (13 h step from baseline).
- The restore set the clock back to NZ wall time by hand (`date +8 s`), so after this case the DUT
  clock is within ~2 s of tb470 instead of the original 54 s behind. Harmless, but later cases' clock
  offset differs from T47226's recorded one.

## Next run: expected outputs
| step | command | expected on this bench |
| --- | --- | --- |
| 0 | `show clock` | `UTC Time: ...` = NZ wall time (no timezone set) |
| 1 | `clock set <UTC hh:mm:ss> <d> <Mon> <yyyy>` then `show clock` | no output; show clock = the set value +1 s |
| 2 | `reload` (y) | login after 163-168 s |
| 2 | `show clock` | set value + elapsed (within 1 s of tb470's elapsed) |
| 2 | `show reboot history` | top line `<today> <set time + ~12 s> Expected   CLI(user request)` |
| after | `rcdiff.py` pre vs post | `-lldp run` unless re-added (../REVIEW.md cross-case 4) |

## Next run: scripts
- Existing and fitting: `tools/ckreload.py` (the reload), `tools/rcdiff.py` (teardown diff).
- Put the post-reload restore (VLAN 103-105 + `lldp run`) in one `cfg.py` file (../REVIEW.md).

## Next run: references
- platforms/x230v2-28GS.md §1 (reload time; reload drops `lldp run`).
