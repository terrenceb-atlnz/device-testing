tb490 (DUT swi_dut, AT-x980-16CDQ, awplus_main-20261029-90) with client traffic from tb5, 2026-10-29.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T33375 | (219) Authentication&Security - MAC Auth/Web Auth | [T33375/T33375.log](T33375/T33375.log) | **PASS**. A known MAC passed MAC authentication (4 of 4 pings) and an unknown MAC did not (0 of 4). A wrong web password got 0 of 4 and the correct one got 4 of 4. MAC and web sessions were held on the port at the same time. |
| T33365 | (205) Authentication&Security_WebAuthentication - Public key encryption(X509) | [T33365/T33365.log](T33365/T33365.log) | **PASS**. The DUT's own X.509 certificate was bound to the web login page. The client accepted it with the exported CA and refused it without. HTTPS login: wrong password 0 of 4, correct password 4 of 4. Authored step 6 (external freeradius) was not run. |
| T33366 | (206) Authentication&Security_WebAuthentication - Promiscuous / Intercept web Authentication | [T33366/T33366.log](T33366/T33366.log) | **PASS**. An unauthenticated HTTP request to 8.8.8.8 port 80 got the DUT's login page. Ports 8080 and 8081 were intercepted only after `intercept-port` was set. After login, the DUT routed the traffic instead. |
| T33357 | (194) Authentication&Security_IEEE 802.1XEncryptionType - EAP-TLS | [T33357/T33357.log](T33357/T33357.log) | **PASS**. A client certificate from the DUT's local CA got EAP-Success and 4 of 4 pings. A certificate from another CA got EAP-Failure and 0 of 4. The client used TLS 1.2. |
