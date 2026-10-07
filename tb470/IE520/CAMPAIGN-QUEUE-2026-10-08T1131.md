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

**Updated 2026-10-08 12:0x–12:36 (Test Engineer):**
- *"the x230 is not on 9600 baud, its now the 115200 or whatever one, since we are not doing automated tests"*
- *"All devices have been mostly depopulated for ports, i need you to tell me what ports to connect"*;
  *"The DUT will be the IE520 stack … everything is available, i just need a topology choice from you."*
  → **DUT = the IE520 stack (u2 member 1, u4 member 4, u5 member 3, by serial in the 10-06 records). Only group 1 runs; group 2 (x230 as DUT) is dropped.**
- Topology chosen (sentinel, 2026-09-29 run's shape): **cable 1** tb470 eth1 ↔ stack port3.0.13 (RJ45, member 3 / u5);
  **cable 2** stack port1.0.2 (member 1 / u2, copper SFP) ↔ x230 port1.0.2 (passive link partner, nothing else cabled on the x230).
  Test Engineer 12:3x: *"the x230 link is to the u2 port1.0.1, as requested."* — the sentinel asked to move it to port1.0.2
  (stack port1.0.1 = known dead cage, platforms/IE520.md); **not yet confirmed moved — the probe/LLDP decides.**
- x230 (u0, 115200) prepared by the sentinel at the Test Engineer's request, running-config only (no write):
  `no lacp global-passive-mode enable`, `lldp run`. Otherwise it keeps the autoburnin running-config (per-port VLANs 10–37, RSTP off).
  x230 port1.0.2 read `running` 12:33, `notconnect` 12:34 (during the stack baud work).
- 12:36: *"bauds are fixed, stack is rebooting. am off of minicoms. all yours"*

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
| 2 | AWPTCM-T22650, T22651, T22652, T22653, T22654, T22655 on the x230v2-28GS (u0) | tb470/x230v2-28GS/modbus-2026-10-08T1131/ | DROPPED 12:2x | Test Engineer: "The DUT will be the IE520 stack" |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

- 2026-10-08 11:31: tmux session `test-mode` (device-testing-49, pid 1424189) from the 10-07 run is
  still alive, stuck since 01:28 on a pending tool call; its sentinel Monitor/cron may still tick.
  It dispatches nothing (its queue is DONE). Not touched.
