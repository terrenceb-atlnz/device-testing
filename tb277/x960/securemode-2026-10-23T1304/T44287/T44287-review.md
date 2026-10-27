# T44287 process review -- securemode-2026-10-23T1304

Reviewed 2026-10-28 by /create-logs from `agent-a3ceda2b4189e77a9.jsonl` and the working files.
Scope: **run 2 (2026-10-28)**, which is the run the final log is built from.

This is the reviewer's own analysis. It is not attached to the case and it may name other runs,
other campaigns and the agent's own process. It changes no verdict.

## Token usage

| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T44287 | 100 | 200 | 171,310 | 14,904,364 | 2,073 | 106 | 2,792 s (47 min) | 152,035 chars |
| overhead | 3 | 6 | 38,678 | 504,889 | 844 | 3 | 48 s | 13,884 chars |
| **total** | **103** | **206** | **209,988** | **15,409,253** | **2,917** | **109** | **2,840 s (47 min)** | **165,919 chars** |

Tool mix in the case segment: Bash 102, ToolSearch 1, SendMessage 3.

**How to read the split.** `case_tokens.py` cuts the case segment at the tester's first tool
call that touches the case folder, and everything before it is group overhead. In a single-case
group that usually leaves almost the whole run in `overhead` and makes the case row look tiny.
Here the opposite happened: the tester went into `T44287/` on its third call, so the case row
holds 100 of the 103 calls and `overhead` holds only the first two reads. Treat the case row as
the whole run. The useful comparison is not case-against-overhead, it is 165,919 characters of
tool output read back for 109 tool calls, which is **1.5 KB per call**.

Cache read is 14.9 M, the largest of the campaign. A 47-minute run with 100 sequential calls
re-reads the whole context on every call, so cache read grows with the square of the step count.
Batching console reads is the only lever that moves it.

## Process taken

1. Read the Session facts and the case block from the campaign queue (2 calls, 13.9 KB).
2. Read the rules: a headings `grep` of `STANDING-ORDERS.md` and `logged-output.md`, then three
   line ranges from both files (2 calls, 23.3 KB).
3. Read two ranges of run 1's working log for the limb table and the recovery ladder
   (2 calls, 16.0 KB).
4. Gate, 10 items: `precheck`, `scratch`, `template`, `probe --read-only`.
5. **The probe was run three times.** Two invocations were spent on the `--template` path:
   it is resolved **on the box**, and the dev-host path for the same tree is different. A wrong
   path prints `no template at <path> -- diff skipped` and **still exits 0**, which looks
   exactly like a MATCH.
6. Copied the running configuration to `flash:/pre-securemode.cfg` as the recovery file, before
   any read and long before `crypto secure-mode` was typed. Proved it on flash with `dir`.
7. Took fresh setup reads: `show system`, clocks, the PKI inventory, host key fingerprints, the
   whole running configuration, and the state of each title clause.
8. Health sample 1.
9. Built the normal-mode baseline: telnet on, an SNMPv1/v2c community, an SNMPv3 user, a
   privilege-7 user, an NTP MD5 key, and a minimal local RADIUS server.
10. Probed the normal-mode CLI surface with `qmark`, prefix by prefix. These strings are what
    finding F-5 is built from.
11. Drove five measurements over the link **before** the enable: `netlogin.py`, `devclient.py`,
    `snmpq.py` twice and `radsend.py`.
12. Enabled secure mode, read the running-config diff, `write`, `reload`, waited for the login.
13. Repeated the whole measurement set in secure mode, plus the `qmark` prefixes again.
14. Disabled secure mode, `write`, `reload`, re-read the PKI store and the host keys.
15. Health sample 2, teardown, flash cleanup, probe after, ping, probe again.

## Wasted input

