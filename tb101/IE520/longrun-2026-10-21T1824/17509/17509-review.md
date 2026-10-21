# T17509 process review -- longrun-2026-10-21T1824
Reviewed 2026-10-22 by /create-logs from agent-a8b6dc9d63bb39f79.jsonl (triage + Phase A),
agent-a5c2c189ca4b1f2e2.jsonl (Phase C) and the working files. Phase B had no tester; its cost
is the sentinel's, in the group [REVIEW.md](../REVIEW.md).

## Token usage
| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| triage + Phase A (a8b6dc9d) | 88 | 178 | 207,732 | 12,065,920 | 19,397 | 89 | 1740 s | 135,371 chars |
| Phase C (a5c2c189) | 60 | 120 | 308,463 | 7,232,279 | 802 | 62 | 1318 s | 133,532 chars |
| hand-back (a5c2c189) | 1 | 2 | 381 | 163,961 | 24 | 1 | 19 s | 143 chars |

`case_tokens.py` puts all of a8b6dc9d under "overhead": that tester never sent a `RESULT` line
(Phase A by design ends without one). Its numbers above are the case's real Phase A cost.

## Process taken
1. Triage: precheck, read-only probe (NEEDS-CHECK, host-NIC portlinks only), read-only IXIA
   status, VID 100 check, `qmark` of the case's show commands. Committed febc1c7.
2. Phase A: baseline probe without `--read-only`; built `tools/ixtcl.py`; pre-run reads; config-mode
   `qmark`; setup config; `write`; whole-stack `reboot`; built `tools/longrun.py` during the reboot.
3. Phase A: before-reads (23 commands, 5023 lines to a file), health 1, `.cfg`, MAC-learn pair,
   control + positive at start, one foreground sampler test, continuous start (one failed
   attempt, fixed), detached sampler launch. Commits 172c201, 6fe1c2f, a8d5a93.
4. Phase B: no tester; the sampler ran 13 samples on tb101 (sentinel committed 0cec1a0).
5. Phase C: gates, IXIA stop + final counters, control + positive at end, after-reads, health 2,
   grading tables, restore (IXIA reset/release, DUT config, write, reboot, rcdiff, probe MATCH),
   one tool fix (`ckcon --stop-on-error` on `remote-diff` report lines). Commits e205267, 5666c25,
   1988f20.

## Wasted input
- Phase A `cat` of the whole queue file, 17,174 chars; Phase C did it again, 22,528 chars. Each
  tester needed only "The plan", "Tools to build", the setup/restore recipe and (Phase C) the
  "Phase A record" and Grading block. `sed -n` on those sections would have been about a third.
- Phase C `cat work/run1.log`, 20,450 chars. Phase C needed the Phase A record lines and the
  health-1 path, not the full Phase A narrative.
- `tools/README.md` read in sections by both testers: 11,913 chars (Phase A) and 10,686 chars
  (Phase C), largely the same entries (console.py, ckcon, cfg, health).
- Phase C `cat progress.tsv; cat ixia.tsv`, 8,803 chars, to build the grading tables by hand.
  An `awk` summary (or the proposed `longrun.py --report`, below) prints the same tables.

## Repetition
- The queue file, `logged-output.md` and `tools/README.md` were read by both testers (and by the
  sentinel). See the group REVIEW.md.
- Phase A hit three tool defects in a row and fixed each in place: IxTclHal's global `bad`
  (exit 3 with every RC 0), the `exec-timeout` advisory stopping `cfg.py`, and `-numFrames 0`
  failing a continuous `stream set`. Phase C hit a fourth: `ckcon --stop-on-error` stopping on
  `remote-diff`'s own `%` report lines. All four are fixed in `tools/` now; a next run should
  not meet them.
- `work/health1.json` was a truncated copy (199 of 373 lines). Phase C spent calls proving that and
  re-copying it from the box.

