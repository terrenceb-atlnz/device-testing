tb490 (DUT swi_dut AT-x980-16CDQ, client on tb5), web authentication, 2026-10-29 to 2026-10-30.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T44274 | (204) Authentication&Security_WebAuthentication - Multiple Authentication | [T44274/T44274.log](T44274/T44274.log) | **PASS**. Web, MAC and 802.1X clients were authenticated together on one port, 4 of 4 ICMP each. Wrong-password and unknown-MAC controls got 0 of 4. |
| T44275 | (207) Authentication&Security_WebAuthentication - Proxy Server for Web Authentication | [T44275/T44275.log](T44275/T44275.log) | **PASS**. With intercept-port 8080, a proxied request got the DUT's login page. Without it, the request got no answer. |
| T44276 | (208) Authentication&Security_WebAuthentication - DHCP Server for Web Authentication | [T44276/T44276.log](T44276/T44276.log) | **PASS**. The web-auth DHCP server leased addresses to clients that had not logged in, and a client then logged in. It also serves with `no service dhcp-server`. |
