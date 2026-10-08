# Campaign queue — tb470, x230v2-28GS as the DUT, 37 AWPTCM cases, from 2026-10-09 08:45 NZDT

The ask, Test Engineer 2026-10-09 08:4x (`/test-mode`, five Zephyr screenshots of "Not Executed" cases):
*"with the x230 as the DUT, what tests can we perform with the current topology"*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-09 08:45 NZDT (Test Engineer's answers to the setup questions):
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470 (not asked as a choice: the last test bench run and this host's default-boxes line; the Test Engineer could name another)
Consoles: "u0-u5 all" (option text: "u0 = DUT; every other unit (stack, IE520-sa u3, AR4050S u1) available as a partner.")
PDU: "10.36.150.14 per tb470.static" (u0=1, u1=7, u2=6, u3=8, u4=4, u5=5)
Constraints: "Triage only for now" (option text: "Probe and triage; report what is runnable and what each blocked case needs; run nothing yet.")

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  The final log is made ONLY by `/create-logs`, on the Test Engineer's request.
- `STANDING-ORDERS.md` applies, **tightened by the constraint above: triage only.** No case runs and
  no device state changes until the Test Engineer says proceed.
- Case texts: Ask-CK `ck.db` table `zephyr_cases` (read-only: `sqlite3 'file:<path>/ck.db?mode=ro'`),
  key `AWPTCM-T<n>`, columns `title`, `objective`, `precondition`, `steps` (JSON). All 37 are present
  (14 Approved, 23 Draft; T15255 has 0 steps, objective only).
- DUT = x230v2-28GS on u0 (S/N A10783G262900002, swi_f), `awplus_main-20261008-57`, bootloader 6.2.40,
  boot config `flash:/default.cfg`, follows `boot system` (no forced file). **No `platforms/` file
  exists for the x230 family**; its traps so far are in the tb470/x230v2-28GS handovers and memory
  `x230v2-5700-control-corpus`.
- Bench at queue creation: probe `2026-10-08T193648Z` MATCH. The DUT's only data link is x230 port1.0.2
  (vlan11) ↔ IE520 stack port1.0.2 (stack VLAN 1, sa2 member); the x230 has no direct testbox cable and
  no IP address (bench-state.md).

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | platform/show + factory run-up: T47226, T47227, T47215, T47214, T45543, T31868, T31863, T31852, T31853, T31854, T31855, T31856, T31866, T31858, T31861, T31859 | tb470/x230v2-28GS/platform-2026-10-09T0845/ | TRIAGE | |
| 2 | crypto secure mode / mgmt protocols: T47120, T47119, T47121, T47114, T47115 | tb470/x230v2-28GS/secure-2026-10-09T0845/ | TRIAGE | |
| 3 | ports, pluggables, link: T47228, T46421, T20358, T44179, T33234, T47209, T47208, T47210 | tb470/x230v2-28GS/ports-2026-10-09T0845/ | TRIAGE | |
| 4 | L2/L3 traffic + SNMP: T38294, T38295, T30403, T18570, T18571, T15255 | tb470/x230v2-28GS/l2l3-2026-10-09T0845/ | TRIAGE | |
| 5 | ATMF: T28218, T46810 | tb470/x230v2-28GS/atmf-2026-10-09T0845/ | TRIAGE | |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues
