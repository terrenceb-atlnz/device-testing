# Campaign queue — tb470, x230v2-28GS as the DUT, 5 AWPTCM cases (office hours), from 2026-10-13 09:49 NZDT

The ask, Test Engineer 2026-10-13 (after the 2026-10-09 campaign's NOT TESTED review):
*"yes to all, reconfigure the devices as you require, write the configs, and then start the office-hours test mode run."*
Cases: T30403, T45543, T20358, T33234, T47228.

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-13 09:49 NZDT (Test Engineer's answers to the setup questions):
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u0,u1 (option text: "u0 = x230v2-28GS DUT (swi_f); u1 = AR4050S partner (swi_e). The IE520 stack (u2/u4/u5) and IE520-sa (u3) are left alone.")
PDU: 10.36.150.14, u0=1, u1=7 (option text: "Per tb470.static. Only these two outlets are written into the run's setup, so a framework post-failure power cycle touches only the x230 and 4050.")
Constraints: "Office hours, no reloads; T33234 too" (option text: "No CLI reload of any unit. T33234 runs now on a u0/u1-only setup: the tester checks its defaulting commands (polarity, speed) on both units first and stops at the first systematic failure, so at worst one x230+4050 power cycle.")

Test Engineer's rulings carried into this campaign (2026-10-13):
- T45543: steps 1-2 only; step 3 is MANUAL-ONLY (MANUAL-ONLY.md). *"'TPM is instantiated' is the same as TPM is OK."*
- T47228: *"use the API commands to enable/disable interfaces, and also add/delete VLANs"*; the API is RESTCONF
  (memory `awplus-restconf-api-reference`: enable steps, interface `enabled` path; the VLAN create/delete path is open and
  is to be settled from the x230's own ietf-yang-library, then the memory updated).
- 10 Mb/s is not supported on the copper SFPs (re the T47208 caveat).
- The x230v2-28GS is x220 hardware; x220 naming on it is expected (platforms/x230v2-28GS.md §1).

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  The final log is made ONLY by `/create-logs`, on the Test Engineer's request.
- `STANDING-ORDERS.md` applies, tightened by the constraint above: **no CLI reload of any unit**. A framework
  post-failure PDU cycle of u0/u1 is accepted (§6); a systematic failure stops the run.
- **Only u0 and u1 are touched.** The IE520 stack (u2/u4/u5) and IE520-sa (u3) are not opened, configured or probed
  beyond `bench_probe.py`'s own read.
- Case texts: Ask-CK `ck.db` table `zephyr_cases` (read-only: `sqlite3 'file:<path>/ck.db?mode=ro'`), key `AWPTCM-T<n>`.
- MANUAL-ONLY.md (repo root) is read at triage.
- Platform traps: [platforms/x230v2-28GS.md](../../platforms/x230v2-28GS.md). The previous campaign's working logs are in git
  history (`git show a6fcbf5^:…`), its final logs and reviews under `*-2026-10-09T0845/`.

## Bench at queue creation (2026-10-13 09:48, before the Test Engineer's apply)

- Probe `2026-10-12T204*Z` (u0-u5): MISMATCH (1): `[portlink] swi_e-swi_f` EXTRA_IN_LIVE `port1.0.5-port1.0.8` (the new
  crossover, x230 port1.0.8 <-> 4050 port1.0.5). `bench_probe.py apply` is the Test Engineer's, requested 09:49.
- x230 (u0) boots `flash:/tb470-bench.cfg` (saved 09:28): VLAN 103/104/105/108 on port1.0.3/1.0.4/1.0.5/1.0.8, `lldp run`,
  **port1.0.7 `shutdown`** (port1.0.6 <-> port1.0.7 is a direct copper lead: a loop unless STP blocks one end).
  Pluggables: 1.0.1 AT-SPTXa, 1.0.2/1.0.3/1.0.6/1.0.7 AT-SPTX, 1.0.4 AT-SPSX, 1.0.5/1.0.8 AT-SPTXc.
- AR4050S (u1) boots `flash:/tb470-bench.cfg` (saved 09:48): port1.0.5 in VLAN 108; port1.0.2 `shutdown` (VLAN 10,
  cabled to x230 port1.0.1, straight-through); port1.0.1 = tb470 eth2.
- Links for this campaign: x230 port1.0.1 <-> 4050 port1.0.2 (straight Cat5e); x230 port1.0.8 <-> 4050 port1.0.5
  (crossover); x230 port1.0.6 <-> port1.0.7 (copper, loop lead); x230 port1.0.5 <-> tb470 eth3.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | CLI / API cases: T30403, T45543, T20358, T47228 | tb470/x230v2-28GS/cli-2026-10-13T0949/ | QUEUED | manual CLI on u0 (+ u1 if needed); T30403 read-only UNSUPPORTED evidence; T45543 steps 1-2; T20358 RSTP on x230, then `no shutdown` port1.0.7, eth3 broadcast; T47228 RESTCONF from tb470 over eth3 (x230 vlan105 IP) |
| 2 | MDI/MDI-X framework: T33234 (scripts 5000.0003 straight, 5000.0004 crossover) | tb470/x230v2-28GS/mdix-2026-10-13T0949/ | QUEUED (needs apply) | the scripts' source: ck.db `scripts` table (`test_scripts/5000_mdi_mdix/`); dut = x230, remote = 4050; u0/u1-only setup; check defaulting commands (polarity) on both units before launch (STANDING-ORDERS §6) |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

- 09:19 (before this queue) x230 port1.0.6 <-> 1.0.7 loop found live (~230 Mbps each way, VLAN 1, STP off); port1.0.7 shut
  by this session, then saved into tb470-bench.cfg 09:28 on the Test Engineer's "write the running config".
