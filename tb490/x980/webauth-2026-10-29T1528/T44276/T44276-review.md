# T44276 process review -- webauth-2026-10-29T1528
Reviewed 2026-10-30 by /create-logs from agent-a5c31a5061ad810f0.jsonl (runs 1-2) and
agent-a68a7860f1d768bd5.jsonl (runs 3-5), and the working files.

## Token usage
| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| runs 1-2 (group A tester, T44276 segment) | 26 | 52 | 37,184 | 4,384,672 | 21,139 | 26 | 691 s | 34,596 |
| runs 3-5 (one tester, whole transcript) | 84 | 176 | 356,790 | 7,845,207 | 62,637 | 84 | 3,559 s | 84,238 |
| **case total** | 110 | 228 | 393,974 | 12,229,879 | 83,776 | 110 | 4,250 s | 118,834 |

The case cost about 3.5 times T44274. Five runs were needed where one would have done (below).

## Process taken
1. Run 1 (10-29): single DISCOVER per try in 5 configurations, no OFFER, graded FAIL.
2. Run 2: after the sentinel's suggestion, `service dhcp-server` on + retries -> OFFERs; steps 1-4 PASS, step 5 (login from the lease) NOT MEASURED: no root route on tb5. PARTIAL.
3. Run 3 (10-30): route60 approved and added to `tools/hostnet.py`; tb5 eth6 had lost 192.168.50.10, so the route failed. PARTIAL.
4. Run 4: the Test Engineer restored eth6's address; step 5 only, PASS.
5. Run 5: the full case in one run for the final log; step 1a showed the DHCP serves with the service OFF. PASS.

## Wasted input
- `sed -n '1495,1541p;1152,1237p' tools/README.md ...` (14,068 chars, run 5): only the `dhcp4`, `arpleg`, `httpq` and `hostnet` usage lines were needed. `grep -n -A6 '^### .dhcp4' tools/README.md` and the same for each tool would do (about 2 k).
- `sed -n '55,110p' .../run2.log` (5,568 chars) re-read in run 5 for the setup lines; the queue's group A recipe plus run 4's setup .out held them.
- Three AW+ docs calls in runs 1-2 (about 13 k chars) on web-auth DHCP. The command reference was the deciding source and is now cited in platforms/x980.md.

## Repetition
- **The whole case ran five times.** The root causes:
  - run 1 sent one DISCOVER per try, and a MAC's first DISCOVER is never answered;
  - run 2 then attributed the missing OFFER to `service dhcp-server` and never tested the service off with retries;
  - step 5 needed a root route that was not approved until 10-30;
  - runs 3 and 4 re-ran only step 5, so no single run had every step.
- The DUT setup (`auth-web-server dhcp ipaddress`, lease, RADIUS user, `dot1x initialize`) was rebuilt by hand in runs 2-5.

## Accuracy risks
- **A wrong platform fact was recorded on 10-29** ("needs `service dhcp-server`") from an under-sampled control. Run 5 corrected it (platforms/x980.md §1.1, 2026-10-30). Any control that expects "no OFFER" must send at least two DISCOVERs per MAC.
- 192.168.50.254/24 (inside vlan1's subnet) "got no OFFER" in run 1, also with single DISCOVERs, so it is unproven either way.
- Step 5's login was sourced from 192.168.50.10 through a host route, not from the leased address. The DUT accepted it. Whether that meets the case's intent is the Test Engineer's call (CAVEAT in the final log).
- The first ICMP leg after a web login lost replies twice (3/4 in run 4, 1/4 in run 5); the next leg was 4/4. Grade on the second leg, or send 8.

## Next run: expected outputs
- web-auth DHCP not configured: 0 OFFERs in 5 DISCOVERs.
- web-auth DHCP configured (service on OR off): first DISCOVER per MAC -> none; later ones -> OFFER/ACK from the DUT's MAC, server_id/router 192.168.60.1, /24, lease 20 (default), T1 10, T2 12.
- `auth-web-server dhcp lease 45` -> option 51 = 45; `lease 300` -> rejected, range `<20-60>`.
- addresses: .2, .3, ... in DISCOVER order across MACs.
- login at 192.168.60.1: wrong pw -> `Connecting`, "Web Authentication failed", ICMP 0/4; right pw -> `Authenticated <user>`, "Web Authentication successful", ICMP 4/4 on the second leg.

## Next run: scripts
- existing: `tools/tb sudotool tb5 <run> dhcp4 client eth6 --mac <mac> --wait 10` (+ `dhcp4 decode`), `hostnet route60-add|route60-del`, `httpq`, `arpleg`, `tools/tb health`, `rcdiff.py`.
- proposed: `tools/dhcpleg.py` -- send K DISCOVERs per MAC for a list of MACs and print one row per try (MAC, OFFER yiaddr, ACK, lease, server MAC). Arguments: `--iface eth6 --macs <m1,m2> --tries 3 --wait 10`. It makes the first-DISCOVER drop impossible to miss.

## Next run: references
- platforms/x980.md §1.1 "Web-auth DHCP server" (corrected 2026-10-30).
- queue tb490/x980/CAMPAIGN-QUEUE-2026-10-29T1528.md, Group A recipe (lines 186-229) and Issues (the route60 and eth6 notes).
