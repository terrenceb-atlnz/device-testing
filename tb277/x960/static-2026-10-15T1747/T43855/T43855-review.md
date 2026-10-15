# T43855 process review -- static-2026-10-15T1747
Reviewed 2026-10-16 by /create-logs from `agent-aeb89f5d96391104b.jsonl` and the working files.

## Token usage
| calls | cache read | cache write | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 33 | 6,065,980 | 48,470 | 377 | 33 | 17m 49s | 17,774 |

33 calls over 17m49s — the group's first case, carrying the shared B/C/D underlay build.

## Wasted input
- The largest outputs are `ckcon.py` console batches (1,433 / 1,162 chars) echoing configuration already known from the script that sent it.

## Repetition
- The underlay build is charged to this case but serves B, C and D. Read the group's setup section once, not per case.

## Accuracy risks
- **`show ip route <address>` prints the non-selected route**, so a tester grading a floating static on that command alone reads it exactly backwards. The case measured the FIB instead.
- **`swi_a.cfg` is missing from this case folder** although swi_a carries the floating-backup proof. It was never saved and cannot be reconstructed now the bench is restored.

## Next run: expected outputs
- 5/5 forwarded with the route, 0/5 at baseline and 0/5 after `no ip route`
- removal in the FIB: `% Network not in table`
- distance 255: in the RIB, never in the FIB
- floating static: egress port moves, attributed by the partner's own ICMP unreachables

## Next run: scripts
- None proposed; `arpleg.py --icmp` carried every leg.

## Next run: references
- The queue's corrected SVI-removal recipe: `no interface vlanN` is refused on this build; ports out of the VLAN first, then the address, then `vlan database` / `no vlan N`.


---
Group-wide findings are in [REVIEW.md](../REVIEW.md) and are not repeated here.
Recommendations are the reviewer's; findings cite the transcript segment or working log they come from. A review never changes a verdict.
