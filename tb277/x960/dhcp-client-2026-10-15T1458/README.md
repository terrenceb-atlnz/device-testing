Testbox tb277, DUT AT-x960-56YSQ S/N A2WQS700B (`sin_x96056-20261012-24`), 2026-10-15.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T35370 | IPv4_DHCPClient - DHCP Extended ID | [T35370/T35370.log](T35370/T35370.log) | **PASS**. The client's whole identity surface measured on the wire — option 61 (type byte plus SVI MAC), option 12 hostname, option 124 carrying IANA enterprise 207, and 125 added to the parameter request list — each absent in the baseline and each removed cleanly by its `no` form |
| T43854 | IPv4_DHCPClient - DNS Relay | [T43854/T43854.log](T43854/T43854.log) | **PASS**. 5 of 5 queries forwarded upstream and 5 correct answers returned, 0 forwarded in the disabled control with the same queries demonstrably on the wire, a DHCP-learned name-server imported and genuinely used, and the settings surviving a reboot. The forwarding-cache limb is UNMEASURED, with its reason in the log |
