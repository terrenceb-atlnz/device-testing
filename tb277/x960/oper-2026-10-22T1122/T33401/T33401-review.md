# T33401 process review -- oper-2026-10-22T1122
Reviewed 2026-10-22 by /create-logs from agent-a39e912de26a7c9d1.jsonl and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | 200 | 140,847 | 17,601,467 | 1,147 | 111 | 41 min (2,462 s) | 81,730 chars |

Boundaries: the case runs from the first tool call that created its folder (23:52:26 UTC)
to its `RESULT` message (00:33:28 UTC). `tools/case_tokens.py` could not split this
transcript on its own, because the tester wrote `RESULT AWPTCM-T33401 ...` and the tool's
regular expression expects `RESULT T33401 ` or `RESULT 33401 `. The numbers above come
from the same tool with that one regular expression widened. See REVIEW.md.

## Process taken
1. Created the three case folders and wrote the run `.setup` for swi_d only (1 call).
2. Probed the box against that `.setup` three times while settling where the template file
   had to live for the box to read it, then saved and reverted `bench-state.md` (calls 2-6).
3. Setup reads in one `ckcon` call: `show clock`, `show system`, `show boot`,
   `show log config`, `show running-config | include log`, `show startup-config | include log`
   (call 7), then read the output file back in two 120-line slices (calls 8-9).
4. `tools/tb health ... --label before` (call 10) and `show log tail 30` to find a stimulus
   that needs no traffic (call 11).
5. Host NIC addresses (calls 12, 16), then read `tools/ntpwire.py` in two slices as the
   model for a new decoder (calls 13, 15) and the matching `tools/README.md` sections
   (calls 14, 29).
6. Wrote `tools/syslogwire.py`, fixed one import, self-tested it offline against a
   hand-built pcap, added its `tools/README.md` entry and committed it (calls 17-21, 24).
7. Read the CLI help surface with `qmark` (call 25), saved `swi_d.cfg` (call 30).
8. STEP 0 to STEP 6: for each window, start one or two `tb capture` calls, send the markers
   with `ckcon`, poll until tcpdump exited, then decode with `syslogwire` (calls 31-101).
9. Health after, `show running-config` diff, post-case probe, working log, commit, RESULT
   (calls 102-111).

## Wasted input
- Call 11 `show log tail 30` and calls 8-9 (240 lines of setup output read back in two
  slices). The second slice was needed; the first was read in full although only the
  `show system` and `show log config` blocks were used. A `sed -n` on the two block
  headings would have cost about a third.
- Calls 13 and 15 read all 229 lines of `tools/ntpwire.py` (5,847 chars in the larger
  slice) as the model for the new decoder. That was a one-off cost and it produced
  `tools/syslogwire.py`, so the next syslog case pays nothing.
- Calls 69, 70 and 71 read `show log config` and the same saved file three times inside two
  minutes while establishing what filter 2 was. One read plus one `sed -n '/Host 10.38.22.33/,/Statistics/p'`
  would have done.

## Repetition
- The "wait until tcpdump has exited" loop
  (`for i in $(seq 1 N); do tools/tb ps tb277 'tcpdump -i eth' ...`) was written out 12
  times in this case alone, each time with a different count. It is the single most
  repeated construct of the whole group.
- The "wait until u2 is free" loop (`tools/tb holders tb277 u2 ...`) was written out 4
  times in this case.
- `tools/tb capture` was called twice in a row (eth3 then eth4) for every two-leg window:
  six pairs. One call that starts both legs would halve it.

## Accuracy risks
- `show log config` is quoted in the working log as "abridged to the fields that matter;
  the full output is in the run transcript". The final log therefore quotes the abridged
  baseline block. The full output is not in a committed file.
- The `swi_d.cfg` header line reads `captured 2026-10-22 13:0x NZDT`, with the last digit
  masked. The exact minute of the capture is not recorded anywhere in the case folder.
- Three capture windows in STEP 1 returned zero while the feature worked. The tester did
  not grade on them; it widened the window and found the cause. Had it graded on the first
  timeout, the case would have been a false FAIL. The rule that saved it is worth repeating:
  a timeout is not a measurement.
- The facility override was measured at two collectors but with one facility value
  (local4). A second value was never put on the wire globally, so "the override sets the
  facility you ask for" rests on one value.

## Next run: expected outputs
| step | what this bench gave |
| --- | --- |
| baseline | `show log config` -> `Facility: default`, `External log: DISABLED`, no `Host ...` section |
| `log host <ip>` alone | accepted in silence; `Filters:` empty; `0 accepted`; nothing on the wire, ever |
| `log host <ip> level <sev>` before the host exists | `% host address "10.38.22.65" not found` / `% Error: Unable to add log filter` |
| default facility on the wire | a mixture: `user(1)` for IMISH messages, `syslog(5)` for syslog-ng's own |
| `log facility local4` | every message PRI 163 (`local4.err`) or 165 (`local4.notice`); `show log config` -> `Facility: local4 (local use 4)` |
| `log host <ip> facility <f>` | no change on the wire; it appears in `show log config` as a second entry under `Filters:` |
| after a reload, nothing typed | 224 messages on vlan10 and 163 on vlan48, all local4, four severities |
| `no log host <ip>` | removes the host and its filter lines together |
| flush behaviour | against a collector that does not listen, the DUT sends in bursts 60 s apart; use a window of at least 170 s |

## Next run: scripts
- `tools/syslogwire.py` now exists and does the whole measurement:
  `tools/tb tool <TB> <scratch> syslogwire /tmp/<scratch>/<f>.pcap [--quiet] [--abs]
  [--to ADDR] [--grep RE] [--limit N] [--msg-width N] [--expect-facility NAME]`.
  Exit 0 means the expectation matched, 2 means no syslog in the file, 4 means a mismatch.
- Proposed `tools/tb` action: `capwait <scratch> <timeout_s>` -- block until no tcpdump is
  running for this scratch. It would replace the 12 hand-written polling loops above.
- Proposed `tools/tb capture` option: accept several NICs in one call, so a two-leg window
  costs one call instead of two.

## Next run: references
- `tools/README.md`, the `syslogwire.py` entry -- the decoder and its exit codes.
- `platforms/x960.md` -- the x960's console and CLI traps used here.
- `logged-output.md` §2 "Check the DUT's health, every case" -- the six health reads.
- memory `campaign-measurement-discipline` -- measure the feature off first.
- memory `two-console-calls-in-one-block-run-sequentially` -- start the captures in a
  separate call before the console call that makes the traffic.
