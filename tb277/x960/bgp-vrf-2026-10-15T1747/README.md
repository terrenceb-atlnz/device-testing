# bgp-vrf-2026-10-15T1747

tb277, AT-x960-56YSQ (swi_d, S/N A2WQS700B, `sin_x96056-20261012-24`), 2026-10-15 22:44 – 2026-10-16 00:00 NZDT.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T43858 | IPv4_UnicastRouting - BGPv4 | [T43858/T43858.log](T43858/T43858.log) | **PASS**. Two eBGP sessions Established to two different AS over two links, with the prefixes carried in real BGP-4 UPDATEs read off the wire (Version 4 OPEN, ORIGIN IGP, AS_PATH, NEXT_HOP) — the AS_PATH is what proves the route arrived by eBGP. Forwarding 0/5 → 5/5 against a control dropped in every leg; a static at AD 1 displaces eBGP AD 20 with the egress move attributed on the wire; one prefix withdrawn to 0/5 while the second neighbour held 5/5 in the same capture, the WITHDRAW itself captured with End-of-Rib. Removal proven in the FIB; survives a reload. |
| T43859 | IPv4_UnicastRouting - VRF-Lite | [T43859/T43859.log](T43859/T43859.log) | **PASS**. Isolation proven three-sided on counted far-side frames: 5/5 crossing in the global table, 0/5 once the two SVIs are in separate VRFs, and 5/5 again with both SVIs in the same VRF and nothing else changed — which is what makes the zero attributable to VRF membership. One overlapping address answers on two ports in two VRFs with each opposite capture empty; static inter-VRF routing opens exactly the prefixes named; per-VRF ARP tables measured. Survives a reload. See the log's CAVEAT: a removed inter-VRF route left a stale ARP-derived entry forwarding until the VRF's ARP cache was cleared. |
