Testbox tb277, DUT AT-x960-56YSQ (swi_d, S/N A2WQS700B, `sin_x96056-20261012-24`), 2026-10-20.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T33407 | (274) Management_RADIUS - Local RADIUS Server | [T33407/T33407.log](T33407/T33407.log) | **PASS**. The DUT's own RADIUS server authenticated a user that exists only on it. |
| T33408 | (275) Management_RADIUS - Radius Client mode | [T33408/T33408.log](T33408/T33408.log) | **PASS**. A user held only on the RADIUS server logged in to the DUT, proven on the wire with 10 of 10 valid reply authenticators and paired Accounting Start/Stop. |
| T33409 | (276) Management_RADIUS - Radius Proxy | [T33409/T33409.log](T33409/T33409.log) | **PASS**. The proxy re-originated each request with a new id and Proxy-State, and the two legs are cryptographically independent. |
