tb470, DUT x230v2-28GS (swi_f, u1) with an AR4050S link partner (swi_e, u0), 2026-10-21 13:46-14:30 NZDT.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T47226 | check for sh version | [47226/47226.log](47226/47226.log) | **PASS**. `show version` answers in full; the x220 build name is the expected build-target name; health clean |
| T47227 | check for sh license | [47227/47227.log](47227/47227.log) | **PASS**. `show license` lists Base License (Full, 11 features) and ACCESS (Full), no error line; health clean |
| T47215 | sh sys environment | [47215/47215.log](47215/47215.log) | **PASS**. `show system environment` reads Overall Status Normal; fan, 5 voltages and 3 temperatures all Ok; health clean |
| T46421 | Link flap | [46421/46421.log](46421/46421.log) | **PASS**. 18 flaps (9 local, 9 remote) at auto 1000/100/10: each logged Port down + Port up, link back in 2.8-4.5 s with LLDP re-learned; health clean |
| T47208 | Copper pluggable with supported speeds | [47208/47208.log](47208/47208.log) | **PASS**. AT-SPTXa linked at auto 10/100/1000, fixed 1000, forced 100 and 10 full; 2500/10000/100000 refused; one module type on the bench; health clean |
| T47210 | MAC/Phy TLV with combination of user defined speed, duplex and auto nego | [47210/47210.log](47210/47210.log) | **PASS**. 9 speed/duplex/autoneg combinations: the TLV decoded at the AR4050S showed the expected autoneg state, advertised set and MAU type each time; health clean |
