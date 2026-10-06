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

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | 5700.2002.110, 5700.2003.10, 5700.2005.3, 5700.2005.4, 5700.2005.5, 5700.2005.6, 5700.2005.7, 5700.2005.8 (one invocation each, in this order) | x230v2-28GS/bootloader-6.2.40 (case folders 5700.2002 / 5700.2003 / 5700.2005; runner dirs 5700_x230v2-28GS_6.2.40_run3/<TestCase>/) | QUEUED | 2005.3–.8 were ~9 h of Feb's 10 h 20 m TestSet; 2005.5 is the longest (225 checks in Feb) |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

- 2026-10-07: Test Engineer re-graded 5700.2005.2 (in the 10-06 campaign) to PASS for that
  TestCase: the only device-side FAIL was the `Erasing flash` / `Erasing nand0:` wording. The
  10-06 Results row is updated to match (TestSet 5700.2005 → PARTIAL, re-graded from FAIL).
