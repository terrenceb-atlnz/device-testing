Testbox tb277, DUT AT-x960-56YSQ (swi_d, S/N A2WQS700B, `sin_x96056-20261019-27`), 2026-10-21.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T33379 | (230) Management - Telnet Client (IPv4) | [T33379/T33379.log](T33379/T33379.log) | **PASS**. The DUT originates IPv4 telnet as a client, proven on the wire and end to end, with server-off, bad-credential and wrong-port controls all failing correctly. |
| T33380 | (231) Management - SSH Server (IPv4) | [T33380/T33380.log](T33380/T33380.log) | **PASS**. The DUT serves SSH over IPv4, graded on TCP/22 from the testbox with a complete off/on arc, and the configuration survives a cold boot. |
| T33381 | (232) Management - SSH Client (IPv4) | [T33381/T33381.log](T33381/T33381.log) | **PASS**. The DUT originates IPv4 SSH as a client, with the control and the real session in one far-end capture. |
