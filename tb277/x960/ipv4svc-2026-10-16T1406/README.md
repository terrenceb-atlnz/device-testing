# ipv4svc-2026-10-16T1406

tb277, DUT swi_d (AT-x960-56YSQ, S/N A2WQS700B, sin_x96056-20261012-24), 2026-10-16.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T44181 | (51) IPv4 - Ping Polling | [T44181/T44181.log](T44181/T44181.log) | **PASS**. All 11 authored steps exercised: 100 instances is the measured maximum, the interval, fail-count and up-count behaviour was read off the wire and confirmed by the DUT's own trigger log to within ~1 s, and removal and reboot persistence were both proven in the dataplane. |
| T44378 | (52) IPv4 - UDP Broadcast Helper | [T44378/T44378.log](T44378/T44378.log) | **PASS**. Nothing relayed by default; both all-ones and subnet-directed UDP broadcasts relayed on a helped port while an unhelped port never was; the port list and the helper address proven independent; a helper address that is a connected subnet's broadcast address forwarded as a true link-layer broadcast. |
| T44182 | (53) IPv4 - Directed Broadcast Forwarding | [T44182/T44182.log](T44182/T44182.log) | **PASS**. Dropped by default and when enabled on the ingress interface; the identical frames forwarded and translated to a link-layer broadcast when enabled on the destination subnet's interface; the optional standard ACL filters on source and is consulted per packet, proven by inverting it. |
