# T20358 process review -- cli-2026-10-13T0949
Reviewed 2026-10-13 by /create-logs from `agent-a3ab1e57621c1d438.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 20 | 22,406 | 1,489,333 | 86 | 11 | 250 s | 18,472 chars |
| *apportioned:* 12 | 24 | 24,887 | 1,722,855 | (not re-split) | 13 | ~275 s | 23,982 chars |

The apportioned row adds two reads made for this case inside the T30403 segment (#3 the LACP memory,
2,730 chars; #4 the linerate/vsend README sections, 2,780 chars). The tool's output figure for this case
(86) looks low against the work done; output was not re-split.

## Process taken
1. #1 setup (`no lacp global-passive-mode enable`, `spanning-tree rstp enable`, port1.0.6-1.0.7 into VLAN 105)
   with the pre-closure proof (running-config, etherchannel, spanning-tree brief, interface brief) -> `setup.out`.
2. #2 `rc2cfg.py` -> `swi_f.cfg`, then the first loop closure with the `@poll` gate plus `show spanning-tree
   interface port1.0.7` under `--stop-on-error`: the gate matched in 5.1 s, then ckcon stopped (rc 2) on the
   `% `-prefixed spanning-tree lines, and the script's safety branch shut port1.0.7 (`emergency-shut.out`).
3. #3-#4 `grep` and `sed -n 95,156p tools/linerate.py` (3,031 chars) to learn the receive options.
4. #5 second closure, same gate, without the spanning-tree show (`loop2.out`): matched in 5.1 s.
5. #6 one call: spanning-tree interface 1.0.6/1.0.7 + counters -> linerate burst -> counters, brief,
   spanning-tree interface, `show log tail 40` (`before-traffic.out`, `traffic.out`, `after-traffic.out`).
6. #7 the log tail re-read from the file (3,674 chars); #8 teardown (port1.0.7 shut first) + `rcdiff.py`.
7. #9 working log; #10 commit + queue; #11 RESULT.

## Wasted input
- #2 (3,951 chars) and #5 (1,368): the first closure's output, then the emergency-shut and second closure,
  all came back in full. The detour itself is the cost (see Repetition); with the fix below, #2 would
  have been the measured closure.
- #4 (3,031 chars): reading `linerate.py` source for `--rx` behaviour. Its README entry (read in #4 of the
  T30403 segment) already gives the run line; `linerate.py --help` would have been ~1k.
- #7 (3,674 chars): `show log tail 40` printed from `after-traffic.out` although only the NSM/MSTP lines
  matter. `grep -a -E 'NSM|MSTP' after-traffic.out` is ~600 chars.

## Repetition
- The loop was closed twice (#2, #5) because `ckcon.py --stop-on-error` reads any `% ` line as a CLI error and
  `show spanning-tree interface` prints every line with a `% ` prefix on this build. One closure was enough:
  the gate had already matched Backup/Discarding. Cost: ~2 calls, ~1 min of the loop lead toggled, and an
  extra `shutdown`/`no shutdown` pair in the device log.

## Accuracy risks
- port1.0.7 transmitted one multicast frame during the counter window. The working log attributes it to LLDP
  (`lldp run`, 30 s interval) by inference; no capture shows it. The final log says only "one multicast frame
  (not broadcast)". To close it: `show lldp statistics interface port1.0.7` before/after, or a mirror capture.
- The case says "Role ... BackUp (Loopback Disabled)"; this build prints only "Backup". Graded on Backup /
  Discarding; the wording difference is in the CAVEAT.
- The objective's second sentence (back to forwarding when BPDUs stop) was not measured on a direct lead;
  stated in the CAVEAT, not graded.
- No claim was left out of the final log for lack of a source.

## Next run: expected outputs
| step | what | expected on this bench |
| --- | --- | --- |
| setup | `show spanning-tree brief` | port1.0.6 / 1.0.7 `Disabled Discarding` (link down / admin down) |
| 1 closure | `no shutdown` port1.0.7 + `@poll 20 port1\.0\.7\s+\S+\s+\S+\s+Backup\s+Discarding show spanning-tree brief` | MATCHED after ~5 s; port1.0.6 `Designated Forwarding`, port1.0.7 `Backup Discarding` |
| 1 log | `show log` | `port1.0.7 user no shutdown`, both ports up, `CIST port1.0.6 now forwarding`; never `port1.0.7 now forwarding` |
| 1 role | `show spanning-tree interface port1.0.7` | `Role Backup - State Discarding`, `Designated Port Id 838e`, `Designated Bridge 800000c28f3f0f5d`, `Received RSTP` |
| 1 traffic | linerate 10 Mb/s x 10 s, 1500 B, broadcast from eth3 | sent 8356; eth3 rx = its own 8356 only |
| 1 counters | after - before | port1.0.6 output broadcast +8356; port1.0.7 output broadcast 0; port1.0.5 output broadcast 0 |

## Next run: scripts
- **`tools/ckcon.py`** (existing): run `show spanning-tree interface` *without* `--stop-on-error`, or (proposed)
  add `--error-regex REGEX` so a caller can narrow "error" to `^% (Invalid|Unrecognized|Incomplete|Ambiguous)`.
  Record the `% `-prefix trap in its README entry.
- **`tools/ifdelta.py`** (proposed): `ifdelta.py BEFORE.out AFTER.out --ports port1.0.5-1.0.7` parses two
  `show interface` captures and prints the per-port deltas of input/output packets, multicast and broadcast.
  The tester did this arithmetic by hand in the working log; the final-log writer had to redo it.
- The case's setup/closure/traffic/teardown is a fixed recipe (queue "Run, group 1" T20358); a case script in
  the next run's `work/` built from it would make the case 3-4 calls.

## Next run: references
- Queue `CAMPAIGN-QUEUE-2026-10-13T0949.md`, "Run, group 1" T20358 setup and restore order (port1.0.7 shut FIRST).
- `platforms/x230v2-28GS.md` §2: STP loop cases need a direct port-to-port lead (now cabled 1.0.6 <-> 1.0.7).
- Memory `lacp-passive-hides-links-from-stp` (why `no lacp global-passive-mode enable` precedes the closure;
  the Test Engineer has since written it into the bench config, so check the baseline before sending it).
