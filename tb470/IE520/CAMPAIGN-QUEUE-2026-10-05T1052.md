# Campaign queue — tb470 IE520, T27887 supplementary re-investigation, from 2026-10-05 10:52 NZDT

Terrence, 2026-10-05, after the 10:31 help probes re-confirmed that the global VLAN-based QinQ
command `vlan-stacking vlan <inner> outer-vlan <outer>` is absent on the IE520 (and, as a new
finding, on the x230 control too):
*"Yes, i think the switchport vlan ones should be tried for sure. is that actually Q-in-Q if it
works"* → *"use 2. and then start test mode"* (2 = observe through the x230, not the SA).

The ask: exercise the two IE520 commands that have never been configured or put under traffic:
- **(A)** `switchport vlan translation vlan <wire> vlan <vid> outer-vlan <outer>`: the combined
  translation + double-tag entry. IE520 help offers both argument orders (`… vlan <vid> outer-vlan
  <outer>` and `… outer-vlan <outer> vlan <vid>`).
- **(B)** `switchport vlan translation default outer-vlan <vid>`: outer VLAN added to tagged frames
  that match no translation entry.

Each forward (customer → provider) and reverse. The question each stage answers: does the customer
tag survive inside the outer tag (true Q-in-Q), or is it dropped (a repeat of O-2 from the 09-30 run)?

**Supplementary evidence only.** T27887's case is VLAN-based QinQ (global mapping, "cannot be
applied per interface", T27895/T27989); these are per-port entries. Terrence's framing: the verdict
stays UNSUPPORTED unless he decides otherwise. Prior run, topology and O-2:
[../../IE520/vlan-2026-09-29/27887-unsupported.log](../../IE520/vlan-2026-09-29/27887-unsupported.log).

Shape: ONE session (orient-dt §10 A, `/test-mode`): this session is the sentinel, `bench-runner`
subagents are the tester.

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-05 10:52 NZDT. These are the Test Engineer's answers, word for word:
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470 (this host's default and the last test bench run, IE520/SESSION-HANDOVER-2026-10-05.md)
Consoles: u0,u2,u4,u5
PDU: No PDU / do not power-cycle
Constraints: Don't power-cycle the SA (u3/outlet 8 is not to be power-cycled; observe via the x230 path (option 2); u1 never touched; sentinel stands down 17:30 today)

Notes from the session (sentinel):
- u1 (AR4050S) is held by the Test Engineer's `minicom --wrap -D /dev/u1 -c off` (PID 527573): never open it.
- u3 (IE520-sa, swi_b) is unresponsive since before 2026-10-05 08:21 (handover 2026-10-05) and is NOT
  in this session's consoles. Its links to the stack (sa3: stack port1.0.13, port4.0.9; SX port4.0.26)
  are down. Do not use the SA path.
- Precheck 2026-10-05 10:30: u0, u2, u3, u4, u5 free; FOUND only the u1 minicom above.
- No PDU this session: nothing is power-cycled, by the tester or the framework.

## Rules carried with the queue

- Verdicts, the working log, the `RESULT` line, the results list and the final log:
  [logged-output.md](../../logged-output.md). The final log is made ONLY by `/create-logs`, on the
  Test Engineer's request.
- `STANDING-ORDERS.md` applies, tightened by the constraints above (no power cycling at all).
- Nothing is `write`n to startup-config. Teardown is verified by diffing `show running-config`
  against the pre-case copy on every device touched.
- Stop on any `% ` CLI line. Gate each dependent step on proven state.
- Drive consoles through `tools/` (console.py-based) with transcripts at tb470
  `/tmp/<campaign>/console-<uN>.log`, so the sentinel's normal mode sees them.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | T27887 supplementary: (A) combined translation + outer-vlan entry, (B) `default outer-vlan`, forward + reverse each | vlan-2026-10-05T1052 | QUEUED | observe the provider side via the x230 (stack port1.0.2 → x230 → tb470 eth3); customer side = tb470 eth1 on stack port3.0.10 (moved from 3.0.13 on 2026-10-01). Group setup/restore recipe: written by the tester below before the first stage |

## Group setup and restore — vlan-2026-10-05T1052

(The tester writes this before the first stage.)

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

- I-1 (carried): SA u3 unresponsive, OPEN since the 2026-10-05 handover. Not this campaign's to fix.
