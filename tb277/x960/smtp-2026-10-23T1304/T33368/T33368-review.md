# T33368 process review -- smtp-2026-10-23T1304

Reviewed 2026-10-28 by /create-logs from `agent-a1874e13c44700abf.jsonl` and the working files.

This is the reviewer's own analysis. It is not attached to the case and it may name other
runs, other campaigns and the agent's own process. It changes no verdict.

## Token usage

| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T33368 | 65 | 130 | 135,356 | 8,929,468 | 12,792 | 69 | 2,736 s (45 min) | 72,466 chars |
| overhead | 10 | 20 | 50,082 | 880,177 | 932 | 16 | 104 s | 47,282 chars |
| **total** | **75** | **150** | **185,438** | **9,809,645** | **13,724** | **85** | **2,840 s (47 min)** | **119,748 chars** |

Tool mix in the case segment: Bash 65, Write 2, ToolSearch 1, SendMessage 1.

**How to read the split.** `case_tokens.py` cuts a case segment at the tester's first tool call
that touches the case folder, and everything before it is group overhead. In a single-case group
that normally pushes almost the whole run into `overhead` and makes the case row look cheap.
That did **not** happen here: the tester wrote into `T33368/` early, so the case row holds 65 of
the 75 calls and the overhead row holds only the pre-case gate work. The numbers above are
usable as they stand. The one thing the overhead row understates is reading: 47 KB of tool
output for 16 calls is 2.9 KB per call, against 1.1 KB per call in the case segment.

## Process taken

1. Gate, 10 items: `precheck` (console free, one standing `ser2net` process), `scratch`,
   `template`, `probe --read-only`, `peek`.
2. `probe` was run **twice**. The first invocation passed `--outlet 1`; the flag wants
   `--outlet u2=1`.
3. Read `logged-output.md` §2 and four separate ranges of the campaign queue file.
4. Probed the mail CLI surface read-only with `qmark`, prefix by prefix. This found that the
   grammar recorded at triage (`mail smtpserver <ip> authentication <mech>`) does not parse.
5. Wrote `tools/smtpsrv.py` and validated it offline with `python3 smtplib` before it touched
   the bench: three mechanisms, right credential and wrong, with and without `--require-auth`.
6. Applied the DUT setup (server address, port, from-address) and captured `swi_d.cfg`.
7. First send attempt used `ckcon`. `mail to <addr> subject <s>` is interactive, so `ckcon`'s
   next command was typed into the message body, it waited out its 90 s timeout and left the
   console parked in body-entry mode. Cost about 4 minutes.
8. Wrote `tools/conkey.py` to recover: raw keys to a console that is not at a prompt, no login.
   Registered it as a `tools/tb` console action.
9. Ran six server windows (L0b, A, B, C, E, F), each one `smtpsrv.py` invocation, with several
   legs sharing a window.
10. Took an independent `tcpdump` on eth3 for the Postfix leg and decoded it with
    `tools/tcpflow.py`.
11. Health before and after, probe after, boot re-read, teardown, running-config diff.

## Wasted input

| call | size | the narrower read |
| --- | --- | --- |
| `sed -n '/^## 2\./,/^## 3\./p' logged-output.md \| head -120` | 7,192 chars | §2 is the working-log rules. The tester needed the `RESULT` line format and the §8 health block, about 25 lines. Read those line ranges, or have the dispatch quote them. |
| four scratchpad Bash calls during the `smtpsrv.py` offline validation | 4,831 + 4,413 + 3,510 + 2,741 = 15,495 chars | Each printed a full `smtplib` transcript. The validation needs one line per mechanism: `PLAIN ok / PLAIN wrong 535 / LOGIN ok / ...`. Six lines instead of 15 KB. Keep the transcripts in a file and read them only on a failure. |
| `sed -n '20,108p' tools/README.md` and `sed -n '1411,1442p;1525,1546p' tools/README.md` (overhead) | 5,973 + 3,880 chars | Two reads of the tool index to find entries the tester could have reached with `grep -n '^### ' tools/README.md` once, then one targeted range. |
| four reads of the campaign queue file (overhead and case) | 6,518 + 5,488 + 4,589 + more = over 20,000 chars | The tester needs its own case block and the Session facts. Two ranges, read once. |

About 48 KB of the run's 120 KB of tool output is rules, index and queue reading. That is 40%.

## Repetition

- **The queue file was read four times** in four different ranges. Read the Session facts and
  the case's own row once, in the gate, and keep them.
- **`show mail` was issued after every configuration change**, at least eight times, and the
  full six-line block came back each time. Only three fields change: Authentication, Username
  and Port. `show mail | include Authentication|Username|Port` cuts it to three lines without
  losing any evidence the log quotes.
- **The probe ran twice** for a flag-syntax mistake (`--outlet 1` instead of `--outlet u2=1`).
  No device effect, but it cost a full probe cycle.
- **`show running-config` was pulled whole** to read the one stored `mail smtpserver
  authentication ...` line. `show running-config | include mail` would have done, and the log
  only quotes the four `mail` lines.

## Accuracy risks

