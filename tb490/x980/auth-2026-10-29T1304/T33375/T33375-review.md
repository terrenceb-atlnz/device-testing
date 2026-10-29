# T33375 process review -- auth-2026-10-29T1304
Reviewed 2026-10-29 by /create-logs from agent-aa136ab5396975428.jsonl and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 14 | 28 | 26630 | 1894840 | 18097 | 14 | 430 s | 11752 chars |

Largest outputs: `tools/tb ckcon` STEP 3 config + legs (2410), `tools/tb health` after (1324),
`ckcon` show log grep (1324), `ckcon` STEP 4 (1274), `head -c 900 t75-s2-get.out` (1195).

Cache read is 97% of the tokens. 1894840 / 14 calls = about 135k tokens carried into each call.
The outputs this case read back total only 11752 chars. The cost is the context size at the
start of the case, not this case's reads (see the group REVIEW.md).

Note on the transcript: every tool call appears twice in the jsonl (two rows per message).
The segment is 13 unique Bash calls plus 1 SendMessage = 14 tool calls.

## Process taken
The segment runs from the first call touching `T33375/` to the `RESULT T33375` SendMessage.
`show system` and the health-before read (13:30:51 NZDT) ran before the segment, in group
overhead. Call 1 pulled the health-before file from the box into scratchpad.

1. Bash (58): `tools/tb tail` of the health-before file to scratchpad; wrote the run1.log header
   (session facts, case, devices, `show system`, health-before raw).
2. Bash (854): `ckcon --verbatim`: add RADIUS users `ckweb` and `02-00-5e-c0-ff-01`,
   `dot1x initialize interface port1.0.81`, `show auth supplicant brief`. (STEP 0)
3. Bash (1003): `show running-config` -> `tools/rc2cfg.py` -> `T33375/swi_dut.cfg`; eth6 ping;
   arpleg leg t75s1u for the unknown MAC. (STEP 1)
4. Bash (677): STEP 1 supplicant read; httpq GET `/`, GET the login page, wrong-password POST;
   eth6 ping; supplicant read. (STEP 2 control)
5. Bash (1195): `head -c 900` / `head -8` / `grep -o '<input'` on the saved httpq files, to learn
   httpq's output format.
6. Bash (652): correct-password POST; eth6 ping; `show auth supplicant brief` and
   `show auth supplicant interface port1.0.81`. (STEP 2)
7. Bash (2410): `auth-mac enable`, `show running-config interface port1.0.81`; four arpleg legs
   (k1, k2, u, u2); eth6 ping. (STEP 3)
8. Bash (1324): `show log | include` the case's MACs and users, last 30 lines.
9. Bash (1274): remove RADIUS user `00-90-0b-2a-11-c3`, `dot1x initialize`, eth6 ping, web
   login POST, three arpleg legs, eth6 ping, supplicant read. (STEP 4)
10. Bash (1324): `tools/tb health --before ...` (health after); teardown; `tools/rcdiff.py`.
    rcdiff failed: `$G` was not set in this shell.
11. Bash (392): rcdiff re-run with the full path. Result: only the echoed prompt line differs.
12. Bash (520): appended the case body to run1.log from the scratchpad files.
13. Bash (69): queue row update and commit e1f54d4.
14. SendMessage (82): `RESULT T33375 PASS`.

## Wasted input
- Call 5, 1195 chars: re-read three saved httpq files to learn the output format. That format
  is in tools/README.md `### httpq.py` (line 1489). The login form is already shown in
  tb277/x960/authmodes-2026-10-23T1304/T44279/T44279.log STEP 3. A narrower read:
  `grep -a -m3 'HTTP/\|<FORM\|refresh' t75-s2-get.out` (under 300 chars).
- Call 7, 2410 chars: it read every frame line of four arpleg legs. The decision needed only
  the reply count per leg. A one-line-per-leg summary (see Scripts) would be about 300 chars.
  The full frame lines can go to run1.log without being read back.
- Call 8, 1324 chars: a broad `show log | include` with seven patterns, last 30 lines. The
  health-after diff (call 10) printed the same success lines by signature. Reading the log
  once, after the last step, would have done.
- run1.log lines 124-201: the health-before raw copies the whole `show cpu` process table
  (about 80 lines). It was written to file, not read into context. It only makes the
  working log longer. The health summary line (line 80) holds everything the final log used.

## Repetition
- Calls 10 and 11: rcdiff ran twice. Call 10 used `$G`, which a fresh Bash shell does not
  have. Define the variables in every call, or use full paths.
- The sequence `dot1x initialize interface port1.0.81`, `@sleep 3`, `show auth supplicant
  brief` was built by hand twice (calls 2 and 9). It is a candidate for one helper.
- The same arpleg argument list was typed for 8 legs (one variable `L` in calls 7 and 9 helped).

## Accuracy risks
- Several `show auth supplicant brief` reads were saved through
  `grep 'port1.0.81 \|Num:'` (calls 4, 6). run1.log then has only part of the output and no
  echoed command line (run1.log lines 246-251, 261-265, 271-279, 333-344). The final log adds
  `x980-CDQ#show auth supplicant brief` above those excerpts. That command is an inference
  from the output's shape. run1.log labels two of these reads `awplus#`, but the device
  prompt is `x980-CDQ#`. Fix: capture these reads with `ckcon --verbatim` and keep the whole
  output in run1.log.
