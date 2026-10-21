Testbox tb277, DUT AT-x960-56YSQ (swi_d, S/N A2WQS700B, `sin_x96056-20261019-27`), 2026-10-21.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T33399 | (262) Management_NTP - IPv4 NTP Server | [T33399/T33399.log](T33399/T33399.log) | **PASS**. Mode-4 replies at the configured stratum with nothing before configuration or after removal, per-client `ntp restrict` denial discriminating two clients of one server, and the server back 13 s after a cold boot. |
| T33400 | (263) Management_NTP - IPv4 NTP Client | [T33400/T33400.log](T33400/T33400.log) | **PASS**. Seven polls, seven replies, seven paired, zero packets to an unreachable control server, a real 14.836 s clock error removed, and polling resumed 9 s after a cold boot. |
| T44298 | (264) Management_NTP - IPv6 NTP Server | [T44298/T44298.log](T44298/T44298.log) | **PASS**. Mode-4 replies over IPv6 at the configured stratum, one `ntp master` shown to serve IPv4 and IPv6 in a single capture, and the server back over IPv6 11 s after a cold boot. |