| call | size | the narrower read |
| --- | --- | --- |
| `sed -n '140,200p' STANDING-ORDERS.md && sed -n '132,175p' logged-output.md && sed -n '171,270p' logged-output.md` | 12,994 chars | Three rule ranges in one call. Necessary content, but it was preceded by the next row, which makes it a second pass over the same two files. |
| `grep -n '^#' STANDING-ORDERS.md && grep -n '^#' logged-output.md && ...` | 10,299 chars | A discovery call to find the line numbers used by the row above. Two headings dumps of 10 KB to locate about 200 lines. The dispatch should carry the section numbers, or the tester should `grep -n '^## '` (two hash marks) which is a tenth of the output. |
| `sed -n '544,650p' .../run1.log` and `sed -n '367,470p' .../run1.log` | 8,757 + 7,261 chars | Run 2 needed run 1's limb table (N1-N15) and its recovery ladder, roughly 60 lines. Those 60 lines belong in the dispatch, not in a 16 KB re-read of the prior log. |
| `sed -n '1394,1440p;1508,1530p;1587,1625p' tools/README.md` | 7,939 chars | Three tool entries read in full to recall their flags. `grep -A12 '^### snmpq.py' tools/README.md` per tool is about 1 KB each. |
| `wc -l <queue> && sed -n '1386,2000p' <queue>` (overhead) | 9,654 chars | 614 lines of queue to reach one case block. Read the case block by its heading. |

**Roughly 47 KB of the 166 KB read back is rules, prior-log and index reading: 28% of the
run's input, spent before a single command reached the device.**

## Repetition

- **The rules files were opened twice**, once to find headings and once to read ranges. One
  call with the section numbers already known removes 10 KB.
- **Three probe invocations where one was needed**, two of them lost to the `--template`
  path-resolution trap. This is the second campaign group to lose probe cycles to a probe flag.
- **`show secure-mode`, `show boot`, `show running-config | include secure` and
  `show startup-config | include secure` were read at each of the five phase boundaries.**
  That is NOT waste. Finding F-1 exists only because those four were read together at a moment
  when they disagreed. Keep it.
- **The `qmark` prefix set was run three times in normal mode and three times in secure mode.**
  Also NOT waste. Finding F-5 is exactly the byte-identical comparison of those two sets, and it
  could not have been made from one pass. It should be a script, not a repetition (below).

## Accuracy risks

1. 🔴 **`tools/snmpq.py` can report a successful GET for a tool usage error, with exit 0.**
   Given `--auth-proto SHA-256`, `snmpq.py` passed the value to net-snmp, net-snmp rejected the
   flag and printed its **usage text**, and `snmpq.py` parsed a line out of that usage dump and
   reported `RESULT VALUE -- v:  print values only (not OID = value)` **with exit 0**. A usage
   error was graded as a successful SNMP GET. **Any case that calls `snmpq.py` with a protocol
   name the local net-snmp does not know will record a false PASS.** This run was not misled,
   because the value printed was obvious nonsense, but a less distinctive usage line would pass
   unnoticed.
   **The fix, and it is small:** `snmpq.py` must check the net-snmp exit status and refuse to
   parse output when the child failed; and it should reject an `--auth-proto` or `--priv-proto`
   value that the local net-snmp does not advertise, before running anything. Until that lands,
   check the `CMD` line and the raw output before trusting a `RESULT VALUE`.
   The tool was deliberately **not** edited during the run, so that no edit landed under a case
   that was using it.
2. 🔴 **tb277 cannot speak SNMPv3 with SHA-256, so one limb of this case is not measurable from
   this box.** Two independent instrument limits, both measured on the box at 10:02:
   - net-snmp is **5.7.3**, and its `-a` flag accepts only `MD5|SHA`:
     `Invalid authentication protocol specified after -a flag: SHA-256`;
   - **pysnmp is installed but unusable**: `import pysnmp.hlapi` raises
     `OSError: Cannot load native module 'Cryptodome.Cipher._raw_ecb'`, so
     `usmHMAC192SHA256AuthProtocol` is unreachable.
   Secure mode refuses both protocols the box can speak, so no SNMPv3 query can be driven
   against a secure-mode DUT from tb277 at all. Fixing either needs a package install, which is
   root, which is the Test Engineer's. **This is an instrument limit, not a DUT property**, and
   the final log says so in STEP N5. The DUT accepted and stored the SHA-256 user, which is the
   strongest statement this bench supports.
3. 🔴 **A PKI inventory read INSIDE secure mode describes the secure-mode store, not the flash
   store, and it looks exactly like catastrophic key loss.** Trustpoint `local` is absent, two
   of three host keys are absent, and `default-selfsigned` appears regenerated. This run read it
   that way and reported destroyed key material to the sentinel at 10:00, then corrected the
   report at 10:09 once the flash store had been read after leaving secure mode. All three host
   key fingerprints and all three trustpoints were byte-identical to the 09:37 baseline.
   **The rule for the next tester: never grade the flash PKI store from a read taken inside
   secure mode.** The product fact is in the final log at STEP N11; this process history is not,
   and belongs here.
