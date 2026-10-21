tb101, IE520 4-member VCStack (AT-IE520-28GSX x4, awplus_main-20261019-75) as the DUT, 2026-10-21.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T17584 | LACP - Startup stable with heavy traffic | [17584/17584.log](17584/17584.log) | **PASS**. LACP aggregator po1 (2 stack members) kept traffic flowing through 2 link shutdowns, 3 member reloads (2 master failovers) and a whole-stack reboot; the LACP system ID stayed the VMAC 0000.cd37.0d6f throughout. The 4-device traffic step is NOT MEASURABLE on tb101. |
