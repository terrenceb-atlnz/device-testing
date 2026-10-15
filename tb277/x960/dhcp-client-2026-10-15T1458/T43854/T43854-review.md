# T43854 process review -- dhcp-client-2026-10-15T1458
Reviewed 2026-10-15 by /create-logs from agent-a355179677143f86e.jsonl and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 16 | 32 | 35,080 | 6,891,647 | 8,993 | 16 | 1362 s | 9,942 chars |

## Process taken
1. Static `ip name-server`, client re-lease on vlan48, `ip dns forwarding` on.
2. Forwarding leg: 5 crafted queries, counted at both NICs with tcpdump alongside the new tool.
3. `no ip dns forwarding` control: same 5 queries on the wire, 0 forwarded.
4. DHCP import leg, then a two-responder leg to find which server the relay actually queries.
5. Cache leg (not graded), then reboot persistence proven on the wire.

## Wasted input
- Five configuration heredocs of 864-1,188 chars each. Same group finding.
- Nothing else of size: 16 calls, 9,942 chars read.

## Repetition
- `dnsctl.sh` / `dnsctl2.sh` and `dnsorder.sh` / `nsorder.sh` are two pairs of near-duplicate drivers.

## Accuracy risks
- **The cache limb is UNMEASURED and this bench cannot close it.** Two identical queries 5.3 s apart inside the TTL both went upstream with the cache enabled. Not graded a failure: the TFS separates a Name Resolver Process from a DNS Relay Process and S1570.1.03/.11 both say "name *resolve result*", which plausibly scopes the cache to the device's own lookups rather than relayed third-party queries. **This wants a developer's answer, not another bench run.**
- **No pre-enable `show ip dns forwarding` exists.** The defaults read-back was taken at 17:01:17, immediately AFTER `ip dns forwarding` was applied, so the baseline step cites the TFS's stated default instead. The working log presents that read-back under its case-source section, where it could be mistaken for a pre-enable capture. Take the baseline read BEFORE the enable.
- **Ordering can be measured only as preference, never as list order.** The relay queried the DHCP-learned `.2` and never ARPed for the static `.9`; a control proves `.9` is reachable and used. `show ip name-server` cannot settle it either -- its display is type-grouped. The limb is recorded as an observation with that scope limit stated.
- **No run span is stated in the working log**; the final log's `Run:` line was derived from timestamps inside the working files.
- **`swi_d.cfg` captured at 17:12, after the legs.**

## Next run: expected outputs
- `ip dns forwarding` on -> every query forwarded upstream and every answer returned; off -> 0 forwarded with the queries still demonstrably on the wire.
- A DHCP-learned server appears as `dynamic (vlanN)` in `show ip name-server` and IS used.
- `ip dns forwarding cache size 100 time 60` -> `DNS Cache: enabled, Size 100, Max-TTL 60`.
- **Wait 20 s after ANY DNS or DHCP-client change before counting.** A leg run ~3 s after such a change forwards nothing and reads as "the device cannot use a static DNS server"; the TFS documents that a DNS update restarts the relay process and clears sessions.
- Use DISTINCT query names within a counted round: repeated names let in-flight duplicate suppression swallow queries.

## Next run: scripts
- `tools/dnsresp.py` -- now hardware-verified. Two responders on one NIC (each filtering on its own `--for` address, with different `--default-answer` values) is how you discover which upstream server a relay prefers.
- The proposed `tools/leg.py` applies.

## Next run: references
- `DNS Relay TFS` S1570.1.01-.37, and its "Limitations" section for the process-restart behaviour.
- `tools/README.md` -> `dnsresp.py`, which carries the 20 s settle rule and the counting discipline.
