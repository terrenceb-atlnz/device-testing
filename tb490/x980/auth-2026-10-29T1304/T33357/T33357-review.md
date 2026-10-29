# T33357 process review -- auth-2026-10-29T1304
Reviewed 2026-10-29 by /create-logs from `agent-aa136ab5396975428.jsonl` and the working files.

The segment runs from the first tool call that touches `T33357/` (00:58:14 UTC, the setup reads)
to the `SendMessage` carrying `RESULT T33357` (01:08:30 UTC). In the transcript each tool call
appears twice: once as sent, and once as a copy with `cd <repo> &&` added in front. The counts
below count each call once.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 17 | 36 | 27 753 | 4 172 199 | 18 163 | 17 (Bash 16, SendMessage 1) | 615 s | 16 801 chars |

Largest outputs: the `for x in C A` EAPOL table compare (call 12, 6 484), mkdir plus setup reads
plus health-before plus qmark (call 1, 2 408), the `tools/tb ckcon` reachability diagnosis
(call 7, 1 486), the legs B and A call with `--method` (call 10, 1 355), the `G=...` health-after
and teardown read (call 13, 818).

## Process taken
1. Setup reads (`show system`, `show auth interface`, `show auth supplicant brief`, PKI), health
   before, and `tb qmark` on `crypto pki enroll local` (call 1, 2 408 chars).
2. A grep of the saved setup output for existing user enrollments (call 2).
3. Configure the local RADIUS user and `dot1x port-control auto`, enroll cktls with `@ask`, export
   the CA as PEM, read back (call 3).
4. Pull the CA out of the console output, write `openssl-tls12.cnf` with `printf`, make the rogue
   certificate, push the files to tb5, then start the PKCS#12 TFTP export. The export stalled
   (call 4).
5. Wait for the console: `tb peek` and a poll loop until the prompt came back (calls 5, 6).
6. Diagnose: route, ping, ARP, supplicant brief, ip interface brief (call 7, 1 486 chars).
7. Force-authorize eth6's MAC, ping, retry the export with `@poll`, which succeeded (call 8).
8. `p12split` on tb5, remove the override, save `swi_dut.cfg` with `rc2cfg` (call 9).
9. Leg B (rogue) and leg A (TLS 1.2), each after `dot1x initialize`, each with a ping and a DUT
   state read (call 10, 1 355 chars).
10. Leg C (default TLS) and a first JSON-vs-RESULT check (call 11).
11. Read the frame tables of C and A, the C JSON and the TLS lines (call 12, 6 484 chars).
12. Health after, teardown with `tb ckyn`, `rcdiff` against the baseline (call 13).
13. Write `run1.log` by script. This ran `p12split` a second time, into `/tmp/auth1304/p12chk`
    (call 14).
14. A second JSON-vs-RESULT check with `tb grep` (call 15), then fix that line in `run1.log`,
    update the campaign queue and commit (call 16).
15. `RESULT T33357` to the sentinel (call 17).

## Wasted input
- **Calls 4-8, 00:59:50-01:03:40 UTC, 230 s (37% of the wall time).** Most of this is the
  PKCS#12 TFTP export to a client behind a port that was already `dot1x port-control auto` and
  Unauthorized. The DUT could not reach tb5, the export hung the console, and it took a peek, a
  poll loop, a 1 486-char diagnosis and a retry with a temporary `auth supplicant-mac ...
  force-authorized`. **The narrower path:** export the PKCS#12 *before* sending
  `dot1x port-control auto` (the port is still web-authorized then, 192.168.50.10 reachable).
  The trap is now in `platforms/x980.md` §1.3, so the next tester only has to read it.
- **Call 12, 6 484 chars: the full frame tables of legs C and A read back into the context.**
  Leg A had already printed `RESULT ... MATCH` in call 10, and the tables were written into the
  working log by script in call 14 anyway. **The narrower read:**
  `grep -a 'msglen\|Success\|Failure\|30\.0' $S/t57-C.out` (about 10 lines) for the one leg that
  needed a diagnosis.
- Call 1, 2 408 chars, is mostly needed reads. The 45-line `head` of the certificates block could
  be a `grep -c 'enrollments ready'`.

## Repetition
- **JSON vs printed RESULT was checked twice** (call 11 with `tb tail ... | grep -o`, call 15 with
  `tb grep`), because the first form did not give a usable answer. Use `tb grep` from the start.
- **`p12split` ran twice** (call 9 to `/tmp/auth1304`, call 14 to `/tmp/auth1304/p12chk`) just to
  capture its output for the log. See accuracy risk 2.
- `show running-config interface port1.0.81` was sent twice in a row (working log lines 445-446).
  Harmless.
- `dot1x initialize interface port1.0.81` before every leg is correct practice, not waste.

