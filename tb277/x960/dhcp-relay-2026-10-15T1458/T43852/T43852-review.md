# T43852 process review -- dhcp-relay-2026-10-15T1458
Reviewed 2026-10-15 by /create-logs from agent-a355179677143f86e.jsonl and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 40 | 80 | 50,778 | 11,671,664 | 7,177 | 40 | 1958 s | 13,834 chars |

## Token usage note
**This case cost 11.67 M cache-read tokens over 40 calls -- 24% of the whole campaign, and more
than double any other case.** Its 1,958 s wall time is also the campaign's longest. The cause is
not the product: four faults in the tester's own scapy harness were found and fixed before any
graded measurement, and each diagnosis round cost a full-context call.

## Process taken
1. Rebuilt the bench for the relay topology: eth3 client side (VLAN 10), eth4 scapy DHCP server (VLAN 48).
2. Found and fixed four harness faults, each of which first presented as "the relay is dropping packets".
3. Ran the forwarding leg and read giaddr, hops and the 1:1 relay timing.
4. Ran both zero-relay controls (`no service dhcp-relay`; relay on with no server address).
5. Ran the hop-threshold matched pair (hops 2 relayed as 3; hops 10 dropped).

## Wasted input
- Several diagnostic heredocs (`diag2.sh` 1,040 chars, `read.sh` 839) were sent as script TEXT in the tool call and then run -- the text is charged once as input and again as part of the growing context. Writing a parameterised leg runner ONCE in `tools/` and calling it with arguments removes almost all of this.
- A 1,484-char `bench_probe.py run` read duplicates the before-state probe already taken in the session overhead segment.

## Repetition
- Four diagnosis rounds all asked the same underlying question -- "did the frame reach the far side?" -- and each rebuilt its own capture-and-count path. One trustworthy counted-both-ends helper would have collapsed them into one.

## Accuracy risks
- **The two independent counters disagree by one frame on three legs.** On `ctl-relay-off`, `ctl-no-server` and `hops10` the client tool reports `sent: 5 DISCOVER` while the eth3 capture counted 4. The verdict does not rest on it (the graded quantity is eth4 = 0 relayed), and the final log prints both figures side by side rather than reconciling them -- but the gap is unexplained. Most likely the scapy sniffer missing the first frame, as seen elsewhere in the campaign; it is worth proving rather than assuming.
- **`swi_d.cfg` was captured at 16:12, after the legs**, not after setup and before step 1 as logged-output.md §2 requires. The header line says so honestly, and the file includes the mid-run static ARP entry.
- **No in-case device-vs-box clock comparison.** The working log points at the first case of another group for it, so this case's final log carries no clock-offset line.

## Next run: expected outputs
- Relay on, server configured -> each DISCOVER/REQUEST relayed 1:1 in about **0.76 ms**, giaddr rewritten to the ingress SVI, hops incremented by 1.
- `no service dhcp-relay` -> 0 relayed. Relay on with no `server-address` -> 0 relayed.
- Default `maxhops` is **10**: a frame arriving with hops 2 is relayed as 3; one arriving with hops 10 is dropped.
- A relayed frame leaves from an EPHEMERAL source port, so a scapy reader must bind BOOTP on dport (67 and 68) or it will decode nothing and read as total loss.

## Next run: scripts
- **Proposed, highest value in the campaign:** `tools/leg.py` -- run one named leg end to end (apply config, start tcpdump on both NICs, run the client, stop, emit per-NIC counts plus the tool's own count, and FAIL LOUDLY when the two disagree). Arguments: `--leg NAME --nics eth3,eth4 --config F --client '<dhcp4.py args>' --out DIR`. Every case in this campaign hand-built a weaker version of it.
- `tools/dhcp4.py` already carries the relay-side binding fix.

## Next run: references
- `tools/README.md` -> `dhcp4.py`, the relayed-frame binding note. This is the single fact that cost this case the most.
- TPS row 28 and the CLI pages `service-dhcp-relay`, `ip-dhcp-relay-server-address`, `ip-dhcp-relay-maxhops`.
