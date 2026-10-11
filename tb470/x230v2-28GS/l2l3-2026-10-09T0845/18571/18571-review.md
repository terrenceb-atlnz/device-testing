# T18571 process review -- l2l3-2026-10-09T0845
Reviewed 2026-10-12 by /create-logs from `agent-a416990ee48b8b1f0.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md). Call numbers are this segment's (after the
T18570 RESULT up to this case's RESULT).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 20 | 16,842 | 2,316,438 | 6,439 | 10 | 387 s | 6,901 chars |

## Process taken
1. #1 x230 setup (VLAN 106, port1.0.3 shut, `channel-group 12 mode active`, po12 trunk) (1,098).
2. #2 stack setup on u5 (port1.0.2 out of sa2, po12 with port1.0.17, trunk, port3.0.13 into 106) (497).
3. #3 x230 port1.0.3 up, `@poll` (correct this time), etherchannel detail, lacp-counter, LLDP,
   running-config, counters (1,532).
4. #4 stack capture: running-config, status, etherchannel detail, log (734). `rc2cfg.py` x2.
5. #5 three linerate runs with counters between, then etherchannel detail and lacp-counter (2,119).
6. #6-#7 loop-safe teardown + two `rcdiff.py` (193 + 366). #8 working log. #9 commit. #10 RESULT.

## Wasted input
none found.

## Repetition
- The case is T18570 with `channel-group 12 mode active` in place of `static-channel-group 2`;
  every setup and teardown list was typed in full again (REVIEW.md: plan-file driver).

## Accuracy risks
- **"1522 tagged on the trunk"**: as in T18570, not measured by a tool and left out of the final
  log. The x230 byte counters give 1521.99 B/frame out on both members in run A, 1521.99 / 1521.84
  in on port1.0.2 / port1.0.3 in run B, and 1518.000 on the access port: the tag is there.
- **LACP stability under load** rests on two reads, before (LACPDUs 14/8, 6/5) and after (18/12,
  10/9) with "synchronized" both times; there is no continuous watch during the 30 s of traffic.
  The x230 log tail across the runs (IMISH echoes only, no port-down) supports it.
- **No Ixia**, small frames not sent (CAVEAT in the log).

## Next run: expected outputs (this bench, this build)
| check | expected |
| --- | --- |
| x230 `show etherchannel detail` | `Receive link count: 2 - Transmit link count: 2`, `Partner LAG: 0x8000,00-00-cd-37-0d-6f,0x000c`, both links `synchronized` |
| stack `show etherchannel detail` | `Partner LAG: 0x8000,00-c2-8f-3f-0f-5d,0x000c`, port1.0.2 and port1.0.17 `synchronized` |
| link-up | `@poll MATCHED after ~3.2 s`; x230 log "Port up notification received for po12" ~40 s before port1.0.3 comes up |
| run A / B / C | 812501 / 812501 / 822501 frames, 100% at exact length, 999.4-999.8 Mbps |
| member split | ~406.25k per member each way; trunk ~1522 B/frame |

## Next run: scripts
- As T18570; the two cases could share one plan file with the aggregator lines as a parameter.

## Next run: references
- T18570's log and review (same topology, static aggregator).
