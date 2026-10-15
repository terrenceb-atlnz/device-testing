---
name: tb277-x960-routing-arp-campaign-2026-10-15
description: "13 AWPTCM routing + ARP cases on the x960-56YSQ, all PASS, run unattended overnight; the keeper is F-9 (a removed inter-VRF route keeps forwarding) and the method lessons about instruments that lie"
metadata:
  node_type: memory
  type: project
---

2026-10-15 into 10-16 on tb277, DUT **AT-x960-56YSQ S/N `A2WQS700B`**, build
`sin_x96056-20261012-24`, with **AT-x960-28YSQ (swi_b)** and **AT-x950 GEN2-52XSTQm (swi_a)** as
live partners — the first campaign on this bench to use all three. **13 of 13 PASS.**
Queue `tb277/x960/CAMPAIGN-QUEUE-2026-10-15T1747.md`, handover
`tb277/x960/SESSION-HANDOVER-2026-10-16.md`, product facts in `platforms/x960.md` §7/§7A/§7B.

Six IPv4_ARP cases (T33246-49, T43848, T43849) and seven IPv4_UnicastRouting (T43855-59, T43861,
T43862: static, ECMP, secondary IP, OSPFv2, RIP v1/v2, BGPv4, VRF-Lite).

**The one finding to carry forward is F-9, and it is security-relevant.** On VRF-Lite, after
`no ip route vrf red <prefix> <vlan>` — with the line gone from running-config and
`show ip route vrf red <addr>` answering `% Network not in table` — **5/5 crafted frames still
crossed the VRF boundary**, over three legs and ~2 minutes. The mechanism was pinned, not
guessed: a never-used host on the same /24 was correctly blocked **0/5**, so the route really is
gone and a **stale ARP-derived per-host forwarding entry** is what survives; `clear arp-cache vrf
<name>` stops it at once. Cold-start isolation is complete and immediate, so the case is a PASS —
but VRF-Lite is documented as *securely isolated*, and an operator closing a path sees config and
RIB agree it is shut while traffic flows. **Wants a developer.** The entry's unaided lifetime was
never measured.

**What made the campaign work, worth repeating:**

1. **One shared L3 underlay built once** at the start of group B and left up through groups C and
   D. Three groups paid no bench-setup cost. Measured consequence: group C's overhead was 3.0M
   cache-read against group A's 24.8M.
2. **Every counted leg carried an instrument control** — the DUT's own address, which must answer
   — so a zero was always a measurement and never a dead instrument. This is what caught two
   instrument faults and one false finding before any of them reached a verdict.
3. **A protocol's own packets are the only thing that can prove which protocol installed a
   route.** OSPF Router LSAs; RIPv1 vs RIPv2 read off the wire; BGP's AS_PATH in a real UPDATE.
   `show ip route` cannot establish any of it. For a unicast control-plane protocol like BGP the
   instrument is **the DUT's own `tcpdump` at privileged exec**, since the traffic never reaches
   a host NIC on another segment.
4. **Baseline the feature OFF first.** T43862 discarded a planned discriminator at baseline
   because it did not discriminate — a frame merely *sourced* in the secondary subnet crosses with
   the feature off too, forwarding being destination-based with no uRPF.

**Three instruments lied, all caught:** `arpleg.py` passing `-p` to tcpdump hid forwarded frames;
an ECMP flow generator varying all four 5-tuple fields by the same index correlated the two
addresses the hash consumes (false 81/19, decorrelated 50/50); and a capture file sized before
its writer exited read 0 bytes and nearly became a false product finding
([[tcpdump-nfs-root-squash-capture]]).

**Bench facts that cost time:** RSTP here is **single-instance**, so "give every routed leg its
own VLAN" does NOT unblock anything and two parallel links between the same bridge pair cannot
both forward — the triage recommended a parallel pair for ECMP and the tester had to measure that
it was impossible. `no interface vlanN` is **refused** on this build; `vlan database` /
`no vlan N` is what removes an SVI. A VRF change **strips the interface's addressing** in both
directions and on VRF deletion.

**Process, measured:** 562 API calls and **118.6M cache-read** across four tester transcripts, of
which **46% is group overhead** — gates, triage, rules and hand-back — not case work. The first
case of a group absorbs the group setup and looks 6× more expensive than its peers; judge cost
within a group, never across that boundary.

Related: [[scapy-for-traffic-tests]], [[awplus-service-gated-routing-daemons]],
[[tb277-x960-dhcp-campaign-2026-10-15]], [[campaign-measurement-discipline]],
[[campaigns-measured-for-token-waste]], [[satisfactory-level-of-testing]],
[[sentinel-session-keeps-long-runs-moving]].
