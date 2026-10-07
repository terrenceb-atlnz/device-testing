# Campaign queue — tb470, AWPTCM Modbus (Proj 2166) on the IE520 stack and the x230v2-28GS, from 2026-10-08 11:31 NZDT

The ask, Test Engineer 2026-10-08 11:2x (`/test-mode`, with a Zephyr screenshot of six Not Executed cases):
*"Can you run these tests on the bench right now??"* — AWPTCM-T22653 (modbus - read port information),
T22654 (modbus - write), T22655 (modbus - dynamic changes), T22651 (S2166.1.10, S2166.1.11, S2166.1.12 -
modbus - read Sensor information), T22650 (… read System information), T22652 (… read alarm information).

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-08 11:31 NZDT (Test Engineer's answers to the setup questions):
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470 (not asked: the last test bench run and this host's default-boxes line; the Test Engineer could name another)
Consoles: "u0 + u2,u4,u5" (option text: "Both, e.g. run the cases on each product." — u0 = x230v2-28GS, u2/u4/u5 = IE520 stack)
PDU: "10.36.150.14 per tb470.static" (outlets by serial in bench-setup/tb470.static: x230v2 swi_f = 1; IE520 swi_a = 6, swi_c = 5, swi_d = 4)
Constraints: "Run now, no power cycles" (option text: "Same scope, and a failing case must not PDU-cycle in office hours: stop and ask instead." — "same scope" = 10-07's "do not interact with any other devices": only the listed consoles and their outlets)

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  The final log is made ONLY by `/create-logs`, on the Test Engineer's request.
- `STANDING-ORDERS.md` applies, **tightened by the constraint above: no power cycles.** Nothing
  that can PDU-cycle a unit runs (no framework TestCase with `powerCycleOnFail`, no `reload` that
  needs a PDU rescue); if a case would need one, `NEEDS TEST ENGINEER:` and move on.
- The cases are **Draft** in Zephyr (folder `/Modbus/Proj 2166 Modbus Support`, label Platform-Test)
  with no framework script; the steps are register reads/writes over Modbus TCP checked against
  the CLI. A Modbus TCP client runs on tb470 (the bench cannot open TCP to office PCs).
- Run each case on each product: group 1 = the IE520 stack, group 2 = the x230v2-28GS.
- Known before triage: the AW+ CLI wiki documents `scada modbus tcp server` for x230 (and AR4050,
  x908Gen2, x930, x950); there are no IE520 pages, and IE520 logs show `modbusd` running.
  bench-state.md was generated 2026-10-06 06:13 and is stale (the IE520 stack is on `main-calanm`,
  bootloader 9.2.0, consoles 9600; u0 at 115200 since the 10-08 autoburnin).

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | AWPTCM-T22650, T22651, T22652, T22653, T22654, T22655 on the IE520 stack (u2,u4,u5) | tb470/IE520/modbus-2026-10-08T1131/ | TRIAGE | |
| 2 | AWPTCM-T22650, T22651, T22652, T22653, T22654, T22655 on the x230v2-28GS (u0) | tb470/x230v2-28GS/modbus-2026-10-08T1131/ | TRIAGE | |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

- 2026-10-08 11:31: tmux session `test-mode` (device-testing-49, pid 1424189) from the 10-07 run is
  still alive, stuck since 01:28 on a pending tool call; its sentinel Monitor/cron may still tick.
  It dispatches nothing (its queue is DONE). Not touched.
