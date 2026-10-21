Testbox tb277, DUT AT-x960-56YSQ (swi_d, S/N A2WQS700B, `sin_x96056-20261019-27`), 2026-10-21.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T44296 | (259) Management_LLDP - LLDP | [T44296/T44296.log](T44296/T44296.log) | **PASS**. Twelve steps designed for a case with no authored steps, every one graded on frames: transmit and receive proven independent, ageing timed against a chosen TTL, traps caught against a silent control, neighbours confirmed on RSTP-blocked ports, and the configuration surviving a cold boot on the wire. |
| T33398 | (260) Management_LLDP - LLDP-Med | [T33398/T33398.log](T33398/T33398.log) | **PASS**. A Class III endpoint drew a 7-TLV reply carrying exactly the configured voice policy, fast start measured at 3 frames 1.00 s apart, and a non-default priority survived a cold boot. |
