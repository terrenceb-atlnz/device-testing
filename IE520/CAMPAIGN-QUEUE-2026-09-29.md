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
| 1 | T33234 Port — Auto MDI/MDI-X; T33235 (3) Port — Fixed port speed | port-2026-09-29 | TRIAGE | copper host-NIC edges: eth1→stack port3.0.13, eth2→IE520-sa port1.0.2, eth3→x230 port1.0.1 (bench-state.md 2026-09-28T181632Z, MATCH) |

## Issues (non-test-case decisions), in the order found

Status: OPEN (waiting on Terrence), CHOSEN (a blocker; recommendation applied, for review),
NOTED (no decision needed now).

- (none yet)
