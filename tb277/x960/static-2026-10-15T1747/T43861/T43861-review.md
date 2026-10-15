# T43861 process review -- static-2026-10-15T1747
Reviewed 2026-10-16 by /create-logs from `agent-aeb89f5d96391104b.jsonl` and the working files.

## Token usage
| calls | cache read | cache write | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 21 | 5,080,430 | 45,249 | 176 | 21 | 23m 9s | 22,333 |

21 calls over 23m9s — the longest-running case in group B, because the distribution legs send and count thousands of flows.

## Wasted input
- 22,333 chars of tool output read back, the highest in the group — per-port counter reads repeated across legs.

## Repetition
- Counter reads were issued per leg via two box-side shell helpers (`ctrs.sh`, `ctrd.sh`) that live on the box and are not in the repo. **A `tools/` helper that snapshots all four counters in one call would remove most of the repetition.**

## Accuracy risks
- **The instrument artefact is the headline.** The first flow set varied all four 5-tuple fields by the same index, which correlates the two addresses the hash actually uses, and produced a misleading 81/19 split. Decorrelated spans gave ~50/50 and the verdict rests on those. **Any ECMP measurement must decorrelate the fields the hash consumes, or it measures its own flow generator.**
- An ECMP next hop with unresolved ARP is silently absent from the dataplane while `show ip route database` still marks it `*>`. Check `show arp` before believing an ECMP route group.
- The triage's recommendation to use the swi_a parallel pair as the two next-hops is **wrong on this bench** — single-instance RSTP blocks one of two parallel links between the same bridge pair. The measured paths are one link to each partner.

## Next run: expected outputs
- one route: all traffic on a single egress port
- two routes: a real split on decorrelated spans (~50/50)
- `maximum-paths 1`: identical flow set collapses onto one port
- hash inputs: IPv4 source and destination addresses only — 64 source *ports* or 64 destination *ports* give 1280/0

## Next run: scripts
- `tools/ecmpflows.py` — already generic and catalogued. **Proposed:** `tools/portctrs.py <dev> <ports...>` to snapshot per-port counters on all devices in one call.

## Next run: references
- The Route Selection guide says ECMP is per-packet; it is **per-flow** on this platform. Documentation defect F-1 in the queue.


---
Group-wide findings are in [REVIEW.md](../REVIEW.md) and are not repeated here.
Recommendations are the reviewer's; findings cite the transcript segment or working log they come from. A review never changes a verdict.
