# T33365 process review -- auth-2026-10-29T1304
Reviewed 2026-10-29 by /create-logs from agent-aa136ab5396975428.jsonl and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 9 | 18 | 16,610 | 1,556,955 | 13,067 | 9 | 247 s | 5,541 chars |

Largest outputs inside the segment: the login-form grep and login run (1,575), the
`grep 'Server protocol'` and httpq checks (1,203), two `G=...` calls (938 and 854), and the
`tools/tb ckyn` zeroize call (561).

**This row covers less than half of the case.** `tools/case_tokens.py` starts a case at its first
tool call into `T33365/`. The tester created `T33365/work/` only at 13:44:00 NZDT, after the CA
export. So 15 earlier tool calls (13:38:57 to 13:43:37, 15,671 chars of tool output) were
counted in the T33375 segment or the group overhead, not here. Those calls held STEP 0, STEPs
7, 2, 3, 4 and 5, the health read before, and both detours. See the group finding below.

Each tool call appears twice in the transcript (two rows with the same `tool_use` id). Only
unique ids were counted above.

## Process taken
Before the measured segment (counted elsewhere by case_tokens.py):
1. 13:38:57 -- read the case's raw steps from ck.db (1,352).
2. 13:39:13-13:39:34 -- read `tools/httpq.py` TLS code (828 + 2,599). Added `--cafile`,
   `--no-hostname-check` and `--peer-cert` (612).
3. 13:39:41 -- help probes for `crypto key`, `crypto pki` and `auth-web-server ssl` (2,828).
   **Detour:** the probe used `crypto pki trustpoint ck-qm` as a qmark `--mode`, and that
   created trustpoint `ck-qm`.
4. 13:40:38 -- **detour:** removed `ck-qm` and checked with rcdiff (608).
5. 13:41:06 -- `show system` and the health read before (1,314).
6. 13:41:45 -- STEP 0: the default HTTPS certificate seen from tb5 (607).
7. 13:41:56 -- STEP 7 then STEP 2: key `ck-web-key`, trustpoint `ck-web` (1,125).
8. 13:42:25 -- STEPs 3 and 4: `crypto pki authenticate` and `enroll` (1,207).
9. 13:42:43-13:43:18 -- **detour:** export syntax. A qmark (227), a rejected
   `crypto pki export ck-web pem rsa terminal` (1,314), a re-read of that output (169), and a
   second qmark (336).
10. 13:43:37 -- STEP 5: exported RSA and ECDSA PEMs and decoded them with openssl (545).

The measured segment:
1. 13:44:00 -- saved the CA file, `tools/tb put` to tb5, then bound `auth-web-server ssl` and
   `trustpoint ck-web`, and added user ckweb. Read `show auth-web-server` (938).
2. 13:44:37 -- grepped `Server protocol` again. Ran httpq checks A1 to A4 and the plain HTTP
   GET (1,203).
3. 13:44:59 -- read the login form. Ran the wrong-password POST, ping and supplicant read,
   then the right-password POST, ping, supplicant read and log tail (1,575).
4. 13:45:40 -- health read after, then teardown with `tools/tb ckyn`. The teardown included
   the rejected `crypto key zeroize rsa ck-web-key` (854).
5. 13:46:27 -- qmark of `crypto key zeroize` (256).
6. 13:46:47 -- `crypto key zeroize ck-web-key` and the key and trustpoint inventory (561).
7. 13:47:45 -- wrote `work/run1.log` from the scratch outputs (60).
8. 13:48:02 -- documented the new httpq options in `tools/README.md` and committed a4a6223 (94).
9. 13:48:08 -- `SendMessage` with `RESULT T33365 PASS` (82).

## Wasted input
- Segment call 2 (1,203): `grep 'Server protocol'` re-read a line that call 1 had already
  printed in its `show auth-web-server` tail. Drop it.
- Segment call 3 (1,575): the form was grepped from the HTTP page and again from an HTTPS fetch
  with `--max-body 6000`. One grep of the HTTP page is enough. It is the page the client meets
  first.
- Pre-segment step 3 (2,828): the help probes asked for the whole `crypto pki` and
  `crypto key` trees. platforms/x980.md §1.3 now holds the answers, so the next run needs no
  probe.
- Pre-segment step 9 (2,046 in 4 calls): an export with the wrong word order, then a re-read of
  its output, then two qmarks. With the known syntax this is one call.
- Segment calls 4-5 (part of 854, plus 256): the rejected zeroize syntax and its qmark.
  With the known syntax this is zero extra calls.
- Pre-segment step 2 (2,599): a full read of `httpq.py` main body. It was needed once, to add
  the X.509 options. The next run does not need it.

## Repetition
- The export was sent twice (rejected, then correct). The zeroize was sent twice (rejected,
  then correct). Both are syntax lookups that platforms/x980.md §1.3 now answers.
- The rejected export output was read back from disk in a separate call (169 chars).
- `Server protocol` was read twice (segment calls 1 and 2).

