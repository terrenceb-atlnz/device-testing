---
name: create-logs
description: Build a campaign's final uploadable output, ON REQUEST ONLY — after the Test Engineer has reviewed the results list. For each attempted case it writes the final <id><suffix>.log from the logged-output.md template using the tester's latest working log, checks the per-device .cfg files, writes each group's README verdict table, then deletes the case's work/ folder and commits. Use when the Test Engineer runs /create-logs, or says "create the logs", "make the final logs", "build the uploadable output". Never run it on your own initiative, and never as part of /test-mode or /wrap-dt.
---

# /create-logs — the final logged output, on request

The rules are **[logged-output.md](../../../logged-output.md)**: §1 verdicts, §2 the working
files and the results list, §3 what this skill does, §4 the template. **Read it in full first.**
This file is only the procedure. Where they disagree, logged-output.md wins, and fix this file.

**Who runs it.** The Test Engineer, after reviewing the campaign's results list. `/test-mode`
ends a campaign with *"please run /create-logs after reviewing the results for the final
uploadable product."* Nothing runs this skill automatically.

**What it needs.** Only what is committed in the repo:
- the campaign's queue file and its `## Results` table;
- each case's `work/` folder;
- each case's `<dev>.cfg` files.

It runs in the sentinel session or in any later session started in this repo. **It never
touches a testbox:** no ssh, no console, no probe.

---

## 1. Find the campaign and its results

1. **Arguments:** an optional queue file path, optionally followed by case ids to limit the run
   (`/create-logs tb470/IE520/CAMPAIGN-QUEUE-2026-10-02T0900.md 24032`).
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

## 6. Clean up and commit

1. **Delete `<id>/work/`** (`git rm -r`) for each case that passed §4. Delete nothing else: the
   `.cfg` files and the final log are the deliverables.
2. Afterwards each case folder holds exactly its one `.log` and its `.cfg` files. Check that
   with `ls`.
3. **Commit once per group**:
   `create-logs: <group>-<STAMP> — <n> logs (<counts by verdict>)`, with the Co-Authored-By
   trailer. The working files remain in git history.
4. **Never push.** Report the hashes; the Test Engineer pushes.

## 7. Report

End with:
- the table of final logs: case, verdict, log path, `.cfg` files;
- anything skipped or failing a check, and why;
- any claim left out for lack of a source;
- any tool moved into `tools/`;
- the commit hashes;
- one line: **"The logs and .cfg files under `<TB>/<FAMILY>/<group>-<STAMP>/<id>/` are ready to
  attach in Zephyr."**

If the campaign's session has not been wrapped yet, add: "Run `/wrap-dt` to close the session."
