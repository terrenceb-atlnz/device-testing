# T33246 process review -- arp-2026-10-15T1747
Reviewed 2026-10-16 by /create-logs from `agent-abaa4bf7d49aa5cc5.jsonl` and the working files.

## Token usage
| calls | cache read | cache write | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 6 | 2,246,661 | 21,535 | 14,406 | 6 | 5m 16s | 6,164 |

6 calls, 5m16s. The most set-up-heavy ARP case: web auth, local RADIUS and an HTTP login.

## Wasted input
- `grep -n ... CAMPAIGN-QUEUE` (4,421 chars) pulled queue text into the case that the group overhead had already read.

## Repetition
- Queue edits were made from inside the case segment; those belong to group overhead.

## Accuracy risks
- **The `.cfg` provenance gap.** The capture point before step 1 was missed, so `swi_d.cfg` was produced afterwards by re-applying the identical setup command set. The final log states this in its `Configs:` line rather than presenting it as an in-run capture. The RADIUS key hash is the one field that cannot match. **Fix for the next run: save the `.cfg` as the first action after setup, before any measurement** — it is cheap and unrecoverable afterwards.
- The title 'ARP Polling' does not name a generic ARP feature on this platform; it is web-auth ping-polling (Project 2561). Grading it as generic ARP would have produced a wrong UNSUPPORTED.

## Next run: expected outputs
- directed unicast ARP polls to the supplicant's MAC at the configured interval
- `type ping`: ICMP instead of ARP
- deauthentication after exactly failcount unanswered polls, attributed by the DUT's own log line naming supplicant and MAC
- stimulus that works: `ip link set eth3 arp off` on the box — link and port stay up

## Next run: scripts
- None proposed.

## Next run: references
- FINDING-A in the queue's triage section: what this case actually is, and why the TFS's proposed CLI does not exist.


---
Group-wide findings are in [REVIEW.md](../REVIEW.md) and are not repeated here.
Recommendations are the reviewer's; findings cite the transcript segment or working log they come from. A review never changes a verdict.
