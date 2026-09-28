# Campaign queue and issue log — tb470, from 2026-09-29 07:50 NZDT

Terrence, 2026-09-29: *"I want to test two scripts, T33234 and T33235. Let me know if the current
topology supports those tests. shouldnt be multi-hour work."* Run through `/test-mode`: this
session is the sentinel, `bench-runner` subagents are the tester.

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Rules carried with the queue

- One log per case holding only the latest run, and its NAME states the outcome (`<id>.log` =
  PASS only; `-fail`, `-partial`, `-skip` otherwise): `STANDING-ORDERS.md` §2, which every queue
  inherits. Teardown is verified by diffing against a pre-test `show running-config` copy.
- Nothing is `write`n to startup-config unless a case requires it.
- Root changes on tb470, a `.setup` apply, a recable or destack go through Terrence via the
  sentinel (`NEEDS TERRENCE:`), never a blocking prompt; the case is logged and the tester moves on.
- Stop on any `% ` CLI line. Gate each dependent step on proven state.
- The scripts are the Ask-CK generated pair in
  `claude/Test-cases/ask-ck/functions/pytest-creator/generated/9001_Port/` (`test-9001.33234.py`,
  `test-9001.33235.py`, `library_9001.py`) and need `ck_media.py` (= `ask-ck/tools/pt_media.py`)
  beside them; run with `-s tb470.setup -v --noupdate --nodefaultcfg` (TESTBOX-ACCESS.md §3).

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | T33234 Port — Auto MDI/MDI-X | port-2026-09-29 | RUN (dispatched 08:4x) | triage 07:56: runnable; test port = a stack copper-SFP link chosen by the frame (nondeterministic, LAG member — log names it); cases 3–7 need Terrence at the bench with an RJ45 crossover (he is); 17–18 UNSUPPORTED (no fibre) |
| 2 | T33235 (3) Port — Fixed port speed | port-2026-09-29 | READY (after row 1) | script defect FIXED in Test-cases 4ef0dc4 (08:5x): `dut.reboot('', timeOut=900)`; frame now orders ports deterministically, LAG members last + flagged; re-run preflight then RUN. Was: TestCase_33 `dut.reboot(None, timeOut=-1)` = erase startup-config + reboot (I-1); fix sent to test-cases-43 08:26; re-triage when its commit lands. Also: take the test link out of its static-channel-group for the run, restore after (Terrence 08:2x: devices reconfigurable as required) |

## Issues (non-test-case decisions), in the order found

Status: OPEN (waiting on Terrence), CHOSEN (a blocker; recommendation applied, for review),
NOTED (no decision needed now).

- **I-1 T33235 TestCase_33 factory-defaults the stack.** `test-9001.33235.py:~6014` `dut.reboot(None, timeOut=-1)`; framework `Switch.reboot(confFile=None)` = `del force default.cfg` / `no boot config-file` / `erase startup-config` / reboot. Fix `dut.reboot('', timeOut=900)` or a literal `reload`. Sent to the Test-cases session 2026-09-29 08:26; FIXED there in 4ef0dc4 (+ a blocking lint against `.reboot(None` / `timeOut=-1`). RESOLVED.
- **I-2 Frame picks the test port from a set** (`Stack.members`), so port/partner vary per run and on tb470 every candidate is a LAG member. Sent with I-1; frame fixed in Test-cases 4ef0dc4 (deterministic order, LAG members last, `[LAG member]` tag + WARNING; not skipped, since on tb470 every candidate is one). NOTED — the test link still comes out of its aggregator for a speed run.
