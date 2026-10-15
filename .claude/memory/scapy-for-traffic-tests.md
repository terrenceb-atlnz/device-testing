---
name: scapy-for-traffic-tests
description: "Test Engineer 2026-10-15: every traffic test uses scapy-crafted frames with a control flow and per-frame counts — a ping proves reachability, never that the DUT treated the right frames the right way"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 87016784-78a9-4107-8bc9-8db7a57a86ad
  modified: 2026-10-15T01:54:10.334Z
---

Test Engineer, 2026-10-15, as a standing rule for **every case, now and in future, whoever runs
it**: *"you will need to use lots and lots of scapy for traffic test. A simple ping won't
sometimes be sufficient."* Written into `STANDING-ORDERS.md` §7 as well, because the
`bench-runner` subagent that actually sends the traffic reads standing orders and its dispatch,
not these memories.

**Why:** a `ping` is a reachability check. It cannot select a protocol number, a port, a source
or destination MAC, a VLAN tag, a TTL, a DSCP value or a frame size; it cannot send the frame a
filter is supposed to DROP; and it leaves no per-frame record to count. Every case whose subject
is *which* frames the DUT forwards, copies, drops, tags, rate-limits or redirects — ACLs,
mirroring, QoS, storm control, snooping, helpers, broadcast forwarding — is unprovable with it.
This bench has already produced the matching failure in the other direction: on the x960,
`show mirror` reported a mirror `Enabled` with the right direction while the dataplane copied
**nothing at all** (`platforms/x960.md` §5, defects M1–M3). A status read-back and a successful
ping would both have scored that a PASS.

**How to apply:**
- Craft the exact frame the rule matches, send a **known count**, count what arrives, and send a
  **control** flow in the same run that the rule must NOT match. The verdict rests on the pair.
- Reach for the existing tools first (`tools/README.md`, all scapy-based): `vsend.py` /
  `vcount.py` (marked bursts, VLAN tags, EtherType, IPv4/IPv6/IPX/ARP), `linerate.py` (UDP at a
  set rate to 1G, counted both ends), `mkpcap.py` / `mkmc.py` (routed and multicast pcaps),
  `igmp.py`, `dhc6.py`, `rs.py`, `ra_decode.py`, `lldpmed_phone.py`. Extend one rather than write
  a near-duplicate; anything new is generic and lands in `tools/` with its README entry.
- scapy 2.4.4 is on tb277 (checked 2026-10-15). Confirm on any other box before assuming.
- `ping` remains right for proving a link is up, for an ARP exchange, and for ping-poll's own
  subject. Say which you used and why in the working log.
- Carry this into every `bench-runner` dispatch, not just the queue file.

Related: [[campaign-measurement-discipline]], [[satisfactory-level-of-testing]],
[[log-is-the-deliverable]].
