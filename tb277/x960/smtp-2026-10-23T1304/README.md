# smtp-2026-10-23T1304

Testbox tb277, DUT swi_d (AT-x960-56YSQ), 2026-10-23.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T33368 | (209) Authentication&Security_SMTP - SMTP server authentication | [T33368/T33368.log](T33368/T33368.log) | **PASS**. SMTP AUTH proved on the wire for PLAIN, LOGIN and CRAM-MD5, each accepted at 235 with the correct credential and refused at 535 with a wrong one, against an OFF baseline that sends no AUTH; the DUT refuses to downgrade when a server offers no AUTH, and the fourth mechanism, oauth2, is an inert command on this build and is graded UNSUPPORTED at step level. |
