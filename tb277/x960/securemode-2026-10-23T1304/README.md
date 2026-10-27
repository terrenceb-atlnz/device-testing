# securemode-2026-10-23T1304

Testbox tb277, DUT swi_d (AT-x960-56YSQ), 2026-10-23 to 2026-10-28.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T44287 | (228) ..._CyptSecureMode - Disable Telnet, SNMPv1/v2, all privilege levels except 1 and 15, weak crypto | [T44287/T44287.log](T44287/T44287.log) | **PASS**. All four clauses of the title driven and confirmed against a normal-mode control: telnet refused by TCP reset where a login had worked, an SNMPv1/v2c GET that returned the software version stopped answering, privilege 7 refused by name while privilege 1 was accepted, and MD5 refused in two independent features with SHA controls accepted. RSA1 and DSA are graded UNSUPPORTED, because this build offers neither keyword in normal mode either, so secure mode has nothing to withdraw. Fifteen limbs, each with its own verdict; eight findings recorded, four of them product deviations worth a developer. |
