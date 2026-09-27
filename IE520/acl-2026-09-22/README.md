# ACL group — IE520, tb470, 2026-09-22

13 cases. Per-case deliverable is `<case>.log` with verdict, evidence and raw transcripts.

| case | title | verdict |
| --- | --- | --- |
| [929](929.log)   | Named IPv6 Hardware on port - IP | **PASS** |
| [931](931.log)   | Named IPv6 Hardware on port - IP and MAC | **PASS** |
| [963](963.log)   | Named IPv6 Hardware applied Globally | **PASS** |
| [940](940.log)   | Named IPv6 Hardware on port send-to-cpu IP | **PASS** |
| [943](943.log)   | Named IPv6 Hardware on port copy-to-mirror IP | **PASS** (mirror delivery unverified) |
| [826](826.log)   | Hardware IP 3000 range - applied to ports | **PASS** |
| [830](830.log)   | Hardware MAC 4000 range - applied to ports | **PASS** |
| [881](881.log)   | Named Hardware on static LAG - IP | **PASS** (LAG not straddling) |
| [885](885.log)   | Named Hardware on static LAG - mac | **PASS** (LAG not straddling) |
| [890](890.log)   | Named Hardware on static LAG - udp | **PASS** (LAG not straddling) |
| [889](889.log)   | Named Hardware on static LAG - tcp port ranges | **PASS** (LAG not straddling) |
| [38413](38413.log) | deny/permit for standard IPv6 access list | **UNSUPPORTED** — not configurable on the IE520 (re-confirmed on awplus_main-20260923-20, 2026-09-24) |
| [942](942.log)   | Named IPv6 Hardware on port send-to-mirror IP | **UNSUPPORTED** — not configurable on the IE520 (re-confirmed on awplus_main-20260923-20, 2026-09-24) |

**11 PASS / 2 UNSUPPORTED.** Both UNSUPPORTED are cases whose *subject* does not
exist on this platform (a standard IPv6 ACL has no application point; there is no
`send-to-mirror` action) — not work left undone.

## Method

Every measurement is on traffic that TRANSITS the DUT — injected with scapy on
tb470 `eth2` into stack `port2.0.2`, captured with tcpdump on `eth1` via the
x230. Every case takes a **no-ACL baseline first**, so a later drop is provably
the ACL and not a dead path. ACL hit counters corroborate each result.

## The two UNSUPPORTED, and why

- **38413** — a *standard* IPv6 ACL builds fine but has **no traffic-filtering
  application point** on this platform. `ipv6 traffic-filter` resolves hardware
  lists only (`% Access-list does not exist` on a list that `show` displays),
  and `ipv6 access-class` does not exist on vty.
- **942** — `send-to-mirror` is **not an action** for IPv6 hardware ACLs here
  (`% Invalid input`). The sub-mode offers copy-to-cpu, copy-to-mirror,
  send-to-cpu, send-to-vlan-port, permit, deny. The case text anticipates this.

## Limitations that cap several PASSes — all bench, not product

- **No straddling LAG** (881/885/890/889). `sa1` had ONE member. The 2026-09-22 reading
  that each IE520-28GSX member has exactly one usable copper port was WRONG (corrected
  2026-09-23: three copper ports per member, `.2/.9/.13`; the limit was cabling). Since the
  2026-09-23 recable, cable pairs that straddle stack members exist (members 3+4 to the 4050,
  1+4 to the IE520-sa — bench-state.md Links), so these four could be re-run on a straddling LAG.
- **Mirror destination not observable** (943, 830). `port3.0.2` is the only
  spare copper port and has no cable, so a mirrored frame cannot be captured
  and the port's TX counters stay 0. Cabling any NIC to `port3.0.2` closes this.
- **QoS service-policy half not run** (929, 931) — deferred to the QoS group.
- CPU-queue counters (`show plat count sdma`) were not read; CPU diversion is
  evidenced by forwarding dropping to 0/10 with the rule taking hits.

## Behaviour worth knowing

**There is no implicit deny** on a hardware IPv6 ACL applied with
`ipv6 traffic-filter`. Traffic matching no rule forwards 10/10; adding an
explicit `deny ipv6 any any` drops it 0/10. Default-deny must be written.

## Bench state at exit

Restored: `port2.0.2` a plain access switchport, no static channel group, no
ACLs (`show access-list` and `show ipv6 access-list` both empty), no mirror
session, transit verified 10/10.
