# snmp-2026-10-16T1406

tb277, DUT swi_d (AT-x960-56YSQ, sin_x96056-20261012-24), 2026-10-16.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T43870 | IPv4_SNMP - SNMPv3 | [T43870/T43870.log](T43870/T43870.log) | **PASS**. All nine authored steps pass once the group's read view is defined: an in-view OID returns a value, an out-of-view OID is refused, an `excluded` entry removes exactly one OID, authPriv varbinds are encrypted on the wire against a plaintext control, and the whole discriminator survives a reboot and is removable. Produced F-12 (GetNext at the MIB-view boundary gets no response) and O-9 (the authored precondition omits the group's read view). |
