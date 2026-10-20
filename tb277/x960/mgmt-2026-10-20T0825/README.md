Testbox tb277, DUT AT-x960-56YSQ (swi_d, S/N A2WQS700B, `sin_x96056-20261012-24`), 2026-10-20.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T33378 | (229) Management - Telnet Server (IPv4) | [T33378/T33378.log](T33378/T33378.log) | **PASS**. The IPv4 telnet server was proven on the wire, with the enable and disable states both measured. |
| T47199 | (273) Management_Operation - Show warning message when user continues to use default PW | [T47199/T47199-fail.log](T47199/T47199-fail.log) | **FAIL**. A device still on the factory password `friend` gave no warning on any path: 0 warnings in 6 logins, with a banner marker proving the instruments see a message at that position. |
| T33416 | (283) Management_Triggers - Interface | [T33416/T33416.log](T33416/T33416.log) | **PASS**. `type interface` triggers activate on a real link event, send a per-trigger SNMP trap and log the activation; removal was proven under identical stimulus. |
| T33427 | (300) Management - Flexera Licensing | — | **NOT TESTED**. Needs a Flexera licence from Chris Robb; installing a licence is the Test Engineer's (STANDING-ORDERS §4). Dropped by the Test Engineer on 2026-10-19. |
