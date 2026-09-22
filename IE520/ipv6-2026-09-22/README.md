# IPv6 routing & protocol group — IE520, tb470, 2026-09-22

16 cases. **6 PASS / 10 UNMEASURED.**

| case | title | verdict |
| --- | --- | --- |
| [8734](8734.log) | Neighbor Advertisement responses | **PASS** |
| [10874](10874.log) | OSPFv3 Syncs with neighbour | **PASS** (5/5 flap cycles) |
| [38427](38427.log) | IPv6 - OSPFv3 - Hardware routing | **PASS** |
| [3111](3111.log) | BGP4+ Advertising Default Route | **PASS** (peer installs it) |
| [3112](3112.log) | BGP4+ Establish peer and create prefixlist | **PASS** |
| [3114](3114.log) | BGP4+ Disconnect / Reconnect Links | **PASS** (3/3) |
| [38430](38430.log) | BGP4+ - BFD fall-over | **UNMEASURED** — peer can't configure BFD |
| [3116](3116.log) | BGPv4 - Unicast Traffic | **UNMEASURED** — needs line rate |
| [8770](8770.log) | IPv6 Neighbors - in silicon | **UNMEASURED** — needs ~5000 emulated neighbours |
| [20930](20930.log) · [38144](38144.log) · [11722](11722.log) · [11736](11736.log) · [11740](11740.log) · [11724](11724.log) · [30681](30681.log) | IPv6 multicast / PIM-SMv6 (7 cases) | **UNMEASURED** — need more hosts than the bench has ports |

## What was actually established

A real routing topology between the DUT and the AR4050S over the vlan10 transit
(`2001:db8:10::1 ↔ ::2`):

- **OSPFv3 adjacency Full**, surviving 5/5 shutdown/no-shutdown cycles, and a
  learned prefix installed: `O E2 2001:db8:427::/64 [110/20] via fe80::…, vlan10`
- **BGP4+ session Established** (AS 65001 ↔ 65002), advertising `::/0` which the
  peer installs as `B ::/0 [20/0] via fe80::…, vlan10`, and recovering 3/3 from
  link disconnects
- **IPv6 ND** answering solicitations with correctly-flagged advertisements (S=1, O=1)

## The syntax that cost the most, now recorded

OSPFv3 interface attachment on AW+ is:

```
interface vlan10
 ipv6 router ospf area 0
```

**Not** the IOS-style `ipv6 ospf <n> area <n>`, and not a command inside the
router sub-mode. Probing `ipv6 ospf ?` shows no `area` option, which led me to
conclude the interface could not be attached at all — the command lives under
`ipv6 router …`.

> **Use the AW+ CLI wiki on the share**:
> `claude/github-copilot-awplus-wiki/awplus_cli_wiki/commands/` — **3437 command
> pages**, one per command, each with syntax, mode and a platform table. Faster
> and safer than probing a live CLI, and it avoids the `?`-plus-CR hazard.
> Note the IE520 is absent from several platform tables for commands that work
> on it, so treat the tables as a guide, not a gate.

## Why 10 are UNMEASURED — all bench, none product

- **7 multicast/PIM-SMv6 cases** need separate sources and receivers on
  *different* DUT ports. Each IE520 member has one usable copper port, giving one
  injection point and one observation point. "Different hosts joining different
  groups" is not constructible.
- **3116** is a line-rate claim; this harness peaks at ~26 Mbps.
- **8770** needs ~5000 *responding* neighbours.
- **38430** needs BFD at both ends; the DUT accepts the BGP-side config but the
  AR4050S rejects it and the DUT exposes no `show bfd session`.

IPv6 itself is well exercised across the campaign — ND (8734), unicast routing
(38427), multicast forwarding and MLD snooping (switching 10300/10304), IPv6 ACLs
(ACL 929/931/963) and IPv6 QoS classification (QoS 13819).

## Bench state at exit

All routing config removed from both devices: no BGP, no OSPFv3, no prefix-list,
vlan10 back to IPv4-only (`10.10.10.1/27`). Stack `Normal operation`, transit
10/10, all three TB paths 0% loss. (`no service ospf6` reports "save and restart
to take effect" — the daemon lingers until reboot but nothing references it.)
