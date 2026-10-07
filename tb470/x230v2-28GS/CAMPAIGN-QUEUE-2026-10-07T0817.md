# Campaign queue — tb470 x230v2-28GS, AWPTCM 5700 bootloader follow-up TestCases on bootloader 6.2.40, from 2026-10-07 08:17 NZDT

Follow-up to [x230v2-28GS/bootloader-6.2.40/CAMPAIGN-QUEUE-2026-10-06T1325.md](../../x230v2-28GS/bootloader-6.2.40/CAMPAIGN-QUEUE-2026-10-06T1325.md)
(final logs b60a24c, wrap 535edd2). The ask, Terrence 2026-10-07:
- 5700.2005: *"If the fail was just that word, thats a Pass for that test case."* (2005.2 → PASS
  for that TestCase; its TestSet stays PARTIAL until 2005.3–.8 have run.)
- 2002.110: *"fix the file then, and re-run it after we sort out the rest of this."*
- *"patch the wording check to add nand0 as well, same as import copy."*
- *"then run them one at a time"*: every TestCase below is its own framework invocation.
- Shape: *"Have the other session's sentinel kick off the sub-agent while you monitor from here"*.
  Session `device-testing-c7` dispatches the `bench-runner` subagent; session `device-testing-13`
  is the sentinel and keeps this file and the Results table.
  **Changed 08:3x (Test Engineer: "Run it from this session"):** c7 was blocked on its own pending
  question, so `device-testing-13` dispatches the `bench-runner` itself (one-session shape) and is its
  sentinel. c7 dispatches nothing (countermand queued to it).

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-07 08:17 NZDT (Test Engineer's answers to the setup questions):
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u0 only (x230v2-28GS, S/N A10783G262900002, 9600; swi_a in the suite's default.setup)
PDU: 10.36.150.14, outlet 1 (u0)
Constraints: "Same as 10-06": "do not interact with any other devices yet" (u0 + its PDU outlet 1 only); sentinel stands down when the run ends. Host session: "Stay in VS Code" for 10-06; for this run "Have the other session's sentinel kick off the sub-agent while you monitor from here".

Occupancy 08:17: `precheck --consoles u0` CLEAR (exit 0).

Decisions 2026-10-07 ~08:45 (Test Engineer, answers to the triage):
- Occupancy 08:3x FOUND calanm minicom on u2, u5, u4 (not ours; u0 free): *"Proceed on u0 only"*.
- D1 run flags: *"Same as 10-06"* -- each invocation `-s default.setup -u -v <n>` (no `--noupdate
  --nodefaultcfg`): initial power cycle, framework default.cfg boot, ACCESS licence step, ~8 min each.
- D2 licences (2005.3-.6 call `update_feature_licenses(featureList=['ALL'])`): *"Allow ALL, remove
  after"* -- run as written; after the last row remove every licence the suite added, leaving u0 at
  Base + ACCESS (read `show license` before row 1 and after the restore; record both).
- Release: *"Accept the swap"* -- whatever build is in /tftproot at each boot; record the build per TestCase.

## The patched suite (Test Engineer's two edits, nothing else)

- Source: the pristine suite `claude/raw-data/test_scripts/5700_bootloader/` (read-only; md5
  `library_5700.py` 0519963993a8ecbbedbb18fad5dd8e44, `test-5700.2002.py` 0be9b375…,
  `test-5700.2003.py` c8c4bc02…, `test-5700.2005.py` 7a75b85e…, `runTestSuite.py` ed903949…).
- Patch: [x230v2-28GS/bootloader-6.2.40/5700_x230v2-28GS_6.2.40_run3/library_5700.diff](../../x230v2-28GS/bootloader-6.2.40/5700_x230v2-28GS_6.2.40_run3/library_5700.diff),
  patched `library_5700.py` md5 7d357e1df0105a934ad15fa076d4fb99. Three lines:
  `import copy` (2002.110's `NameError`), and `'Erasing nand0'` added to the security-level
  reset's wait list and pass condition (`library_5700.py` ~613; 6.2.40 prints `Erasing nand0:`).
- **Where the scripts live:** the lab-tree hook refuses `.py` files in the repo, so the scripts
  are staged on tb470 in `/tmp/x230/run3/` (tmpfs): the pristine `test-5700.200{2,3,5}.py`,
  `runTestSuite.py`, the patched `library_5700.py`, and a `framework -> /home/st-art/framework`
  symlink. Each invocation runs with **cwd = its own runner dir** in the repo (Folders, below; holds
  `default.setup` + the framework's logs, no `.py`), invoking the script by absolute path.
- `default.setup`: copied unchanged from `x230v2-28GS/bootloader-6.2.40/5700_x230v2-28GS_6.2.40_run2/`.

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  The final log is made ONLY by `/create-logs`, on the Test Engineer's request.
- A "case" here is ONE framework TestCase (id `5700.<set>.<n>`), run alone: from its runner dir,
  as root, `/tmp/x230/run3/test-5700.<set>.py -s default.setup -u -v <n>` (confirm the
  TestCase-selection syntax against ATTestSet before the first launch). One invocation per row,
  in queue order; never two at once.
- **Folders (Test Engineer 2026-10-07: one clean log per TestSet, re-runs overwrite;
  logged-output.md §3 "Merging TestCase re-runs"):** everything lands in the 10-06 campaign's own
  folders under `x230v2-28GS/bootloader-6.2.40/`:
  - working log: `<set>/work/run3-<TestCase>.log`, e.g. `5700.2005/work/run3-2005.4.log`;
  - runner dir (cwd, `default.setup`, framework logs), one per invocation:
    `5700_x230v2-28GS_6.2.40_run3/<TestCase>/`, e.g. `5700_x230v2-28GS_6.2.40_run3/2005.4/`.
  `/create-logs` later merges each re-run into the TestSet's existing final log.
  The framework holds u0 for the whole invocation, so no tester `.cfg` is captured mid-run (as
  on 10-06); the device config is the framework's `default.cfg` + what the case logs in `swi_a_<set>.log`.
- **Bench setup, set ONCE before the first row and restored ONCE after the last**
  (STANDING-ORDERS §6): u0's bootloader default boot source = TFTP `x230-tb470.rel` (Boot Menu
  2 → 3, prompts as in the 10-06 queue's "Row #1" section); `/tftproot/x230-tb470.rel ->
  x230v2_28GS-tb470.rel` must resolve (re-create only with the Test Engineer if tb470 rebooted:
  root). Restore after the last row: Boot Menu 2 → 9 ("Boot from default (determined by main
  CLI)") + plain-reload proof (`Loading flash:x230v2_28GS-tb470.rel`, no forced banner), u0 back
  to the 10-07 07:53 state (boot image `flash:/x230v2_28GS-tb470.rel`, boot config
  `flash:/default.cfg`, manager/friend, Boot Security Level none), logged out.
- `STANDING-ORDERS.md` applies; §6: the framework's post-failure power cycle (outlet 1) is accepted.
- Root-owned output on the NFS share is chowned back to terrenceb before commit.
- After a deliberate erase (2005.x security-level resets) the framework's boot-config reset fails
  and flags "TestSet configuration file missing" (framework c1e7679). With one TestCase per
  invocation that only affects the case's tear-down; the tester restores u0's release and
  `default.cfg` between rows if the erase removed them (the 10-06 queue's "Run 2 baseline /
  restore recipe"; **never delete the current boot config**).

## Row 1 — group setup and restore recipe (bench-runner, 2026-10-07 08:42, before any device change)

**Gates 08:38–08:41 (read-only):** precheck `--consoles u0` exit 5 = calanm's minicom on u2/u4/u5 only
(Test Engineer: "Proceed on u0 only"); `/dev/u0` free, `sudo fuser` no holder; peek: `awplus login:`.
Read-only probe (`--out /tmp/x230/run3/bench-state-u0-pre.md`, capture 2026-10-06T193902Z) exit 1
MISMATCH = the swi_a/swi_f naming + hub lines only (as 10-06); NEEDS-CHECK eth3 (read-only, no ping);
device row: AT-x230-28GS V2, A10783G262900002, 9600, awplus_main-20261006-52, bootloader 6.2.40,
boot image flash:/x230v2_28GS-tb470.rel. tb470 up 19:54 (no reboot), `/nfsHome` mounted,
`/tftproot/x230-tb470.rel -> x230v2_28GS-tb470.rel` resolves (36,553,967 B, .info -52). Framework
`/home/st-art/framework` HEAD 89900a6. pt_preflight on default.setup: 2002/2003/2005 RUNNABLE.
Single-TestCase CLI confirmed in ATTestSet.py 1528–1589/1749: positional `<n>` matched against
`testCaseNum` (int from `TestCase_<n>`).

**u0 baseline 08:39 (ckcon; evidence `x230v2-28GS/bootloader-6.2.40/5700.2002/work/run3-group-baseline-pre.txt`):**
boot image `flash:/x230v2_28GS-tb470.rel` (file exists), backup Not set, boot config
`flash:/default.cfg` (file exists), Boot Security Level none; flash = `default.cfg` (512 B) +
`x230v2_28GS-tb470.rel` (36,553,967 B) + `log/`; licences **Base License + ACCESS**; bootloader
default boot source = 9 "determined by main CLI" (wrap 07:53); running-config saved as
`5700.2002/work/run3-u0-prerun-running-config.txt` (manager/friend, near-factory).

**Group setup (once, before 2002.110):**
1. tb470 `/tmp/x230/run3/` (tmpfs): pristine `test-5700.2002/2003/2005.py` + `runTestSuite.py`
   (md5s = the queue's), `library_5700.py` patched with `library_5700.diff` (md5 7d357e1d…),
   `framework -> /home/st-art/framework`, `tools/` copy. Done 08:38.
2. Runner dirs `x230v2-28GS/bootloader-6.2.40/5700_x230v2-28GS_6.2.40_run3/<TestCase>/` × 8, each with
   `default.setup` (md5 71e33a5c…, = run2's). Done 08:39.
3. u0 Boot Menu 2 → 3 (TFTP default: IPv4, 10.38.215.34, 255.255.255.224, 0.0.0.0, 10.38.215.33,
   x230-tb470.rel → `Saving settings... Complete`), plain-reload proof (forced banner + `Loading
   tftp://10.38.215.33/x230-tb470.rel`), log out. Driver `/tmp/x230/run3/blmenu23.py`.
   **Done 08:41–08:47:** `Saving settings... Complete` 08:41:50; proof reload 08:44–08:47: `Warning: System has
   been forced to boot from a non-standard location` → `Loading tftp://10.38.215.33/x230-tb470.rel via USB Ethernet
   adapter...` → `Verifying release... OK` → login, `Current software : x230-tb470.rel`, show boot = baseline; logged
   out (rc 0). Evidence `5700.2002/work/run3-group-blmenu23-3.out` (driver source `run3-group-blmenu23.py.txt`).

**2002.110 launched 08:47:30** (wrapper pid 133067, test-5700.2002.py 133070).

**Per TestCase:** `sudo -n setsid nohup /tmp/x230/run3/launch1.sh <set> <n>` → cd runner dir,
`/tmp/x230/run3/test-5700.<set>.py -s default.setup -u -v <n> > run.stdout 2>&1`; markers
`/tmp/x230/run3/<set>.<n>/{start,rc,done}`. Between rows, if the case erased u0: the 10-06 queue's
"Run 2 baseline / restore recipe" (release back over port1.0.1 with temporary vlan1 10.38.215.74/27,
`boot system`, keep/recreate `default.cfg` as boot config — **never delete the current boot config** —
security level none, manager/friend).

**Group restore (once, after 2005.8), or by a fresh tester if this one dies:**
1. Let any in-flight test-5700 process / PDU cycle finish (or stop it by PID, root); outlet 1 ON.
2. u0 console: back out of any Boot Menu (submenu `0`, main `9`); if Boot Security Level ≠ none,
   Boot Menu `S` → `1` (level 1, erases flash) and then the between-rows restore above.
3. AW+: the between-rows restore; delete leftover `mainrelease.rel`/`backuprelease.rel`/`copy*`/
   `swi_a_5700_*.cfg`/`TestCase_*.cfg`; `show boot` = the baseline above.
4. Licences: remove every licence the suite added so `show license` = Base License + ACCESS
   (Test Engineer: "Allow ALL, remove after"); record `show license` after.
5. Boot Menu 2 → 9 ("Boot from default (determined by main CLI)"), plain-reload proof
   (`Loading flash:x230v2_28GS-tb470.rel`, no forced banner); `exit` (log out).
6. precheck CLEAR for u0; read-only u0 probe to `/tmp` only. Leave `/tftproot` as found.

## Tonight's start — 18:00 2026-10-07 (for the session that runs `--resume` on this file)

Test Engineer 15:2x: *"queue the test again to start at 6pm and watch it until its done"*. The
session that set this up (device-testing-73) expires before 18:00, so a new session started in
tmux on the dev host (`tmux new -s test-mode`) takes it over with `/test-mode --resume` on this file.
It does this instead of dispatching straight away:

1. **Before 18:00 dispatch nothing and touch nothing.** Arm the sentinel (`/test-mode` §3:
   Monitor `sentinel.sh SELF=1` on its own transcript, `UNTIL='2026-10-08 12:00'`, `CLI_GLOB` /
   `FW_GLOB` over `x230v2-28GS/bootloader-6.2.40/5700_x230v2-28GS_6.2.40_run3/*/`; the 15-min cron
   backstop, silent before 18:00). If session `device-testing-73` is still listed in `ListAgents`,
   SendMessage it `tmux session armed for 18:00` (it then deletes its own 18:00 trigger).
2. **CronCreate one-shot `0 18 7 10 *`** that:
   a. gates read-only: `bench_probe.py --box tb470 precheck --consoles u0` says `/dev/u0` free,
      and no `test-5700` process on tb470; else NEEDS YOU, dispatch nothing;
   b. sets the Queue row to IN PROGRESS and commits;
   c. dispatches a FRESH background `bench-runner`, mode RUN, sentinel: parent, with these rows in
      order:
      - u0 recovery: Boot Menu `S` → `1`. Expected: Security Level 2, password `abc 123`
        (verify). This erases flash. Then the between-rows restore.
      - 5700.2005.5 from scratch (overwrites `run3-2005.5.log`, Test Engineer's overwrite rule).
      - 5700.2005.6, .7, .8, one invocation each.
      - The group restore (below).
      Commit per case, one RESULT line per case. **No new TestCase is launched after 07:00
      2026-10-08 without the Test Engineer** (reboot noise; NEEDS TEST ENGINEER instead).
3. **When the group restore is done:**
   a. Post the results list (`/test-mode` §7), ending with *"please run /create-logs after
      reviewing the results for the final uploadable product."*
   b. Delete `x230v2-28GS/bootloader-6.2.40/current_test.log` (Test Engineer: "when its over,
      delete it").
   c. Give Terrence `sudo rm /tftproot/x250-tb470.rel /tftproot/x230-copy-tb470.rel
      /tftproot/x230-tb470.rel` (root's; "when this is done, delete them").
   d. Run `/wrap-dt`. The handover notes:
      - the licence-key printout earlier today was reviewed by the Test Engineer, no action;
      - on 10-07 two copies of session 73 ran at once and two testers collided on u0 (2005.4
        re-run);
      - calanm took over u0 at 14:53 to stop the noise.
   e. **Never `/create-logs`** unless the Test Engineer asks.
4. `device-testing-c7` (pid 512164, an unreachable desktop session) is not part of this. It is
   stuck at an old prompt and has been told to ignore the handover queued to it.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | 5700.2002.110, 5700.2003.10, 5700.2005.3, 5700.2005.4, 5700.2005.5, 5700.2005.6, 5700.2005.7, 5700.2005.8 (one invocation each, in this order) | x230v2-28GS/bootloader-6.2.40 (case folders 5700.2002 / 5700.2003 / 5700.2005; runner dirs 5700_x230v2-28GS_6.2.40_run3/<TestCase>/) | **HELD until 18:00 2026-10-07** (Test Engineer 15:2x: "queue the test again to start at 6pm and watch it until its done"). Next: u0 Boot Menu S → 1 + between-rows restore, then 5700.2005.5 from scratch, .6, .7, .8, group restore. **Nothing touches u0 before 18:00.** 2002.110–2005.4 done (Results) | 2005.3–.8 were ~9 h of Feb's 10 h 20 m TestSet; 2005.5 is the longest (225 checks in Feb) |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| 5700.2002.110 | Test all options for one-off boot (TestCase 110) | bootloader-6.2.40 | PASS | run4 (replaces run3, Test Engineer's overwrite rule): 13/13, rc 0, 09:22-09:49; one-off boots of main release, backup release and a TFTP copy each booted, default reverted to TFTP after each; step 4 ran (import-copy patch); in-line fix: baseline .rel deleted from flash before launch | 5700.2002/work/run4-2002.110.log | tester |
| 5700.2003.10 | Boot stage 2 diagnostics: Filesystem FLASH test (TestCase 10) | bootloader-6.2.40 | PASS | 2/2, rc 0, 09:51-10:03: stage-2 Filesystem FLASH test "Result for test 2/2 (pass 1): PASS" (8 NAND bad blocks skipped, "expected"); Q returned to the stage 2 menu. The test erases the filesystem by design (ACCESS licence removed too; u0 restored between rows) | 5700.2003/work/run3-2003.10.log | tester |
| 5700.2005.3 | Set Security Level 3 (TestCase 3) | bootloader-6.2.40 | PASS | 30/30 of its own checks, 10:06-10:55: level 3 set, passwords, protected options, factory restore keeps level 3, reset to level 1 ("Erasing nand0" accepted by the patch). Framework FAIL 30/1 = c1e7679 post-erase config reset (harness). ALL licence step: ACCESS accepted, 5 refused (Base + ACCESS). 10:06 start-shell refusal = ACCESS missing after 2003.10's erase, re-added 10:07:25, case unaffected | 5700.2005/work/run3-2005.3.log | tester |
| 5700.2005.4 | Check the password length limits, >5 and <24 (TestCase 4) | bootloader-6.2.40 | PASS | run4 (re-run after the 10:58 attempt was disturbed by a second tester and stopped, Test Engineer: "Stop it now, re-run"): 44/44 own checks, 11:11-12:23: 24-char "Maximum password length is 23", 5-char "Minimum ... 6", 23/6-char passwords gate menus 1/2/3/5, level 1 via the patched nand0 gate. Framework 44/1 = c1e7679 harness. ALL licences -> ACCESS only | 5700.2005/work/run4-2005.4.log | tester |

## Issues

- 2026-10-07: Test Engineer re-graded 5700.2005.2 (in the 10-06 campaign) to PASS for that
  TestCase: the only device-side FAIL was the `Erasing flash` / `Erasing nand0:` wording. The
  10-06 Results row is updated to match (TestSet 5700.2005 → PARTIAL, re-graded from FAIL).
- 2026-10-07 15:2x, Test Engineer: calanm stopped the 2005.5 run (his minicom on u0 at 14:53:19)
  *"at the behest of those around him, the automated rebooting was causing distress due to the
  noise."* Decision: *"queue the test again to start at 6pm and watch it until its done"*.
  2005.5 re-runs from scratch at 18:00; 2005.6–.8 and the group restore follow in the same
  evening. **The reboot-heavy rows run after hours only:** no row is launched after 07:00
  2026-10-08 without asking the Test Engineer. u0 sits as calanm left it (expected: bootloader
  Security Level 2, password "abc 123") until 18:00.
