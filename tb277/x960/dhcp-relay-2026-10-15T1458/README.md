Testbox tb277, DUT AT-x960-56YSQ S/N A2WQS700B (`sin_x96056-20261012-24`), 2026-10-15.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T43852 | IPv4_DHCPServer - DHCP Relay | [T43852/T43852.log](T43852/T43852.log) | **PASS**. Crafted DISCOVERs and REQUESTs relayed 1:1 with giaddr rewritten and hops incremented, every reply returned to the right client, both zero-relay controls clean, and the hop threshold enforced at its documented default of 10 |
| T43850 | IPv4_DHCPServer - Option 82 | [T43850/T43850.log](T43850/T43850.log) | **PASS**. Circuit-id and remote-id correct on the wire, the ASCII override and its revert proven in captured frames, remote-id correctly refused while agent-option is disabled, all four information-policy actions correct, option 82 stripped from the reply per RFC 3046, and the settings survive a reboot |