## Accuracy risks
1. **The two graded legs ran with the supplicant held at TLS 1.2.** The final log says so in the
   CAVEAT. EAP-TLS over TLS 1.3 is not measured. **What would close it:** wpa_supplicant 2.10 or
   newer on tb5 (a root install, so the Test Engineer's), then rerun leg C.
2. **The `p12split` command in the working log does not match its output.** The command reads
   `--out-dir /tmp/auth1304`, but the output says `wrote: /tmp/auth1304/p12chk/...`. The output is
   from the re-run in call 14. The legs used `/tmp/auth1304/cktls-leaf.pem` from call 9. Both runs
   split the same bundle, so the certificate facts are the same. But the final log shows a command
   and an output that do not belong together, because it must copy them unchanged. **Next run:**
   tee the first `p12split` output into the working log.
3. **The CA PEM body was cut to one line in the working log** (line 318). The CA's identity rests
   on the dev host's decode of the saved file. /create-logs checked that again:
   `openssl x509 -fingerprint -sha1` on the saved file gives `B7:8E:AF:...:12:DD`, which is the
   trustpoint's RSA root. The final log says the body was shortened.
4. **The DUT reads after legs B and A are grep fragments with no command lines** (working log
   516-521 and 569-586). A reader cannot tell which command printed which line. The final log
   says so. **Next run:** keep the whole output of `show auth supplicant brief` and
   `show auth interface port1.0.81`.
5. **After the rogue leg, the supplicant row reads Mode `W`, Status `Connecting`** (working log
   520), not `D`. The port has `auth-web enable` too, so the entry probably fell back to web
   authentication. That is not explained in the run. It does not change the verdict: the port is
   Unauthorized and 0 of 4 pings passed.
6. **No DUT log line proves the local RADIUS server decided for cktls.** The health-after log tail
   lists `Login OK: [ckweb]` and the enrollment lines, but no `Login OK: [cktls]` and no
   `802.1X Authentication successful for cktls`. On x960 (tb277 T9032) both were logged. The
   `show radius local-server statistics` lines (31 successes, 7 failed) have no reading before
   the leg. So the final log uses EAP-Success plus Mode D Authenticated cktls, and does not claim
   a RADIUS log line. **What would close it:** read the statistics before and after each leg, and
   `show log | include cktls|802.1X` after each leg.
7. **The setup read of `show crypto pki certificates local` printed nothing** (working log 112).
   So "no user enrollment before the case" has no printed proof. It was left out of the final
   log. **Next run:** send `terminal length 0` and read it again, or grep for
   `enrollments ready`.
8. **`show system` in the working log ends at `System Location`** with no line after it. It is
   copied as captured. The value is probably blank, as on x960.
9. **The working log takes session facts from another case's working log** (T33375 run1.log, for
   the clock offset and host MACs). When `work/` is deleted, that reference dies. The final log
   uses only the facts this run printed.

## Next run: expected outputs
| step | what this bench gave |
| --- | --- |
| 0, port before | `dot1x: disabled`, `authWeb: enabled`, eth6 `W Authenticated ... ckweb` |
| 1, enroll | `Successfully enrolled user "cktls".` then `Local RADIUS server user enrollments ready for export` / `cktls` |
| 1, CA | CN `AlliedWarePlusCAA10732A263200035`, RSA root SHA-1 `B78EAFBE AB9B50EE 860ACFB5 98238F21 699612DD` |
| 1, after `dot1x port-control auto` | `portStatus: Unauthorized`; DUT ping to 192.168.50.10 0/2; TFTP export hangs. Export first. |
| 1, PKCS#12 export | `Copying...` / `Successful operation` (16.2 s with force-authorized) |
| 1, p12split | LEAF 874 bytes DER, CA[0] 888 bytes DER, predicted payload leaf-only 883, whole chain 1774 |
| 2, rogue cert, TLS 1.2 | 16 frames, EAP-Failure at 1.0526 s, port Unauthorized, ping 0/4 |
| 3, DUT cert, TLS 1.2 | 20 frames, EAP-Success at 1.0613 s; DUT flight msglen=2367 in 3 pieces; client flight msglen=2175 in 2; `D Authenticated -- cktls`; ping 4/4 |
| 4, DUT cert, default TLS | 21 frames; DUT first flight msglen=99; client flight msglen=2162 stops after piece 1; DUT re-ACK at 30.03 s; EAP-Failure at 31.04 s |
| health | CLEAN: no new reboot, exception log None, 0 new non-echo lines |

## Next run: scripts
- `tools/wpasup.py <iface> --method tls --identity U --client-cert F --private-key F
  --ca-cert F --env OPENSSL_CONF=F --expect success|failure --timeout 45 --label L --pcap F
  --json F` (existing). It did all three legs.
- **`openssl-tls12.cnf` should become a tools/ asset** (proposed `tools/assets/openssl-tls12.cnf`).
  This run rebuilt it with `printf` in call 4. Its 9 lines match the tb277 T9032 copy exactly.
  Better still, the `wpasup.py --tls-max 1.2` flag that the T9032 review proposed, which writes
  the file itself. It is still not built.
- `tools/p12split.py <bundle> --passwd P --out-dir D --name N` (existing). Run it once and keep
  its output.
- **Proposed: a `tb ckcon` recipe (or `tools/pki_client.py`) for "enroll user, export CA PEM,
  export PKCS#12 to the client"** that orders the export *before* `dot1x port-control auto`,
  writes the CA PEM from the console output, and checks its SHA-1 against
  `show crypto pki trustpoint`. Arguments: `<tb> <run> <console> <user> <tftp-host> <port>`.
  Calls 3, 4 and 9 would become one call. If `crypto pki export local pkcs12` can write to the
  terminal instead of TFTP, that also avoids the reachability problem. Check it with `tb qmark`
  first, because this run did not.
- Use `tools/tb grep <box> '"(verdict|eapol_frames|label)"' <json>` for the JSON-vs-RESULT
  check (call 15), not `tb tail | grep -o`.

## Next run: references
- `platforms/x980.md` §1.3 (PKI: enroll prompts, export order, the TFTP-behind-dot1x trap and
  its two fixes) and §1.4 (EAP-TLS results and the TLS 1.3 stall).
- `tools/README.md`, the `wpasup.py` entry around line 1810, for `--env OPENSSL_CONF` and the
  TLS 1.2 ceiling.
- `tb277/x960/dot1x-2026-10-23T1304/T9032/T9032.log` STEP C/D, for why TLS 1.3 stalls on
  wpa_supplicant 2.6, with the wire evidence.
- RFC 5216 for the EAP-TLS flags: `0xc0` LM, `0x80` L, `0x00` plain or empty ACK, `0x20` Start.
