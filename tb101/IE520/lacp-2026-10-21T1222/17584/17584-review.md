# T17584 process review -- lacp-2026-10-21T1222
Reviewed 2026-10-21 by /create-logs from agent-aa263e65e1ba965a5.jsonl (the RUN tester) and the working files.
The triage agent (agent-aca2a1875cb17111e.jsonl) is reviewed in the group [REVIEW.md](../REVIEW.md).

Note on the transcript: every tool call appears twice in it, once as an `assistant` record and once as an
`api-request-blob` record with the same tool-use id. The 190 calls below are the real ones; nothing was run twice.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 71 | 1,772 | 492,481 | 17,387,599 | 1,166 | 174 | 5,440 s (90.7 min) | 143,569 chars |

Cache read is 97% of all tokens. Each of the 71 API calls re-reads the whole conversation, and the
conversation grew through 6 events. So the cost driver is the NUMBER of calls late in the case, not
the size of any one output.

## Process taken
1. Calls 1-13 (group overhead, see REVIEW.md): read the queue, rules, platform file, memories, tools README.
2. Calls 14-23: gate. precheck, scratch, template, 4 console peeks, hostinfo, probe (MATCH), ckcase.
3. Calls 24-31: wrote `tools/bondctl.py`, added it to `SUDO_TOOLS` in tools/tb, wrote the group recipe into
   the queue, ran the pre-run reads (one ckcon batch, 20 commands), committed.
4. Call 32: pre-LACP control (2 linerate runs, 20 s each).
5. Calls 33-45: STEP 1 setup (bondctl up, cfg channel-group, E0 reads, copy + boot config-file via ckyn,
   rc2cfg -> IE520.cfg). Wrote `tools/lacpdu.py` and `hostinfo.py --stats`.
6. Calls 46-72 (E0, E1): per event, l2flows + 2 linerate + captures started as separate calls, then the
   event, then bondctl status during/after, cfg reads during/after, flowstat, linerate output, hostinfo
   stats, port counters, a working-log append, then 2 full-rate windows.
7. Calls 73-165 (E2-E6): the same sequence 5 more times, with `listen`/`reloadc`/`ckreload` for reloads
   and a `ckcon @poll` for member Ready.
8. Calls 166-174: STEP 5 control flows. Two capture attempts failed (`bond0` refused by `NIC_RE`; a
   captured file path refused), then `NIC_RE` was patched and the captures re-run on eth3 + eth4.
9. Calls 175-190: restore (cfg, bondctl down twice, delete t17584.cfg on 4 members, rcdiff, peeks),
   final probe, commit, RESULT, hand-back.

## Wasted input
- **Call 30 (7,867 chars) and call 29 (5,477 chars):** the pre-run capture was printed into the context
  after it was saved to a file. Only `show system` (needed verbatim for the log) and about 10 summary lines
  were needed. Narrower: `sed -n '/>>> show system/,/>>> show stack/p'` plus `grep -a` for the fields.
- **Call 143 (5,323 chars) and call 167 (3,238 chars):** health reads printed `show cpu` with its full
  process list (about 680 lines per sample on the box). Narrower: save the output, then
  `grep -a -E 'Stack member|CPU averages|1 second|userspace'` on it.
- **Call 105 (5,546 chars):** E3 post-reads printed in full, including `show reboot history` for all 4
  members (about 300 lines). Narrower: the first 2 entries per member (`awk` on the saved file), which is
  what the log used.
- **Calls 101, 119, 135, 157 (2,076-3,262 chars each):** each `ckcon @poll` returned every poll iteration.
  Narrower: print only the MATCHED/TIMED OUT line and the final reads.

## Repetition
- **The event sequence was hand-built 6 times.** Each event took 15-20 tool calls: start l2flows, start 2
  linerate senders, start captures, sleep, fire the event, bondctl status during and after, cfg reads
  during and after, flowstat, linerate results, hostinfo --stats, port counters, two full-rate windows,
  and a log append. About 120 of the 190 calls (calls 46-165) were this sequence. Because each call re-reads the
  growing context, the late events (E4-E6) cost the most. A script (below) would make each event 1-2 calls.
- **Waiting with `sleep N` in a foreground call** (calls 98-102, 116-120, 132-136, 151-156): each wait is a
  full API call. A `tools/tb waitfor` on a done-file, or one script that sleeps internally, removes them.
- **The working log was appended in 27 separate heredoc calls.** Writing per event is correct
  (logged-output.md §2); folding the append into the event script would keep that and save the calls.

## Accuracy risks
- **Mid-event reads were saved to the session scratchpad, not to `work/`.** E1-E5 `show etherchannel
  detail`, `show lacp sys-id`, `show stack` and bondctl status outputs exist only as recorded fields in
  run1.log. The final log had to mark 55 lines with `~` (recorded field, not verbatim output). Fix: `cp`
  each `$S/eN-*.out` into `work/` as it is taken, as was done for pre-run, post-setup, e6-pre and health2.
