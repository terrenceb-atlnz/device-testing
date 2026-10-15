# T43856 process review -- igp-2026-10-15T1747
Reviewed 2026-10-16 by /create-logs from `agent-a6f1baf6d4e3e024b.jsonl` and the working files.

## Token usage
| calls | cache read | cache write | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 44 | 11,381,671 | 75,365 | 383 | 44 | 34m 51s | 36,831 |

44 calls over 34m51s — 11.4M cache-read, the second-highest of the campaign, because the garbage-collect limb requires long observation windows.

## Wasted input
- 36,831 chars read back; the long polls re-read the same `show ip rip database` output repeatedly.

## Repetition
- `poll.py` was used for timed observation, which is the right tool; the repetition is inherent to a 120 s timer, not waste.

## Accuracy risks
- **`show ip route` alone cannot distinguish a 180 s timeout from a 120 s garbage collect.** This case separated them by reading the triggered update at metric 16 off the wire and then watching the database timer count down. A tester without the packet capture would report one mechanism and miss the other.
- The F-3 narrowing conclusion rests on another case's measurement, so the final log keeps only this run's own fact: 15/15 forwarded against a completely cold ARP table.

## Next run: expected outputs
- default is RIPv2: multicast 224.0.0.9, TTL 1, explicit prefix length, route tag and next-hop per entry
- `version 1`: subnet broadcast at ff:ff:ff:ff:ff:ff, TTL 64, no masks, 10/8 entries collapsed to classful 10.0.0.0
- version mismatch: the v2-only neighbour times out at exactly 180 s, 0 bad packets
- withdrawal: metric 16 triggered update, out of the FIB in 13 s, then 120 s garbage collect
- reload: all three routes relearned in ~39 s

## Next run: scripts
- None proposed.

## Next run: references
- `platforms/x960.md` §7A for both protocols' measured facts, including `service <proto>` and `router <proto>` not sharing a console batch.


---
Group-wide findings are in [REVIEW.md](../REVIEW.md) and are not repeated here.
Recommendations are the reviewer's; findings cite the transcript segment or working log they come from. A review never changes a verdict.
