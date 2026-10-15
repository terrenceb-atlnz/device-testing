# T43857 process review -- igp-2026-10-15T1747
Reviewed 2026-10-16 by /create-logs from `agent-a6f1baf6d4e3e024b.jsonl` and the working files.

## Token usage
| calls | cache read | cache write | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 52 | 8,688,536 | 90,196 | 443 | 52 | 29m 59s | 53,613 |

52 calls over 29m59s. 53,613 chars of tool output read back — the highest of any case in the campaign.

## Wasted input
- Largest outputs are a ck.db query (3,580 chars), a guide extract re-read from `/tmp` (2,985 chars) and multi-command `ckcon.py` batches (2,850 / 2,402 chars). The guide text was read into context twice.

## Repetition
- The service-gate discovery (start is asynchronous; `router ospf` is rejected ~1 s after `service ospf` and accepted within ~7 s) was worked out here and then re-derived in T43856. **It belongs in the group's setup section, written once.**

## Accuracy risks
- The daemon instrument `show process | include ospf` appears in this case only in the teardown table, so the final log carries no `show process` line. **Put the daemon read in a graded step, not in teardown.**
- Partner-side port numbers for the vlan41/vlan61 links are nowhere in the working log, so the topology labels DUT-side ports only.

## Next run: expected outputs
- adjacency Full to two neighbours in ~17 s after the gate clears
- routes as code `O`, AD 110, each carried by the owning partner's Router LSA in the LSDB
- withdrawal with link/port/adjacency up: subject 0/5 in under 7 s, second neighbour 5/5 in the same leg
- `passive-interface`: 0 OSPF packets in 30 s while the neighbour's held LSA still carries the network
- reload: back in ~61 s

## Next run: scripts
- None proposed; `arpleg.py --icmp` carried all legs.

## Next run: references
- Memory `awplus-service-gated-routing-daemons`, and `platforms/x960.md` §7A for the measured gate timings.


---
Group-wide findings are in [REVIEW.md](../REVIEW.md) and are not repeated here.
Recommendations are the reviewer's; findings cite the transcript segment or working log they come from. A review never changes a verdict.
