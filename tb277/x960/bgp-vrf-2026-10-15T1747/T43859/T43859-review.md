# T43859 process review -- bgp-vrf-2026-10-15T1747
Reviewed 2026-10-16 by /create-logs from `agent-ab60d6243d8eb4d8a.jsonl` and the working files.

## Token usage
| calls | cache read | cache write | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 30 | 8,331,568 | 60,326 | 250 | 30 | 20m 29s | 29,024 |

30 calls over 20m29s.

## Wasted input
- 29,024 chars read back; nothing conspicuously wasteful.

## Repetition
- None found.

## Accuracy risks
- **F-9, the finding that matters most in this campaign.** After `no ip route vrf red ...`, with the line gone from running-config and the RIB answering `% Network not in table`, 5/5 frames still crossed the VRF boundary — reproduced over three legs and ~2 minutes. The mechanism was pinned rather than guessed: a never-used host on the same /24 was correctly blocked 0/5, so the route really is gone and a stale ARP-derived per-host entry is what survives; `clear arp-cache vrf blue` stopped it at once. Cold-start isolation is complete, so the case is a PASS — but config and RIB agreeing that a path is closed while traffic flows is a security-relevant gap.
- The unaided lifetime of the stale entry was not measured; the log's CAVEAT says so.
- A direct VRF-to-VRF interface move is refused (`% vlan48: VRF is already associated`) although the guide describes it as supported.
- The working log is internally inconsistent on the total leg count (twelve vs fourteen), so the final log quotes every per-leg count and claims no total.

## Next run: expected outputs
- moving an interface between VRFs **strips its addressing**, in both directions and on VRF deletion — re-apply the address before deleting the VRF
- isolation: 5/5 global, 0/5 split across VRFs, 5/5 again with both SVIs in one VRF
- overlapping address: answers on two ports in two VRFs, each opposite capture empty
- `show ip route` renders a `[VRF: name]` section per VRF; `show arp vrf <name>` is VRF-aware
- inter-VRF static: the VLAN-only form works; the guide's 'must specify both' overstates it

## Next run: scripts
- None proposed.

## Next run: references
- The VRF-lite Feature Overview and Configuration Guide C613-22142-00 REV B — eight claims quoted and confirmed in this case's log.


---
Group-wide findings are in [REVIEW.md](../REVIEW.md) and are not repeated here.
Recommendations are the reviewer's; findings cite the transcript segment or working log they come from. A review never changes a verdict.
