# T9032 process review -- dot1x-2026-10-23T1304
Reviewed 2026-10-28 by /create-logs from `agent-a8a5628ecbb2b564a.jsonl` and the working files.

This case ran in its own session with its own tester, so unlike the other three cases in the
group the segment below covers the **whole** case: the gate, the five legs, the teardown and the
write-up. Its numbers are therefore the honest cost of one case and are the best figure in this
group for planning the next one.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 62 | 124 | 147 912 | 8 236 973 | 10 988 | 72 (Bash 63, Edit 6, Write 1, ToolSearch 1, SendMessage 1) | 1 628 s | 143 716 chars |
| overhead | 6 | 50 743 | 403 282 | 93 | 4 | 40 s | 11 993 chars |

## Process taken
1. Read the prior working log in four separate ranges and the campaign queue in one (calls 1-4).
2. Read the rules and the tool index: `ls tools/`, the `tools/README.md` headings, the headings
   of `STANDING-ORDERS.md`, `logged-output.md` and `platforms/x960.md`, then two sections of
   `tools/README.md` and two line ranges of the rules (calls 5, 6, 7, 9).
3. Gate: `tb precheck`, `tb template`, read the run `.setup`, then three attempts at `tb probe`
   (calls 8, 10, 11, 12, 13, 14, 15).
4. Resolve the probe's one NEEDS-CHECK by sending pings and reading the DUT's MAC table
   (calls 16, 18, 19).
5. Setup reads and the before-health sample (calls 19, 20, 23).
6. Write `tools/p12split.py`, check its syntax, run it on the box (calls 24, 25, 26).
7. Put the CA file on the box and confirm both credential files are there (calls 27, 28).
8. Start the working log (call 29), then run the five legs, each preceded by
   `dot1x initialize interface port1.0.48` (calls 30, 31, 34, 41, 43).
9. Diagnose between legs: read the supplicant's own log for the certificate lines (call 32),
   read how `wpasup.py` builds its config file (calls 33, 36, 37), count certificates in the leaf
   PEM (call 34), compare every leg's JSON against its printed RESULT (calls 35, 44).
10. Add `--env` to `tools/wpasup.py` and write the OpenSSL ceiling file (calls 38, 39, 40).
11. Read the DUT's view after the success leg and after the control (calls 42, 45).
12. Capture the running-config, write `swi_d.cfg`, take the after-health sample (calls 46-48).
13. Probe the PKI removal surface with `tb qmark`, then run the restore and prove it by reading
    back (calls 49, 50, 51, 52).
14. Re-probe twice, with pings between, until `MATCH` exit 0 (calls 53, 54, 55).
15. Copy every leg's JSON and supplicant log off the box, log the console out, confirm the
    transcript's final state (calls 56, 57).
16. Finish the working log, update `tools/README.md` and the campaign queue, commit, send the
    RESULT line (calls 58-72).

## Wasted input
- **Calls 13, 14, 15: three attempts at the same probe.** The first used `--outlet 1` and
  `--name swi_d` where the tool wants `--outlet u2=1` and `--name u2=swi_d`; the second used a
  repository-relative `--template` path where the tool wants an absolute one. Two whole probe
  runs, each with a 420 s timeout, were spent on argument form. **The narrower path:** copy the
  probe line out of the gate record in the campaign queue, which already holds the working form.
- **Calls 1, 3, 4, 17, 22: five separate reads of the prior working log**, in ranges 148-250,
  324-392, 549-610, 1-100, plus a grep. That is most of a 35 KB file, read piecemeal. **The
  narrower path:** one `grep -n` for the section headings, then one read of the two sections
  actually needed.
- **Calls 5, 6, 7, 9: 35 KB of rules and indexes read before the first console command.** Calls 6
  (9 711 chars) and 9 (9 625 chars) overlap: call 6 lists the headings of three files and call 9
  then reads ranges from two of them. **The narrower path:** the dispatch should name the exact
  sections, and the tester should read those, not the heading lists first.
- Call 12 combined a directory listing, the whole run `.setup` and 60 lines of `tb --help`
  (7 132 chars). The `.setup` was needed; the help was a guess that the three failed probes then
  had to correct anyway.

## Repetition
- `tools/wpasup.py` was edited twice (calls 38, 39) and the campaign queue twice (calls 67, 68).
  Both are small.
- The DUT's state was read back after each leg with overlapping command sets (calls 42, 45, 51).
  That is correct practice, not waste: each read back belongs to its own leg.
- Two re-probes (53, 55) were needed because the first found stale MAC entries again. That is the
  same artefact as the pre-run probe and was already understood by then. **One ping on each leg
  before the first re-probe would have avoided the extra run.**

## Accuracy risks
1. **The two graded legs ran with the supplicant held at TLS 1.2.** That is a change to the test
   instrument, not to the DUT, and the final log says so in the CAVEAT. The DUT itself was not
   configured for any TLS version; it exposes no such command. **What would close the remaining
   gap:** `wpa_supplicant` 2.10 or newer on tb277, which is a root install and so the Test
   Engineer's. Until then EAP-TLS over TLS 1.3 is not measurable on this bench.
