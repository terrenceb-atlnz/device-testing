# Campaign queue — tb470, x230v2-28GS as the DUT: re-run of the cases previously UNSUPPORTED, after a FULL licence was installed (AR4050S = partner), from 2026-10-27 08:55 NZDT

The ask, Test Engineer 2026-10-27 ~08:45 (after `/orient-dt`, bench tb470): *"Ive installed a Full license on the x230v2 now,
we need to re-run any test that was previously listed as UNSUPPORTED, including 30403."* Scope agreed 08:5x (AskUserQuestion):
T30403, T31863, T31866 (always), plus **T28218 with the x230 as the AMF MASTER**; T33234 (MDI/MDI-X) left out (a hardware
ruling, not a licence one). Then `/test-mode T30403 T31863 T31866 T28218`.

Titles (ck.db `zephyr_cases`): AWPTCM-T30403 Check traffic is fowarded with static mroutes (IPv4); AWPTCM-T31863
FactoryRunup-BIST (if supported); AWPTCM-T31866 FactoryRunup-PRBS (if supported); AWPTCM-T28218 ATMF provisioning.

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-27 08:55 NZDT (Test Engineer's answers to the setup questions):
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u0,u1 (u0 = AR4050S swi_e; u1 = x230v2-28GS swi_f, the DUT; both 115200) — "Yes, as stated"
PDU: "10.36.150.14 u0=3 u1=4" — "Yes, as stated"
Constraints: "Reloads allowed (Recommended)" (option text: "The x230 and the 4050 may reload as the cases need, during office hours.") + "None beyond reloads allowed". Sentinel stand-down: "When the run ends". Host: "Stay in VS Code (Recommended)" (risk accepted).

At 08:46 Terrence opened `minicom --wrap -D /dev/u1 -c off` (PID 309802) on tb470 (installing the licence). **u1 is not opened by
this campaign until that holder is gone** (precheck CLEAR); never displace it.

Triage answers, 2026-10-27 09:19 NZDT (AskUserQuestion):
- Go: "Proceed (Recommended)" (option text: "Run groups 1 and 2 now; T28218 waits in the queue as BLOCKED").
- T28218 backup media: "Move the 4050's stick" (option text: "Move swi_e's USB to the x230; the 4050 loses its usb:/atmf trees from 09-21 and 10-21 while it's away"). The move is physical, so the Test Engineer does it; group 3 is re-triaged when he says it is done.

Test Engineer's answers, 2026-10-27 10:3x NZDT (AskUserQuestion):
- T28218: "Yes, moved, go" (option text: "Re-triage group 3 (confirm usb: Avail Y on the x230), then run T28218 with the x230 as master (~45 min)"). The 31 GB stick in the x230 is the 4050's; the 4050 has no USB stick while it is away.
- Health flag on T31866 and T30403 (`HTTP: HTTP server restarted`, a boot line already in the before sample): "Agree, clean" -- both runs stay labelled clean.

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  The final log is made ONLY by `/create-logs`, on the Test Engineer's request.
- `STANDING-ORDERS.md` applies (§7 scapy for traffic, §8 health reads twice per case). Startup config: nothing written unless a case requires it.
- **Only u0 and u1 are touched.**
- **First read of the campaign, before any case:** on u1 `show license`, `show license brief`, `show feature` (or the build's
  equivalents): what the FULL licence enabled. Record it in the triage. Whether a licensed feature needs a reload to take
  effect is a measurement, not an assumption (reloads are allowed).
- **Prior verdicts are method only, never the verdict.** A case that is still refused gets UNSUPPORTED again, with the
  licence read as evidence; one that now works is graded on its steps.
  - T30403 UNSUPPORTED 2026-10-13 (`cli-2026-10-13T0949/30403/30403-unsupported.log`): `ip multicast-routing`, `ip mroute`,
    `ip pim`, `show ip mroute` absent from the parser; `show license` had no multicast/PIM feature.
  - T31863 UNSUPPORTED 2026-10-09 (`platform-2026-10-09T0845/31863/`): `platform bist instance …` → `% BIST test not supported.`
  - T31866 UNSUPPORTED 2026-10-09 (`platform-2026-10-09T0845/31866/`): `platform prbs …` → `% PRBS not supported on this platform`.
  - T28218 with the x230 as master: triaged UNSUPPORTED 2026-10-09 (x230 lacked AMF-MASTER), never run. T28218 PASSED
    2026-10-21 with the **4050** as master (`atmf-2026-10-21T0835/`, queue `CAMPAIGN-QUEUE-2026-10-21T0835.md`: the
    exact steps, setup and restore). This run is the x230-as-master limb.
- Case texts: Ask-CK `ck.db` table `zephyr_cases`, key `AWPTCM-T<n>`, read-only (`tools/ckcase.py`; on the dev host the db is
  `/media/terrenceb/mnt/testbox_home/claude/Test-cases/ask-ck/db/ck.db`).
- MANUAL-ONLY.md (repo root) is read at triage.
- Platform traps: [platforms/x230v2-28GS.md](../../platforms/x230v2-28GS.md) (reload ≈ 165 s; a reload drops running-only
  config incl. `lldp run`; `show reboot history` is unsorted). AMF memories: `atmf-recovery-residue-and-reboots`,
  `ie520-master-ignores-remote-backup-server`, `x230v2-atmf-campaign-2026-10-21`.

## Bench at queue creation (orient probe `2026-10-26T190212Z`, 08:02, u0/u1, **MISMATCH**; reads 08:02–08:06)

- Probe MISMATCH = the 2026-10-22 recable only (`[portlink] swi_e-swi_f` adds port1.0.3-port1.0.3; `tb-swi_f eth2-port1.0.10`
  absent from the template). `apply` not done (the Test Engineer's). No Advisories.
- u0 AR4050S swi_e S/N A10401G214000005, awplus_main-20261008-57, bootloader 5.2.8, boots `flash:/AR4050S-awplus_main-20261008-57.rel (file exists)`
  + `flash:/tb470-bench.cfg (file exists)`; flash 3.4 GB free, USB 28.6 GB free; up 11 d; newest reboot 2026-10-15.
- u1 x230v2-28GS swi_f S/N A10783G262900002, awplus_main-20261019-75, bootloader 6.2.40, boots `flash:/x230v2_28GS-awplus_main-20261019-75.rel (file exists)`
  + `flash:/tb470-bench.cfg (file exists)`; flash 60.6 MB free; **no USB stick** (`usb:` Avail N); up 6 d 20 h; newest reboot 2026-10-20.
  Admin down AND saved: port1.0.7, **port1.0.16, port1.0.26** (the self-loop legs; leave them shut — 1.0.15<->1.0.16 copper,
  1.0.25<->1.0.26 SX, all vlan1 with STP off would storm). These read before the licence install; re-read at triage.
- Links (probe): tb eth1 -> x230 port1.0.2; tb eth2 -> x230 port1.0.10; tb eth3 -> 4050 port1.0.1; 4050 port1.0.2 <-> x230
  port1.0.1 (x230 side `switchport atmf-link`); 4050 port1.0.3 (vlan10, sa1) <-> x230 port1.0.3 (vlan103).

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | platform: T31863 (BIST), T31866 (PRBS) | tb470/x230v2-28GS/platform-2026-10-27T0855/ | DONE 09:51 — T31863 UNSUPPORTED, T31866 UNSUPPORTED (bench-runner; restored: running-config identical to pre-run, boot cfg tb470-bench.cfg, u0/u1 logged out) | u1 CLI; no licence reload needed (the unit already booted with FULL at 08:48). Parser offers both, as on 10-09; whether they still refuse is the run's measurement |
| 2 | mcast: T30403 (static mroutes, IPv4) | tb470/x230v2-28GS/mcast-2026-10-27T0855/ | DONE 10:08 — T30403 UNSUPPORTED (bench-runner; nothing accepted, running-config identical to pre-case, boot cfg tb470-bench.cfg, post probe = pre probe, u0/u1 logged out; X220 Software TPS: Multicast Routing PIM-SM/DM/SSM = NO; x230v2 target `mcast-ip-cmd = no`) | licence now lists PIM / PIM6 / L3-MC-ROUTE, but after a licensed boot `ip multicast-routing`, `ip mroute`, `ip pim`, `show ip mroute`, `show ip pim` are still `% Unrecognized command`: expect UNSUPPORTED again (~10 min, no device change) |
| 3 | atmf: T28218 (ATMF provisioning, **x230 as master**) | tb470/x230v2-28GS/atmf-2026-10-27T0855/ | DONE 11:24 — T28218 PASS (bench-runner; x230 = AMF master on the moved USB stick; restored: provision delete + rmdir of the empty nodes/future_node, `no atmf master`, one u1 reload for the Restricted-login residue; running-config identical to pre-case on u0 and u1, boot cfg tb470-bench.cfg both, post probe = groups 1/2's MISMATCH, u0/u1 logged out; the 10-21 leftover `usb:/atmf/Enterprise-AMF/info/backup_future_node.info` was rewritten by step 1 and stays). Re-triage 11:00: Test Engineer (relayed) on the precheck FOUND (minicom on /dev/u2): *"dont touch u2, its irrelevant"* |

## Group 1 bench setup and restore recipe (bench-runner RUN, written 09:24 before the first case)

- **Gate 09:20–09:22:** precheck `tb470 0,1` CLEAR (exit 0); peek u0 `4050-5g login:`, u1 `x230-28GSv2 login:`;
  `/nfsHome` mounted, `tb470.setup` present; probe `2026-10-26T202129Z` (session facts, `--baud 115200`) **exit 1
  MISMATCH = the same 2026-10-22 recable as triage** (no Advisories, no USER-CONFLICT); no case here binds a `.setup`.
  Box scratch `/tmp/plat-1027/` (transcripts `console-u1.log`, `console-u0.log`).
- **Devices used:** u1 (swi_f, x230v2-28GS, the DUT) only. u0 (4050) is NOT touched by either case (standalone DUT,
  "no loopbacks"); it is opened only to confirm it is logged out at the end.
- **Baseline (09:22, u1):** `Current boot config: flash:/tb470-bench.cfg (file exists)`, boot image
  `flash:/x230v2_28GS-awplus_main-20261019-75.rel`; `show running-config` == `show startup-config` (only the
  startup header differs; saved 2026-10-26 19:48 UTC by manager via con0), so a reload loses nothing.
  port1.0.7/1.0.16/1.0.26 are saved `shutdown`.
- **Setup per case (u1):** `reload` (no save) → login → `configure terminal` / `line con 0` / `exec-timeout 0` / `end`
  (running only) → `exit` + fresh login → the case's command → `show platform bist|prbs` → `reload` (no save).
- **Restore recipe (for a fresh tester if this one dies):** on u1, never `write`. A `reload` (answer `n` to any save
  question) returns the unit to `flash:/tb470-bench.cfg`; prove it with `show running-config` diffed against the
  pre-case copy (only `exec-timeout 0 0` under `line con 0` may differ before the reload; nothing after it), and
  `show boot` still naming `flash:/tb470-bench.cfg`. Then `exit` u1 to `login:`.

## Group 2 bench setup and restore recipe (bench-runner RUN, written 09:58 before the case)

- **Gate 09:56–09:57:** precheck `tb470 0,1` CLEAR (exit 0); peek u0 `4050-5g login:`, u1 `x230-28GSv2 login:`;
  `/nfsHome` mounted, `tb470.setup` present; probe `2026-10-26T205715Z` (session facts, `--baud 115200`) **exit 1
  MISMATCH = the same 2026-10-22 recable** (no Advisories, no USER-CONFLICT); T30403 binds no `.setup` (manual CLI).
  Box scratch `/tmp/mc-1027/` (transcript `console-u1.log`).
- **Devices used:** u1 (swi_f, x230v2-28GS, the DUT) only. u0 (4050) is not needed while step 1 cannot be configured;
  it is only peeked/probed. The 31 GB USB stick in the x230 is group 3's: not touched.
- **Setup (u1):** none beyond the setup reads (no reload, no config). Step 1 = the case's config forms sent in config
  mode WITH CR (`ip multicast-routing`, `ip mroute …`, `ip pim …` on an interface), each expected `% ` refused.
- **Restore recipe (for a fresh tester if this one dies):** on u1, `end`; never `write`. Diff `show running-config`
  against the pre-case copy `mcast-2026-10-27T0855/30403/work/pre.out` (`python3 tools/rcdiff.py`); any line that
  landed is removed with its `no` form (or a `reload`, answering `n` to save, returns the unit to
  `flash:/tb470-bench.cfg`). Prove `show boot` still names `flash:/tb470-bench.cfg`. Then `exit` u1 to `login:`.

## Group 3 bench setup and restore recipe (bench-runner RUN, written 11:05 before the first device change)

- **Gate 10:58–11:01:** precheck `tb470 0,1` exit 5 FOUND = Terrence's `minicom --wrap -D /dev/u2 -c off` (PID 384135) only;
  Test Engineer (relayed 11:00): *"dont touch u2, its irrelevant"*. u0/u1 free; peek u0 `4050-5g login:`, u1 `x230-28GSv2 login:`;
  `/nfsHome` mounted, `tb470.setup` present; probe `2026-10-26T220056Z` exit 1 MISMATCH = the 2026-10-22 recable only.
  No `.setup` bound (manual CLI). Box scratch `/tmp/atmf-1027/` (transcripts `console-u0.log`, `console-u1.log`).
- **Devices used:** u1 (swi_f, x230v2-28GS) = the AMF MASTER and the only unit configured. u0 (4050, no USB stick now,
  no `atmf network-name`) is NOT configured: the case as written runs entirely on the master, so no member is needed.
  u0 is only read (running-config before/after) and logged out.
- **USB stick before the run (u1 11:01, `dir recursive usb:/atmf`):** `usb:/` = `atmf/`, three IE520 `.rel`, one `.kwb`;
  `usb:/atmf/tb470/` (Sep 21 tree: x230-10GP, IE520-stk, 4050-5g nodes); `usb:/atmf/Enterprise-AMF/{nodes,info,logs,areas,guests/{info,logs,nodes}}`
  from 10-21, `nodes/` EMPTY, `info/backup_future_node.info` (40 B, Oct 20 20:29 UTC, a 10-21 leftover). All of that stays
  exactly as it is; only what this run adds is removed.
- **Setup (u1, running-config only, no `write`):** `configure terminal` / `atmf master` / `end` (network-name Enterprise-AMF,
  mgmt vlan 3500, domain vlan 1234 are already the x230's baseline). Gate: `show atmf` Role Master; `show atmf backup` /
  `show atmf provision nodes` → Backup Media USB.
- **Steps (u1):** `atmf provision node future_node` → `create` → `locate` → `copy flash:/x230v2_28GS-awplus_main-20261019-75.rel
  ./x230v2_28GS-awplus_main-20261019-75.rel` (36.7 MB to the STICK; x230 flash 60.6 MB free is not written) → `configure boot
  system x230v2_28GS-awplus_main-20261019-75.rel` → `copy flash:/tb470-bench.cfg ./tb470-bench.cfg` → `configure boot config
  tb470-bench.cfg` → `exit` → `show atmf provision nodes`.
- **Restore recipe (u1; for a fresh tester if this one dies):** `atmf provision node future_node` / `delete` (answer y if asked)
  / `exit`; `dir recursive usb:/atmf` and compare with the list above: `rmdir` only what is new (10-21 left an empty
  `nodes/future_node/` after `delete`); `configure terminal` / `no atmf master` / `end`; never `write`. Then `show atmf`:
  if master/depth residue shows, `reload` u1 (answer `n` to any save question; boots `flash:/tb470-bench.cfg`, ~165 s).
  Prove: `tools/rcdiff.py` of `show running-config` against `atmf-2026-10-27T0855/28218/work/pre-u1.out` (and u0 against
  `pre-u0.out`, which must be identical untouched), `show boot` both `flash:/tb470-bench.cfg (file exists)`. `exit` both
  consoles to `login:`.

## Results

| case | verdict | reason | graded by | working log |
| --- | --- | --- | --- | --- |
| T31863 FactoryRunup-BIST (if supported) | UNSUPPORTED | build -20261019-75 with the FULL licence booted: `platform bist instance all` / `0` / `all full` each `% BIST test not supported.`; `show platform bist` "Not run"; health CLEAN; restored (running-config identical, boot cfg tb470-bench.cfg). Finding: each `show platform bist` logs ~96 `local7.err EXFX … Attempt to access illegal devGroup 99` debug lines | tester | platform-2026-10-27T0855/31863/work/run1.log (c8ce3cc) |
| T31866 FactoryRunup-PRBS (if supported) | UNSUPPORTED | build -20261019-75 with the FULL licence booted: `platform prbs all-fabric duration 20` (for the case's `all`), `internal-fabric duration 20`, `all-fabric` and the literal `all duration 20` each `% PRBS not supported on this platform`; `show platform prbs` "No previous PRBS run?"; restored (diff 0). Health: health.py flagged DIRTY on `HTTP: HTTP server restarted` (20:40:19 UTC), a boot-time line already in the before sample; tester reads it as a tool false positive, run labelled clean -- Test Engineer to confirm | tester | platform-2026-10-27T0855/31866/work/run1.log (212a6d5) |
| T30403 Check traffic is fowarded with static mroutes (IPv4) | UNSUPPORTED | FULL licence enabled on this boot (PIM, PIM-100, PIM-1024, PIM6, L3-MC-ROUTE listed), yet on -20261019-75 `ip multicast-routing`, `ip mroute` (with/without `static`), `ip pim sparse-mode|dense-mode`, `ip multicast` and `show ip mroute|pim|multicast` are each `% Invalid input` / `% Unrecognized command`; nothing landed (running-config diff 0). Docs: X220 Software TPS (wiki) lists Multicast Routing PIM-SM/DM/SSM = NO for this platform, so a licence cannot add it; the local Feature Overview Guides directory is absent. Health: health.py flagged DIRTY on `HTTP: HTTP server restarted` (20:47:54 UTC, a boot line from group 1's restore reload, already in the before sample; 0 new lines); tester reads it as the same tool false positive, run labelled clean -- Test Engineer to confirm | tester | mcast-2026-10-27T0855/30403/work/run1.log (338de97) |
| T28218 ATMF provisioning (x230v2-28GS as AMF master) | PASS | FULL licence (AMF-MASTER-20…250), backup media = the 4050's 31 GB USB stick moved to the x230; run-only `atmf master` → Role Master, Backup Media USB; `atmf provision node future_node` → `create` → `locate` → copy the x230's own `.rel` (36,747,551 B) + `tb470-bench.cfg` to the stick, `configure boot system/config` → `show atmf provision nodes`: future_node, Provision Path `usb:/atmf/Enterprise-AMF/nodes/future_node/flash/`, both boot entries `(file exists)`; health CLEAN; restored (running-config identical on both units after a u1 reload for the Restricted-login residue). Notes: `delete` leaves an empty node dir and the node listed until `rmdir` (as 10-21); step 1 rewrote the 10-21 leftover `info/backup_future_node.info` | tester | atmf-2026-10-27T0855/28218/work/run1.log (eb9706f) |
| T28218 ATMF provisioning (x230 as AMF master) | PASS | x230v2-28GS as AMF master (FULL licence, AMF-MASTER) with the 4050's USB stick (moved by the Test Engineer) as backup media: all 5 steps -- future_node provisioned, its directory on usb:, the x230's .rel and tb470-bench.cfg copied to usb:/atmf/Enterprise-AMF/nodes/future_node/flash/ and set, `show atmf provision nodes` both "(file exists)"; health clean; restored (provision deleted, node dir removed, `no atmf master`, one u1 reload for the Restricted-login residue; running-config identical on u0/u1). Left on the stick: the pre-existing 10-21 `info/backup_future_node.info` was REWRITTEN by the provisioning (now "PASS 26/10/2026 22:07:08 … PROV") -- not deleted | tester | atmf-2026-10-27T0855/28218/work/run1.log (eb9706f) |

## Issues


## Triage 2026-10-27 09:10 NZDT (bench-runner, TRIAGE dispatch from the /test-mode sentinel)

Read-only apart from the probe. No device state changed, no case run. u0 and u1 left at `login:` (logged out with
`exit`, checked with `peek` 09:10). Box scratch `/tmp/triage-0855/` (transcripts `console-u0.log`, `console-u1.log`).

### Gate

| gate | result |
| --- | --- |
| 1 occupancy (`tools/tb precheck tb470 0,1`, 09:03) | **CLEAR** (exit 0): u0, u1 free; Terrence's minicom on u1 gone. Only sshd/bash logins of terrenceb (information) |
| 2 parked consoles (`peek`, 09:03) | u0 `4050-5g login:`, u1 `x230-28GSv2 login:` — neither parked mid-state |
| 3 template | `/nfsHome` mounted (nfs4); `/home/st-art/st-art/configs/tb470.setup` exists (685 B, Oct 22 12:44) |
| 4 probe (`2026-10-26T200411Z`, 09:04, session facts as dispatched) | **exit 1 MISMATCH = exactly the 2026-10-22 recable**: `[portlink] swi_e-swi_f` bench `{port1.0.2-port1.0.1, port1.0.3-port1.0.3}` vs template `port1.0.2-port1.0.1`; `[portlink] tb-swi_f eth2` EXTRA_IN_LIVE `eth2-port1.0.10`. **No Advisories, no USER-CONFLICT.** `apply` remains the Test Engineer's (handover 10-22 OPEN 1). No case in this queue binds `tb470.setup` (all manual CLI), so the MISMATCH blocks nothing here |
| 5 run `.setup` | not needed: no framework script; manual CLI via `tools/tb ckcon/cfg` on u0/u1 only |
| 6 preflight | N/A (no script) |
| 7 boot baseline | u0 `flash:/tb470-bench.cfg (file exists)`, `.rel` AR4050S-awplus_main-20261008-57, up 11 d 18 h; u1 `flash:/tb470-bench.cfg (file exists)`, `.rel` x230v2_28GS-awplus_main-20261019-75, backup image/config Not set |
| 9 sentinel | `sentinel: parent` |
| 10 defaulting CLI | N/A (no framework script) |
| MANUAL-ONLY.md | none of T31863, T31866, T30403, T28218 listed |

### u1 (x230v2-28GS swi_f) licence read, 09:04 (`ckcon`; `show feature` does not exist on this build: `% Invalid input`)

- **The x230 rebooted at 2026-10-26 19:48:04 UTC = 08:48 NZDT** (`show reboot history`: `Expected CLI(user request)`;
  `show system` uptime 0 d 00:16:18 at 20:04:43 UTC). That is inside Terrence's minicom window (08:46–09:02).
  The current boot's buffered log has no licence command line (`show log | include icens` lists only this triage's own
  `show license` commands; `show log permanent | include icens` empty), so the licence was installed **before** that
  reboot: **the unit has already booted with FULL; no reload is needed for the licence to take effect.**
- `show license` (Board region Global): index 1 **Base License** (Full, issued 26-Oct-2026: BASE-AW+, BW-UNLIMITED,
  IPv6Basic, L3-FORWARDING, LAG-FULL, MLDSnoop, No-License-Lock, RADIUS-100, RIP, UFO, VCStack); index 2 **ACCESS**
  (ATI-EMEA, 16-Oct-2009); index 3 **FULL** (ATL-NZ Internal Use Only, Full, qty 1, issued 11-Feb-2019): 10G_SFP+, ACCESS,
  AMF-APP-PROXY, AMF-CONTROL-10/30/60, AMF-GUEST, AMF-INTERMEDIATE, **AMF-MASTER-120/20/250/40/80**, AMF-Starter,
  BASE-AW+, BGP-256/5K/64/FULL, BGP4+, BW-UNLIMITED, CFM, CPU-L3-Route, Continuous POE, DPI_RMT_CLIENT, EPSR-MASTER,
  FIREWALL, G8032, IPv6-6to4, IPv6Basic, ISIS-FULL, L3-FORWARDING, **L3-MC-ROUTE**, LAG-FULL, LICD Dev, MACSEC,
  MLDSnoop, MODBUS, MRP, No-License-Lock, No-Tier-Check, OSPF-128/16/256/64/FULL, OSPFv3-256/64/FULL, OpenFlow,
  **PIM, PIM-100, PIM-1024, PIM6**, POE++, PROFINET, PTP-BOUND/ORD/TRANS, RADIUS-100/3/FULL, RIP, RIP-16/256, RIPNG,
  RIPNG-256, SES, SFP+, STATIC-128, UDLD, UFO, VCS_Mixed-Mode, VCStack, VLAN-TRANS-FULL/LITE, VPN, VRF-LITE-63/8/FULL,
  VRRP, VXLAN, VlanDT. "Release licenses on stack member 1:" has no rows (both `show license` and `brief`).
- `show license brief` → "Current enabled features": the same list as FULL (none reads pending/inactive), with
  `VRF-LITE-0` where `show license` lists `VRF-LITE-8` (noted, not relevant here).
- `show license external`: URL Filtering, Application Control, Web Control, IP Reputation … "Currently licensed: Yes";
  AMF Intermediate Node "Currently licensed: Yes".
- **The FULL licence is the generic internal all-features licence** (it lists POE++, 10G_SFP+, FIREWALL, VPN, which this
  unit has no hardware or image for). A listed feature therefore says nothing about platform support: the parser is the test.
- Raw: dev-host scratchpad of this triage (`u1-lic.out`, `u1-qexec.out`, `u1-qcfg.out`, `u1-amf.out`) and the box
  transcript `/tmp/triage-0855/console-u1.log`.

### u1 parser checks, 09:05–09:08 (`qmark`, help only, self-test OK; nothing executed; console left at exec, then logged out)

| probe | 2026-10-27 (licensed, booted) | before (10-09/10-13) |
| --- | --- | --- |
| exec `show ip ?` | access-list dhcp dhcp-relay dns domain-list domain-name flooding-nexthops forwarding igmp interface irdp name-server prefix-list protocols resolve-via-default rip route sockets source traffic — **no mroute, no pim, no multicast** | same gap |
| `show ip mroute ?` / `show ip pim ?` / `show ip multicast ?` | `% Unrecognized command` ×3 | absent |
| config `ip ?` | dhcp … igmp … prefix-list radius resolve-via-default route source tacacs tcp … — **no multicast-routing, mroute, pim** | same gap |
| config `ip multicast-routing ?` / `ip mroute ?` / `ip pim ?` / `ip multicast ?` | `% Unrecognized command` ×4 | absent |
| exec `platform ?` | bist, command, eyescan, led, memory, portstorm, prbs | offered then too |
| `platform bist ?` → `instance ?` | `instance` → `<0-127>`, `all` | same |
| `platform prbs ?` | `all-fabric`, `internal-fabric` | same (the case's `all` does not exist; 10-09 used `all-fabric`) |
| config `atmf ?` | includes `master`, `backup`, `recovery-server`, `controller` | (master refused/unlicensed 10-09) |
| config `atmf master ?` | `<cr>` | — |
| config `atmf backup ?` → `server ?` | HH:MM, area-masters, bandwidth, default, enable, guests, redundancy, server → `id` | — |

Read-only `show` (ckcon, 09:07): `show atmf` → Status Enabled, Network Name Enterprise-AMF, Node x230-28GSv2, **Role Member**,
Current ATMF Nodes 1 (the 4050 is not in the AMF network now). `show atmf backup` → `% Error: Device configuration does not
support ATMF backup commands.` (expected on a non-master). `show atmf provision nodes` → `Backup Media .......... NONE`.
`show file systems`: flash 95.6M / 60.6M free; debug; nvs; **`usb:` usbstick dynamic Avail N**; `fserver:` dynamic network
Avail N; no `card:`. `show interface brief`: **admin down = port1.0.7, port1.0.16, port1.0.26 only** (all others admin up;
running: 1.0.1, 1.0.2, 1.0.3, 1.0.10; vlan1/103/1000 running). Saved shut state held through the 08:48 reboot.

### Summary (STANDING-ORDERS §3): 3 runnable now / 1 blocked by topology / 0 blocked otherwise

**Runnable now, in queue order:**
1. **T31863 BIST** (group 1). Licence: BIST is not a licensed feature (none in the list); the parser offers
   `platform bist instance <0-127>|all` exactly as on 10-09, when it refused at run time (`% BIST test not supported.`).
   Build is now -20261019-75 (10-09 was -20261008-57). Whether it still refuses is the run's measurement. No licence reload
   needed. The case itself says restart the DUT before and after (reloads allowed; ~165 s each, boots `tb470-bench.cfg`).
2. **T31866 PRBS** (group 1). Same: not a licensed feature; parser offers `all-fabric|internal-fabric` (the case's
   `platform prbs all duration 20` has no `all` keyword; 10-09 mapped it to `all-fabric`). Group 1 est. ~30 min with the
   two restarts.
3. **T30403 static mroutes** (group 2) — **runnable only as a re-grade**. The licence now carries PIM, PIM-100, PIM-1024,
   PIM6 and L3-MC-ROUTE, but on a boot that already had the licence, every multicast-routing command is still absent from
   the parser (table above). Expect **UNSUPPORTED** again, now with the licence as evidence that the gap is the
   platform/build, not licensing (the x230v2 is x220 hardware, platforms/x230v2-28GS.md §1). A further reload is not
   expected to change it (the unit booted 08:48 with FULL installed); if the Test Engineer wants that excluded, one reload
   + the same `qmark` set is ~5 min. Est. ~10 min, no config change. A TPS/Feature-Overview check of x230v2 multicast
   routing support belongs in the run (memory `review-feature-docs-before-testing`: TPS Yes + DUT lacks it = a finding).

**Blocked by topology:**
4. **T28218 ATMF provisioning, x230 as master** (group 3). The licence blocker is GONE (AMF-MASTER-20/40/80/120/250
   present, `atmf master` offered). The new blocker is **backup media**: provisioning's `create` makes the node directory
   on the master's backup media, and the x230 has none — `usb:` Avail N, no SD/`card:`, `show atmf provision nodes` →
   `Backup Media .......... NONE`. **Exact change:** plug a USB stick (FAT32, ≥ 1 GB; the file-set needs the 36.7 MB x230
   `.rel` + `tb470-bench.cfg`) into the USB port of **swi_f, the x230v2-28GS on tb470 console u1** (S/N A10783G262900002),
   then a re-triage reads `show file systems` → `usb: … Y`. Moving the 4050's stick across also works but leaves the
   4050 (swi_e) without its USB (it holds `usb:/atmf/…` trees from 09-21 and 10-21): Test Engineer's choice.
   **Alternative (a decision, not a cable):** a remote backup server — `atmf backup server id 1 <tb470 address on
   eth1/eth2> username <u> path <dir>` (the parser offers `atmf backup server id`; `fserver:` exists, Avail N). It needs
   an ssh account + directory on tb470 for the x230 and host-key trust (root / device trust → the Test Engineer), and it is
   unmeasured whether AMF provisioning accepts a remote server as media (memory `ie520-master-ignores-remote-backup-server`:
   an IE520 master accepted the server and never mounted it). Recommend the USB stick.
   Once unblocked, the 10-21 recipe applies with u1 as the master: run-only `atmf master` on u1 (network-name Enterprise-AMF,
   mgmt vlan 3500, domain vlan 1234 are already the x230's baseline), `show atmf` Role Master, `show atmf backup` →
   `Backup Media: USB`; steps `atmf provision node future_node` → `create` → `locate` → `copy flash:/x230v2_28GS-awplus_main-20261019-75.rel ./…` →
   `configure boot system …` → `copy flash:/tb470-bench.cfg ./…` → `configure boot config tb470-bench.cfg` → `exit` →
   `show atmf provision nodes`; restore: provision `delete`, `rmdir usb:/atmf/Enterprise-AMF/nodes/future_node`,
   `no atmf master`; a reload if master residue shows (allowed). Est. ~45 min.

**Blocked otherwise:** none.
