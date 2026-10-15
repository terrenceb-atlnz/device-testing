# T33248 process review -- arp-2026-10-15T1747
Reviewed 2026-10-16 by /create-logs from `agent-abaa4bf7d49aa5cc5.jsonl` and the working files.

## Token usage
| calls | cache read | cache write | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 21 | 3,108,319 | 50,499 | 12,889 | 21 | 14m 20s | 16,543 |

21 calls over 14m — **the most expensive case in group A, and six times the five that follow it.** That is a sequencing artefact, not a property of static ARP: as the group's first case it absorbed the bench setup, the VLAN/SVI build and the first build of the ARP instrument.

## Wasted input
- The five largest tool outputs are `cfg.py` console batches echoing back the full config they just sent (2,344 / 1,527 / 1,453 chars). The driver already returns a tail; `| tail -6` was used on some calls and not others.
- `sed -n '220,255p' tools/README.md` (2,229 chars) re-read the tool catalogue that the group overhead had already read.

## Repetition
- The instrument was built and debugged inside this case rather than before the group. Every later ARP case reused it in 3-6 calls.

## Accuracy risks
- **The instrument fault is the one real accuracy risk, and it is now only half-recorded.** `tools/arpleg.py` was passing `-p` to tcpdump, so a frame carrying a next-hop MAC that was not the NIC's own was invisible and a working leg read `0 forwarded`. Baseline and measurement were re-run on the fixed instrument and the verdict rests on those. §4 excludes setup detours, so the final log does not carry it — it now lives only in `work/run1.log` and the `arpleg.py` docstring. **A zero from this tool is only a measurement once a non-zero has been seen on the same instrument in the same run.**

## Next run: expected outputs
- static entry installed: `show arp` shows the configured MAC with Type `static`
- forwarding with entry: 5/5 rewritten to the configured MAC on the configured port
- control address, no entry: broadcast ARP observed, 0/5 forwarded
- after `no arp <ip>`: entry gone from `show arp`, dataplane back to 0/5

## Next run: scripts
- `tools/arpleg.py` — already generic and catalogued. Run it **once as a group gate** before case 1 with a known-good flow, so the instrument is proven before any case depends on it.

## Next run: references
- `platforms/x960.md` §6 (DHCP campaign ARP/SVI facts) and the queue's bench-facts block — read once per group, not per case.


---
Group-wide findings are in [REVIEW.md](../REVIEW.md) and are not repeated here.
Recommendations are the reviewer's; findings cite the transcript segment or working log they come from. A review never changes a verdict.