- STEP 2: the HTTP reply is the same for a wrong and a correct password (both refresh to
  `index.cgi?authenticating=1`). The verdict rests on the DUT supplicant table and the eth6
  ping. Both were captured, so the verdict holds. A next run must not grade on the HTTP body.
- STEP 3: the inherited rig made eth6's MAC `00-90-0b-2a-11-c3` a RADIUS user (group TWOSTEP).
  With `auth-mac enable` on, eth6 MAC-authenticated instead of logging in by web. STEP 4 had
  to remove that user to get a web session beside a MAC one. The next run should plan this
  from the start.
- STEP 3: `auth-mac enable` ended eth6's existing web session (DUT log 00:33:28 UTC). The tester
  recorded it and did not grade it as a defect. Whether that is expected behaviour is a
  question for the Test Engineer. This review does not change the verdict.
- STEP 4: run1.log has no DUT log line for the STEP 4 web and MAC logins. The proof is the
  supplicant table and the pings, which is enough.
- Claims the final log left out for lack of a source in run1.log:
  - why the probe is ICMP and not ARP (`auth forward arp` forwards ARP for clients that are
    not logged in). run1.log uses `--icmp` but does not say why. T44279.log explains it.
  - whether swi_dut is a stack. run1.log does not say.
- The correct web password is redacted (`<correct>`) in run1.log's httpq lines, but it is in
  clear in the STEP 0 config lines and in swi_dut.cfg. The final log copies those lines as
  the device printed them.

## Next run: expected outputs
| step | expected on this bench |
| --- | --- |
| 0 | after `dot1x initialize interface port1.0.81` + 3 s: `totalSupplicantNum: 0`, `No supplicants`; log `Supplicant webuser unauthorized, Mac 0090.0b2a.11c3` |
| 1 | eth6 ping 0 of 4; unknown MAC 02:00:5e:c0:ff:09 leg: x4 `t8/c0`, no `t0/c0`; `port1.0.81  1    W    0200.5ec0.ff09 Connecting` |
| 2 | GET `/` -> 200 with `<FORM action="http://192.168.50.1/index.cgi" ... method="POST">`; wrong password -> W Connecting, ping 0 of 4, radiusd `Login incorrect (pap: ...)`; correct -> `W    0090.0b2a.11c3 Authenticated     192.168.50.10   ckweb`, `webBasedAuthenticationSupplicantNum: 1`, ping 4 of 4 |
| 3 | known MAC 02:00:5e:c0:ff:01: first leg x3 `t0/c0` (3 of 4), second leg 4 of 4; unknown MAC 0 of 4 twice; `authenticationMethod: mac/web`; side effect: `Supplicant ckweb unauthorized`, then eth6 shows as `M    0090.0b2a.11c3 Authenticated` |
| 4 | after removing user `00-90-0b-2a-11-c3`: `No supplicants`, eth6 ping 0 of 4; after the POST: `macBasedAuthenticationSupplicantNum: 1`, `webBasedAuthenticationSupplicantNum: 1`, W ckweb and M ff01 Authenticated, W ff09 Connecting; eth6 ping 4 of 4 |
| health | CLEAN; reboots 29 entries, newest 2026-10-28 21:19:45; exception log None; memory free about 15.37 GB of 16033676 kB |

## Next run: scripts
- Existing, used well: `tools/tb sudotool <TB> <scope> arpleg ... --icmp`, `tools/tb tool <TB>
  <scope> httpq`, `tools/tb health --before <json>`, `tools/rc2cfg.py`, `tools/rcdiff.py`.
- Proposed: `tools/tb authlegs <TB> <scope> --iface eth6 --target 192.168.50.1
  --gw-mac e0:1a:ea:d5:04:56 --count 4 --client <tag>=<MAC>=<IP> [...]`. It runs one arpleg
  leg per client, keeps the full output in files, and prints one line per leg:
  `tag MAC sent=4 replies=N`. It would replace the read-back in calls 7 and 9.
- Proposed: `tools/tb webauth <TB> <scope> --url http://192.168.50.1/index.cgi --user ckweb
  --password <pw> --iface eth6 --ping 192.168.50.1`. It does the POST, then the ping, and
  prints `POST <code>, ping n/4`. The HTTP body does not show the result, so the ping must
  always follow.
- Proposed: `tools/tb authreset <TB> <scope> <u> <baud> <port>`. It sends
  `dot1x initialize interface <port>`, waits 3 s and prints `show auth supplicant brief`
  verbatim. Used twice in this case (calls 2 and 9).

## Next run: references
- platforms/x980.md §1.1: no `clear auth` (use `dot1x initialize interface`), and
  `auth-mac enable` ends an existing web session.
- tb490/x980/CAMPAIGN-QUEUE-2026-10-29T1304.md lines 97 and 154: the inherited local RADIUS
  users, including `00-90-0b-2a-11-c3` in group TWOSTEP (eth6's own MAC).
- tools/README.md `### httpq.py` (line 1489): httpq's arguments and output.
- tb277/x960/authmodes-2026-10-23T1304/T44279/T44279.log: STEP 3 (the web login is one form
  POST) and the topology note on why the probe is ICMP when `auth forward arp` is on.
