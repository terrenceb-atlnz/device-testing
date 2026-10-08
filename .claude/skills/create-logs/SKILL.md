---
name: create-logs
description: Build a campaign's final uploadable output, ON REQUEST ONLY — after the Test Engineer has reviewed the results list. For each attempted case it writes the final <id><suffix>.log from the logged-output.md template using the tester's latest working log, checks the per-device .cfg files, writes each group's README verdict table, measures each case's token usage from the tester's transcript and writes a process review (<id>-review.md per case, REVIEW.md per group: wasted input, repetition, accuracy risks, expected outputs, scripts and references for a faster next run), then deletes the case's work/ folder and commits. Use when the Test Engineer runs /create-logs, or says "create the logs", "make the final logs", "build the uploadable output". Never run it on your own initiative, and never as part of /test-mode or /wrap-dt, except `--auto`, which the sentinel runs at the end of a campaign whose queue says Driver: ask-ck (manual cases only, no confirm, work/ kept).
---

# /create-logs — the final logged output, on request

The rules are **[logged-output.md](../../../logged-output.md)**: §1 verdicts, §2 the working
files and the results list, §3 what this skill does, §4 the template. **Read it in full first.**
This file is only the procedure. Where they disagree, logged-output.md wins, and fix this file.

**Who runs it.** The Test Engineer, after reviewing the campaign's results list. `/test-mode`
ends a campaign with *"please run /create-logs after reviewing the results for the final
uploadable product."* Nothing runs this skill automatically, **except a campaign whose queue
says `Driver: ask-ck`**: there the sentinel runs `/create-logs --auto` at the end (§0 below).
User-driven campaigns are unchanged (Terrence, 2026-10-09: *"I still do not want user-driven
/test-mode sessions to create logs automatically."*).

**What it needs.** Only what is committed in the repo:
- the campaign's queue file and its `## Results` table;
- each case's `work/` folder;
- each case's `<dev>.cfg` files.

It runs in the sentinel session or in any later session started in this repo. **It never
touches a testbox:** no ssh, no console, no probe.

---

## 0. `--auto` — Ask-CK campaigns only (Terrence, 2026-10-09)

`/create-logs --auto <queue file>` is the one automatic form. It differs from the normal run in
exactly these ways:
- **It refuses unless the queue's `## Session facts` has a `Driver: ask-ck (<run id>)` line**
  (written by `/test-mode --from-ask-ck`). Without it, say "`--auto` is for Ask-CK campaigns only"
  and stop. A person typing `/create-logs` gets the normal run.
- **Manual cases only.** A case run from a framework script keeps its framework TestSet log as
  the final output, so skip it. A script case is one whose queue row or working log names the
  `.py` it ran. List what was skipped.
- **No confirm.** Skip §2's AskUserQuestion. Re-grading happens in Ask-CK's results table, and
  Terrence has the final say on every grade.
- **Keep `work/`.** Skip §6 step 1: *"we may require the evidence"*. A re-grade before acceptance
  is a re-run, `/create-logs --auto <queue file> <id>`. It rebuilds that case's final log from
  `work/`, replacing the old one.
  - `work/` is deleted only when Terrence presses "Accept results" in Ask-CK.
  - How that acceptance reaches this repo is open (Ask-CK `plans/PLAN-agent-sessions.md`). Until
    it is designed, nothing here deletes an Ask-CK campaign's `work/`.
- Everything else (the §3 template, the §4 checks, the §5 README, the §5b review, one commit per
  group, never push) is unchanged.

## 1. Find the campaign and its results

1. **Arguments:** an optional queue file path, optionally followed by case ids to limit the run
   (`/create-logs tb470/IE520/CAMPAIGN-QUEUE-2026-10-02T0900.md 24032`). `--auto` first selects
   §0's Ask-CK mode; it needs the queue file named.
   - With no queue file, take this session's campaign if it ran one. Otherwise take the newest
     `*/*/CAMPAIGN-QUEUE-*.md` whose Session facts name this Test Engineer (`whoami`@`hostname`).
     Say which file you took.
2. **Read the queue file's `## Results` table** (logged-output.md §2). Its columns are case,
   title, group, verdict, reason, working log and graded-by.
   - **No Results table** means a campaign from before 2026-10-02. Say so and stop; those logs
     are not regenerated (logged-output.md §4, "Existing logs").
3. **Reconcile with the tree, never from memory.** For every row:
   - **An attempted case** (any verdict but NOT TESTED) needs `<group>-<STAMP>/<id>/work/` with
     at least one `run<N>.log`. The latest run's `VERDICT:` line must agree with the table, or
     the table's graded-by must say the Test Engineer re-graded it.
   - **A row whose case already has its final log and no `work/`** is done. Skip it and say so.
     (An `--auto` campaign keeps `work/` beside the final log; §0 says when its log is rebuilt.)
   - **A case with a `work/` folder but no Results row** is still running, or was never
     reported. Leave it alone and list it.
   - **NOT TESTED** needs no folder. It still gets its README row.

## 2. Confirm once — this is the Test Engineer's last chance to re-grade

Show the table you are about to build from: case, verdict, graded-by, the working log you will
use, and the `.cfg` files present. Under it, list anything step 1.3 found that does not
reconcile. Then ask **one** AskUserQuestion:

- **"Create the final logs for these N cases?"**
  - "Yes, create them" (Recommended)
  - "Re-grade first": take their changes, write each into the Results table with graded-by
    `Test Engineer, re-graded from <VERDICT> on <date>`, show the table again, and ask again.
  - "Not yet": stop and change nothing.

Never re-grade on your own. A verdict that looks wrong to you goes in the summary for them to
decide, not into the log.

## 3. Write each final log

For each confirmed case, in queue order:

1. **Read the latest `work/run<N>.log` in full**, plus the files under `work/` that it names.
   The final log describes **that run only** (logged-output.md: each run stands alone). Earlier
   runs are not mentioned.
   **Exception, TestCase re-runs** (`work/run<N>-<TestCase>.log`): merge them into the TestSet's
   one log per logged-output.md §3 "Merging TestCase re-runs" — the re-run TestCase's result
   replaces its earlier one, everything else in the base log stays verbatim.
2. **Write `<group>-<STAMP>/<id>/<id><suffix>.log`** from the §4 template:
   - the suffix comes from the Results verdict: PASS → none, FAIL → `-fail`, PARTIAL →
     `-partial`, UNSUPPORTED → `-unsupported`;
   - the header comes from the working log and the queue's Session facts: Run, Bench, Tester,
     Graded, Case, Build, Configs;
   - VERDICT, then the verdict block for that verdict, then CAVEAT;
   - TOPOLOGY AS TESTED;
   - one STEP block per case step: the commands with their prompts, the raw output, `<--` notes
     and the `=> STEP n <VERDICT>:` line.
3. **Source every line.** Copy device output verbatim from the working log; never retype or
   tidy it. A claim with no source in the working log is left out. List it for the Test
   Engineer instead.
4. **Leave out** everything logged-output.md §4 "Out" lists: earlier runs, detours,
   infrastructure findings, conversations, the teardown proof.
5. **Check the folder** against the log's TOPOLOGY. Every device in it needs its `<dev>.cfg`,
   starting with the three `!` header lines. If one is missing, say so in the summary. Never
   invent or reconstruct a `.cfg`.
6. **Check the tools.** Every helper the working log names must be in `tools/`. If one exists
   only in `work/`, `git mv` it into `tools/`, add its `tools/README.md` entry (logged-output.md
   §2), and list it in the summary.

**Many cases?** For a large campaign, dispatch one background subagent per group (`claude`
agent type) to do steps 1–6 for that group. Give each one logged-output.md, the group's rows
and this section. It must not commit, delete or touch any other group. Then check each log it
wrote against §4 below before going on.

## 4. Check every final log before cleaning up

Nothing is deleted until every check passes for that case:

- The file name's suffix matches the Results verdict, and only a PASS is a plain `<id>.log`.
- The header has Run, Bench, Tester, Graded, Case, Build and Configs. Graded matches the
  Results table.
- The `VERDICT:` line matches the file name. A FAIL has `FAIL CONDITION:`, a PARTIAL has
  `NOT RUN:` and `UNBLOCK:`, and an UNSUPPORTED has `NEEDS:` and `ABSENT:`.
- Every STEP heading carries a step verdict, and every non-baseline STEP ends with its `=>`
  line.
- Every `.cfg` the Configs line names exists in the folder.
- No mention of an earlier run, another campaign, a sentinel message or `work/`.

A case that fails a check keeps its `work/`. Say what failed in the summary and go on to the
next case.

## 5. The group README

For each group touched, write `<group>-<STAMP>/README.md` exactly as logged-output.md §3 step 5
gives it:
- one line naming the testbox, the DUT and the date span;
- a verdict table with every Results row of the group, NOT TESTED included;
- no other prose.

Rewrite the whole file each time from the Results table, so a later `/create-logs` run for the
same group leaves it complete.

## 5b. Review the process — token usage, waste, repetition (Test Engineer, 2026-10-08)

The rules and the file layout are logged-output.md §5. Do this **before §6 deletes `work/`**: it
reads the working files as well as the tester's transcript.

1. **Measure.** From the repo root:
   `python3 -I tools/case_tokens.py --find ~/.claude/projects/<repo slug> --cases <ids, run order>`
   (`<repo slug>` = the repo root path with every non-alphanumeric character turned into `-`).
   Add `--json > <scratchpad>/tokens.json` for the numbers you will tabulate. It names the
   transcript it used; check that its `RESULT` lines are this campaign's. No transcript found
   → say so in each review and go on from the working files.
2. **Read the process, not just the numbers.** For each case, the tool's largest outputs and
   repeated commands are where to look first. Then read that case's tool calls in the
   transcript segment (never the whole transcript into context: extract the segment's tool
   inputs and result sizes with a short script in the scratchpad), and its `work/` scripts.
3. **Find, per case** (logged-output.md §5 "What it looks at"): wasted input, repetition,
   accuracy risk — each citing the call or working-file line — and what the next run should
   reuse: expected outputs per step, scripts (an existing `tools/` entry, or a proposed one
   with its arguments), and references to read instead of rethinking.
   - Include the claims the final-log writers had to leave out for lack of a source (§3 step
     3); they are accuracy risks with a known fix.
   - Anything that applies to every case of the group (gate overhead, rules re-read per case,
     a driver rebuilt per case) goes once in the group `REVIEW.md`, and the case file points
     to it rather than repeating it.
4. **Write** `<id>/<id>-review.md` for each attempted case and `<group>-<STAMP>/REVIEW.md` for
   the group, in the layout logged-output.md §5 gives. Never change a verdict here; a doubt
   about one goes in the report to the Test Engineer.
5. **Do not build the proposed scripts in this skill.** List them; building one is the Test
   Engineer's call (and a hand-built `.py` belongs in `tools/`, never loose in the lab tree).

## 6. Clean up and commit

1. **Delete `<id>/work/`** (`git rm -r`) for each case that passed §4. **Not with `--auto`**:
   an Ask-CK campaign keeps `work/` (§0). Delete nothing else: the
   `.cfg` files and the final log are the deliverables, and `<id>-review.md` stays beside them.
2. Afterwards each case folder holds exactly its one `.log`, its `.cfg` files and its
   `<id>-review.md`. Check that with `ls`.
3. **Commit once per group**:
   `create-logs: <group>-<STAMP> — <n> logs (<counts by verdict>)`, with the Co-Authored-By
   trailer. The working files remain in git history.
4. **Never push.** Report the hashes; the Test Engineer pushes.

## 7. Report

End with:
- the table of final logs: case, verdict, log path, `.cfg` files;
- the token table (per case plus overhead and total) and the three biggest savings the
  reviews propose, with a link to the group `REVIEW.md`;
- anything skipped or failing a check, and why;
- any claim left out for lack of a source;
- any tool moved into `tools/`;
- the commit hashes;
- one line: **"The logs and .cfg files under `<TB>/<FAMILY>/<group>-<STAMP>/<id>/` are ready to
  attach in Zephyr."**

If the campaign's session has not been wrapped yet, add: "Run `/wrap-dt` to close the session."
