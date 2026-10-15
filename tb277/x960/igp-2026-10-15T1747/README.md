# igp-2026-10-15T1747

tb277, AT-x960-56YSQ (swi_d, S/N A2WQS700B, `sin_x96056-20261012-24`), 2026-10-15 21:35–22:38 NZDT.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T43857 | IPv4_UnicastRouting - OSPFv2 | [T43857/T43857.log](T43857/T43857.log) | **PASS**. OSPFv2 proven across nine counted legs: Full adjacency to two neighbours, routes learned from the protocol (code `O`, AD 110, carried by each partner's Router LSA) forwarding 5/5 + 5/5 against a control dropped in every leg. Withdrawing one advertisement with link, port and adjacency still up dropped the subject to 0/5 in under 7 s while the second neighbour held 5/5 in the same leg. Static AD 1 displaces OSPF AD 110 in the dataplane; `passive-interface` gives 0 OSPF packets in 30 s. Survives a reload. |
| T43856 | IPv4_UnicastRouting - RIP v1/v2 | [T43856/T43856.log](T43856/T43856.log) | **PASS**. Both RIP versions read out of the protocol's own packets rather than a `show`: v2 to 224.0.0.9, TTL 1, explicit masks, tags and next-hop; v1 to the subnet broadcast at ff:ff:ff:ff:ff:ff, TTL 64, no masks, the 10/8 entries collapsed to one classful route. The version mismatch had a selective measured effect — the v2-only neighbour timed out at exactly 180 s and went 5/5 → 0/5 while the v1 prefixes held in the same leg. Withdrawal caught both mechanisms: a triggered update at metric 16 out of the FIB in 13 s, then the 120 s garbage collect. Survives a reload. |
