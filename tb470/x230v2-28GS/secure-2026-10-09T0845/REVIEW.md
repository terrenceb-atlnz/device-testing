# Process review -- secure-2026-10-09T0845 (tb470, x230v2-28GS swi_f on u0, T47114-T47115)
Reviewed 2026-10-12 by /create-logs from `agent-aace2d4eb36f55205.jsonl` (the bench-runner transcript for this group)
and the cases' working files. Numbers: `tools/case_tokens.py --cases 47114,47115` on that transcript. Findings cite the
transcript call (segment #n, in the order the calls were made) or the working log. Recommendations are the reviewer's.
T47120, T47119 and T47121 were NOT TESTED and have no review.

## Token usage

| segment | API calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| overhead (gates, reading, hand-back) | 20 | 40 | 89,237 | 1,801,640 | 312 * | 22 | 160 s | 134,005 chars |
| T47114 | 29 | 58 | 37,990 | 3,806,463 | 4,277 | 31 | 648 s | 24,975 chars |
| T47115 | 36 | 72 | 51,254 | 6,259,219 | 347 * | 36 | 864 s | 28,023 chars |
| **total** | **85** | **170** | **178,481** | **11,867,322** | **4,936 *** | **89** | **1,672 s** | **187,003 chars** |

\* The output column is under-recorded for this transcript. T47115's segment wrote an 18 kB working log in one call
(~5k output tokens), yet shows 347. The per-message usage records seem to keep only part of the output count. The
cache columns are consistent and are what this review uses.

**Where the tokens go.** Cache reads are 98% of the volume. The context averaged ~90k tokens per call during the gates,
~131k per call in T47114 and ~174k per call in T47115. **The single largest cost is not a case: it is the group restore
inside T47115's segment** (#14-#35: 22 tool calls, 4.19M cache read, 35% of the group's total). Next comes the 134k chars
read up front, carried by every one of the 65 later calls.

## Overhead findings

**Wasted input: 134k chars (~34k tokens) read before the first case.**

| call | size | what | narrower read |
| --- | ---: | --- | --- |
| #9 | 33,214 | TESTBOX-ACCESS.md, Read in full | none: the lab-home CLAUDE.md requires reading it in full before touching a testbox. Only the Test Engineer can relax that rule |
| #2-#3 | 11,574 + 19,936 | the queue file, lines 1-95 and 165-232 + 270-400 | the dispatch carried the group's rows and constraints. Only the group's own row, its "Run 4 ... restore recipe" block and the Results rows are needed (`grep -n` for them, then one `sed` range) |
| #15-#16 | 7,505 + 9,951 | STANDING-ORDERS excerpts + **another group's working log** (`platform-.../31858/work/run1.log`, 165 lines), read as a template, + `tools/tb --help` | logged-output.md §2 is the working-log template. `tools/tb --help` alone for the wrapper's verbs |
| #6 | 14,451 | tools/README.md lines 20-250 | `grep -A8` on the seven entries used (`tb`, `ckcon.py`, `ckyn.py`, `ckreload.py`, `qmark.py`, `rcdiff.py`, `rc2cfg.py`) |
| #7 | 7,625 | logged-output.md §1-§2 | fine (the tester's part only) |
| #10-#14 | ~18k | two memories, the wiki `crypto-secure-mode.md` + `show-secure-mode.md`, repo-wide greps for "secure mode" | needed this time (first secure-mode run). Next time: platforms/x230v2-28GS.md §2 now carries the result |

**Repetition / detours.** None of note in the gate itself: precheck, scratch, peek and probe took 4 calls (#18-#21).

## Cross-case findings (said once here)

1. **The group restore was planned on an assumption that did not hold, and it dominated the group's cost.** The
   dispatch asked the tester to back `flash:/default.cfg` up before the first write and "restore it byte for byte" after.
   The tester made the backup (T47114 #12-#14) without checking that a copy back was possible. In T47115 #15-#21 every
   route was refused (`% Cannot overwrite flash:/default.cfg as it is configured as the boot config file`, `... as it is
   the default config file`, `% Config files must end in .cfg`, `% Cannot delete flash:/default.cfg ...`). The restore
   then went through `no boot config-file`, removing the running-only lines, `write` and a reload. The startup config is
   NOT byte-identical: a new header, `service password-encryption` gone, `security-password minimum-length 8` /
   `history 1` added (T47115 run1.log R2d). This is teardown, so it is out of both final logs.
   - **Process:** check a restore route read-only BEFORE the first write (`copy ... ?` and the platform file), and agree
     the fallback with the Test Engineer at triage, not mid-run. Memory `awplus-default-cfg-cannot-be-overwritten` and
     platforms/x230v2-28GS.md §1 now record the rule.
   - **Accuracy:** the bench's x230 startup config differs from before this group (above). Any later case that reads
     the startup config, or relies on `service password-encryption`, sees the changed file.
   - **Record keeping:** the group restore is recorded only in T47115's working log, so it reads as part of a case.
     A group-level `work/restore.log` (or the queue's run block) is the right home.
2. **Captures were read by guessed line ranges.** T47114 #27 read `stepD-u0.out` to line 212, and the `show log` output
   began at 213. So the `Verification of the release file has failed` warning was not seen at grading. The sentinel
   caught it, and it cost 4 calls to correct (T47115 #3-#6). Read a capture by command marker, or with the proposed
   `tools/capcmd.py`.
3. **The boot excerpt was hand-extracted twice** (T47114 #22-#25: 4 calls, two of them empty; T47115 #26). A reload
   helper that saves the boot text (proposed below) does it in the same call as the reload.
4. **The case database has no steps for either case** (both Draft, one empty step). The tester built a procedure for
   each from the title and the AW+ command pages, and the final logs quote those procedures. The procedures and this
   review's expected outputs are worth giving to the Test Engineer for the cases in Zephyr, so the next run grades
   against the case and not against a tester's reading of a title.
5. **Terminal control bytes in captures.** The console's screen-size query (`ESC 7 ESC[r ESC[999;999H ESC[6n`) leads the
   output of `show log` and `show file` in ckcon/ckyn captures (`stepD-u0.out` line 214, `verify-obs-u0.out`,
   `backup-u0.out`). The final logs strip it. Having ckcon strip it at capture time would keep `grep` and diffs clean.
6. **The release-verification warning** (`user.warning ... Verification of the release file has failed, please verify
   it.`) is logged by every secure-mode boot of this dev build. Both final logs quote it with a CAVEAT that release
   verification was not part of the case. platforms/x230v2-28GS.md §2 explains why `crypto verify` does not apply to a
   dev build. For the Test Engineer: whether it should be raised against the build.

## Next run: scripts

| need | today | recommended |
| --- | --- | --- |
| one command's output from a capture | `sed -n '<guessed lines>p'` (missed the warning) | **`tools/capcmd.py <capture> "<command>"`** (proposed): print that command's block by its `>>>` marker |
| boot text of a reload | `tools/tb tail` 400 lines + grep, 1-4 calls per reload | **`ckreload ... --boot-log <file>`** (proposed): save console text from `reload` to the login prompt |
| grade expected rejections | read 15 `% ` lines by eye | **`ckcon --expect '<regex>'`** per command, or a plan file `command<TAB>regex` (proposed) |
| log in as a test user | not possible (`tools/tb` drops the environment) | **`tools/tb` passing `CK_USER`/`CK_PASSWORD`**, or `awlogin.py --user` (proposed); and one line in the `tb` README entry |
| startup-config restore on x230 | 22 calls of trial and error | a written recipe in platforms/x230v2-28GS.md §1 (exists now); no script needed |

Build none of these without the Test Engineer's go. They go in `tools/` with README entries.

## Next run: references (read these instead of re-deriving)

- `platforms/x230v2-28GS.md` §1 (default.cfg cannot be overwritten; secure-mode boot ≈ 265 s) and §2 (the
  `crypto secure-mode` advisory; `show secure-mode` reports config; the release-verification warning; no `no` form for
  `security-password minimum-categories`).
- Memory `awplus-default-cfg-cannot-be-overwritten`.
- The two case reviews' expected-output tables (`47114/47114-review.md`, `47115/47115-review.md`).
- AW+ wiki on the share: `crypto-secure-mode.md`, `crypto-verify.md`, `security-password-*.md`.

## Suggested shape of the next secure-mode run

1. Gate (precheck, peek, probe): 4 calls, plus the group's queue rows only.
2. Agree the restore with the Test Engineer at triage (write-based restore, or a root-shell copy), and check it read-only.
3. T47114: capture, step A+B (without stop-on-error), C with `--boot-log`, D, working log, RESULT: ~8 calls.
4. T47115 (plus T47120's CLI half, which needs secure mode too): one plan-driven `ckcon` call for steps 1-3, teardown,
   working log, RESULT: ~6 calls.
5. Group restore (`no crypto secure-mode`, write, reload with `--boot-log`, re-apply isolation): ~4 calls, logged in a
   group file.

That is about 25 calls against 85 here, and it avoids the 4.2M cache read the restore detour cost.
