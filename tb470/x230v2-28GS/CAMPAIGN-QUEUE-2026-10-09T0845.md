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
| 1 | platform/show + factory run-up: T47226, T47227, T47215, T47214, T45543, T31868, T31863, T31852, T31853, T31854, T31855, T31856, T31866, T31858, T31861, T31859 | tb470/x230v2-28GS/platform-2026-10-09T0845/ | TRIAGED: 8 run / 4 after-hours / 4 human-or-TE | RUNNABLE now (read-only): T47226, T47227, T47215, T31852, T31853, T31855 (no eth0 → step 3 N/A, confirm at run), T31856, T31861. AFTER HOURS (reload, no bench change): T31858 (1 reload; DUT clock reads NZ local time labelled UTC, +13 h), T31863 BIST (reload before+after), T31866 PRBS (reload after; parser takes `platform prbs {internal-fabric|stack-fabric|all-fabric}`, not the case's `all`), T31868 Autoboot (≥3 reloads; USB 28.8G present, no SD slot; 2nd .rel = x230-2.rel on the stick). HUMAN: T47214 (magnet on the fan), T31854 (LED watch; precondition no SFP/no cable), T31859 (CLI ready, fault-LED look needs a person). TE: T45543 steps 1–2 runnable (`show system tpm` answers `TPM is instantiated`, expected `TPM is OK`); step 3 needs an idevid account + x230 internet via eth1. |
| 2 | crypto secure mode / mgmt protocols: T47120, T47119, T47121, T47114, T47115 | tb470/x230v2-28GS/secure-2026-10-09T0845/ | TRIAGED: 5 after-hours (secure mode reloads) | AFTER HOURS, no bench change: all five need x230 secure mode = write + reload in, `no crypto secure-mode` + reload out (`crypto secure-mode` present in config). All Draft with empty steps. T47120 CLI half runnable; GUI half needs a person at a browser (x230 vlan1 IP via eth1). T47119/T47121 need a reference device: TE to name it (AR4050S supports secure mode = 2 more 4050 reloads). T47115, T47114 runnable. Run T15255 (SNMPv2) BEFORE secure mode. |
| 3 | ports, pluggables, link: T47228, T46421, T20358, T44179, T33234, T47209, T47208, T47210 | tb470/x230v2-28GS/ports-2026-10-09T0845/ | TRIAGED: 3 run / 3 topology / 1 unsupported / 1 TE | RUNNABLE now on port1.0.2↔stack port1.0.2 (flaps the DUT's only link): T46421 (no steps), T47208 (AT-SPTX only; AT-SPTXa in port1.0.1 needs change A), T47210 (no steps; LLDP on both ends). BLOCKED topology: T20358 needs change B (2nd x230↔stack link; stack STP already disabled). T47209 needs change C (fibre: AT-SPSX into x230 port1.0.4, MM LC-LC to stack port1.0.3; 1000BASE-SX only). T44179 jumbo needs change A + root MTU on eth3/eth1 + x230 `platform jumboframe` (write+reload x2, after hours) + jumbo on the stack path (unverified). UNSUPPORTED: T33234 (x230-28GS has no fixed copper port, every port a cage; ruling 2026-09-29 in test-9001.33234.py). TE: T47228 has no steps and does not say which API (REST/NETCONF). |
| 4 | L2/L3 traffic + SNMP: T38294, T38295, T30403, T18570, T18571, T15255 | tb470/x230v2-28GS/l2l3-2026-10-09T0845/ | TRIAGED: 1 run / 4 topology / 1 unsupported | RUNNABLE now: T15255 (in-test: x230 vlan1 IP in 10.38.215.0/27 outside dhcp .2–.10, snmp community; snmpwalk from tb470 eth1 via stack VLAN1). BLOCKED topology: T38294, T38295 need change A (eth3 → x230 port1.0.1; route eth3↔port1.0.1 / port1.0.2↔stack↔eth1; T38295 needs an IPv6 pcap, linerate.py is IPv4-only). T18570, T18571 need A + B (LAG port1.0.2+1.0.3 ↔ stack port1.0.2+1.0.17, traffic eth3→x230→LAG→eth1; x230 has `lacp global-passive-mode enable`). UNSUPPORTED: T30403 (`ip mroute` absent from the x230 parser; its licence has no L3-MC-ROUTE). |
| 5 | ATMF: T28218, T46810 | tb470/x230v2-28GS/atmf-2026-10-09T0845/ | TRIAGED: 1 topology / 1 TE | T46810 BLOCKED topology: change D (USB stick into AR4050S; usb:/card: both unavailable) + AR4050S as master (FULL has AMF-MASTER); x230 cannot be master. Needs atmf network-name + atmf-link on 4050, stack, x230 and a reload per node → AFTER HOURS. No steps. T28218 TE decision: master-side steps; x230 lacks AMF-MASTER (UNSUPPORTED as master). The only way to run it is with the AR4050S as master (then the 4050 is the DUT) + change D. |

## Triage 2026-10-09 (bench-runner, TRIAGE mode)

Probe `2026-10-08T194710Z` (08:47 NZDT): **MATCH**, all six consoles OK at 115200. Boot configs: x230 `flash:/default.cfg`; AR4050S, stack and IE520-sa `flash:/tb470-bench.cfg`. Advisory: eth1 is learned on swi_c port3.0.13 AND swi_f port1.0.2, so the x230 shares eth1's L2 segment (10.38.215.0/27) through stack VLAN1. The x230's port1.0.2 is in **VLAN 1** (the dispatch said vlan11).
Totals: **12 runnable now / 8 blocked by topology / 17 blocked otherwise** (11 of the 17 are after hours, human or TE; 3 UNSUPPORTED: T33234, T30403, T28218-as-master).

Bench changes that unblock (each is the Test Engineer's; `bench_probe.py apply` afterwards):
- **A**: move the tb470 **eth3** cable from IE520-sa (swi_b, u3) port1.0.2 to **x230 (swi_f, u0) port1.0.1**. The AT-SPTXa copper SFP is already fitted there. The IE520-sa loses its host link. Unblocks T38294, T38295, T44179 (with B's caveats) and T47208's 2nd pluggable.
- **B**: take the AT-SPTX copper SFP out of IE520 stack **port1.0.20** (free) and fit it in **x230 port1.0.3**. Then patch Cat5e/6 from x230 port1.0.3 to stack **port1.0.17** (AT-SPTXa, free). Unblocks T20358, plus T18570 and T18571 (with A).
- **C**: take the AT-SPSX out of stack **port1.0.7** (free) and fit it in **x230 port1.0.4**. Then patch a multimode LC-LC lead from x230 port1.0.4 to stack **port1.0.3** (AT-SPSX, free). Unblocks T47209, 1000BASE-SX only.
- **D**: put a USB stick into the **AR4050S** (swi_e, u1) as AMF backup media. Unblocks T46810.
- T44179 also needs: A; raising the MTU on tb470 eth3 and eth1 (root, the TE's call); `platform jumboframe` on the x230 (write + reload, twice); and jumbo carried on the IE520 stack path port1.0.2→port3.0.13 (not verified).

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues
