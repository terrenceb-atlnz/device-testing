# T33366 process review -- auth-2026-10-29T1304
Reviewed 2026-10-29 by /create-logs from `agent-aa136ab5396975428.jsonl` and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 21 | 46 | 28,780 | 4,348,053 | 16,865 | 23 | 463 s | 10,640 chars |

Tools: Bash 19, ToolSearch 1, Monitor 1, SendMessage 2. Largest outputs read back:
`t66-s34-sniff.out` (1,576 chars), `cat t66-s1-sniff.out` (1,311), two `G=...` calls (884 for
setup, 734 for teardown), the `timeout 40` until-loop (671).

**Why the cache read is about 2.8x T33365's (1,556,955) for a similar case.** Tool output
does not explain it: the case read back only 10,640 chars, about 3k tokens. Cache read is
roughly (API calls) x (context already held). Both numbers were larger here:

- **More calls: 21 against about 9 for T33365 (about 2.3x).** The extra calls are all waits and
  the S5 retry (see Process taken 9 to 17), plus 2 calls per capture leg.
- **A larger context: 195,474 tokens of cache read on the first call, rising to 223,177 on
  the last.** T33365 ran at 166,800 to 181,844 tokens (about 1.2x less). Between the two cases
  the tester read 4 documentation results (12,343 chars), wrote and committed `tools/hostnet.py`,
  and edited `tools/tb`. That work counts as group overhead, but every T33366 call paid for it
  again as cache read.
- 2.3 x 1.2 = 2.8. Calls 9 to 11 and 13 to 15 alone cost about 1.24M of cache read.

## Process taken
(Each call appears twice in the transcript, once with a `cd <repo> &&` prefix. The 23 below are
unique tool-use ids.)
1. One Bash: setup reads (`show system`, `show clock`, `show auth-web-server`,
   `show auth supplicant brief`, `show ip route`), health before, `user ckweb` under
   `radius-server local`, running-config to `swi_dut.cfg` with `rc2cfg.py`, `hostnet route-add`.
   A good batch: 6 jobs in one call, 884 chars back.
2. S1 capture `t66s1` started in the background (`arpleg --sniff-only`, 40 s).
3. S1 requests: `httpq` to 8.8.8.8 ports 80, 8080, 8081.
4. S3 configuration: `intercept-port 8080` and `show auth-web-server`.
5. `cat t66s1-sniff.out` to read the S1 capture (1,311 chars).
6. S3/S4 capture `t66s34` started in the background (75 s).
7. S3 requests (8080, 8081), S4 configuration (`intercept-port any`), S4 request (8081).
8. S5 setup: ping before, the login POST, ping after, `show auth supplicant brief` (grep).
9. `ls` / `tail` on the background task to see if `t66s34` had finished. It had not.
10. `ToolSearch select:Monitor`.
11. `Monitor` on the `pcaps:` line, 3 min.
12. A Bash `timeout 100` until-loop on the same file, then the capture (1,576 chars). Calls 9 to
    12 are 4 calls for one wait.
13. S5 capture `t66s5` started in the background (35 s).
14. S5 requests 4 s later, then a wait. The capture had 0 frames: tcpdump was not yet running.
15. `hostnet show` and `tools/tb nics tb5` to rule out a missing route on tb5. The route was
    PRESENT.
16. S5 capture `t66s5b` started in the background (45 s).
17. `tools/tb ps tb5 'tcpdump.*t66s5b'` until-loop (`timeout 40`), then the requests and the
    capture (671 chars). This is the graded S5.
18. Health after, with `--before`.
19. Teardown: two `no ... intercept-port`, `no user ckweb`, `show running-config`, `rcdiff.py`
    against the group baseline, `hostnet route-del`, `hostnet show`.
20. `SendMessage` to the sentinel, answering its question about the first S5 attempt.
21. Wrote `work/run1.log` with a heredoc and `tools/tb tail` of the health file.
22. Updated `CAMPAIGN-QUEUE-2026-10-29T1304.md` (results row, next case).
23. `SendMessage` `RESULT T33366 PASS`.

## Wasted input
- **Call 5, `cat t66s1-sniff.out | head -30` (1,311 chars).** All of it was needed as evidence.
  The separate call was the cost: a `pcaps:` until-loop folded into call 3 would have read it
  in the same turn.
- **Calls 9 to 12 (status `ls`, ToolSearch, Monitor, then a Bash until-loop anyway).** Only call
  12 was needed. The Monitor was armed and then not used, because call 12 blocked on the same
  condition. 3 calls wasted, about 620k tokens of cache read.
- **Calls 13 to 15 (the first S5 attempt and its check).** 3 calls, about 630k tokens of cache
  read, plus a sentinel question and the answer in call 20. The capture started 4 s before the
  requests (00:52:58 -> 00:53:02 UTC), and `arpleg` over `sudotool` had not started tcpdump by
  then. S1 (7 s gap) and S3/S4 (8 s gap) worked only because the gap was longer.
- Nothing large was read whole. Every console read was grepped into the turn and saved to a file.

## Repetition
- **Start capture, then send requests, as 2 calls per leg, 4 times (S1, S3/S4, S5, S5b).** One
  call per leg would do: start the capture with `&`, wait for `tools/tb ps`, send the requests,
  then wait for `pcaps:`. Call 17 already has that shape, except for the background start.
- **`H="tools/tb tool tb5 auth1304 httpq"` plus `sed -n 3p` / `grep -o '<form'` repeated in 5
  calls.** A helper would print the status and the form action in one line (see Scripts).
- The S1 sniff wait was done 3 different ways in one case (a `cat` at call 5, the Monitor at
  call 11, a `timeout` loop at calls 12, 14 and 17).

## Accuracy risks
- **The first S5 attempt (`t66s5`, 0 frames) must not be graded.** It is not in the final log.
  The graded S5 rests on `t66s5b`, where `tools/tb ps` confirmed tcpdump was running first, and
  the capture holds both SYNs and the DUT's 2 ICMP t3/c0. Sound.
- **Errno 101 is the host's report of the DUT's ICMP net unreachable.** This is an inference,
  but `t66s5b` shows the ICMP from 192.168.50.1 to 192.168.50.10 next to the SYNs. Good enough.
- **"4 SYNs to 8081, no answer" in the `t66s34` capture rests on the tester's reading.** The
  arpleg summary hides `... 5 more distinct flow(s)`. To close it, read the full pcap on tb5:
  `tcpdump -nr /tmp/auth1304/t66/t66s34-eth6.pcap 'tcp port 39278'`.
- **The S3 and S4 `show auth-web-server` reads were cut to the two intercept lines** in the
  working log. The final log says so in its Method line.
- **Claims left out of the final log for lack of a source in `run1.log`:**
  - The command that printed the S5 supplicant table. The transcript (call 8) shows it was
    `show auth supplicant brief`, filtered with `grep 'port1.0.81 \|Num:'`, but `run1.log`
    does not name it. The final log calls it "the DUT's supplicant table".
  - The setup `show auth supplicant brief`. `run1.log` holds only `Interface port1.0.81`,
    but the tester's grep at call 1 printed `No supplicants`. The working log lost the line,
    so the baseline "no session at the start" is not in the final log as output. The ping
    0 of 4 before login in STEP 4 stands in for it.
  - `show ip route` output. `run1.log` gives only the tester's summary ("connected
    10.38.235.0/27 eth0 and 192.168.50.0/24 vlan1 only"), so the final log states it in prose.
    The two `C` lines were in the call 1 output.
  - The client path through tb5's swi_x530 and swi_x950. That comes from the dispatch and from
    T33375's working log. `run1.log` does not name it, and no ports for it are recorded.
- **Bench path:** the tb5 route was PRESENT at setup (route-add AFTER) and at teardown
  (route-del BEFORE). Call 15 confirms it was PRESENT during S5.

## Next run: expected outputs
| step | what this bench gave |
| --- | --- |
| help | `auth-web-server mode ?` -> `% Unrecognized command`. No `gateway` keyword. `intercept-port` is present |
| baseline | `HTTP Intercept Port No: 80`, `HTTPS Intercept Port No: 443` |
| DUT routing | connected only: 10.38.235.0/27 eth0, 192.168.50.0/24 vlan1, so no route to 8.8.8.8 |
| S1 port 80 | `HTTP 200 OK` with `<FORM action="http://192.168.50.1/index.cgi" ... name="AUTH" method="POST">`. The SYN-ACK and PA "from 8.8.8.8:80" carry `e0:1a:ea:d5:04:56` |
| S1 controls | 8080 and 8081: `TRANSPORT FAILED: <urlopen error timed out>`, 4 SYNs each, 0 answered |
| S3 | `HTTP Intercept Port No: 80 8080`. 8080 -> login page, 8081 still times out |
| S4 | `HTTP Intercept Port No: any`. 8081 -> login page. The running-config keeps BOTH `intercept-port any` and `intercept-port 8080`; remove both at teardown |
| S5 login | ping 0 of 4 -> POST `USERNAME=ckweb&PASSWORD=...&ACTION=login` -> 200 -> ping 4 of 4. `port1.0.81 1 W 0090.0b2a.11c3 Authenticated 192.168.50.10 ckweb` |
| S5 after | both requests: `[Errno 101] Network is unreachable`. Capture: 1 SYN each to the DUT's MAC, 2 x `ICMP t3/c0 192.168.50.1 -> 192.168.50.10` |
| capture start | `arpleg --sniff-only` through `tools/tb sudotool` needs more than 4 s before tcpdump runs. Always gate on `tools/tb ps tb5 'tcpdump.*<tag>'` |

## Next run: scripts
- **Existing, reuse:** `tools/hostnet.py` (`route-add` / `route-del` / `show`) through
  `tools/tb sudotool tb5 <tag> hostnet ...`. `tools/httpq.py` with `--method POST --data`.
  `tools/arpleg.py --sniff-only --filter`. `tools/tb ps`. `tools/rc2cfg.py`, `tools/rcdiff.py`.
- **Proposed: a `--ready` option for `arpleg.py --sniff-only`** (or a `tools/tb sniff` action).
  It would start the capture, return only once tcpdump is running, and leave a handle to wait on.
  Arguments: `--tag --iface --filter --wait`. This removes the S5 retry and the 2-calls-per-leg
  pattern.
- **Proposed: `tools/webprobe.py URL...`** (or an `httpq --summary` flag). For each URL it would
  print one line: status or transport error, plus the `<FORM action=...>` if there is one.
  This replaces the `sed -n 3p` / `grep -o '<form'` repeated in 5 calls.
- **Proposed: one `tools/tb waitfile <path> <regex> <timeout>`** for the background-capture
  waits. Use it in place of the mix of `cat`, Monitor and inline `timeout` loops.

## Next run: references
- `platforms/x980.md` (lines 17-24) already records, from this case, that
  `auth-web-server mode` is absent, that the default intercept is port 80, and that
  `intercept-port any` and `intercept-port 8080` are both kept in the running-config. Read it
  first next time.
- Command Reference 5.5.6-1, `auth-web-server intercept-port` (the default of port 80 and the
  `any` keyword). AW+ Technical Tips and Tricks rev D, p.73 and p.78 (the older modes). Cite
  them; do not search for them again.
- `tools/README.md`, the `hostnet` and `arpleg --sniff-only` entries.
- **Left for a next run:** HTTPS interception (port 443, with the T33365 trustpoint), and the
  "promiscuous" gateway behaviour on a build that still has `auth-web-server mode`.
