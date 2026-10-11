# T18570 process review -- l2l3-2026-10-09T0845
Reviewed 2026-10-12 by /create-logs from `agent-a416990ee48b8b1f0.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md). Call numbers are this segment's (after the
T38295 RESULT up to this case's RESULT).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 13 | 26 | 22,244 | 2,753,518 | 6,793 | 13 | 458 s | 8,973 chars |

## Process taken
1. #1 extended `tools/linerate.py` with `--mac-prefix` (so the two directions never share a source MAC).
2. #2 x230 setup (VLAN 106, port1.0.3 shut, sa2 built as a trunk, port1.0.5 into 106) (1,163).
3. #3 stack setup on u5 (VLAN 106, port1.0.17 into sa2, trunk, port3.0.13 into 106) (1,169).
4. #4 x230 port1.0.3 `no shutdown` + an `@poll` with the command written `show\sinterface\sbrief`:
   sent literally, refused for 30 s, exit 3 (440).
5. #5 the same poll re-sent correctly + aggregator / LLDP / running-config / counters (735).
6. #6 stack running-config, status, log (1,475). `rc2cfg.py` for both .cfg files.
7. #7 three linerate runs (A, B reverse, C 1500) with x230 counters between them (1,558).
8. #8 grep of the four counter files for the per-member deltas (1,148).
9. #9-#10 loop-safe teardown (x230 port1.0.3 shut, stack, x230) + two `rcdiff.py` (37 + 534).
10. #11 working log. #12 README for `--mac-prefix`. #13 RESULT.

## Wasted input
- #4: 30 s of polling and one extra call, caused by the `@poll` command being written with `\s`
  in place of spaces. It also left eight `user.err ... Command [show\sinterface\sbrief] failed`
  lines in the x230 log, which then sit in every log tail read before the traffic. Cause and fix
  in REVIEW.md (the ckcon README wording).

## Repetition
none found within the case. The setup and teardown command lists were typed out in full, as in
T18571 (REVIEW.md: a plan-file driver).

## Accuracy risks
- **"1522 bytes tagged on the trunk"** (working log) was not measured by any tool and is left out
  of the final log, which proves "no 4-byte deficit" end to end (exact length at the far access
  port). **The x230's own byte counters, already quoted in the log, do measure it:** bytes / packets
  per run on the access port and on the trunk members:

  | run | x230 port1.0.5 | x230 port1.0.2 | x230 port1.0.3 |
  | --- | ---: | ---: | ---: |
  | A 1518 eth3->eth1 | in 1518.000 B/frame | out 1521.993 | out 1521.993 |
  | B 1518 eth1->eth3 | - | in 1522.000 | in 1521.843 |
  | C 1500 eth3->eth1 | - | out 1503.997 | out 1503.997 |

  So the trunk carries each frame 4 bytes longer (the 802.1Q tag) and the access port gets it back
  at 1518. This is the reviewer's arithmetic, not the tester's; if the Test Engineer wants it in
  the final log, it is two lines in STEP 1's table, from figures the log already quotes.
- **No Ixia**: tcpreplay with 64 rotating source MACs stands in (CAVEAT in the log). Small frames
  were not sent.
- **Stack member serials** in TOPOLOGY come from the stk_a.cfg header order (members 1/3/4); the
  working log names no member-to-serial mapping.

## Next run: expected outputs (this bench, this build)
| check | expected |
| --- | --- |
| x230 `show static-channel-group` | `Static Aggregator: sa2` members port1.0.2, port1.0.3 |
| stack `show static-channel-group` | sa2 = port1.0.2, port1.0.9, port1.0.17 |
| `show vlan brief` (x230) | `106 VLAN0106 STATIC ACTIVE sa2(t) port1.0.2(t) port1.0.3(t) port1.0.5(u)` |
| link-up | `@poll MATCHED after ~1.4 s` on `port1\.0\.3\s+-\s+connected` |
| run A / B / C | 813001 / 812501 / 822501 frames, 100% at exact length, 999.6-999.8 Mbps on the wire |
| member split | ~406.5k / 406.5k per member each way (50/50); trunk 1522 B/frame, access 1518 |

## Next run: scripts
- `tools/linerate.py --src-macs 64 --mac-prefix 02:cc:00:00` / `02:cd:00:00` as used.
- Proposed `tools/ifdelta.py` (REVIEW.md) would print the member split and the B/frame above.

## Next run: references
- T18571 (the same topology with LACP) and REVIEW.md's loop-safe teardown order.
