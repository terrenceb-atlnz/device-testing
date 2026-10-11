tb470, DUT x230v2-28GS swi_f on u0 (AT-x230-28GS V2, S/N A10783G262900002, awplus_main-20261008-57), 2026-10-09.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T46421 | Link flap | [46421/46421.log](46421/46421.log) | **PASS**. 21 flaps (12 local on x230 port1.0.2-1.0.5, 9 remote from the IE520 stack) each logged one Port down + one Port up; every link back at a-full a-1000 in its VLAN with its LLDP neighbour |
| T47208 | Copper pluggable with supported speeds | [47208/47208.log](47208/47208.log) | **PASS**. SPTXa (vs AR4050S) and SPTXc (vs tb470 eth3) link full at auto 10/100/1000 and fixed 1000; SPTX at auto 100/1000, fixed 1000 and forced 100/full; SPTX at 10 Mb/s not measurable (the IE520 SPTXa partner rejects 10) |
| T47210 | MAC/Phy TLV with combination of user defined speed, duplex and auto nego | [47210/47210.log](47210/47210.log) | **PASS**. 9 speed/duplex/autoneg combinations on x230 port1.0.1 <-> AR4050S port1.0.2: the x230's MAC/PHY TLV decoded at the AR4050S showed the matching autoneg state, advertised set and MAU type each time |
| T20358 | Loopback between two ports on same switch | [20358/20358-partial.log](20358/20358-partial.log) | **PARTIAL**. RSTP on; the STP-disabled IE520 stack did not return the x230's BPDUs (port1.0.4 "Received None", Designated Forwarding 20 s), so the loop was not closed; needs a direct x230 port1.0.6 <-> 1.0.7 fibre loop or a hub |
| T47209 | Fibre pluggable with supported speeds | [47209/47209-fail.log](47209/47209-fail.log) | **FAIL**. AT-SPSX runs 1000 full (auto and fixed) and refuses 10/2500/10000/half, but `speed 100` / `speed auto 100` are accepted and the port reads "connected a-full 100" while passing no frames either way (counters flat 40 s, LLDP lost, partner at 1000) |
| T47228 | API-enable/disable interface, add/delete vlans | — | **NOT TESTED**. Test Engineer's: no steps and the API under test is unspecified; not in the 18:00 scope |
| T44179 | Jumbo Frames | — | **NOT TESTED**. Needs x230 `platform jumboframe` (write + reload, x2), stack `platform jumboframe` (stack reload, x2) and root MTU on tb470 eth3/eth1 (Test Engineer's); not in the 18:00 scope |
| T33234 | Port - Auto MDI/MDI-X | — | **NOT TESTED**. Triaged UNSUPPORTED: no fixed copper on the x230v2-28GS (all 28 ports are SFP cages); not in the 18:00 scope |
