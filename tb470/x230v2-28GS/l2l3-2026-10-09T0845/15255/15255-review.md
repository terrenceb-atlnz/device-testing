# T15255 process review -- l2l3-2026-10-09T0845
Reviewed 2026-10-12 by /create-logs from `agent-a416990ee48b8b1f0.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md). Call numbers are this segment's, from its first
call into `15255/` to its RESULT line (see REVIEW.md, "How the segments were cut").

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 24 | 48 | 47,714 | 3,621,781 | 10,876 | 25 | 472 s | 31,073 chars |

The group's most expensive case, but about half of it is group work done inside it: the
pre-run captures of all three units, the qmark re-check of T30403, and queue bookkeeping.

## Process taken
1. #1 group pre-run capture of the x230 (u0, 14 shows) to `prerun-u0-1932.out`.
2. #2-#3 read it back: running-config (961 chars), then `show vlan brief` .. `show system` (6,005).
3. #4 pre-run captures of the stack (u5) and the AR4050S (u1); #5-#6 read the stack's back (1,957 + 3,635).
4. #7 `sed -n '134,200p' tools/README.md` (3,350) for the qmark entry.
5. #8 `tools/tb qmark` on u0: the multicast commands for T30403, the route commands, the SNMP
   community and the aggregator commands for the later cases (1,740).
6. #9 address-free checks (ping .90 and .29). #10-#12 two Edits and a `sed -i` on the queue file (status IN PROGRESS).
7. #13 setup + before-state on u0 (one ckcon call). #14 `rc2cfg.py` -> swi_f.cfg, ping, walk 1 (GETBULK).
8. #15 walk 2 (GETNEXT). #16-#17 pulled both 12k-line walk files to the session scratchpad, diffed
   the OID lists and grepped the two dynamic tables (1,200 + 1,565).
9. #18 stability shows + teardown in one ckcon call. #19 read back the log tail and cpu (3,834).
10. #20 clocks of the other units again (1,404). #21 working log. #22 README entry for snmpwalk.py.
11. #23 commit. #24 ToolSearch for SendMessage. #25 RESULT.

## Wasted input
- #3 (6,005 chars): the whole `show vlan brief` .. `show system` span of the pre-run capture,
  read to learn the standing VLAN/port state. A `grep -E '^(port1\.0\.[1-5]|sa|po|[0-9]+ +VLAN)'`
  on that file gives the same facts in under 1k.
- #5-#6 (5,592 chars): the stack's running-config and aggregator sections. The facts used later
  (sa2 members, port1.0.17/1.0.3 VLANs, LACP passive off) are a 10-line grep.
- #7 (3,350): a second slice of `tools/README.md` (the overhead had read 20-135, 217-236 and
  352-460). One `grep -A12 '^### \`qmark.py\`'` would do, or include qmark in the first read.
- #20 (1,404): re-reading clock lines already read in #4 to write the working log's clock line.

## Repetition
- The queue file was edited three times in this case (#10, #11, #12) for one status change.
- #4 and #20 read the same `show clock` lines.

## Accuracy risks
- **No steps in the test-case database.** The case holds only an objective whose lines read like
  expected results ("Runs to completion", "Device is stable"). The three steps are the tester's;
  a Test Engineer may want SNMPv1/v3 or an IPv6 walk as well.
- **The walk-difference explanation** (icmpMsgStatsTable and tcpConnTable rows) is sourced only
  from the working log's prose: the diff output (#16-#17) went to the session scratchpad
  (`w1.txt`, `w2.txt`, `o1`, `o2`), not to `work/`. Save the `diff | head` output in `work/` next time.
- **Uptime arithmetic:** the working log says "+1 min 41 s for 1 min 39 s of box time", but its
  own box stamps (19:36:47 -> 19:38:28) are 1 min 41 s apart. The final log uses the device's
  `show system` clock instead (19:36:44 -> 19:38:26, 1 min 42 s). Harmless, but it shows hand arithmetic.
- **The `[SCRIPT]` lines** at 19:36:52 (IMISH pid 6650, one second after
  `snmp-server community ckwalk ro`) were called "the device's own" in the working log. That is
  an inference, so the final log quotes the lines without characterising them. On tb470,
  `[SCRIPT]` log lines together with a `<dev>_<test>_<run>` hostname mean the Test Engineer's own
  ART run (memory "Terrence's ART pipeline is the consumer"); here the hostname stayed `awplus`,
  so this is not that. Worth one question to the Test Engineer if it recurs.

## Next run: expected outputs (this bench, this build)
| step | expected |
| --- | --- |
| setup | `snmp-server community ckwalk ?` offers `<1-99> ro rw view <cr>`; `show snmp-server community` "Community Name ........... ckwalk / Read-only"; NSM "vlan105 installed address 10.38.215.90/27" |
| 1 GETBULK | `varbinds 12448  requests 623  retries 0  elapsed 9.7 s`, 31 subtrees, `stopped: END`, last OID `1.3.6.1.6.3.16.1.5.2.1.6.7.86.97.73.116.69.114.87.1.1` |
| 2 GETNEXT | `varbinds 12469  requests 12470  retries 0  elapsed 26.6 s`, same first/last OID; ±tens of varbinds from icmpMsgStatsTable / tcpConnTable are normal |
| 3 stable | `show exception log` None; uptime advances with the clock; no log line during the walks; `show cpu` 1 s back to ~1% |

## Next run: scripts
- `tools/snmpwalk.py` (built in this case) already does the walk. Add `--compare <other-outfile>`
  so step 2's OID-set diff and its per-subtree counts are printed by the tool and land in the
  working files, not the session scratchpad.
- The group pre-run capture (#1, #4) belongs to the group, not to the first case: see REVIEW.md.

## Next run: references
- `tools/README.md` `snmpwalk.py` entry (arguments, exit codes, the numbers above).
- This file's expected outputs; the x230 standing state (VLAN 103/104/105 isolation, no IPs) is
  in the queue's restore recipe, so the pre-run capture needs no read-back beyond a grep.