2. **The diagnosis that TLS 1.3 is the blocker rests partly on the supplicant's own debug log**,
   not on the DUT. The wire evidence is strong: with the flight reduced to one piece the DUT's
   next frame changes from an empty ACK (flags `0x00`) to a length-included data frame (flags
   `0x80 L`), which is what RFC 9190 requires. The claim that this frame is specifically the
   commitment message is read from the specification, not decrypted. **What would close it:**
   decrypt the TLS record with the session keys the supplicant logs, and name the handshake
   message.
3. **The 879-byte arithmetic is sound and checkable.** 2141 minus 1262 is 879, and the CA is 874
   DER bytes, measured by `tools/p12split.py`, plus 5 bytes of TLS framing. The framing figure is
   the reviewer's reading of the TLS structure; the two measured sizes are not.
4. **The rogue certificate used for the control was generated on the box in an earlier session**
   and reused. It is a self-signed RSA-2048 certificate with the same identity. The control is
   still sound, because the only thing that differs from the success leg is which authority
   issued the certificate. The final log says what it is and does not say where it came from.
5. **`tools/p12split.py` was written during the case.** Its output is used for one number, the
   874-byte CA size, and that number is corroborated by the wire arithmetic above.
6. **A PKI user enrolment named `cktls` remains on the unit.** No CLI removes it: `crypto pki` is
   exec-only on this build and exec offers only `authenticate`, `enroll`, `export` and `import`.
   It was reported to the sentinel and left alone. It is **not** in the final log, because it is
   bench state rather than this case's evidence.

## Next run: expected outputs
| step | what this bench gave |
| --- | --- |
| gate, probe | one NEEDS-CHECK, `CHECK_CABLE` on eth4, caused by an idle port whose MAC aged out. Ping first, then re-probe. |
| 0, MAC table before | `48   port1.0.48   000d.b955.770f   discard       static` -- `discard static` is normal for an Unauthorized dot1x port |
| 0, p12split | LEAF 867 bytes DER, CA[0] 874 bytes DER, predicted leaf-only payload 876 bytes |
| A, whole p12, default TLS | 17 frames, client flight `msglen=2141` in two pieces, two empty ACKs 30 s apart, no conclusion |
| B, leaf-only with ca_cert | 17 frames, `msglen=2141` **unchanged to the byte** -- OpenSSL rebuilds the chain from the verify store |
| C, leaf-only, no ca_cert | one piece, 1262 bytes, DUT's next frame flags `0x80 L`, still no conclusion |
| D, TLS 1.2 cap | 18 frames, EAP-Success at 1.0471 s; DUT flight 2339 bytes in 3 pieces; client flight 2154 bytes in 2 pieces; `portStatus: Authorized`; MAC entry `forward`; `show radius` auth status `Alive` |
| E, rogue certificate | 14 frames, EAP-Failure at 1.0363 s, `PAE: state: Held`, MAC entry back to `discard` |
| restore | `show auth` all three Disabled, `show radius` -> `No RADIUS servers currently defined`, `show radius local-server nas` empty, `show running-config \| include radius\|dot1x` empty, all three trustpoints still present |

## Next run: scripts
- `tools/wpasup.py <iface> --method tls --identity U --client-cert F --private-key F
  [--private-key-passwd P] [--ca-cert F] [--env VAR=VALUE] --expect success|failure --timeout N
  --label L --pcap F --json F`. The `--env` flag is the one that made this case work: it sets the
  environment of the supplicant child process only.
- `tools/p12split.py <bundle.p12> --passwd P [--out-dir D] [--name N] [--no-chain]` splits a
  PKCS#12 and prints the DER size of every certificate in it, so a flight size becomes arithmetic
  instead of a guess.
- The OpenSSL ceiling file is small and reusable; a copy is in `work/openssl-tls12.cnf`.
  **Proposed:** `wpasup.py --tls-max 1.2` that writes that file itself, so the next tester does
  not have to know the OpenSSL configuration format.
- **Always compare the `--json` file against the printed RESULT.** This run did it for all five
  legs and they agreed. An earlier run in this group saw them disagree once.

## Next run: references
- RFC 5216 for EAP-TLS fragmentation: flags `0xc0` is Length-included plus More-fragments,
  `0x80` is Length-included, `0x00` is a plain or empty frame, `0x20` is Start.
- RFC 9190 for EAP-TLS over TLS 1.3 and the commitment message the server must send after the
  client's Finished.
- `tools/README.md`, the `wpasup.py` entry, for the credential forms and the `--env` flag; the
  `p12split.py` entry for the split.
- `platforms/x960.md` section 7E.8: entering `crypto pki trustpoint local` CREATES the object.
  Trustpoint `local` already exists on this unit, so do not enter that sub-mode and do not remove
  it.
- On this platform `show crypto pki trustpoint`'s `Applications` line is derived from what is
  configured right now, not stored with the trustpoint. It loses `RADIUS` when
  `no radius-server local` is sent and gains it back when the server is configured again. That is
  not damage.
