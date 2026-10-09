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

**Updated 2026-10-09 ~12:0x (Test Engineer) — the run is scheduled:**
- *"cron job the campaign to start at 6pm tonight"* → constraint "Triage only for now" is **lifted for an 18:00 NZDT start**.
- Scope: **"18 + after-hours reloads"** (option text: "Also the reload cases that need no person or decision: T31858
  SettingClock, T31863 BIST, T31866 PRBS, T47114/T47115 secure mode (x230 only). Reloads drop the running-only VLAN
  103/104/105 isolation, so each case restores it after the reload. T31868 Autoboot, T46810 ATMF, the reference-device
  and person cases stay blocked.")
- Run host: **"This VS Code session"** (option text: "I arm a one-shot cron here for 18:00. It dies if VS Code / this
  window closes or restarts before or during the run.") — sentinel = session 50f164f5 (`/test-mode`, shape A).

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
| 1 | platform/show + factory run-up: T47226, T47227, T47215, T47214, T45543, T31868, T31863, T31852, T31853, T31854, T31855, T31856, T31866, T31858, T31861, T31859 | tb470/x230v2-28GS/platform-2026-10-09T0845/ | DONE (run 1, 18:00-18:38): 9 PASS, 2 UNSUPPORTED; 5 NOT TESTED | RUNNABLE now (read-only): T47226, T47227, T47215, T31852, T31853, T31855 (no eth0 → step 3 N/A, confirm at run), T31856, T31861. AFTER HOURS (reload, no bench change): T31858 (1 reload; DUT clock reads NZ local time labelled UTC, +13 h), T31863 BIST (reload before+after), T31866 PRBS (reload after; parser takes `platform prbs {internal-fabric|stack-fabric|all-fabric}`, not the case's `all`), T31868 Autoboot (≥3 reloads; USB 28.8G present, no SD slot; 2nd .rel = x230-2.rel on the stick). HUMAN: T47214 (magnet on the fan), T31854 (LED watch; precondition no SFP/no cable), T31859 (CLI ready, fault-LED look needs a person). TE: T45543 steps 1–2 runnable (`show system tpm` answers `TPM is instantiated`, expected `TPM is OK`); step 3 needs an idevid account + x230 internet via eth1. |
| 2 | crypto secure mode / mgmt protocols: T47120, T47119, T47121, T47114, T47115 | tb470/x230v2-28GS/secure-2026-10-09T0845/ | TRIAGED: 5 after-hours (secure mode reloads) | AFTER HOURS, no bench change: all five need x230 secure mode = write + reload in, `no crypto secure-mode` + reload out (`crypto secure-mode` present in config). All Draft with empty steps. T47120 CLI half runnable; GUI half needs a person at a browser (x230 vlan1 IP via eth1). T47119/T47121 need a reference device: TE to name it (AR4050S supports secure mode = 2 more 4050 reloads). T47115, T47114 runnable. Run T15255 (SNMPv2) BEFORE secure mode. |
| 3 | ports, pluggables, link: T47228, T46421, T20358, T44179, T33234, T47209, T47208, T47210 | tb470/x230v2-28GS/ports-2026-10-09T0845/ | RUNNING (run 2, from 18:45): T46421, T47208, T47210, T20358, T47209; NOT TESTED T47228, T44179, T33234 | RE-TRIAGE 10:0x (B+C done). RUNNABLE: T46421, T47208 (SPTX on 1.0.2/1.0.3; the SPTXa on 1.0.1 against the 4050's fixed copper once 4050 port1.0.2 is up), T47210, T20358 (B done; in-test: RSTP on the x230 and loop-protection off on stack port1.0.17/1.0.3; broadcast from eth1), T47209 (C done: x230 port1.0.4 ↔ stack port1.0.3, 1000BASE-SX only). All have no steps. BLOCKED topology: T44179, see row 4's path. Jumbo also needs: x230 `platform jumboframe` (reload); 4050 `mru jumbo` per port; stack `platform jumboframe` (stack reload) if eth1 is the far end; root MTU on two tb470 NICs. UNSUPPORTED: T33234 (no fixed copper on the x230). TE: T47228 (no steps, API unspecified). RE-TRIAGE 11:2x: T44179 is no longer topology-blocked (eth3 → x230 port1.0.5 → port1.0.2 → stack → eth1). It still needs x230 `platform jumboframe` (write + reload, x2), stack `platform jumboframe` (stack reload, x2) and root MTU on eth3/eth1 → AFTER HOURS + TE. |
| 4 | L2/L3 traffic + SNMP: T38294, T38295, T30403, T18570, T18571, T15255 | tb470/x230v2-28GS/l2l3-2026-10-09T0845/ | TRIAGED-3: 5 run / 1 unsupported | RE-TRIAGE 11:2x (A' done: eth3 ↔ x230 port1.0.5). RUNNABLE: T15255. T38294: in-test, port1.0.5 → own VLAN + IP in 10.38.215.64/27 (ping-check first), vlan1 IP in 10.38.215.0/27, `ip route 192.0.2.0/24 10.38.215.1`; linerate.py --tx eth3 --rx eth1 --ttl 2, after an L2 baseline. T38295: same, plus an IPv6 pcap (linerate.py is IPv4-only; scapy pcap in /tmp, hop limit 2); next hop = eth1's link-local, so no root change on tb470. T18570/T18571: in-test, LAG x230 port1.0.2+1.0.3 ↔ stack sa2(port1.0.2)+port1.0.17 (out of VLAN 103), 802.1Q tagged; eth3 → port1.0.5 (access) → LAG → stack → eth1 (port3.0.13 in the test VLAN, or tagged + tcpdump); multi-MAC via l2flows.py; x230 has `lacp global-passive-mode enable`. UNSUPPORTED: T30403. |
| 5 | ATMF: T28218, T46810 | tb470/x230v2-28GS/atmf-2026-10-09T0845/ | TRIAGED-2: 2 TE/after-hours | RE-TRIAGE 10:0x. D done: AR4050S usb: 28.9G is available and already holds an `atmf/` dir dated 2026-09-21 (old backups; TE to say keep or clear). T46810: no steps. Topology OK: AR4050S master (FULL has AMF-MASTER), x230 member via stack or the 4050 link. Needs atmf network-name + atmf-link on 4050, stack and x230, then reload of each → AFTER HOURS. T28218: TE decision; the x230 cannot be master (no AMF-MASTER). |

## Run plan — 18:00 NZDT 2026-10-09 (23 cases; Test Engineer's scope above)

The one-shot cron fires at 18:00. The sentinel re-runs the occupancy precheck (FOUND: stop, report and run nothing), arms
the Monitor watch and the 15-min cron backstop, then dispatches one `bench-runner` RUN per group, in THIS order:

| run | queue row | cases (in order) |
| --- | --- | --- |
| 1 | row 1 platform | T47226, T47227, T47215, T31852, T31853, T31855, T31856, T31861, then the reload cases T31858, T31863, T31866 (PRBS: the parser takes `platform prbs {internal-fabric\|stack-fabric\|all-fabric}`, not the case's `all`) |
| 2 | row 3 ports | T46421, T47208, T47210, T20358, T47209 |
| 3 | row 4 L2/L3 | T15255 (before any secure mode), T38294, T38295, T18570, T18571 |
| 4 | row 2 secure | T47114, T47115 (x230 only; secure mode in, then out; LAST, after SNMP) |

Every other case stays BLOCKED with its triage reason (NOT TESTED rows in Results): T47214, T45543, T31868, T31854, T31859,
T47120, T47119, T47121, T47228, T44179, T33234, T30403, T28218, T46810.

**After ANY x230 reload, before the next step:** re-apply the running-only isolation on the x230 (it boots `default.cfg`):
`vlan database` / `vlan 103,104,105`; `interface port1.0.3` / `switchport access vlan 103`; `interface port1.0.4` /
`switchport access vlan 104`; `interface port1.0.5` / `switchport access vlan 105`. Verify with `show vlan brief`. The
stack keeps its side (103/104), so no loop forms in between, but eth3 shares eth1's domain until port1.0.5 is back in 105.

**Shared with test-cases-2b (Test Engineer's instruction, 13:15):** *"work with the other peer session to execute tests
before the 1800 window, and if it needs more testing after your x230 tests are complete. /wrap-dt after everything is done
between sessions, and have it let you know when it is completely done so you both can stand down."*
- Before 18:00 tb470 is test-cases-2b's. It releases it by 17:45 ("tb470 released"): consoles closed at exec, no tool
  processes, the x230 VLAN 103/104/105 isolation in place, and any DUT changes restored or listed.
- At the end of the run: message test-cases-2b "tb470 free". It tests again if it needs to, then sends "test-cases-2b
  completely done".
- Only THEN run /wrap-dt for tb470 (this overrides the cron prompt's "do not run /wrap-dt"; /create-logs stays the TE's).
  Tell test-cases-2b the wrap is done, and both stand down.
- 13:59: test-cases-2b released tb470 (2 Ask-CK E2E runs: probe MATCH, no device state changed, consoles at exec, no
  holders). It needs NO bench time after the run; it will still send "completely done" before the wrap.
- 14:12: test-cases-2b sent "completely done". After the run, go straight to /wrap-dt (no "tb470 free" round needed),
  then tell it the wrap is done. Wrap note: its deliberate 14:10 test against a nonexistent box left `tb999/NO-FAMILY/`
  (commit 0b5cc3e); list it in the handover for the TE to keep or delete, do not delete it.

### Run 1 (row 1 platform) — bench setup and restore recipe (bench-runner, written 18:0x before the first case)

Gate 18:00–18:02 NZDT: precheck u0-u5 CLEAR; scratch `/tmp/x230plat-1800/` on tb470; `/nfsHome` mounted, deployed
`tb470.setup` 1256 B; peek: u0 `awplus login:`, u1 `4050-5g#`, u2/u4/u5 `IE520-stk#`, u3 `IE520-sa#` (none in config or a
root shell); probe `2026-10-09T050106Z` (115200) **MATCH**. Boot configs: x230 `flash:/default.cfg`; 4050, stack, IE520-sa
`flash:/tb470-bench.cfg`. x230 running-config holds VLAN 103-105 on port1.0.3/1.0.4/1.0.5. No framework script in this
group (manual CLI cases driven with `tools/ckcon.py` / `ckreload.py` on u0 only), so gates 6, 8 and 10 are N/A.

- **Bench setup for the group:** none beyond the standing state above. Only the x230 (u0, swi_f) is touched; partners are
  not configured.
- **Restore recipe (a fresh tester can run it if this run dies):**
  1. If the x230 was reloaded (T31858, T31863, T31866), re-apply the running-only isolation on u0:
     `configure terminal` / `vlan database` / `vlan 103,104,105` / `interface port1.0.3` / `switchport access vlan 103` /
     `interface port1.0.4` / `switchport access vlan 104` / `interface port1.0.5` / `switchport access vlan 105` / `end`;
     verify `show vlan brief`. Do NOT `write`.
     Also `lldp run` (config mode): it was in the x230's running-config only (bench_probe.py turns it on) and the reload
     drops it (found in T31858, 18:09). Verify with a running-config diff against the pre-case capture.
- **After run 1 (18:36-18:38 NZDT):** precheck u0-u5 CLEAR; probe `2026-10-09T053648Z` **MATCH**; boot configs unchanged
  (x230 `flash:/default.cfg`, the others `flash:/tb470-bench.cfg`); `show running-config` of u0-u3 identical to the pre-run
  capture `2026-10-09T050106Z` (x230 VLAN 103-105 isolation and `lldp run` in place, clock back on NZ local time); no tool
  processes on tb470; every console closed at exec after `terminal no monitor` (transcripts `/tmp/x230plat-1800/console-uN.log`).
  The x230 was reloaded 5 times (T31858 x1, T31863 x2, T31866 x2), each by CLI `reload`; no PDU cycle, nothing written.
  2. T31858 changes the x230 clock: set it back to the baseline (the box's NZ local time, written as the x230's UTC, since
     the x230 has `no clock timezone`): `clock set <tb470 local hh:mm:ss> <dd> <Mon> <yyyy>`; verify `show clock`.
  3. T31863/T31866: `line con 0` / `exec-timeout 0` is set by the case; remove it (`line con 0` / `no exec-timeout`) unless
     the pre-case running-config already had it. A reload (the case's own last step) clears any BIST/PRBS state.
  4. `show boot` must still name `flash:/default.cfg`; nothing is written. Then `end`, `terminal no monitor`, re-probe.

### Run 2 (row 3 ports) — bench setup and restore recipe (bench-runner, written 18:45 before the first case)

Gate 18:40–18:44 NZDT: precheck u0-u5 CLEAR; scratch `/tmp/x230port-1840/` on tb470; `/nfsHome` mounted, deployed
`tb470.setup` 1256 B; peek: u0 `awplus#`, u1 `4050-5g#`, u2/u4/u5 `IE520-stk#`, u3 `IE520-sa#` (none in config or a root
shell); probe `2026-10-09T054049Z` (115200) **MATCH**. Boot configs: x230 `flash:/default.cfg`; 4050, stack
`flash:/tb470-bench.cfg`. Stack master = member 3 (u5). Pre-run captures (show running-config etc. of u0, u5, u1):
`ports-2026-10-09T0845/46421/work/prerun-u{0,5,1}-1842.out`. No framework script in this group (manual CLI cases, no
steps in the DB except T20358), so gates 6, 8 and 10 are N/A.

- **Bench setup for the group:** none beyond the standing state: x230 port1.0.3/1.0.4/1.0.5 in VLAN 103/104/105, stack
  port1.0.17/1.0.3 in VLAN 103/104, `lldp run` on the x230, STP disabled on x230 / stack / 4050 (`spanning-tree mode rstp`
  + `no spanning-tree rstp enable`), 4050 port1.0.2 `shutdown` (VLAN 10). Every change below is made inside one case and
  undone at that case's end. Links used: x230 port1.0.1 (AT-SPTXa) ↔ 4050 port1.0.2; port1.0.2 (AT-SPTX) ↔ stack
  port1.0.2 (sa2); port1.0.3 (AT-SPTX) ↔ stack port1.0.17 (AT-SPTXa); port1.0.4 (AT-SPSX) ↔ stack port1.0.3 (AT-SPSX);
  port1.0.5 (AT-SPTXc) ↔ tb470 eth3.
- **Loop rule:** x230 port1.0.3 and port1.0.4 are never in one x230 VLAN while stack port1.0.17 and port1.0.3 share a stack
  VLAN, UNLESS the x230 runs RSTP and port1.0.4 already reads Backup/Discarding (T20358 only). x230 port1.0.1 goes into
  its own VLAN 101 whenever 4050 port1.0.2 is up.
- **Restore recipe (a fresh tester can run it if this run dies; nothing is ever written):**
  1. If the x230 reloaded: re-apply the isolation exactly as in Run 1's recipe step 1 (VLAN 103/104/105 + `lldp run`).
  2. x230 (u0), `configure terminal`:
     `interface port1.0.1-1.0.5` / `speed auto` / `duplex auto` / `no shutdown`;
     `interface port1.0.1` / `switchport access vlan 1`; `interface port1.0.2` / `switchport access vlan 1`;
     `interface port1.0.3` / `switchport access vlan 103`; `interface port1.0.4` / `switchport access vlan 104`;
     `interface port1.0.5` / `switchport access vlan 105`; any `lldp tlv-select` a case added → `no lldp tlv-select …`;
     `spanning-tree mode rstp` THEN `no spanning-tree rstp enable` (mode first; memory `stp-mode-change-reenables-…`);
     `vlan database` / `no vlan 101` (if created); `end`. Verify `show vlan brief`, `show spanning-tree brief`.
  3. Stack (u5, master): `interface port1.0.2,port1.0.3,port1.0.17` / `speed auto` / `duplex auto` / `no shutdown`;
     `interface port1.0.17` / `switchport access vlan 103`; `interface port1.0.3` / `switchport access vlan 104`;
     loop-protection is not changed by any case. `end`.
  4. AR4050S (u1): `interface port1.0.2` / `speed auto` / `duplex auto` / `shutdown`. `end`.
  5. Diff each device's `show running-config` against the pre-run capture above (must be empty); `show boot` unchanged;
     `end`, `terminal no monitor` on every console; re-probe (must MATCH).

Unattended end-of-run order (memory `unattended-session-stalls-on-permission-prompt`): commit the Results, post the
results list, THEN anything that can prompt. Nothing that touches root-owned files or anything outside the repo.

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
| T47226 | show version | platform | PASS | show version answers in full (AW+ 0.0.0, build 2026-10-08 00:10:09); build name x220-awplus_main-20261008-57 is the x230v2 build target (same in every earlier x230v2 log) | platform-2026-10-09T0845/47226/work/run1.log | tester |
| T47227 | show license | platform | PASS | show license lists Base License (Full) and ACCESS (Full) with features | platform-2026-10-09T0845/47227/work/run1.log | tester |
| T47215 | show system environment | platform | PASS | Overall Normal, fan 3691 rpm, all 8 voltage/temp sensors Ok | platform-2026-10-09T0845/47215/work/run1.log | tester |
| T31852 | licences (sh lic) | platform | PASS | Base License and ACCESS both Full, no errors | platform-2026-10-09T0845/31852/work/run1.log | tester |
| T31853 | flash contents (dir all) | platform | PASS | flash lists .configs/ .home/ .rnd .certs/ log/; gui-userdata/ absent (used unit, no GUI), noted for re-grade | platform-2026-10-09T0845/31853/work/run1.log | tester |
| T31855 | system MAC | platform | PASS | system MAC = vlan1 MAC = 00c2.8f3f.0f5d, valid unicast; step 3 N/A (no eth0 on x230v2) | platform-2026-10-09T0845/31855/work/run1.log | tester |
| T31856 | exception log | platform | PASS | show exception log: None | platform-2026-10-09T0845/31856/work/run1.log | tester |
| T31861 | show system | platform | PASS | show system carries all 15 fields with reasonable values | platform-2026-10-09T0845/31861/work/run1.log | tester |
| T31858 | setting the clock (survives reload) | platform | PASS | clock set 05:05:52 9 Oct 2026 accepted; after a 163 s reload the DUT read 05:09:01 at box 18:09:02 (within 1 s); clock, VLAN 103-105 isolation and lldp run restored, running-config diff empty | platform-2026-10-09T0845/31858/work/run1.log | tester |
| T31863 | BIST (built-in self test) | platform | UNSUPPORTED | `platform bist instance all` / `0` / `all full` each answer "% BIST test not supported." on the x230v2-28GS; `show platform bist`: Instance 0 Not run (precondition: feature must be supported); 2 reloads, restored, running-config diff empty | platform-2026-10-09T0845/31863/work/run1.log | tester |
| T31866 | PRBS (pseudo-random bitstream) | platform | UNSUPPORTED | `platform prbs all-fabric duration 20` (the case's "all"), `internal-fabric` and `all-fabric` each answer "% PRBS not supported on this platform" on the x230v2-28GS; no results file (the parser offers only internal-fabric\|all-fabric, no stack-fabric); 2 reloads, restored, running-config diff empty | platform-2026-10-09T0845/31866/work/run1.log | tester |
| T46421 | link flap events | ports | PASS | 21 flaps (12 local on x230 port1.0.2-1.0.5, 9 remote from the stack) each give one down + one up event; links back at 1000/full, LLDP restored, config diffs empty | ports-2026-10-09T0845/46421/work/run1.log | tester |
| T47214 | Fan Alarm: verify alarm is trigger when fan speed is interrupted | platform | NOT TESTED | needs a person at the bench to interrupt the fan (magnet on the fan); not in the 18:00 scope | | tester |
| T45543 | TPM Support | platform | NOT TESTED | Test Engineer's: steps 1-2 runnable (`show system tpm` answers `TPM is instantiated`, expected `TPM is OK`), step 3 needs an idevid account and x230 internet via eth1; not in the 18:00 scope | | tester |
| T31868 | FactoryRunUp-Autoboot | platform | NOT TESTED | 3+ reloads with a 2nd .rel on USB (x230-2.rel on the 28.8G stick; no SD slot); kept out of the 18:00 scope by the Test Engineer | | tester |
| T31854 | FactoryRunUp-LEDtesting | platform | NOT TESTED | needs a person to watch the LEDs; precondition no SFP and no cable, but the x230 carries bench SFPs and cables | | tester |
| T31859 | FactoryRunUp-SystemEnvCheck | platform | NOT TESTED | CLI half runnable, but the fault-LED check needs a person at the bench; not in the 18:00 scope | | tester |
| T47228 | API-enable/disable interface, add/delete vlans | ports | NOT TESTED | Test Engineer's: no steps and the API under test is unspecified; not in the 18:00 scope | | tester |
| T44179 | Jumbo Frames | ports | NOT TESTED | needs x230 `platform jumboframe` (write + reload, x2), stack `platform jumboframe` (stack reload, x2) and root MTU on tb470 eth3/eth1 (Test Engineer's); not in the 18:00 scope | | tester |
| T33234 | Port - Auto MDI/MDI-X | ports | NOT TESTED | triaged UNSUPPORTED: no fixed copper on the x230v2-28GS (all 28 ports are SFP cages); not in the 18:00 scope | | tester |

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
- **2026-10-09 11:23:49–11:24:03 NZDT, bench change authorised by the Test Engineer ("Own VLAN, running-only"), x230 only, NO `write`.**
  - Why: eth3 on x230 port1.0.5 (VLAN 1) had joined eth1's L2 domain through the stack's VLAN1.
  - What changed, on the x230 via u0: `vlan database` / `vlan 105`; `interface port1.0.5` / `switchport access vlan 105`. VLAN 105 was unused on both the x230 and the stack beforehand. No `% ` line.
  - Verified by re-reading:
    - x230 `show vlan brief`: 105 = port1.0.5(u).
    - x230 `show interface status`: port1.0.5 connected 105, a-full a-1000.
    - tb470 eth3: UP, LOWER_UP.
    - Stack: eth3's MAC 00f0.4d00.7718 was still on sa2 at 11:24 (the dynamic entry had not aged out) and was gone at 11:29:58 after normal ageing. I did not clear it.
  - Lost at the next x230 reload. Revert by hand: `interface port1.0.5` / `switchport access vlan 1`; then `vlan database` / `no vlan 105`. Reverting re-joins eth3 to eth1's L2 domain.
- **2026-10-09 11:34:47 NZDT: `bench_probe.py --box tb470 apply`, authorised by the Test Engineer ("Apply now").**
  - Pre-apply probe `2026-10-08T223419Z` (precheck CLEAR): MISMATCH with exactly the three expected items and no NEEDS-CHECK or USER-CONFLICT:
    - `swi_a-swi_f` = port1.0.17-port1.0.3, port1.0.2-port1.0.2, port1.0.3-port1.0.4;
    - `tb-swi_b eth3` missing;
    - `tb-swi_f eth3-port1.0.5` extra.
  - Apply: render 63d4a21d24f4aa8facb1c2eb306634615e7dc4de (1256 B) replaced live f3fb487a1dc3d9f96f505493f20b47b34dce5c97 (1213 B), verified by readback.
  - Snapshots: `bench-setup/backups/2026-10-08T223447Z.tb470.setup` and `bench-setup/backups/2026-10-08T223447Z.bench-state.md`.
  - Confirming probe `2026-10-08T223456Z`: **exit 0 MATCH**. The deployed `/home/st-art/st-art/configs/tb470.setup` sha1 is 63d4a21d.
  - The VLAN 103/104/105 isolation (running-only, above) is not written; a reload of the x230 or the stack undoes it.
