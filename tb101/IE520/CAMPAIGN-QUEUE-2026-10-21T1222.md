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

**Test Engineer's answers to the triage, 2026-10-21 12:4x (option text, word for word):**
- Go: "Proceed now" — *Dispatch the RUN as planned: DUT po1 on port1.0.1+port2.0.1, host bond0 eth3+eth4, eth2 far side, events E1-E6.*
- Root traffic tools: "Yes, that reading" — *Traffic tools under sudo -n are test traffic; root CHANGES on tb101 are limited to the bond build/restore.*

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
| 1 | T17584 LACP - Startup stable with heavy traffic | tb101/IE520/lacp-2026-10-21T1222/ | DONE 14:12 NZDT -- PASS (run 1, 12:45-14:11; bench restored, probe 2026-10-21T011059Z MATCH; 4-device/4-route step NOT MEASURABLE; O-1 broadcast-duplicate transient at member rejoin, O-2 lacp Pckt err 2) | manual CLI + host bond (802.3ad) + line-rate traffic; member reloads + whole-stack reload inside the case; sudo -n on tb101 for the bond only |

## Triage 2026-10-21 12:35 NZDT (bench-runner, TRIAGE dispatch; read-only apart from the probe)

**Gate.** `precheck tb101 0-3` → exit 5 FOUND with ONE item, `ser2net` (pid 594, holds no `/dev/u*`; normal on
tb101) — u0–u3 all `free`; proceeded as the dispatch says. Probe `tools/tb probe tb101 --consoles 0-3 --baud 115200
--no-prompt` → **exit 0 MATCH**, capture `2026-10-20T232549Z`, advisories none. `tools/tb template tb101` reports
"no deployed tb101.setup" at the legacy `/home/st-art/st-art/` path (`/nfsHome` unmounted) — expected; the probe's
`/home/st-art/configs/tb101.setup` fallback is what matched. Reads on u0 via `ckcon` (scratch `lacp-1222`,
transcript `/tmp/lacp-1222/console-u0.log`) and one read-only `qmark` help probe; u0 left at `IE520#` with
`terminal no monitor` sent (transcript tail). No device state changed; no case run. No console outside u0–u3 touched.

### Report (STANDING-ORDERS §3): 1 runnable now / 0 blocked by topology / 0 blocked otherwise

T17584 is **runnable now** with the accepted fit. The one thing the bench cannot give — four devices and four
opposite-pair traffic routes — is reported inside the case as **NOT MEASURABLE**, never a FAIL (details below).
MANUAL-ONLY.md: T17584 is not listed, and no person-needed step was found (every event is a CLI shut or reload;
no cable pull, no PDU). Nothing added.

### What was measured at triage

