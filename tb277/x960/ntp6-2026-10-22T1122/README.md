Testbox tb277, DUT swi_d (AT-x960-56YSQ, S/N A2WQS700B), 2026-10-22.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T44299 | (265) Management_NTP - IPv6 NTP Client | [T44299/T44299.log](T44299/T44299.log) | **PASS**. The DUT sends NTPv4 mode-3 requests to a configured IPv6 server and is answered (8, 11, 13 and 13 requests in four captures, every one paired), reaches Stratum 6 from a stratum-5 IPv6 source, corrects real clock errors of 2.241471 s and 50.914095 s over IPv6, never polls an identically configured unreachable IPv6 server, goes silent when the configuration is removed, and resumes polling after a cold boot with nothing typed into the device. |
