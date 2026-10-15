# T43858 process review -- bgp-vrf-2026-10-15T1747
Reviewed 2026-10-16 by /create-logs from `agent-ab60d6243d8eb4d8a.jsonl` and the working files.

## Token usage
| calls | cache read | cache write | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 62 | 11,551,543 | 103,053 | 828 | 62 | 34m 26s | 46,773 |

62 calls over 34m26s and 11.6M cache-read — **the most expensive case in the campaign.** About a third of that went on a port-mirror limb that did not end up carrying any verdict.

## Wasted input
- 46,773 chars read back. The mirror limb's captures, config reads and status checks are the bulk of it.

## Repetition
- The mirror was configured, measured, re-checked and removed; the protocol evidence came from the DUT's own `tcpdump` instead. **Reaching for the DUT's `tcpdump` first would have removed the whole limb.**

## Accuracy risks
- **A finding was raised against the port mirror and retracted before hand-back.** A zero-byte capture was read as 'the mirror copied nothing' when the real cause was an unflushed buffer behind a `kill` that never reached tcpdump (`$!` was the wrapper). Reading the same file after the process exited showed 14 mirrored TCP/179 frames. **A `tcpdump -w` file size read after an unverified kill is not a measurement** — confirm the process exited, or read tcpdump's own `N packets captured` line. This matters beyond this case: `platforms/x960.md` §5's evidence for three real mirroring defects is built on capture sizes.
- `show running-config` renders ` bgp graceful-restart` while `copy running-config` writes ` no bgp graceful-restart` and the OPEN advertises no GR capability. The display is the outlier; which is intended is not established.
- No end timestamp exists in the working log past 23:19:34, so the log's `Run:` line says so rather than inventing one.

## Next run: expected outputs
- BGP is **not** service-gated on this build: `bgpd` runs from boot, `router bgp` is accepted immediately, and `service bgp` takes only `evpn` (bare form: `% Incomplete command.`)
- session Established with Version 4, remote router ID, 1 accepted / 1 announced prefix
- prefix as code `B`, AD 20, carried in an UPDATE with ORIGIN IGP / AS_PATH / NEXT_HOP
- withdrawal: UPDATE with `Withdrawn routes:` + End-of-Rib; subject 0/5, second neighbour 5/5 in the same capture
- reload: both sessions up and both prefixes forwarding ~12 s after the interfaces come up, from a cold ARP table

## Next run: scripts
- **Proposed:** `tools/dutcap.py <console> <iface> <bpf> <count>` wrapping the DUT's own privileged-exec `tcpdump`. It is the correct instrument for a unicast control-plane protocol on this platform and was hand-assembled here.
- BPF note worth keeping: `greater N` counts the 14-byte Ethernet header, so a 19-byte BGP Keepalive is an 85-byte frame — `greater 90` isolates UPDATEs.

## Next run: references
- `platforms/x960.md` §5 (the read-back-vs-dataplane defect class) and the new §7B.


---
Group-wide findings are in [REVIEW.md](../REVIEW.md) and are not repeated here.
Recommendations are the reviewer's; findings cite the transcript segment or working log they come from. A review never changes a verdict.