4. **`tools/tb health` grades any deliberate reboot DIRTY.** Its matcher counts the ~34 ordinary
   kernel boot messages (`Linux version`, `KASLR disabled due to lack of seed`,
   `mv_xor_v2 ... XOR driver`) because they contain the word `kernel`. They are not crashes. The
   tester attributed all 34 by timestamp to the reload it caused 32 seconds earlier. That
   attribution was done by hand and it is the kind of work that gets skipped under time
   pressure, producing either a false fault report or a sanitised health line.
5. **Three limbs rest on the ABSENCE of a difference** (N13's TACACS+, licensing and security
   banner rows). The tester graded them NOT CONFIRMED or NOT DISCRIMINABLE rather than PASS,
   which is correct. The evidence that would close the TACACS+ and rsa1/dsa rows is a build that
   offers those keywords in normal mode; nothing on this bench can supply it.
6. **N6's password-length limb is confounded by a pre-existing setting.** The unit already
   carried `security-password minimum-length 8`, which produces the same refusal in normal mode.
   Clearing it would separate the causes but would weaken a standing security setting on a
   shared bench. Correctly declared NOT DISCRIMINABLE rather than measured.
7. **Claims the final log had to leave out for lack of a source: none.** Every statement in the
   campaign's results row for this case is sourced in the working log.

## Next run: expected outputs

| step | what this bench gave |
| --- | --- |
| `crypto secure-mode` | `% Save the config and restart the system for this change to take effect.` There is **no (y/n) prompt**. Drive it with a verbatim console send, never with a yes/no driver. |
| `show secure-mode` right after | `Secure mode is enabled` -- **before it is enforced**. Do not grade from this. |
| does it reboot itself? | No. Uptime unchanged three minutes later. `write` then `reload` are the tester's. |
| `reload` to secure mode | login seen after **61 s** |
| `reload` back to normal | login seen after **60 s** |
| running-config diff at enable | exactly four lines: `-service telnet`, `-no service telnet ipv6`, `+no service telnet`, `+crypto secure-mode` |
| at the secure-mode boot | `WARNING: Failed to execute the following commands:` followed by every refused line, and one `local6.warning startup-config: <n>: <line> -- <reason>` per rejection in `show log` |
| telnet server | `TRANSPORT FAILED: telnet 10.38.22.34:23 -- [Errno 111] Connection refused` (a TCP reset) |
| telnet client | **still works.** `CLIENT RESULT: REFUSED` from the far end, not from the DUT |
| `service telnet ip` | `% Action not allowed in crypto-secure mode.` |
| SNMPv2c GET | `RESULT TIMEOUT -- Timeout: No Response from 10.38.22.34.` exit 4 |
| `snmp-server community X ro` | `% Community is not allowed in crypto secure-mode` |
| `snmp-server user ... auth md5 ...` | `% MD5 authentication is not allowed in crypto secure-mode` |
| `snmp-server user ... auth sha ...` | `% SHA-1 authentication is not allowed in crypto secure-mode` -- **stricter than the documentation** |
| `snmp-server user ... auth sha-256 ... priv aes ...` | accepted and stored encrypted |
| `username X privilege 7 ...` | `% Only the following privilege levels are allowed in crypto secure-mode:` then `% Privilege level 1` and `% Privilege level 15` |
| `ntp authentication-key N md5 ...` | `% Command is not allowed when crypto secure-mode is enabled.` |
| `ntp authentication-key N sha1 ...` | accepted, stored as `sha1-encrypted` |
| `ssh server allow-legacy-ssh-rsa` | `% allow-legacy-ssh-rsa is not supported in crypto secure-mode.` |
| `ssh server disallow-cbc-ciphers` | accepted |
| `show running-config unencrypted` | `% Command not supported in secure-mode` |
| `dir nvs:` | `% Invalid URL: nvs:` in secure mode; full listing in normal mode and again after disabling |
| `radius-server local` | `% radius-server local is not supported in secure mode.` **and the prompt still becomes `(config-radsrv)#`** |
| RADIUS request | `<- NO REPLY after 5.0s (x1) [ICMP port unreachable: nothing listening on that UDP port]` |
| `crypto secure-mode-selftest ?` | `% Unrecognized command`, in **both** modes |
| `crypto ?` | the same four sub-commands in both modes: key, pki, random, secure-mode |
| `show post` in secure mode | the six normal lines plus an **empty** `SECURE-MODE POST` heading |
| `crypto key generate hostkey ?` | ecdsa, ed25519, rsa -- in **both** modes. No rsa1, no dsa. |
| `aaa group server ?` | ldap, radius -- in **both** modes. No tacacs+. |
| PKI inside secure mode | one ECDSA host key, trustpoint `local` absent, `default-selfsigned` roots **different**. This is the secure-mode store. It is not loss. |
| PKI after the round trip | all three host keys and all three trustpoints byte-identical to the before reading |
| `nvs:hostkey` | a 350-byte file left behind after the round trip. Device-generated key material, inert while secure mode is off. |
| console login | unaffected. Ten logins at privilege 15 with secure mode on, no banner, no password demand. |
| health after a deliberate reboot | DIRTY by the tool, with ~34 kernel boot lines and one `Expected CLI(user request)` reboot per reload |

