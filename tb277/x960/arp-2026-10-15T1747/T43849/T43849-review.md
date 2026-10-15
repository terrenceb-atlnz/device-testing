# T43849 process review -- arp-2026-10-15T1747
Reviewed 2026-10-16 by /create-logs from `agent-abaa4bf7d49aa5cc5.jsonl` and the working files.

## Token usage
| calls | cache read | cache write | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 916,706 | 17,009 | 14,404 | 3 | 0m 37s | 279 |

3 calls, 37s — the only case in the campaign with real authored step text (ck.db AWP-4357), and the cheapest of the six-case group relative to what it proved.

## Wasted input
- None found.

## Repetition
- None found.

## Accuracy risks
- The comparison 'with plain `ip proxy-arp` the same-subnet target drew zero replies in T43848' was dropped as cross-case. This case's own same-subnet boundary leg stands on its own.
- **The authored expected result is a ping that fails in BOTH states.** The discriminator is the *source* of the unreachable — `From 23.1.1.2` (the partner itself) vs `From 23.1.1.1` (the DUT). A tester grading this case on ping success alone would mis-grade it in either direction.

## Next run: expected outputs
- feature on: partner's `ping 23.1.1.3` fails 100% AND its ARP table holds `23.1.1.3 -> e01a.ead4.7043` (the DUT's MAC)
- crafted ARP: 0 replies off, 3 replies carrying the DUT's MAC on
- bounded by the DUT interface's own /24, not the neighbour's /16

## Next run: scripts
- None proposed.

## Next run: references
- ck.db keys on `AWP-nnnn`, not `AWPTCM-T<id>` — join on `title`. Memory `ckdb-case-lookup-by-title`.


---
Group-wide findings are in [REVIEW.md](../REVIEW.md) and are not repeated here.
Recommendations are the reviewer's; findings cite the transcript segment or working log they come from. A review never changes a verdict.