## Accuracy risks
- **Run label.** `tools/health.py` printed `!! DIRTY -- exception log not None -- report NEEDS
  TEST ENGINEER, label the run confounded`. The tester labelled the run clean, because the
  exception log was byte-identical before and after (2026-10-20 entries). That reading is
  well supported, but it is the tester overriding its own tool's label. It waits for the Test
  Engineer's confirmation (queue `## Issues`, 2026-10-22 07:13). Fix: either `clear exception
  log` before the next campaign (Test Engineer's call), or teach `health.py --before` to report
  an unchanged exception log as "unchanged since before" instead of DIRTY.
- **Equal totals on both ports.** Both IXIA ports read 51,445,932,572 sent and received. A reader
  can suspect one port's row was printed twice. The tester closed this with the end control
  burst (10/5 sent 1000, 10/6 sent 0). Keep that check in the log.
- **Which stack link carried the traffic was not measured.** The log says the traffic crossed
  the stack from member 3 to member 4. No stack-port counter was read. Reading `show interface
  port3.0.27,port3.0.28,port4.0.27,port4.0.28` before and after would show the path.
- **Case adapted to the bench.** The case names an XS916MXT/XS916MXS pair and a TeraTerm macro.
  The log says so in CAVEAT. The case's "spannig-tree" typo was corrected and noted.
- Claims left out of the final log for lack of a source: none.

## Next run: expected outputs
- Setup: `stack 3 priority 1` + `no stack 1 priority`, then `write` + `reboot` -> member 3 Active
  Master; `IE520-1 login:` about 193 s after `y`.
- `exec-timeout 0 0` prints `% The new exec-timeout settings will apply to new sessions only`
  (advisory; now on `console.ADVISORY`).
- 512 B at 50 % of 10G -> 1,174,764-1,174,766 fps each way; UDS1 fps == tx fps.
- Free memory per member: m1/m2/m4 about 279-282 MB, m3 (master) about 269-273 MB of 506724 kB;
  hour-to-hour noise up to about 4 MB.
- CPU busy 1-9 % per member under traffic; `show cpu history` 30-min average in the 10 % row.
- 278 new `show log` lines over the run, all `IMISH` echoes (15 per hourly sample).
- Control: 0 of 1000 VLAN 3 frames at 10/6 UDS2, switch input +1000, output +2 multicast.
- Final counters: framesReceived - UDS1 = 1446 per port (the switch's own multicasts).

## Next run: scripts
- Existing, reuse as they are: `tools/ixtcl.py` (status, take, release, reset, filter, stream,
  burst, clear, start, stop, counters), `tools/longrun.py --detach`, `tools/health.py`,
  `tools/rc2cfg.py`, `tools/rcdiff.py`, `tools/tb reloadc`.
- Proposed: `tools/longrun.py --report <out dir>` -> prints the 13-sample memory / CPU / rate
  tables (markdown), per-member min / max / range / least-squares slope, and the "steady fall"
  flag. Phase C built these by hand from `progress.tsv`.
- Proposed: `tools/ixtcl.py pair --ports 10/5,10/6 --control-sa ::03 --control-vlan 3 --count 1000`
  -> runs control-then-positive as one call and prints the four counter lines. The pair was
  rebuilt by hand twice (start and end) from five calls each.
- Proposed: `health.py --before` reports "exception log unchanged since before" as CLEAN with a
  note, not DIRTY (only if the Test Engineer agrees; see Accuracy risks).

## Next run: references
- Memory `ixia-chassis-82-tcl-access` (Tcl client env, TclServer step, ownership, stream idiom).
- Memory `tb101-ie520-bench-map` (consoles, serials, IXIA cabling 10/5 <-> port3.0.25, 10/6 <->
  port4.0.25).
- The queue's "Phase A record" section (tb101/IE520/CAMPAIGN-QUEUE-2026-10-21T1824.md) and this
  case's final log for every value above.
- `tools/README.md` entries for `ixtcl.py` and `longrun.py` (arguments as used here).
