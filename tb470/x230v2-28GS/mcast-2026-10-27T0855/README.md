tb470, DUT x230v2-28GS (swi_f, u1), standalone with the FULL licence, 2026-10-27 09:57-10:05 NZDT.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T30403 | Check traffic is fowarded with static mroutes (IPv4) | [30403/30403-unsupported.log](30403/30403-unsupported.log) | **UNSUPPORTED**. The licence enables PIM, PIM6 and L3-MC-ROUTE, but `ip multicast-routing`, `ip mroute`, `ip pim` and `show ip mroute` are all refused, and nothing reached the running-config. The X220 Software TPS lists multicast routing as NO. Steps 2 and 3 not run. Health clean |