1. **The base64 decode in STEP 1 is the tester's, not the device's.** The log states that
   `AGNrbWFpbABja1NtdHAx` is `"\0ckmail\0ckSmtp1"`. The server's own transcript independently
   printed `PLAIN decoded: authzid='' user='ckmail' pass=<7 chars>`, so the reading is
   confirmed by the instrument and the risk is low. It is still an inference and is named here.
2. **The health "after" sample was taken before teardown.** The teardown commands are therefore
   outside the health diff. Nothing in this case makes that likely to matter, but the next run
   should sample after teardown, or sample a third time.
3. **The oauth2 verdict rests on an absence**, that running-config never changes. The tester
   closed that correctly: three reproductions, from a configured state and from a clean state,
   plus the device's own contradicting message `% The smtpserver is not configured for OAUTH2`.
   The log does not claim oauth2 would fail given a token, and it should not.
4. **One instrument, one wire.** Legs 0 to 8 are graded from our own `smtpsrv.py` transcript.
   STEP 9 is the control that removes this risk: a real Postfix and a `tcpdump` taken outside
   the instrument give the same result. Without STEP 9 every claim would depend on code the
   tester wrote the same afternoon. Keep that control in any future SMTP case.
5. **Claims the final log had to leave out for lack of a source: none.** Everything in the
   queue's results row is sourced in the working log.

## Next run: expected outputs

| step | what this bench gave |
| --- | --- |
| CLI grammar | `authentication`, `port` and `tls` are SIBLINGS of the address. `mail smtpserver 10.38.22.33 authentication` is `% Unrecognized command`. |
| mechanisms offered | crammd5, login, oauth2, plain. username and password are required for the first three and absent for oauth2. |
| baseline `show mail` | `State : Dead / SMTP Server : Not Set / Port : 25` |
| after setup | `State : Alive`, and `Port` survives a later `authentication` line |
| PLAIN on the wire | `C: AUTH PLAIN AGNrbWFpbABja1NtdHAx` then `S: 235 2.7.0 Authentication successful` |
| LOGIN on the wire | `C: AUTH LOGIN`, `S: 334 VXNlcm5hbWU6`, `S: 334 UGFzc3dvcmQ6`, then 235 |
| CRAM-MD5 on the wire | `C: AUTH CRAM-MD5`, `S: 334 <base64 challenge>`, digest verified, then 235 |
| wrong credential | `S: 535 5.7.8 Authentication credentials invalid`, and the DUT then sends no MAIL FROM at all |
| no mechanism configured | server with `--require-auth` answers `530 5.7.0 Authentication required`, three times, because msmtp pipelines |
| server offers no AUTH | the DUT sends EHLO then QUIT, 23 bytes total, and prints `msmtp: the server does not support authentication` |
| oauth2 | accepted in silence, running-config unchanged, `show mail oauth2 url` -> `% The smtpserver is not configured for OAUTH2` |
| stored credential | `password 8 <base64>` -- encrypted, and `show mail` never prints it |
| SMTP client identity | msmtp, configured from `/etc/msmtprc`, and it prints the server's reply text unaltered |
| a refused message | stays in the DUT's queue and is retried on the next send |

## Next run: scripts

- **`tools/smtpsrv.py` already exists** and was written for this case. Do not rebuild it.
  `--port <n> --bind 0.0.0.0 --hostname <name> --user <u>:<pw> [--mech none] [--require-auth]
  --maildir <dir> --log <file> --stopfile <file> --seconds <n>`. It logs a timestamped C:/S:
  transcript of both directions and decodes PLAIN, LOGIN and CRAM-MD5. It never logs a password
  in clear unless `--show-secrets` is passed, which this run did not use.
- **`tools/conkey.py` already exists** and was written for this case. Use it for ANY interactive
  AW+ exec command, not just `mail to`. A prompt-driven driver cannot answer a command that
  reads free text until Ctrl-D. `tools/tb conkey <box> <scratch> <uN> <baud> wait:2
  'line:<command>' wait:2 'line:<body>' key:ctrl-d wait:12 --final 6`.
- **Proposed: a `--summary` flag for the offline validation path of `smtpsrv.py`**, printing one
  line per mechanism instead of the full `smtplib` transcript. That alone removes 15 KB from the
  next run's context.
- **Unprivileged listener beats root.** `mail smtpserver port <1-65535>` is configurable, so an
  SMTP test needs no root and no change to the box's Postfix. Reach for a high port first.

## Next run: references

- `logged-output.md` §4 -- the final log template and the plain-English rule.
- `STANDING-ORDERS.md` §7 -- frame-level evidence with a control that must not match, in the
  same run. §8 -- the health read. §4 -- what needs the Test Engineer (root, package installs).
  §1 -- a missing feature is UNSUPPORTED, not FAIL.
- `tools/README.md` -- the entries for `smtpsrv.py`, `conkey.py` and `tcpflow.py`.
- Memory *"Bench scripts stop on CLI errors"* -- a `% ` line looks like success to a prompt
  driver. This case's `qmark`-first method is the countermeasure, and it caught the wrong
  grammar before a single command was sent.
- Memory *"Never send CLI help through a CR driver"* -- `<cmd> ?` plus a carriage return
  EXECUTES the command. `tools/tb qmark` self-tests for this on every invocation.
