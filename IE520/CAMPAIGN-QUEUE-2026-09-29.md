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
| 1 | T33234 Port — Auto MDI/MDI-X | port-2026-09-29 | DONE — FAIL ([33234-fail.log](port-2026-09-29/33234-fail.log)) | run 2 08:48–08:57: case 1 FAIL = script defect `no polarity` (I-3); case 2 FAIL = REAL: IE520 copper-SFP port shows `current polarity auto`, no mdi/mdix (I-5); framework power-cycled the whole bench after each failed case (I-4), run stopped by SIGINT; cases 3–18 not run, no cable swap asked. Test link was stack port1.0.9 <-> x230 port1.0.4 (both sa2 members freed + VLAN-isolated, I-6). Bench restored: configs IDENTICAL, boot pointers tb470-bench.cfg, probe 09:07 MATCH. Re-run needs: I-3 fix in Test-cases AND a decision on I-5/I-4 |
| 3 | T33234 Port — Auto MDI/MDI-X — RE-RUN | port-2026-09-29 | PAUSED (tester holding) → waits for the Test-cases regeneration after the I-5 ruling; expected outcome on tb470: UNSUPPORTED (`33234-skip.log`), no fixed copper port | free BOTH sa2 legs (recipe in 33234-fail.log), cases 3–7 with Terrence at the bench (crossover), DUT-side role verdicts expected FAIL per I-5, restart-on-fail accepted (I-4) |
| 2 | T33235 (3) Port — Fixed port speed | port-2026-09-29 | RUN (resumed 12:3x, ahead of row 3) | script defect FIXED in Test-cases 4ef0dc4 (08:5x): `dut.reboot('', timeOut=900)`; frame now orders ports deterministically, LAG members last + flagged; re-run preflight then RUN. Was: TestCase_33 `dut.reboot(None, timeOut=-1)` = erase startup-config + reboot (I-1); fix sent to test-cases-43 08:26; re-triage when its commit lands. Also: take the test link out of its static-channel-group for the run, restore after (Terrence 08:2x: devices reconfigurable as required) |

## Issues (non-test-case decisions), in the order found

Status: OPEN (waiting on Terrence), CHOSEN (a blocker; recommendation applied, for review),
NOTED (no decision needed now).

- **I-1 T33235 TestCase_33 factory-defaults the stack.** `test-9001.33235.py:~6014` `dut.reboot(None, timeOut=-1)`; framework `Switch.reboot(confFile=None)` = `del force default.cfg` / `no boot config-file` / `erase startup-config` / reboot. Fix `dut.reboot('', timeOut=900)` or a literal `reload`. Sent to the Test-cases session 2026-09-29 08:26; FIXED there in 4ef0dc4 (+ a blocking lint against `.reboot(None` / `timeOut=-1`). RESOLVED.
- **I-2 Frame picks the test port from a set** (`Stack.members`), so port/partner vary per run and on tb470 every candidate is a LAG member. Sent with I-1; frame fixed in Test-cases 4ef0dc4 (deterministic order, LAG members last, `[LAG member]` tag + WARNING; not skipped, since on tb470 every candidate is one). NOTED — the test link still comes out of its aggregator for a speed run.
- **I-3 `no polarity` is not a command on the IE520 or the x230** (T33234 run 2, 08:51:32/08:51:37): `library_9001.py` `configureDefaultPort()` and `test-9001.33234.py` `TestSet.configure()`/`tear_down()` send it; the negation is `polarity auto`. TestCase_1 grades the refusal as a STEP-1 FAIL. OPEN (Test-cases fix, then re-run). **RESOLVED 09:2x: Test-cases b734b40** (`polarity auto` in configureDefaultPort, TestSet configure/tear_down, TestCase_1 tear_down; `duplex auto`; a `noform:` lint). Re-run = row 3.
- **I-4 The framework power-cycles the WHOLE bench after every failed TestCase** ("Setup is no longer reliable - all devices will be rebooted": stk_a, swi_b, swi_e, swi_f via the PDU, ~3.5 min to all-ports-running; twice in T33234 run 2 at 08:52:21 and 08:57:18). With a platform-wide FAIL (I-5) an 18-case script means up to 18 bench power cycles. Decide before re-running: accept, or fix the failing step first, or find the framework switch. OPEN (Terrence). **RESOLVED 09:1x: Terrence accepts the restart** ("I dont mind that restart"); what is not accepted is a script whose systematic defect makes every case pay it — STANDING-ORDERS §6, bench-runner gate 9 (check defaulting CLI before launch, stop a systematically failing run).
- **I-5 A linked IE520 copper-SFP port reports `current polarity auto`** — no resolved mdi/mdix role (T33234 TestCase_2 FAIL 08:56:54; also read by hand on port1.0.2 AT-SPTXa and port1.0.9 AT-SPTXc). The x230's fixed copper reports mdi/mdix on the same links. The IE520-28GSX has no fixed copper port, so every DUT-side role assertion in T33234 depends on a value the platform does not expose. Platform limitation, defect, or display gap — Terrence's call; the case cannot PASS on this platform as written. OPEN (Terrence). **RULED by Terrence 12:0x (T33234-specific): UNSUPPORTED, not a defect** — per the AW+ `polarity` usage note ("applies to copper 10/100/1000BASE-T switch ports; does not apply to fiber ports"), for MDI/MDI-X an SFP/SFP+ cage is a fibre port whatever it holds. Test-cases to remove the pluggable cases and mark the case UNSUPPORTED when the DUT has no fixed copper switchport. SCOPE: MDI/MDI-X only — a copper pluggable keeps its copper identity for speed/duplex/media in every other test.
- **I-6 Freeing ONE LAG link is not enough on tb470**: the frame binds `cusfp` before `copper` and sorts non-LAG links first, so run 1 put the copper role back on a LAG member; both sa2 members had to come out (VLAN-isolated, STP is off everywhere). Removing the last member auto-deletes `interface sa2` on both platforms — the restore recreates it. NOTED (frame feedback to Test-cases).
- **I-7 `polarity` cannot be set on a LAG member or on `saN`** (Terrence, by hand, 09:3x): `% Cannot configure aggregator member.` on port1.0.2, `% L2/L3 mode cannot be explicitly configured on aggregator interface sa2` on sa2. Confirms the two-link isolation is required, not optional. Recorded in orient-dt §2. NOTED.
