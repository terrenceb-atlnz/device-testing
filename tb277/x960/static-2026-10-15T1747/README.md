# static-2026-10-15T1747

tb277, AT-x960-56YSQ (swi_d, S/N A2WQS700B, `sin_x96056-20261012-24`), 2026-10-15 20:13–21:21 NZDT.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T43855 | IPv4_UnicastRouting - IPv4 Static | [T43855/T43855.log](T43855/T43855.log) | **PASS**. Static route proven on the wire: 5/5 forwarded against 0/5 at baseline and 0/5 after `no ip route`, with a control flow to an unrouted prefix dropped in every leg. Removal proven in the FIB (`% Network not in table`). Three syntax forms measured; the floating-static egress move attributed by the partner's own ICMP unreachables; the distance-255 RIB-not-FIB rule confirmed. Survives a reload. |
| T43861 | IPv4_UnicastRouting - ECMP Routing | [T43861/T43861.log](T43861/T43861.log) | **PASS**. ECMP proven per egress port across four counters on three devices, never from `show ip route`: one route = all traffic on a single port; two routes = a real split; `maximum-paths 1` collapses the identical flow set onto one port; removal returns all traffic to the survivor. The distribution rests on decorrelated 5-tuple spans. Survives a reload. |
| T43862 | IPv4_UnicastRouting - Secondary IP Address (Multi homing) | [T43862/T43862.log](T43862/T43862.log) | **PASS**. The secondary address proven serving traffic, not merely displayed: ARP 0/4 off → 4/4 on → 0/4 removed, and forwarding into the secondary subnet 0/5 → 5/5 → 0/5, with the connected route appearing and disappearing with it. Multiple secondaries coexist; a secondary with no primary is refused; removing the primary while a secondary exists is refused, not cascaded. Survives a reload. |
