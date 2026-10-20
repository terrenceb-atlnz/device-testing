# Campaign queue — tb101, IE520 4-stack as the DUT, 1 AWPTCM case (T17584 LACP heavy traffic), from 2026-10-21 12:22 NZDT

The ask, Test Engineer 2026-10-21 ~10:50 (after `/orient-dt tb101` + `/wrap-dt`, handovers moved to `tb101/IE520/`):
*"i would like to start /test-mode and run T17584 to the best of our ability. The test Step isnt going to be able to
do 4 traffic routes, just 3 with tcpreplay, but let me know what we can do according to the Objective and how we can
test this to the best of our ability."*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-21 12:2x NZDT (Test Engineer's answers to the setup questions):
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb101
Consoles: u0,u1,u2,u3 (= stack members 1,2,3,4; all 115200)
PDU: none (nothing is power-cycled; the framework's post-failure cycle silently does nothing)
Constraints: none ("Confirm as stated"). Run window: "Reloads now, stand down at end of run, stay in VS Code" (member and
whole-stack reloads during office hours are fine; sentinel stands down when the run ends; risk accepted that a closed
editor kills the tester). Sentinel hard ceiling 2026-10-21 17:30 NZDT.

**Test Engineer's answers to the approach questions, 2026-10-21 12:2x (option text, word for word):**
- Topology: "Bond eth3+eth4 <-> po1 on members 1+2; eth2 far side" — *LAG spans the master and member 2, so a master
  reload loses one leg and the LAG must carry on. Far side on member 3. Two bidirectional routes at line rate.*
- Root on the box: "Tester may use sudo -n for the bond and its restore" — *Within the case only: ip link bond0
  add/del, enslave/release, re-add the NIC addresses, verify with ip -br addr. Nothing else as root.*

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  The final log is made ONLY by `/create-logs`, on the Test Engineer's request.
- `STANDING-ORDERS.md` applies (§7 scapy/crafted frames with a control flow; §8 health check twice per case).
  Reloads of any member and of the whole stack are allowed within the test. No PDU exists.
- **Only u0-u3 are touched.** tb101 is the Test Engineer's own box (not shared); ser2net's `precheck` FOUND is normal.
- **Root on tb101 is limited to the bond** (above). Anything else as root → `NEEDS TEST ENGINEER`.
- Case text: Ask-CK `ck.db` table `zephyr_cases`, key `AWPTCM-T17584` (`tools/ckcase.py`, ON a testbox or with
  `--db <dev-host path>`). Title "LACP - Startup stable with heavy traffic", folder
  `/VCS (Virtual Chassis Stacking)/VCS (VMAC)/VMAC - L2 Features`, labels Stress, Platform-Test.
  **Objective:** *"Conduct several topology changes and check that port interfaces configured of LACP handles heavy
  traffic and still uses the virtual-mac of the stack."* **Steps (one row):** 1. Configure as shown in the
  Setup/Configs (NOT in ck.db) 2. Start traffic into all 4 devices destined for opposite pair e.g.
  Left<->right/top<->bottom. 3. Conducted multiple port down events so that topology had to change totally 4. reboot
  stack 5. Check traffic and MAC tables of Stack. **Expected:** Traffic should be flowing without a problem; the MAC
  tables should reflect the correct MAC addresses. Siblings T17582/T17583 (LACP uses VMAC / master MAC) are NOT in scope.
- MANUAL-ONLY.md (repo root) is read at triage (T17584 is not listed).
- Platform traps: [platforms/IE520.md](../../platforms/IE520.md) (§3: `lacp global-passive-mode` fights explicit
  config, memory `lacp-passive-hides-links-from-stp`; a master reload drops the CLI session on every backup console;
  a refused stack command can land on backups → `remote-diff all show running-config`). Bench map: memory
  `tb101-ie520-bench-map`; handovers [SESSION-HANDOVER-2026-10-21.md](SESSION-HANDOVER-2026-10-21.md),
  [SESSION-HANDOVER-2026-10-20.md](SESSION-HANDOVER-2026-10-20.md).

## The fit (sentinel's proposal, accepted by the Test Engineer 12:2x) — the tester triages and may refine it

- **Four "devices" cannot be had**: the stack is the only switch on tb101, and there are three host edges
  (eth4↔port1.0.1 member 1 = master, eth3↔port2.0.1 member 2, eth2↔port3.0.1 member 3). Member 4 has no host link
  (its port4.0.26 far end is unknown, OPEN since 10-20). The IXIA ports (port3.0.25 vlan3, port4.0.25 vlan2) are
  the Test Engineer's to drive, not the tester's.
- **LACP partner = tb101 itself:** Linux bonding 802.3ad (module 3.7.1 present; `sudo -n` works; tcpreplay and
  scapy 2.4.4 present; eth2/3/4 all 1000/full). `bond0` = eth3 + eth4 ↔ stack `po1` = port2.0.1 + port1.0.1
  (`channel-group 1 mode active`), a cross-member LAG over members 2 and 1. Far side: eth2 ↔ port3.0.1 (member 3).
  Check `nmcli`/NetworkManager ownership of eth3/eth4 before enslaving; restore their addresses exactly
  (10.37.101.33/27 + fd32:b1f0:dff7:6503::1/64 on eth3, 10.37.101.65/27 + fd32:b1f0:dff7:6504::1/64 on eth4) and
  confirm the probe reads MATCH afterwards.
- **Heavy traffic:** raw L2 at line rate both ways, bond0→eth2 and eth2→bond0 (`tools/linerate.py` or tcpreplay of a
  scapy-built pcap; counted on the receiving NIC), plus a control flow that must NOT pass (STANDING-ORDERS §7).
  Loss is expected only inside each event window and must recover after it.
- **Topology events (step 3):** shut/no-shut port1.0.1, then port2.0.1 (one LAG leg at a time); `reload
  stack-member 1` (master failover with a LAG leg on it); `reload stack-member 2`; optionally `reload stack-member 4`
  (ring → chain). **Step 4:** whole-stack `reload`. `show stack` before every event: mastership moves and never
  pre-empts.
- **VMAC evidence (the objective):** `show lacp sys-id` = VMAC 0000.cd37.0d6f and the host's
  `/proc/net/bonding/bond0` "Partner Mac Address" = 00:00:cd:37:0d:6f, read before and after EVERY event; LACPDUs
  captured on eth3/eth4 carry that actor system MAC. **MAC tables (step 5):** bond0's MAC on po1, eth2's MAC on
  port3.0.1, on `show mac address-table` from the master, after every event and after the reboot.
- Baseline first (feature OFF: a single leg, no channel-group) is NOT required here: the subject is LACP under
  events, but DO record the pre-LACP MAC table and traffic counts once as the control.

## Bench at queue creation (2026-10-21 10:3x NZDT, probe `2026-10-20T213624Z`, MATCH, advisories none)

- One 4-member stack `IE520`, Normal operation, 8/8 stackports learnt (ring), VMAC 0000.cd37.0d6f, `stack 1 priority 1`.
  Member 1 (u0, S/N 264A23061, swi_a) Active Master; 2 (u1, 264A23068, swi_b), 3 (u2, 264A23052, swi_d),
  4 (u3, 264A23066, swi_c) Backup. Build `awplus_main-20261019-75`, bootloader 9.2.0 on all four. Boot
  `flash:/IE520-awplus_main-20261019-75.rel` + `flash:/tb101-bench.cfg`, both `(file exists)`. Free flash
  64.9/64.7/64.6/59.2 MB.
- Reboot history newest on every member: `2026-10-20 20:30:19 Expected User Request` (UTC) = the 09:29 reload. Baseline.
- Host: eth2 10.37.101.1/27, eth3 10.37.101.33/27, eth4 10.37.101.65/27 (+ fd32:b1f0:dff7:650{2,3,4}::1/64), carrier up,
  all learned on physical ports. `bootnet` 10.36.200.101/17 is the box's management NIC: never touched.
- Deployed template: `/home/st-art/configs/tb101.setup` (`/nfsHome` unmounted; the probe's fallback). python3.8.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | T17584 LACP - Startup stable with heavy traffic | tb101/IE520/lacp-2026-10-21T1222/ | PENDING triage | manual CLI + host bond (802.3ad) + line-rate traffic; member reloads + whole-stack reload inside the case; sudo -n on tb101 for the bond only |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