## Next run: scripts

- **Proposed `tools/qmarkdiff.py`.** Finding F-5 -- that the CLI help reflects no restriction at
  all -- is a byte-for-byte diff of the same `?` prefixes in two device states. The tester did
  it by hand across six `qmark` runs. A helper would run a prefix list twice and print only the
  differences.
  `tools/qmarkdiff.py <box> <scratch> <uN> <baud> --prefixes <file> --label-a before
  --label-b after [--mode 'configure terminal']`. It is reusable for any before/after CLI
  surface question, not only secure mode.
- **Proposed `tools/secmode.py`.** The enable and disable round trip is a fixed five-step
  sequence: send the command, read the advisory, `write`, `reload`, answer `y`, wait for the
  login prompt, re-read `show secure-mode` and `show boot`. The tester hand-drove it twice.
  `tools/secmode.py <box> <scratch> <uN> <baud> --enable|--disable --wait 120`, exiting non-zero
  if the unit does not return.
- **Proposed: `--expect-reboots N` for `tools/health.py`.** A case that reboots on purpose will
  always trip the DIRTY verdict, because the matcher cannot tell a boot message from a crash.
  The flag would accept N reboots whose reason reads `Expected CLI(user request)` and would
  classify the kernel lines stamped within a short window after each one as boot messages.
  That turns a paragraph of manual attribution into a tool result.
- **Fix `tools/snmpq.py` first** (accuracy risk 1 above). It is the only item here that can
  change a verdict.
- **Already exist, do not rebuild:** `tools/netlogin.py` (login over telnet or SSH from the
  box), `tools/devclient.py` (drives the DUT's own client from the console),
  `tools/radsend.py` (a RADIUS Access-Request with authenticator validation),
  `tools/snmpq.py`, `tools/tb qmark`, `tools/tb cfg`, `tools/tb ckcon`, `tools/tb health`.

## Next run: references

- `platforms/x960.md` §7F.2 -- a `show` command on this platform describes the configuration,
  not what is enforced. §7F.3 -- the telnet advisory is an advisory, not an error, and is
  already in `console.ADVISORY`. §7F.1 -- `service telnet ip` is stored as `service telnet`
  plus `no service telnet ipv6`. §7E.6 -- an AW+ login lands at privilege 1, so `USER` with
  exit 1 is the success result for a login test. §7E.7 -- there is no `tacacs+` keyword on this
  build. §7J.7 -- this unit has two power supplies, so a single-outlet power cycle does
  nothing; cycle both outlets or neither.
- `STANDING-ORDERS.md` §4 -- root, package installs and licence changes are the Test Engineer's.
  §7 -- drive the measurement, do not read it from a `show`. §8 -- the health read.
- `logged-output.md` §4 -- the final log template.
- Memory *"AW+ CLI confirmations need Enter"* -- but `crypto secure-mode` prompts for nothing at
  all, so a yes/no driver is the wrong instrument here.
- Memory *"Bench scripts stop on CLI errors"* -- gate each step on proven state. Finding F-8 is
  the reason: a refused command still changed the CLI mode, so the prompt alone is not proof.
