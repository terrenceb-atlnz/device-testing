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

**Updated 2026-10-09 ~10:1x–10:5x (Test Engineer):**
- Blocker changes: *"B: done  C: done  D: done"*; on A: *"x230 port1.0.1 is already connected to the 4050, would that break other tests? or would we route traffic over the stack to the 4050 instead"*, then *"its connected to the 4050 port1.0.2, but the light is off"* (4050 port1.0.2 admin-shut since 09-03).
- Loop from B+C (all VLAN 1, STP off): *"VLAN-isolate the new links"* → done by the tester 10:43, running-config only (Issues list).
- eth3: *"I unplugged it pending your direction as to where it should actually go"* → answer: **"x230 port1.0.5"** (option text: "Move the AT-SPTXc from stack port4.0.14 (free) into x230 port1.0.5 and cable eth3 to it. … IE520-sa loses its host link.") — **pending the Test Engineer's recable**.
- AR4050S USB stick (D): **"Clear before the case"** (option text: "The tester deletes atmf/ and the old .rel files from usb: within the ATMF test setup.")

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
| 3 | ports, pluggables, link: T47228, T46421, T20358, T44179, T33234, T47209, T47208, T47210 | tb470/x230v2-28GS/ports-2026-10-09T0845/ | TRIAGED-3: 5 run / 1 unsupported / 2 TE-or-after-hours | RE-TRIAGE 10:0x (B+C done). RUNNABLE: T46421, T47208 (SPTX on 1.0.2/1.0.3; the SPTXa on 1.0.1 against the 4050's fixed copper once 4050 port1.0.2 is up), T47210, T20358 (B done; in-test: RSTP on the x230 and loop-protection off on stack port1.0.17/1.0.3; broadcast from eth1), T47209 (C done: x230 port1.0.4 ↔ stack port1.0.3, 1000BASE-SX only). All have no steps. BLOCKED topology: T44179, see row 4's path. Jumbo also needs: x230 `platform jumboframe` (reload); 4050 `mru jumbo` per port; stack `platform jumboframe` (stack reload) if eth1 is the far end; root MTU on two tb470 NICs. UNSUPPORTED: T33234 (no fixed copper on the x230). TE: T47228 (no steps, API unspecified). RE-TRIAGE 11:2x: T44179 is no longer topology-blocked (eth3 → x230 port1.0.5 → port1.0.2 → stack → eth1). It still needs x230 `platform jumboframe` (write + reload, x2), stack `platform jumboframe` (stack reload, x2) and root MTU on eth3/eth1 → AFTER HOURS + TE. |
| 4 | L2/L3 traffic + SNMP: T38294, T38295, T30403, T18570, T18571, T15255 | tb470/x230v2-28GS/l2l3-2026-10-09T0845/ | TRIAGED-3: 5 run / 1 unsupported | RE-TRIAGE 11:2x (A' done: eth3 ↔ x230 port1.0.5). RUNNABLE: T15255. T38294: in-test, port1.0.5 → own VLAN + IP in 10.38.215.64/27 (ping-check first), vlan1 IP in 10.38.215.0/27, `ip route 192.0.2.0/24 10.38.215.1`; linerate.py --tx eth3 --rx eth1 --ttl 2, after an L2 baseline. T38295: same, plus an IPv6 pcap (linerate.py is IPv4-only; scapy pcap in /tmp, hop limit 2); next hop = eth1's link-local, so no root change on tb470. T18570/T18571: in-test, LAG x230 port1.0.2+1.0.3 ↔ stack sa2(port1.0.2)+port1.0.17 (out of VLAN 103), 802.1Q tagged; eth3 → port1.0.5 (access) → LAG → stack → eth1 (port3.0.13 in the test VLAN, or tagged + tcpdump); multi-MAC via l2flows.py; x230 has `lacp global-passive-mode enable`. UNSUPPORTED: T30403. |
| 5 | ATMF: T28218, T46810 | tb470/x230v2-28GS/atmf-2026-10-09T0845/ | TRIAGED-2: 2 TE/after-hours | RE-TRIAGE 10:0x. D done: AR4050S usb: 28.9G is available and already holds an `atmf/` dir dated 2026-09-21 (old backups; TE to say keep or clear). T46810: no steps. Topology OK: AR4050S master (FULL has AMF-MASTER), x230 member via stack or the 4050 link. Needs atmf network-name + atmf-link on 4050, stack and x230, then reload of each → AFTER HOURS. T28218: TE decision; the x230 cannot be master (no AMF-MASTER). |

## Triage 2026-10-09 (bench-runner, TRIAGE mode)

Probe `2026-10-08T194710Z` (08:47 NZDT): **MATCH**, all six consoles OK at 115200. Boot configs: x230 `flash:/default.cfg`; AR4050S, stack and IE520-sa `flash:/tb470-bench.cfg`. Advisory: eth1 is learned on swi_c port3.0.13 AND swi_f port1.0.2, so the x230 shares eth1's L2 segment (10.38.215.0/27) through stack VLAN1. The x230's port1.0.2 is in **VLAN 1** (the dispatch said vlan11).
Totals: **12 runnable now / 8 blocked by topology / 17 blocked otherwise** (11 of the 17 are after hours, human or TE; 3 UNSUPPORTED: T33234, T30403, T28218-as-master).

Bench changes that unblock (each is the Test Engineer's; `bench_probe.py apply` afterwards):
- **A**: move the tb470 **eth3** cable from IE520-sa (swi_b, u3) port1.0.2 to **x230 (swi_f, u0) port1.0.1**. The AT-SPTXa copper SFP is already fitted there. The IE520-sa loses its host link. Unblocks T38294, T38295, T44179 (with B's caveats) and T47208's 2nd pluggable.
- **B**: take the AT-SPTX copper SFP out of IE520 stack **port1.0.20** (free) and fit it in **x230 port1.0.3**. Then patch Cat5e/6 from x230 port1.0.3 to stack **port1.0.17** (AT-SPTXa, free). Unblocks T20358, plus T18570 and T18571 (with A).
- **C**: take the AT-SPSX out of stack **port1.0.7** (free) and fit it in **x230 port1.0.4**. Then patch a multimode LC-LC lead from x230 port1.0.4 to stack **port1.0.3** (AT-SPSX, free). Unblocks T47209, 1000BASE-SX only.
- **D**: put a USB stick into the **AR4050S** (swi_e, u1) as AMF backup media. Unblocks T46810.
- T44179 also needs: A; raising the MTU on tb470 eth3 and eth1 (root, the TE's call); `platform jumboframe` on the x230 (write + reload, twice); and jumbo carried on the IE520 stack path port1.0.2→port3.0.13 (not verified).

### Re-triage 2026-10-09 10:00 NZDT (after the Test Engineer did B, C and D)

Probe `2026-10-08T210024Z`: **exit 1 MISMATCH**.
- `[portlink] swi_a-swi_f` is now `{port1.0.17-port1.0.3, port1.0.2-port1.0.2, port1.0.3-port1.0.4}`; the template says `port1.0.2-port1.0.2`. Needs `apply` (the TE's call).
- NEEDS-CHECK: `tb-swi_b eth3` has **no carrier**, and IE520-sa port1.0.2 shows notconnect.

Measured:
- B is up: x230 port1.0.3 (AT-SPTX) ↔ stack port1.0.17, LLDP both ends.
- C is up: x230 port1.0.4 (AT-SPSX, 1000BASE-SX) ↔ stack port1.0.3, LLDP both ends.
- D is in: the AR4050S's usb: is available (28.9G).
- x230 port1.0.1 (AT-SPTXa): link DOWN, admin UP, no LLDP. The TE says it is cabled to **AR4050S port1.0.2**. That port is **administratively DOWN**: its running-config has `shutdown`, VLAN 10 "transit". It was shut on 2026-09-03 to keep the then-triangle a tree (IE520/SESSION-HANDOVER-2026-09-03.md). That shutdown is the cause of the dark light; copper-SFP autoneg can only be judged once the port is up.
- **LIVE LOOP:** x230 port1.0.2/1.0.3/1.0.4 and stack sa2/port1.0.17/port1.0.3 are all untagged VLAN1, with spanning tree off on both units. Only the stack's loop-protection (vlan-disable, 7 s) holds it: port1.0.17 and port1.0.3 were Blocking at 10:01. A run must isolate the ports it does not use (in-test). The standing fix is the TE's.
- Jumbo:
  - x230: `platform jumboframe` (reload).
  - AR4050S: per-port `mru jumbo` (config-if); there is no `platform jumboframe`.
  - IE520 stack: `platform jumboframe` only (no per-port mru/mtu), which means a stack reload.

Totals now: **14 runnable / 5 blocked by topology / 18 blocked otherwise**.

### Re-triage 2026-10-09 11:2x NZDT (A' done: tb470 eth3 → x230 port1.0.5, AT-SPTXc moved from stack port4.0.14)

Probe `2026-10-08T222130Z`: **exit 1 MISMATCH (3)**:
- `swi_a-swi_f` is now 3 links.
- `tb-swi_b eth3` is MISSING_IN_LIVE.
- `tb-swi_f eth3 = eth3-port1.0.5` is EXTRA_IN_LIVE.

All three are the TE's changes, waiting for `apply`.

- eth3 is UP. Its MAC 00f0.4d00.7718 is learned on x230 port1.0.5 (connected a-full a-1000, 1000BASE-T, VLAN 1).
- The B/C isolation still holds: VLAN 103/104 on both ends, and every stack loop-protection row is Normal.
- **NEEDS-CHECK:** x230 port1.0.5 is in VLAN 1, so eth3's segment (10.38.215.64/27) and eth1's (10.38.215.0/27) now share one L2 domain through the x230 and stack VLAN1. eth3's MAC is also learned on stack sa2. This is not a loop, because tb470 routes and does not bridge. It does mean one broadcast domain holds two tb470 DHCP scopes and possible ARP flux.
  - Each traffic case moves port1.0.5 into its own VLAN within the test.
  - The standing fix (port1.0.5 in its own VLAN) is the TE's call.
- The IE520-sa no longer has a host link. Its vlan1 .69 is not reachable from tb470; it still reaches the stack via port4.0.26 in VLAN 4000. **No case in this queue uses it.**

Totals now: **18 runnable / 0 blocked by topology / 19 blocked otherwise** (T44179 moved to after hours + TE).

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

- **2026-10-09 10:43 NZDT, bench change authorised by the Test Engineer ("VLAN-isolate the new links"), running-config only, NO `write` on either unit.**
  - Why: links B and C had formed a VLAN1 loop with spanning tree off on both units. The stack's loop-protection held port1.0.17 and port1.0.3 in Blocking (vlan-disable, 7 s).
  - What changed (all values were free on both units beforehand):
    - Stack, via the master on u5 (member 3): `vlan database` / `vlan 103,104`; `interface port1.0.17` / `switchport access vlan 103`; `interface port1.0.3` / `switchport access vlan 104`.
    - x230, via u0: `vlan database` / `vlan 103,104`; `interface port1.0.3` / `switchport access vlan 103`; `interface port1.0.4` / `switchport access vlan 104`.
    - No `% ` line on either unit.
  - Verified 10:44–10:45 by re-reading:
    - `show vlan brief` on both units: 103 = stack port1.0.17 / x230 port1.0.3; 104 = stack port1.0.3 / x230 port1.0.4.
    - All four ports still `connected` a-full a-1000.
    - Stack loop-protection: port1.0.17 and port1.0.3 `Normal`, with no new log events across about 60 s (the only new log lines are the two `port mode access updated VLAN` lines).
    - LLDP still sees all three x230↔stack links.
  - Re-probe `2026-10-08T214518Z`: exit 1 MISMATCH, the same as before the change. `swi_a-swi_f` is now 3 links (needs `apply`, the TE's call), and the NEEDS-CHECK on eth3 is no carrier (unplugged by the TE, pending direction).
  - Lost at the next reload, because nothing was written. Revert sooner by hand:
    - Stack: `interface port1.0.17,port1.0.3` / `switchport access vlan 1`; then `vlan database` / `no vlan 103,104`.
    - x230: `interface port1.0.3-1.0.4` / `switchport access vlan 1`; then `vlan database` / `no vlan 103,104`.
    - Reverting re-creates the loop unless links B and C are unplugged first.
