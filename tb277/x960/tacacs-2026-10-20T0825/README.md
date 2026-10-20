Testbox tb277, DUT AT-x960-56YSQ (swi_d, S/N A2WQS700B, `sin_x96056-20261012-24`), 2026-10-20.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T33411 | (278) Management_TACACS+ - Authentication | [T33411/T33411.log](T33411/T33411.log) | **PASS**. An account held only on the TACACS+ server logged in to the DUT, proven on three independent instruments. Enable authentication and reboot persistence are NOT MEASURED. |
| T33410 | (277) Management_TACACS+ - Accounting | [T33410/T33410.log](T33410/T33410.log) | **PASS**. Accounting works, with three defects recorded; each is an attribution or coverage gap, not a failure to account. Reboot persistence is NOT MEASURED. |
| T33412 | (279) Management_TACACS+ - Logging | [T33412/T33412.log](T33412/T33412.log) | **PASS**. Five of the seven logging specifications were driven on this bench. Three are satisfied, two reveal gaps, and two could not be measured. |