## Accuracy risks
- **Hostname check off.** The certificate has no subjectAltName, so every chain check used
  `--no-hostname-check`. With the check on, the client rejected the certificate
  (`IP address mismatch`). To close: add `subject-alt-name` with the IP address to the
  trustpoint and repeat STEP B with the hostname check on. This would be outside the authored
  case, so the Test Engineer decides.
- **Which server certificate was used is not recorded.** The trustpoint enrolled an RSA and an
  ECDSA server certificate. The peer-cert read shows subject, issuer and serial, but not the key
  type. Both CAs have the same subject, so the issuer line does not tell them apart. To close:
  print the public key algorithm in `httpq --peer-cert`, or match the serial against
  `show crypto pki certificate`.
- **The ECDSA server certificate used an existing key.** `enroll` used `server-default-ecdsa`,
  which belongs to trustpoint `local`. The tester left it in place. The final log says so.
- **STEP 6 NOT RUN.** The Test Engineer chose the local RADIUS server (decision D3). The
  external freeradius path in the authored case was not tested.
- **Claims left out or sourced outside run1.log:**
  - run1.log does not name the command behind the supplicant tables. The final log uses
    `show auth supplicant brief`, from run1.log line 68 (the precondition) and transcript
    segment call 3.
  - The httpq command lines in run1.log are the tester's summaries (lines 447-450, 458, 467),
    not the full commands. The final log quotes them as recorded. The real calls also had
    `--max-body 100` and the `tools/tb tool tb5 auth1304` prefix.
  - run1.log does not say if the config was saved to startup. "saved to startup: no" came
    from the dispatch, and the CAVEAT relies on it.
  - The client path through tb5's swi_x530 and swi_x950 came from the dispatch. run1.log
    gives only "client tb5 eth6", and gives no port names for those two switches.
  - The tester's `SendMessage` says "`auth-web-server mode` does not exist on this build".
    run1.log does not hold it, so the final log leaves it out. platforms/x980.md line 19 holds
    it.
- **run1.log is not self-contained.** Line 3 sends the reader to T33375's run1.log for the
  session facts. Those files are deleted with `work/`, so the line will point to nothing.

## Next run: expected outputs
| step | value or CLI line this bench gave |
| --- | --- |
| STEP 0 | peer cert `commonName=AlliedwarePlusDefault`, issuer `commonName=AlliedWarePlusCA`, SAN `-` |
| STEP 7 | `crypto key generate rsa label ck-web-key 2048` -> `Created the key "ck-web-key".` |
| STEP 2 | `Created trustpoint "ck-web".`; `Type : Non-authenticated trustpoint` |
| STEP 3 | `Successfully authenticated trustpoint "ck-web".` (makes an RSA and a P-384 ECDSA CA) |
| STEP 4 | `Successfully enrolled the local server.`; `Using ECDSA private key "server-default-ecdsa"...` |
| STEP 5 | `crypto pki export ck-web pem terminal rsa` and `... ecdsa`; log `Trustpoint ck-web exported`; openssl sha1 = trustpoint Root Certificate value |
| STEP 6 | not run (local RADIUS) |
| STEP A | `Server protocol: HTTPS`, `Certification: user` |
| STEP B | `--cafile` + `--no-hostname-check`: verified, subject `commonName=192.168.50.1`; `--verify` (system store): `unable to get local issuer certificate`; `--cafile` with hostname check: `IP address mismatch` |
| STEP C | wrong password: `W ... Connecting`, ping 0/4; right password: `W ... Authenticated ... ckweb`, ping 4/4; radiusd `Login OK: [ckweb]` |
| teardown | `crypto key zeroize ck-web-key` -> `Deleted the key "ck-web-key".` |

## Next run: scripts
- Existing: `tools/httpq.py` with `--cafile F --no-hostname-check --peer-cert` (tools/README.md,
  "X.509 options"). Use it as is for STEP 0 and STEP B.
- Existing: `tools/tb ckyn` for `crypto pki authenticate` / `enroll` and the `YN?:` teardown
  lines.
- Proposed: `tools/pkitp.py <scratch> <uN> <baud> --tp ck-web --key ck-web-key --subject
  /CN=<ip> [--san <ip>] --export-to <dir> [--teardown]`. It would run STEPs 7, 2, 3, 4 and 5 in
  one call with the known syntax. It would save both PEMs into one CA file, compare each openssl
  sha1 with the trustpoint Root Certificate line, and print MATCH or MISMATCH. With
  `--teardown` it removes the trustpoint and zeroizes the key, then checks the key list.
- Proposed: add the public key algorithm to `httpq.py --peer-cert` output, to close the
  RSA-or-ECDSA question above.

## Next run: references
- platforms/x980.md §1.3 "PKI": key, export and zeroize syntax, and the trap that entering
  `crypto pki trustpoint <name>` creates it (also as a qmark `--mode`).
- platforms/x980.md line 19: `auth-web-server mode` does not exist on this build.
- tools/README.md, httpq "X.509 options": what `--cafile`, `--no-hostname-check` and
  `--peer-cert` do, and why a CN-only certificate fails the IP hostname check.
- tb490/x980/auth-2026-10-29T1304/T33375/T33375.log: the web-auth setup on port1.0.81 and the
  client path that this case inherits.
