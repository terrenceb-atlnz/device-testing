# Process review -- platform-2026-10-09T0845 (tb470, x230v2-28GS swi_f, 11 cases)
Reviewed 2026-10-12 by /create-logs from `agent-a591963d08f049547.jsonl` (the bench-runner transcript)
and the cases' working files. Raw numbers: `tools/case_tokens.py --find ~/.claude/projects/<slug>
--cases 47226,47227,47215,31852,31853,31855,31856,31861,31858,31863,31866`. Findings cite the
transcript tool call (#n = the n-th tool call of the transcript, 83 in all) or a working file.
Recommendations are the reviewer's.

## Token usage

**The tool's split is wrong for this group, so the table below is re-apportioned.** The tester ran
the eight read-only cases (T47226 ... T31861) in **one console login** (#26) and reported all eight
in **one** SendMessage (#40). `case_tokens.py` starts a case at its first tool call that names
`<group>/<id>/`; the tester's calls named the group dir through a shell variable (`$G/$id`), so the
tool saw almost no case boundaries. It gave T47226 8 calls, T47227-T31856 nothing, and put 67 of 81
calls in overhead.

**Method used here.** Segments are bounded by the RESULT SendMessage timestamps (#40 18:05:26,
#49 18:10:41, #70 18:25:40, #75 18:36:39 NZDT); usage is attributed to the API call that issued
each tool call. Inside the read-only batch (#26-#40, 15 calls, 18:02:19-18:05:26): #28 (show version
read back) and #30 (repo-wide `Build name` grep) served only T47226 and are charged to it; the other
13 calls (the console run, output reads, `.cfg` writes, working-log generation, commits, RESULT) are
split evenly over the eight cases. Wall time is split the same way (#28 + #30 = 45 s to T47226).
Fractions are rounded.

| segment | API calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| overhead, before the cases (#1-#25: dispatch, reading, gate, probe, queue edit) | 23 | 46 | 106,458 | 1,843,705 | 469 | 25 | 154 s | 114,654 chars |
| T47226 (share of batch + #28, #30) | 3.6 | 7 | 6,402 | 419,268 | 38 | 3.6 | 63 s | 12,822 chars |
| T47227 (1/8 of batch) | 1.6 | 3 | 3,252 | 197,178 | 22 | 1.6 | 18 s | 1,672 chars |
| T47215 (1/8 of batch) | 1.6 | 3 | 3,252 | 197,178 | 22 | 1.6 | 18 s | 1,672 chars |
| T31852 (1/8 of batch) | 1.6 | 3 | 3,252 | 197,178 | 22 | 1.6 | 18 s | 1,672 chars |
| T31853 (1/8 of batch) | 1.6 | 3 | 3,252 | 197,178 | 22 | 1.6 | 18 s | 1,672 chars |
| T31855 (1/8 of batch) | 1.6 | 3 | 3,252 | 197,178 | 22 | 1.6 | 18 s | 1,672 chars |
| T31856 (1/8 of batch) | 1.6 | 3 | 3,252 | 197,178 | 22 | 1.6 | 18 s | 1,672 chars |
| T31861 (1/8 of batch) | 1.6 | 3 | 3,252 | 197,178 | 22 | 1.6 | 18 s | 1,672 chars |
| T31858 (#41-#49, 1 reload) | 9 | 18 | 13,405 | 1,271,564 | 70 | 9 | 299 s | 7,352 chars |
| T31863 (#50-#70, 2 reloads) | 21 | 42 | 21,853 | 3,325,557 | 291 | 21 | 889 s | 12,669 chars |
| T31866 (#71-#75, 2 reloads) | 5 | 10 | 179,556 | 694,105 | 82 | 5 | 643 s | 2,909 chars |
| overhead, after the cases (#76-#83: after-probe, queue Results, tools/README edit, hand-back) | 8 | 16 | 7,785 | 1,455,084 | 79 | 8 | 139 s | 5,288 chars |
| **total** | **81** | **162** | **358,225** | **10,389,526** | **1,186** | **83** | **2,363 s** | **167,396 chars** |

Totals reconcile with `case_tokens.py` (81 API calls; cache write 358,225). The tool's own per-case
rows, for the record: T47226 8 calls / 1,005,297 cache read; T31861 1 / 133,506; T31858 3 / 438,409;
T31863 1 / 170,397; T31866 1 / 175,672; the rest 0; overhead 67 / 8,466,245.

**Where the tokens go.** Cache reads are 97% of the volume: every API call re-reads the whole context,
which grew from 44k tokens at the first call (dispatch + system prompt) to ~107k when the first case
started and ~186k at hand-back. Two things dominate:
1. **The up-front reading** (#1-#25, 115k chars, ~29k tokens) is carried by every one of the ~58
   later calls: roughly 1.7M of the 10.4M cache-read tokens.
2. **One cache expiry in T31866** (#72 at 18:31:09): the previous tool call (#71) blocked for
   5 min 13 s (pre-capture + a 165 s reload + setup + logout), longer than the prompt cache's
   5-minute lifetime, so the next call **re-wrote the whole 173,222-token context** into the cache.
   That one write is 48% of the group's cache write. At cache-write pricing (about 12x a cache read)
   it cost more than all of T31866's other calls together. See "Cross-case findings" 1.

The cases themselves were lean: the batch spent ~1.6 calls per read-only case, T31858 9 calls and
T31866 5 calls for a case with two reloads. T31863 (21 calls) carried the BIST/PRBS discovery for
both reload cases plus a four-call teardown detour (its review).

## Overhead findings

**Wasted input -- 115k chars read before the first case (#1-#25).**

| call | size | what | narrower read |
| --- | ---: | --- | --- |
| #7 | 33,214 | `TESTBOX-ACCESS.md`, Read in full | none: the lab-home CLAUDE.md requires reading it in full before touching a testbox. Only the Test Engineer can relax that rule |
| #2-#3 | 13,356 + 6,916 | queue file lines 1-250 | Session facts (lines 10-32) + this group's Run section (`sed -n '/^### Run 1/,/^### Run 2/p'`) |
| #8 | 14,062 | `tools/README.md` lines 1-235 | `grep -A8` the entries this group used: ckcon.py, ckyn.py, ckreload.py, qmark.py, poll.py, rcdiff.py, rc2cfg.py (~5k) |
| #5-#6 | 7,196 + 8,019 | STANDING-ORDERS 1-120, logged-output.md 40-188 | logged-output §2 is what a tester needs; STANDING-ORDERS §1-§3 only |
| #13 | 6,744 | orient-dt SKILL.md 26-60 + x230 grep | `platforms/x230v2-28GS.md` (now exists, ~6k) carries the x230 traps |
| #11 | 4,408 | the eleven case texts from `ck.db` | needed (the working logs quote them); fine |

**Repetition.** Each working log repeats the same ~2k-char session-facts / devices / gate block (11
copies). logged-output.md §2 allows later cases to point to the first case's log; the tester did that
for the clock and NIC facts but not for the rest. It cost output tokens, not context, so it is minor.

**Accuracy (group-wide).**
- **The DUT clock has no timezone** and holds NZ local wall time labelled "UTC" (54 s behind tb470 at
  18:02; within 2 s after T31858's restore). Every DUT timestamp reads as NZDT. Recorded once in the
  T47226 working log, as it should be.
- **The `?` help output was never saved into `work/`.** #50/#51 (`tools/tb qmark`) wrote
  `q1.out`/`q2.out` to the session scratchpad only, and the working logs carry a condensed summary
  (`platform ? -> bist ..., prbs, ...`). The final logs of T31863 and T31866 therefore state the
  parser's forms as Method/CAVEAT text and cannot quote them. Fix: copy every `qmark` capture into
  the case's `work/` (or name it in the working log as `work/qmark-<n>.out`).

## Cross-case findings (said once here; case reviews point here)

1. **Keep every blocking tool call under ~4.5 minutes** (T31866 #71, 5 min 13 s -> a 173k-token
   cache rewrite). A reload is ~165 s on this x230 (platforms/x230v2-28GS.md §1), so "pre-capture +
   reload + setup + verify + logout" in one call crosses the line. Split at the reload: one call for
   capture + reload, the next for setup. T31863 kept its reload calls at 3-3.5 min and had no expiry.
2. **`ckcon.py --stop-on-error` stops on AW+'s informational `% The new exec-timeout settings will
   apply to new sessions only`** (T31863 #58, T31866 #71). The command is applied, but the rest of
   the sequence (`end`, verify, `exit`) is lost and needs another call. Either send `exec-timeout 0`
   without `--stop-on-error`, or give ckcon an allow-list (proposed below).
3. **Refused platform commands are cheaper as one non-stopping call.** T31863 #60 (`ckyn`, stopped
   at the first `% BIST test not supported.`, exit 2) then #61 for the other forms. One `ckcon`
   without `--stop-on-error` carrying every form + `show platform bist` + `show exception log` gives
   the same evidence in one call.
4. **Each reload drops the running-only `lldp run`** (found by `rcdiff.py` in T31858 #44; re-added
   in #45 and in both later teardowns). It is now in the queue's restore recipe and in
   platforms/x230v2-28GS.md §1. Put it in the post-reload block from the start.
5. **Working logs were generated by a scratch shell library** (`loglib.sh` in the session scratchpad,
   #33) and then spliced (#47, #68). It worked, but it died with the session and the next tester will
   rebuild it. Proposed as a tool below.

## Next run: scripts

| need | today | recommended |
| --- | --- | --- |
| the eight read-only factory cases | one `tools/tb ckcon` login, then the output read back in full (#28-#29, 15.7k chars) and graded by reading | **`tools/cliplan.py`** (proposed, the CLI twin of `mbplan.py`): a plan file of `case  command  expect-regex  [forbid-regex]` lines, one login via ckcon, prints one PASS/FAIL row per line and writes the capture. The expected outputs below become the plan; grading is a diff, not a read |
| informational `% ` lines | `--stop-on-error` stops on them | **`ckcon.py --allow-pct REGEX`** (proposed flag): a `% ` line matching REGEX does not stop the run (first entry: `apply to new sessions only`) |
| working-log generation | scratch `loglib.sh` (header from session facts, step blocks from a capture) | **`tools/wlog.py`** (proposed): `wlog.py header --facts <group facts file> --case <id>` and `wlog.py block <capture> "<command>"` (verbatim block by command name, ANSI/CR stripped). /create-logs needs the same block extractor |
| reload + post-reload restore | `tools/tb ckreload ... 720`, then a hand-typed VLAN 103-105 + `lldp run` block per case | keep `ckreload.py`; add the restore as a `cfg.py` file (`x230-tb470-restore.cfg`) applied after each reload |
| config diff after teardown | `tools/rcdiff.py <pre> <post>` | existing; fits |

Build none of these without the Test Engineer's go; they go in `tools/` with README entries.

## Next run: references (read these instead of re-deriving)

- **`platforms/x230v2-28GS.md`** (written at this campaign's wrap): §1 build name x220, reload
  163-168 s, reload drops `lldp run`; §2 table: no eth0 (T31855 step 3), `platform bist`/`platform
  prbs` refused at run time and the prbs forms, `no exec-timeout` quirk. Reading it first replaces
  #30 (repo-wide grep), #52-#56 (ckyn/ckcon source, wiki) and the qmark probes for a re-run.
- **tools/README.md `ckcon.py` entry:** `CKTO` (per-command timeout, default 90 s) is documented
  there (#52 and #56 read tool source for it).
- **This group's README.md** as the expected verdict per case.

## Suggested shape of the next platform run

1. Gate (precheck, probe) -- as now, ~8 calls; read the platform file instead of orient-dt 26-60.
2. Read-only cases: `cliplan.py platform-ro.plan` (one login) + one call writing the eight working
   logs + one commit + one RESULT message -- 4 calls instead of 15.
3. Clock case: as T31858 (it was already lean), with `lldp run` in the post-reload block.
4. BIST/PRBS: one capture + reload call (<4.5 min), one setup + `exec-timeout 0` + logout call, one
   non-stopping call with every form + show + exception log, one closing reload + restore call --
   about 5 calls each, no help probing, no config-level teardown before the closing reload.