DUT (u0, 12:26): stack Normal, member 1 (u0) Active Master prio 1, members 2/3/4 prio 128 with MACs
84e3.2787.0780 / 09c0 / 0740; `Stack MAC address 0000.cd37.0d6f (Virtual MAC)`; **`show lacp sys-id` = System
Priority 0x8000, MAC 0000.cd37.0d6f** (the VMAC, already the objective's actor system id). No LAGs exist
(`show static-channel-group` / `show etherchannel`: Static 0, Dynamic 0, max 124); `show etherchannel detail`
and `show lacp-counter` are accepted (empty). Running-config: `stack virtual-mac`, `stack virtual-chassis-id 3439`,
`spanning-tree mode rstp` + **`no spanning-tree rstp enable`** (STP off — a LAG member leaving the aggregator can
not be blocked by STP, nor needs to be: the host bond is the only partner, no loop path exists), **`no lacp
global-passive-mode enable`** (good — memory `lacp-passive-hides-links-from-stp`). port1.0.1 / port2.0.1 /
port3.0.1: `connected`, vlan 1, a-full a-1000, 1000BASE-T, config = `switchport` + `switchport mode access` only
(identical, so both LAG members match). MAC table: `000d.b951.4da1` (eth2) on port3.0.1, `4da2` (eth3) on
port2.0.1, `4da3` (eth4) on port1.0.1, all dynamic vlan 1. vlan1 = every front port except port3.0.25 (vlan3) and
port4.0.25 (vlan2). `show boot`: image `flash:/IE520-awplus_main-20261019-75.rel (file exists)`, **boot config
`flash:/tb101-bench.cfg (file exists)`** = gate-7 baseline. `show reboot history`: newest on all four members still
`2026-10-20 20:30:19 Expected User Request` (UTC) — unchanged baseline. (History before that: member 4 logged 13
`Unexpected System reboot` entries 10-15 → 10-19 and member 3 four; all predate the 10-20 reload and the current
build; noted so a new one is not mistaken for an old one.) `qmark` on `interface port1.0.1` (config mode entered
and left; nothing executed): `channel-group <1-248>`, `channel-group 1 mode active|passive`, `lacp timeout
long|short` — the forms the wiki's x230 page gives.

Host (`tools/hostinfo.py`, new generic read-only helper, run via `tools/tb tool`): Ubuntu 18.04.5, kernel
4.15.18-atlnz-rc2, python3 3.6.9 + python3.8.0, 4 GB RAM (2.9 GB free), /tmp tmpfs 2.0 G (1.9 G free).
**NetworkManager is inactive and `nmcli` is not installed**; eth2/eth3/eth4 are static in
`/etc/netplan/01-netcfg.yaml`, renderer **networkd** (systemd-networkd active): eth2 10.37.101.1/27 +
fd32:b1f0:dff7:6502::1/64, eth3 10.37.101.33/27 + …6503::1/64, eth4 10.37.101.65/27 + …6504::1/64, all
`optional: true`, `accept-ra: false`; `bootnet` is DHCP (never touched). All three NICs igb 5.4.0-k, 1000/full,
autoneg on, link detected, MACs 00:0d:b9:51:4d:a1/a2/a3. No bonding interface exists; bonding module v3.7.1 is on
disk, not loaded. `sudo -n true` OK. tcpreplay 4.2.6, scapy 2.4.4 (both pythons), iproute2 180129.
`/usr/sbin/tcpdump` is `-rwsr-x--- root grp_everyone` and answers *Permission denied* to this user → tcpdump runs
only under `sudo -n` (which `linerate.py` and `tools/tb capture` already do). `tools/` on the box: linerate.py,
l2flows.py, flowstat.py, vsend.py, vcount.py, mkpcap.py present (62 files + hostinfo).

### The fit, as I will run it

**Topology (accepted 12:2x):** host `bond0` (802.3ad) = eth3 + eth4 ↔ DUT `po1` = port2.0.1 (member 2) +
port1.0.1 (member 1 = master), `channel-group 1 mode active`; far side eth2 ↔ port3.0.1 (member 3). Two
bidirectional routes through the stack: po1 → stack links → port3.0.1 and back. Member 4 carries no edge; it is
a transit node whose reload turns the ring into a chain under traffic.

**DUT setup (u0, `cfg`/`ckcon`, stop on any `%`):**
```
configure terminal
 interface port1.0.1
  channel-group 1 mode active
 interface port2.0.1
  channel-group 1 mode active
 end
show etherchannel detail ; show lacp-counter ; show lacp sys-id ; show static-channel-group
copy running-config flash:/t17584.cfg          <- the case's own boot config, so step 4's reload boots WITH the LAG
configure terminal / boot config-file flash:/t17584.cfg / end ; show boot
```
No `write`: `tb101-bench.cfg` stays byte-identical. `remote-diff all show running-config` after the config
(memory `stack-refused-command-lands-on-backups`). `.cfg` for the log: `IE520.cfg` from the master's
`show running-config` after setup (one device = the stack).

**DUT restore:** `boot config-file flash:/tb101-bench.cfg`; `interface port1.0.1` / `no channel-group`,
`interface port2.0.1` / `no channel-group` (each returns the port to a plain access port; check with
`show running-config interface port1.0.1`); `delete force flash:/t17584.cfg` on the master (and on each
member's `flash:` if the copy was synced — `dir` reads the master only, check `show file systems` / per-member
delete as the image procedure does); `show boot` = baseline; `tools/rcdiff.py` of the post-run running-config
against the pre-run capture = no diff; probe MATCH.

**Host bond build (sudo -n, exactly the allowance — nothing else as root):**
```
ip -br addr > /tmp/lacp-1222/addr.before            # the restore target, recorded first
ip link add bond0 type bond mode 802.3ad miimon 100 lacp_rate fast xmit_hash_policy layer2
ip addr flush dev eth3 ; ip addr flush dev eth4      # the addresses below are re-added at restore
ip link set eth3 down ; ip link set eth4 down
ip link set eth3 master bond0 ; ip link set eth4 master bond0
ip link set bond0 up ; ip link set eth3 up ; ip link set eth4 up
cat /proc/net/bonding/bond0                          # "Partner Mac Address: 00:00:cd:37:0d:6f", both slaves
                                                     #  "Aggregator ID" equal, "port state 61/63"
```
NetworkManager handling: none needed (absent). **networkd:** eth3/eth4 keep their netplan `.network` units; a
slave enslaved outside networkd is left alone in networkd 237 (addresses are flushed above so no stray route
survives), and at restore `ip addr replace` is idempotent whether or not networkd re-applied them first. This is
the one host behaviour I have not measured here; the restore is verified by diff, not assumed.
**Host restore:**
```
ip link set eth3 nomaster ; ip link set eth4 nomaster ; ip link del bond0
ip addr replace 10.37.101.33/27 dev eth3 ; ip -6 addr replace fd32:b1f0:dff7:6503::1/64 dev eth3
ip addr replace 10.37.101.65/27 dev eth4 ; ip -6 addr replace fd32:b1f0:dff7:6504::1/64 dev eth4
ip link set eth3 up ; ip link set eth4 up
ip -br addr | diff /tmp/lacp-1222/addr.before -      # must be empty (eth2 untouched throughout)
```
then the probe: MATCH with eth3/eth4 learned on physical ports again (the bond's single MAC vanishes from po1).
The three `sudo -n ip …` sequences run as one `tools/` helper each (bond up / bond down) so the allowance is
visible as exactly those commands in the working log.

**Traffic (STANDING-ORDERS §7, existing tools only):**
- *Heavy:* `linerate.py` (root, tcpreplay + tcpdump) **both directions at once**: `--tx bond0 --dst-mac
  00:0d:b9:51:4d:a1 --rx eth2 --src-macs 16 --mac-prefix 02:cc:0a:00 --rate top` and `--tx eth2 --dst-mac
  <bond0 MAC> --rx bond0 --src-macs 16 --mac-prefix 02:cc:0b:00 --rate top`, 1500-byte UDP, 60 s per window.
  `--src-macs 16` rotates source MACs so the bond's layer2 hash AND the DUT's aggregator hash spread frames over
  both legs (proved from `show interface port1.0.1` / `port2.0.1` input+output packet counters before/after).
  Each direction is capped at ~984 Mbps by eth2's 1G link, so "heavy" = ~1 Gbps each way through the LAG, ~82 kpps
  each. Expected outside events: received = sent (±0, kernel drops 0). A first 5-s `--rate 10` run proves
  tcpreplay injects on `bond0` (not yet exercised on a bond) before any line-rate window.
- *Continuity across events:* `l2flows.py <secs> 100 <outdir> bond0 eth2` (4 sequence-numbered flows,
  broadcast + unicast each way, EtherType 0x88B5, tags B02/B20/U02/U20) runs through every event window; the
  event epoch goes to `flowstat.py`, which reports the outage length per flow. Loss is expected only inside the
  window and must stop afterwards. `loopwin.py` must report 0 windows (no duplicates: proves the LAG never
  delivered one frame twice).
- *Control flows (must NOT pass, same run):* `vsend.py` marked bursts, counted with `vcount.py` on a
  `tools/tb capture` of the far side: (1) from eth2, 500 frames to a unicast MAC the DUT has just learned on
  port3.0.1 itself (a second source MAC announced from eth2) → expected 0 on bond0 (same-port filtering);
  (2) from bond0, 500 frames to a MAC learned on po1 → expected 0 on eth2; (3) from eth2, 500 frames tagged
  VLAN 3 → expected 0 on bond0 (port3.0.1 is access vlan1). Paired positive bursts (untagged, far-side MAC)
  expected 500/500. The verdict rests on the pairs.
- *Pre-LACP control (recorded once, before `channel-group`):* the same linerate pair over the single eth4 ↔
  port1.0.1 leg (eth3 idle), plus the MAC table — so the LAG's figures have a non-LAG reference.

**Ordered events (step 3 and 4), with the check after each:**
| # | event | how | verified by |
| --- | --- | --- | --- |
| E0 | LAG up, no event | `show etherchannel detail`, `/proc/net/bonding/bond0` | both legs Collecting/Distributing; partner MAC = VMAC; linerate 60 s both ways = 0 loss; MAC table: bond MAC + 16 rotated MACs on **po1**, eth2 MACs on port3.0.1; `show lacp sys-id` = 0000.cd37.0d6f; LACPDU capture on eth3 (`tools/tb capture … 'ether proto 0x8809'`, 35 s) carries actor system 00:00:cd:37:0d:6f |
| E1 | `shutdown` port1.0.1 (the master's leg), 60 s under traffic, `no shutdown` | `/proc/net/bonding/bond0`: eth4 slave down, eth3 alone carries; flowstat outage ≤ a few hundred ms; after no-shut both legs back; sys-id, partner MAC, MAC table unchanged |
| E2 | same on port2.0.1 | as E1, mirror |
| E3 | `reload stack-member 1` (master, carries a LAG leg) via `reloadc` on **u1**; u0 shows the boot | predicted new master = member 4 (lowest MAC 0740 among the prio-128s; no pre-emption when 1 returns). Every backup console session drops (IE520.md §3): re-login before the next command. After rejoin (`show stack` all Ready): `show lacp sys-id` **still 0000.cd37.0d6f**, bond partner MAC unchanged, po1 has both legs, traffic 0 loss in a fresh 60-s window; MAC table from the new master |
| E4 | `reload stack-member 2` (the other LAG leg) | as E3 (master stays 4) |
| E5 | `reload stack-member 4` — the master, and the ring → chain 1-2-3 while traffic crosses the stack links | new master predicted = member 2 (0780 < 09c0); as E3 |
| E6 | **step 4: whole-stack `reload`** (`ckreload`, boots `flash:/t17584.cfg`) | member 1 back as master (prio 1); LAG forms from config; sys-id = VMAC; `/proc/net/bonding` partner = VMAC; traffic 60 s both ways 0 loss; MAC table correct (step 5) |
Before every event: `show stack` (mastership never pre-empts). After every event: the VMAC pair of reads,
`show etherchannel detail`, `show lacp-counter` (LACPDU counts rising, pckt err 0), `show mac address-table |
include po1|port3.0.1`, `show log | include LACP|port1.0.1|port2.0.1|po1|stack` (filtered on the console).
Health check twice (SO §8): before step 1 and after E6, before teardown. A new reboot-history entry is expected
for E3/E4/E5 (one member each) and E6 (all four) and will be matched to those times.

**NOT MEASURABLE here (reported as such in the log, never a FAIL):**
- *Step 2, "traffic into all 4 devices destined for the opposite pair":* tb101 has ONE switch (the stack) and
  three host edges. There is no second device pair and no "top/bottom" route. Measured instead: two bidirectional
  line-rate routes, po1 (members 1+2) ↔ port3.0.1 (member 3), crossing the stack links; member 4 only as
  transit. The IXIA ports (port3.0.25 / port4.0.25) are the Test Engineer's and are not driven.
- *An AW+-to-AW+ LACP partner:* the partner is a Linux 802.3ad bond. The DUT's actor side (sys-id, LACPDUs,
  aggregator behaviour, VMAC after failover) is fully measured; a peer switch's view of the LAG is not.
- *Physical cable pulls:* every port-down event is a CLI `shutdown` (link-down is signalled either way; a pull
  would be a manual step). Member 4's front ports carry no traffic at all (no host link; port4.0.26 far end is
  OPEN since 10-20).
- *Per-leg balance figures* are reported as measured, not graded: hashing is the bond's and the DUT's policy, not
  the objective.

**Needs the Test Engineer (none blocks the run; flagged for the record):**
1. Confirm the reading that the root traffic tools (`linerate.py`, `l2flows.py`, `vsend.py`, `tools/tb
   capture` — raw sockets / tcpreplay / tcpdump under `sudo -n`) are *test traffic from the box's host NICs*
   (within a test), and that the "root only for the bond" constraint is about root *changes*. I will proceed on
   that reading at RUN unless told otherwise. (tcpdump cannot run unprivileged on tb101 at all.)
2. After the run: `port4.0.26`'s far end (OPEN 1) is still unknown; not needed by this case.

**Time estimate:** setup + controls 25 min; E0–E2 15 min; E3/E4/E5 ≈ 8 min each (IE520 member boot ~3 min +
rejoin + re-login + a 60-s traffic window); E6 ≈ 10 min; health, teardown, restore, probe 20 min → **about 1 h
45 min**, finishing well inside the 17:30 ceiling if started by 15:00. Reload-heavy: 3 member reloads + 1
whole-stack reload, inside the "Reloads now" window.

**Gate items that do not apply:** gate 5 run `.setup` — the stack is one device made of all four units, so the
run `.setup` is the deployed one unchanged (every unit is used); gate 6 preflight — no framework script (manual
CLI + host tools); gate 8 — not a server run. Framework post-failure power cycle: no PDU, so nothing cycles
(recorded in the working log as the dispatch requires).

## Group lacp-2026-10-21T1222 — bench setup and exact restore recipe (tester, RUN dispatch, written 2026-10-21 12:5x NZDT BEFORE the first device change)

Gate re-run at RUN: `precheck tb101 0-3` FOUND ser2net only (u0–u3 free); `peek` u0–u3 all `IE520#`; probe
`2026-10-20T234243Z` **MATCH**; sentinel = parent session (device-testing-23). Run `.setup` = the deployed one
unchanged, copied to `lacp-2026-10-21T1222/tb101-u0u3.setup` (every unit is used: the stack is one device).

**Setup, in this order** (all through `tools/tb … tb101`, scratch `lacp-1222`; stop on any `% ` line):
1. Host bond (root, the one allowed root change): `tools/tb sudotool tb101 lacp-1222 bondctl up bond0
   /tmp/lacp-1222/bond-state.json eth3 eth4` — records `ip -br addr` + eth3/eth4 addresses into the state file
   FIRST, then `ip link add bond0 type bond mode 802.3ad miimon 100 lacp_rate fast xmit_hash_policy layer2`,
   `ip addr flush` / `link set down` / `set master bond0` on eth3 and eth4, bond0 and both NICs up. (Helper:
   `tools/bondctl.py`, new, README entry.)
2. DUT (u0, `cfg`): `configure terminal` / `interface port1.0.1` / `channel-group 1 mode active` /
   `interface port2.0.1` / `channel-group 1 mode active` / `end`; `copy running-config flash:/t17584.cfg`;
   `configure terminal` / `boot config-file flash:/t17584.cfg` / `end`; `show boot`. **No `write`**:
   `flash:/tb101-bench.cfg` stays byte-identical.

**Restore, whatever happened, in this order** (a fresh tester runs exactly this; the master may be on any
console after E3–E6, so read `show stack` first and use the master's console, or any backup console re-logged in):
1. DUT (`cfg`): `configure terminal` / `boot config-file flash:/tb101-bench.cfg` / `interface port1.0.1` /
   `no channel-group` / `interface port2.0.1` / `no channel-group` / `end`. Check `show boot` reads
   `flash:/tb101-bench.cfg (file exists)` and `show running-config interface port1.0.1` (and 2.0.1) reads
   `switchport` + `switchport mode access` only; `show etherchannel` Dynamic 0.
2. DUT files (`ckyn`): `YN?:delete force flash:/t17584.cfg` on the master; then `dir IE520-N/flash:/` for each
   backup N (memory `ie520-image-update-procedure`: `<hostname>-N/flash:`) and delete any synced copy.
3. `remote-diff all show running-config` (memory `stack-refused-command-lands-on-backups`), then
   `tools/rcdiff.py` of the post-run `show running-config` against the pre-run one = no diff.
4. Host: `tools/tb sudotool tb101 lacp-1222 bondctl down bond0 /tmp/lacp-1222/bond-state.json` — nomaster
   eth3/eth4, `ip link del bond0`, `ip addr replace 10.37.101.33/27` + `fd32:b1f0:dff7:6503::1/64` on eth3,
   `10.37.101.65/27` + `fd32:b1f0:dff7:6504::1/64` on eth4, links up, and it prints `RESTORE DIFF: empty`.
   If the state file is gone (box reboot wipes /tmp): run those four `ip addr replace` lines by hand.
   No NIC pinning is ever set (`ethtool` untouched).
5. Consoles u0–u3: `end`, `terminal no monitor`, exec prompt (`peek`). Kill nothing left behind
   (`tools/tb ps tb101 'linerate|l2flows|tcpdump|vsend'` empty).
6. `tools/tb probe tb101 --consoles 0-3 --baud 115200 --no-prompt` = MATCH; `show boot` = baseline on every
   member.

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| T17584 | LACP - Startup stable with heavy traffic | lacp-2026-10-21T1222 | PASS | po1 (members 1+2) carried ~600 Mbps bidirectional through 2 leg shuts, 3 member reloads (2 master failovers) and a whole-stack reload; LACP sys-id, LACPDUs and the bond's partner MAC stayed the VMAC 0000.cd37.0d6f throughout; loss only inside event windows, controls 0 beside positives 500, MAC tables correct, health clean; step 2's 4-device routes NOT MEASURABLE; O-1 4 broadcast frames duplicated in a 30-ms window at each member rejoin, O-2 lacp-counter Pckt err Sent 2 on the master's leg | 17584/work/run1.log | tester |

## Issues

