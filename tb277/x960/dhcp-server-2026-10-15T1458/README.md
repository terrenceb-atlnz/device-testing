Testbox tb277, DUT AT-x960-56YSQ S/N A2WQS700B (`sin_x96056-20261012-24`), 2026-10-15.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T43851 | IPv4_DHCPServer - DHCP ARP Probe | [T43851/T43851.log](T43851/T43851.log) | **PASS**. Probe count and spacing honoured on the wire, zero probes when disabled and at `probe packets 0`, an answered probe withholds the address and records a conflict binding, `no` forms restore the TFS defaults, and the configuration survives a reboot |
| T43853 | IPv4_DHCPServer - DHCP 120-day lease | [T43853/T43853.log](T43853/T43853.log) | **PASS**. Option 51 = 10,368,000 s in OFFER and ACK with the binding expiring exactly 120 days out, the parser accepts 120 and refuses 121 and 999, 1-day and 1-hour controls measured in the same run, `no lease` restores the default, and the setting survives a reboot |
