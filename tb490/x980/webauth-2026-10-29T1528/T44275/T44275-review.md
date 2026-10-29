# T44275 process review -- webauth-2026-10-29T1528
Reviewed 2026-10-30 by /create-logs from agent-a5c31a5061ad810f0.jsonl and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 16 | 32 | 25,826 | 2,140,446 | 15,377 | 21 | 464 s | 17,969 chars |

## Process taken
1. Added `--proxy HOST:PORT` to `tools/httpq.py` and checked it against a local listener (before the case segment).
2. STEP 0: web user ckproxy, default intercept ports read, `hostnet route-add` (8.8.8.0/24); health before; swi_dut.cfg saved.
3. STEP 1: proxied GET to 8.8.8.8:8080 without `intercept-port 8080` -> 4 SYNs unanswered.
4. STEP 2: `intercept-port 8080` -> HTTP 200 login page from the DUT's MAC; 8081 control timed out.
5. STEP 3: login POST through the proxy -> no response; three AW+ docs calls found the "No Proxy" requirement.
6. STEP 4-5: direct login (wrong 0/4, right 4/4); after login 8080 routed, not intercepted.
7. Health after, teardown (route-del proved), rcdiff.

## Wasted input
- Three allied-telesis-docs calls (about 9.5 k chars) to explain the proxied-POST behaviour. Now recorded in platforms/x980.md, so the next run reads that instead.

## Repetition
- none found.

## Accuracy risks
- STEP 3 is an observation, not graded. The PASS rests on STEPs 1, 2, 4 and 5, each with a control.

## Next run: expected outputs
- STEP 1: 0 replies to 4 SYNs on 8080.
- STEP 2: HTTP 200 with `<form ... action="...index.cgi">` from the DUT's MAC; 8081 timeout.
- STEP 3: login POST via the proxy -> "Remote end closed connection".
- STEP 4: direct POST to 192.168.50.1/index.cgi: wrong 0/4, right 4/4 (`W ... Authenticated`).
- STEP 5: after login, 8.8.8.8:8080 -> ICMP net-unreachable from the SVI, not the login page.

## Next run: scripts
- existing: `httpq --proxy`, `hostnet route-add|route-del`, `arpleg`, `tools/tb health`, `rcdiff.py`.

## Next run: references
- platforms/x980.md §1.1 (interception, intercept-port, after-login routing).
- AW+ Tips and Tricks rev D p.65 ("No Proxy" for the login network).