- **l2flows pins each flow to one LAG link.** Each flow has one source MAC, so the bond's layer-2 hash
  puts it on one link. At E2 every bond0 -> eth2 flow sat on the surviving link and measured nothing; the
  tester rightly used DUT counters instead (run1.log lines 330-343). Fix: give l2flows one flow per link
  (source MACs chosen to hash to each link), or a `--src-macs N` option like linerate.
- **No DUT in = out accounting for E3 and E4.** port1.0.1 and port2.0.1 counters reset with their member
  (run1.log line 398). Read counters on the surviving members only, or on port3.0.1 + the host.
- **O-1 (broadcast duplicates at member rejoin) is an inference.** The cause ("flooded over both ring
  directions") is not proven. To close: capture both sides with timestamps at 1,000 pps during one member
  reload, and read `show log` for stack-link and MAC-flush events in the same second.
- **O-2 (`Pckt err Sent 2` on port1.0.1)** has no explanation. To close: read `show lacp-counter` right
  after a fresh LAG forms on member 1 alone, then on member 2 alone, to see if it follows the master.
- **E5 master prediction in the triage was wrong** (member 2 predicted, member 1 won). The run corrected
  it from `stack 1 priority 1` in tb101-bench.cfg. Not a verdict risk, but the next triage should read
  the priorities from the probe's capture before predicting.
- **`show system` in run1.log ends at `System Location`.** It may be cut after that line by the capture.
  The final log copies it as recorded.

## Next run: expected outputs
| step | value on this bench (tb101, awplus_main-20261019-75) |
| --- | --- |
| 0 | `show lacp sys-id` -> `MAC Address: 0000.cd37.0d6f`; `show etherchannel` -> `LAG Dynamic Count  : 0` |
| 0 | single-link control, linerate top 20 s: ~712 Mbps, 100.0% both ways |
| 1 | `show etherchannel detail` -> `Receive link count 2 Transmit link count 2`, Partner LAG `0xffff,00-0d-b9-51-4d-a2,0x0009`; bond Partner Mac `00:00:cd:37:0d:6f` |
| 1 | `boot config-file` sync takes > 60 s the first time: use `CKTO=300` with ckyn/cfg |
| 2 | concurrent linerate top: ~375 Mbps A / ~441 Mbps B; host rx_fifo_errors rise, DUT counters in = out |
| 3 E1/E2 | outage toward the DUT 380 ms / 0.8 s (host bond detection); none toward the host |
| 3 E3 | `reload stack-member 1` -> member 4 master; 770 ms outage; member 1 Ready ~285 s after |
| 3 E4 | `reload stack-member 2` -> no outage >= 50 ms; Ready ~288 s |
| 3 E5 | `reload stack-member 4` -> member 1 master (priority 1); no outage >= 30 ms; Ready ~289 s |
| 4 | whole-stack `reload` -> 202.5 s outage, login after 206 s, LAG back from flash, member 1 master |
| all | `show lacp sys-id` = 0000.cd37.0d6f after every event; 4 duplicated broadcast frames at each member rejoin (O-1) |
| 5 | control bursts 0/0/0, positives 500/500 |

## Next run: scripts
- **Existing:** `tools/bondctl.py up|status|down` (bond with recorded-address restore), `tools/lacpdu.py`
  (decode LACPDUs), `tools/hostinfo.py --stats` (host NIC drop counters), `tools/linerate.py`,
  `tools/l2flows.py` + `flowstat.py` + `loopwin.py`, `tools/vsend.py` + `vcount.py`, `tools/reloadc.py`,
  `tools/ckreload.py`, `tools/listen.py`, `tools/rcdiff.py`, `tools/rc2cfg.py`.
- **`tools/eventwin.py`** (BUILT 2026-10-21 on the Test Engineer's "yes, all"; tested offline, not yet on hardware): one call per event.
  The arguments as built are in `tools/README.md` (`--act`, `--read`, `--poll`, `--after`, `--save work/eN`).
  It starts l2flows + both linerate senders, fires the timed actions, polls Ready, saves every read,
  runs flowstat + loopwin + hostinfo --stats, and writes one summary.
- **`l2flows.py --per-link N`** (BUILT 2026-10-21): N sub-flows per flow, each with its own source MAC, so a leg event is always measured; `flowstat.py`/`loopwin.py` read the sub-flows.
- **`tools/rcdiff.py` FIXED 2026-10-21**: it now uses only a header whose command is exactly
  `show running-config`, so the filtered read earlier in the capture no longer gives a false diff.

## Next run: references
- The group recipe and the event plan: the `## Group lacp-2026-10-21T1222` and `## Triage` sections of
  [CAMPAIGN-QUEUE-2026-10-21T1222.md](../../CAMPAIGN-QUEUE-2026-10-21T1222.md). Reuse them; do not re-plan.
- Backup consoles drop their session at a master reload: `platforms/IE520.md` §3 (last row).
- Election: lowest priority value wins, no pre-emption on rejoin: `/orient-dt` §6; tb101 sets
  `stack 1 priority 1` (memory `tb101-ie520-bench-map`).
- Host limits on tb101 (tcpreplay ~700 Mbps one way; igb rx_fifo_errors under concurrent load): run1.log
  "Observations" and this file's expected outputs.
- Health-read filtering: logged-output.md §2 "Check the DUT's health, every case".
