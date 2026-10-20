# Campaign queue — tb470, x230v2-28GS as the DUT, 2 AWPTCM ATMF cases (4050 = AMF master), from 2026-10-21 08:35 NZDT

The ask, Test Engineer 2026-10-21 08:3x (after `/orient-dt`):
*"today we will be running two ATMF tests, with the 4050 being the ATMF master."* Screenshot: AWPTCM-T28218 (1.0)
ATMF provisioning, AWPTCM-T46810 (1.0) ATMF Backup. *"The parallel session will remain on tb101, that is out of our
scope. we will be on tb470 today running those x230v2 tests."*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-21 08:35 NZDT (Test Engineer's answers to the setup questions):
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u0,u1 (u0 = AR4050S swi_e, the AMF master; u1 = x230v2-28GS swi_f, the DUT). No other console exists on tb470 today (u2-u9 absent).
PDU: 10.36.150.14, u0=3, u1=4 (per tb470.static, applied by the Test Engineer 2026-10-21 08:3x)
Constraints: "Reloads allowed now" (option text: "The two cases may reload / power-cycle the x230 and the 4050 as their steps need, during office hours."). Sentinel stand-down: "When the run ends". Host: "Stay in VS Code" (risk accepted). The 4050 is the ATMF master (Test Engineer). The parallel session on tb101 is out of scope.

Test Engineer's rulings carried into this campaign (2026-10-21):
- The `Unexpected System reboot` entries on the x230 dated 2026-10-19/20 are his unplugging ("i unplugged it a few times"). *"if there are any more, notify me."*

**Test Engineer's answers to the triage, 2026-10-21 09:0x (word for word):**
- Q1 T46810 definition: *"the backup should be with the provisioned node."* (sentinel's reading, relayed to the tester as an assumption: T46810 = the x230 joins the 4050's AMF network and is backed up to the master's USB media; that backup is the file-set T28218's provisioned node is built from; backup first, one AMF session.)
- Q2 T28218 file-set: "(b1) x230's own files via backup (Recommended)"
- Q3 network: "Yes, Enterprise-AMF, omit device (Recommended)"
- Go: "Proceed (Recommended)"

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  The final log is made ONLY by `/create-logs`, on the Test Engineer's request.
- `STANDING-ORDERS.md` applies. Reloads and PDU cycles of u0/u1 are allowed within a test; a systematic failure stops the run.
- **Only u0 and u1 are touched.** Nothing else is on tb470's consoles today.
- Case texts: Ask-CK `ck.db` table `zephyr_cases` (read-only: `sqlite3 'file:<path>/ck.db?mode=ro'`), key `AWPTCM-T<n>`.
  T28218 has 5 steps (provision node "future_node", create its directory on the backup media, copy + set the release
  file, copy + set the config file, `show atmf provision nodes`). **T46810 has NO steps and no objective in ck.db**
  (one empty step; folder "/5.5.5-2/Gomboc/Project:ER-7243 ..."): triage reports it as blocked otherwise unless the
  Test Engineer defines what to run.
- MANUAL-ONLY.md (repo root) is read at triage.
- Platform traps: [platforms/x230v2-28GS.md](../../platforms/x230v2-28GS.md). AMF memories: `ie520-master-ignores-remote-backup-server`
  (the AR4050S's FULL licence carries AMF-MASTER; `atmf master` took on it 2026-09-23; the x230-10GP could not be master),
  `atmf-recovery-residue-and-reboots`. Prior ATMF evidence on tb470: `IE520/atmf-2026-09-21/` (README, TOPOLOGY, 38479 =
  provisioning capture) and `IE520/atmf-2026-09-23/`.

## Bench at queue creation (2026-10-21 08:27-08:33, probe `2026-10-20T192716Z`, MATCH after the Test Engineer's apply)

- u0 AR4050S swi_e S/N A10401G214000005, awplus_main-20261008-57, bootloader 5.2.8, boots `flash:/AR4050S-awplus_main-20261008-57.rel`
  + `flash:/tb470-bench.cfg`; flash 3.4 GB free; **a USB stick is mounted (`usb:` 28.9G, Avail Y)** = candidate AMF backup media; uptime 5 d 17 h.
- u1 x230v2-28GS swi_f S/N A10783G262900002, awplus_main-20261019-75, bootloader 6.2.40, boots `flash:/x230v2_28GS-awplus_main-20261019-75.rel`
  + `flash:/tb470-bench.cfg` (saved 10-19 22:31 on its clock); flash 60.5 MB free (one 36.7 MB .rel); no USB; uptime 20 h 58 m.
- Link swi_e port1.0.2 <-> swi_f port1.0.1 (LLDP both ends). tb470 eth1/eth2/eth3 all carrier DOWN. Lock files `LCK..u0`/`LCK..u1`
  on tb470 are stale (PIDs dead, 2026-10-20 08:44); fuser shows no holder.
- Clocks: the x230 reads 13 h behind the 4050 (UTC-like); its `show reboot history` is in that clock.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | ATMF: T28218 (provisioning), T46810 (backup) | tb470/x230v2-28GS/atmf-2026-10-21T0835/ | DONE 09:37 (T46810 PASS [Assumed], T28218 PASS; restored, probe 203651Z MATCH) | manual CLI; 4050 (u0) = AMF master, x230 (u1) = AMF member/DUT; backup media = the USB stick in the 4050 (`usb:`, 29 GB free, measured 08:41); T46810 has no steps in ck.db: waits for the Test Engineer's definition (proposal in the Triage section, Q1); T28218 waits only for Q2 (file-set) and Q3 (network name / `device`) if he wants other than the defaults stated there |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| T46810 | ATMF Backup | atmf-2026-10-21T0835 | PASS | Assumed: x230 member backed up by the 4050 master to its USB media (ck.db has no steps); `atmf backup now x230-28GSv2` -> Good in 32 s, the x230's .rel (36,747,551 B) + tb470-bench.cfg (1914 B) + default.cfg on usb:/atmf/Enterprise-AMF/nodes/x230-28GSv2/flash/ at flash sizes; no health change, no new Unexpected System reboot on either unit | atmf-2026-10-21T0835/46810/work/run1.log | tester |
| T28218 | ATMF provisioning | atmf-2026-10-21T0835 | PASS | all 5 steps as written on the 4050 master: future_node created on usb:, the x230's .rel (36,747,551 B) and tb470-bench.cfg (1914 B) copied from its AMF backup and set as boot system/config, `show atmf provision nodes` matches the expected block field for field (media USB instead of a file server); no health change, no new Unexpected System reboot | atmf-2026-10-21T0835/28218/work/run1.log | tester |

## Issues


## Triage 2026-10-21 08:45 NZDT (bench-runner, TRIAGE dispatch from the /test-mode sentinel)

**Gate (all read-only; no device state changed, no case run):**
- `tools/tb precheck tb470 0,1` → exit 5 with exactly the two known stale lock files (`/run/lock/LCK..u0` pid 2717,
  `LCK..u1` pid 2735, both stale, no fuser holder) that the Test Engineer chose to proceed over → treated as CLEAR.
  No other holder, no minicom/screen/tmux, no python script; only the Test Engineer's own shells are logged in.
- `tools/tb peek` u0/u1 at 115200: both at a privileged exec prompt (`4050-5g#`, `x230-28GSv2#`), nothing parked.
- `tools/tb template tb470`: `/nfsHome` mounted, `/home/st-art/st-art/configs/tb470.setup` present (08:29, 633 B).
- `tools/tb probe tb470 --consoles 0,1 --baud 115200 --no-prompt --pdu 10.36.150.14 --outlet u0=3 --outlet u1=4
  --name u0=swi_e --name u1=swi_f` → **exit 0 MATCH**, capture `bench-setup/captures/2026-10-20T194059Z/` (box clock
  is UTC; = 08:40 NZDT). Boot pointers unchanged = the baseline (gate 7): u0 `flash:/AR4050S-awplus_main-20261008-57.rel`
  + `flash:/tb470-bench.cfg`; u1 `flash:/x230v2_28GS-awplus_main-20261019-75.rel` + `flash:/tb470-bench.cfg`.
  Running-configs byte-identical to the 08:27 capture (`2026-10-20T192716Z`) on both units.
- Reboot-history watch (Test Engineer's standing request), read 08:41 with `show reboot history`: **no new
  `Unexpected System reboot` on either unit.** 4050 newest = 2026-10-15 15:01:55 (uptime 5 d 17 h agrees). x230 newest
  (top of its list) = 2026-10-19 22:30:23 on its own clock (13 h behind the 4050; uptime ≈ 21 h agrees); the entries
  below it dated 2026-10-20 07:26:02 / 08:05:54 are OLDER boots written while its clock read differently (the list is
  newest-first, not date-sorted) and are the ones already ruled "his unplugging". Baseline for the run = these lists.
- Session facts vs bench: no disagreement (names, outlets, consoles, baud all as the facts say).

**Measured AMF state (read-only `show`s, 08:41; transcripts `/tmp/atmf-0835/console-u0.log`, `console-u1.log`):**
- **u0 AR4050S (`4050-5g`)**: `show atmf` → ATMF Enabled, Network Name **Not Set**, Role Member, node name
  `host_0000_cd40_0394`; `show atmf backup` → `% Error: ATMF is not configured.` Licence (`show license brief`):
  FULL + AT-FL-AR4-AM20, enabled features include **AMF-MASTER-20/40/80/120/250**, AMF-APP-PROXY → can be master (as on
  2026-09-23). `dir usb:` → the stick is readable: `atmf/` (Sep 21 2026, the IE520-stk campaign's backup tree for
  network `tb470`), three IE520 `.rel` and one `.kwb` (~124 MB); `show file systems` on 10-20 said 28.9 G, Avail Y.
  `dir flash:` → `tb470-bench.cfg` (1814 B), `AR4050S-awplus_main-20261008-57.rel` (67.7 MB), `default.cfg`,
  `gui-userdata/`; 3.4 GB free. **No `atmf` line in its running-config** (no leftovers).
- **u1 x230v2-28GS (`x230-28GSv2`)**: its baseline `tb470-bench.cfg` already carries AMF config: `atmf network-name
  Enterprise-AMF`, `atmf management vlan 3500`, `atmf domain vlan 1234`, `atmf group network-A`, and `port1.0.1`
  (`switchport mode trunk`) is `switchport atmf-link`. `show atmf` → Enabled, network Enterprise-AMF, Role Member,
  Current ATMF Nodes 1. `show atmf links` → `1.0.1 Downlink Up OneWay A2-core-x950 0 Blocking`: a **stale adjacency
  name from the network it came from** (nothing on tb470 is called that); the link hears no valid AMF peer. `dir flash:`
  → `x230v2_28GS-awplus_main-20261019-75.rel` (36,747,551 B), `tb470-bench.cfg` (1914 B), `default.cfg`, `burnin.log`,
  `log/`; **95.6 MB flash, 60.5 MB free**; `usb:` Avail **N** (no stick); no `fserver`.
- **Cabling now (capture `194059Z`, same as 08:27):** ONE link, 4050 `port1.0.2` (access VLAN 10, up, 1000/full) <->
  x230 `port1.0.1` (trunk, atmf-link). LLDP both ends. 4050 `port1.0.1`, `.5`, `.8` notconnect; x230 `port1.0.2`, `.5`,
  `.8` notconnect (`not present`: no SFP). tb470 eth1/2/3 carrier DOWN → **no host link to either unit, so no TFTP/SCP
  path exists today** (the 4050's vlan1 10.38.215.70/27 would reach eth3 if eth3 were cabled; it is not).
  The 10-13 handover's second lead (x230 1.0.8 <-> 4050 1.0.5, VLAN 108) is **not** cabled now.

### Summary (STANDING-ORDERS §3): 1 runnable now / 0 blocked by topology / 1 blocked otherwise

**Runnable now (queue order): T28218 ATMF provisioning** — as written (5 steps), with the defaults below; nothing
needs cabling, a licence, or a second unit. **MANUAL-ONLY.md: neither case is listed and neither has a person-needed
step; no row added** (the only person-needed item below is an *alternative* file-transfer route, not a case step).

**Blocked otherwise: T46810 ATMF Backup** — ck.db holds ONE empty step, no objective, no precondition (folder
`/5.5.5-2/Gomboc/Project:ER-7243 Increase the number of managed devices by AMF Plus of ARX200S-GTX`, i.e. an
AMF-Plus scale item for an ARX200S-GTX). There is nothing to grade against. **Q1 for the Test Engineer** — proposed
reading, as a question not a decision: *"4050 = AMF master with the USB stick as backup media; the x230 joins as the one
member over the existing link; `atmf backup now` (and/or the scheduled `atmf backup 03:00`), then `show atmf backup`
→ status Good, `show atmf backup` / `dir usb:/atmf/Enterprise-AMF/nodes/x230-28GSv2/flash/` lists the x230's `.rel`
(36,747,551 B) and `tb470-bench.cfg` at their flash sizes; optionally `atmf backup delete x230-28GSv2` and a second
backup; `show atmf backup` Node table `In ATMF / On Media / Status`."* The ER-7243 *scale* reading (many managed
devices) is impossible on this bench (one member) and needs an ARX200S-GTX, which is not here. If Q1 is answered
"yes, the functional reading", T46810 becomes runnable with the same setup as T28218 and SHOULD RUN FIRST (its backup
also supplies T28218's x230 file-set, Q2b).

### T28218 — what it needs, exactly

**The case text** (ck.db, 5 steps): (1) `atmf provision node future_node` [optionally `device x530`]; (2) `create`
("an empty directory on the backup media"); (3) copy + `configure boot system <rel>`; (4) copy + `configure boot
config <cfg>`; (5) `show atmf provision nodes` — expected block names a Node, Date, Provision Path, Current boot
image/config `(file exists)`. **It does not include `atmf cleanup` or the DUT actually booting the file-set** (those are
AWPTCM 38479's steps 3–6, PASSED 2026-09-21 with an x230-10GP). So, as written, T28218 runs **entirely on u0** and the
x230 is untouched.

**Setup (u0, run-only config, no `write`):** `atmf network-name Enterprise-AMF` (Q3), `atmf master`; verify
`show atmf` Role Master and `show atmf backup` → `Backup Media: USB (Total … Free …)` (AMF picks the USB stick as
default media; 38479 saw `usb:/atmf/<net>/nodes/<node>/flash/` as the Provision Path). Nothing is needed on u1 for
the as-written case. Est. 10 min.

**Steps (u0):** `atmf provision node future_node` → `create` → `locate` → `copy flash:<rel> ./<rel>` →
`configure boot system <rel>` → `copy flash:tb470-bench.cfg ./tb470-bench.cfg` → `configure boot config
tb470-bench.cfg` → `exit` → `show atmf provision nodes` (expect Node Name `future_node`, Provision Path
`usb:/atmf/Enterprise-AMF/nodes/future_node/flash/`, both boot entries `(file exists)`). Ordering traps from 38479 that
stop the case dead: `create` refuses while a BACKUP exists for the same node name (`future_node` is new, so not hit);
`configure boot …` refuses while that node name is a live member (not hit). Est. 10 min (the 67.7 MB `.rel` copy to USB
is the slow step).

**Q2 — which files are "the release file" and "the configuration file"?** The master's media has NO x230 release file
and there is no host link to fetch one. Defaults proposed:
- **(a) default, runnable now:** the 4050's own `flash:/AR4050S-awplus_main-20261008-57.rel` + `flash:/tb470-bench.cfg`.
  Satisfies every step literally (the case names no model; `device x530` is "optional"). The file-set is then NOT
  bootable by the x230 and must never be delivered to it (see (c)).
- **(b) the x230's own files**, the realistic file-set: needs them on the master's media first. Routes: (b1) the x230
  joins the AMF network and `atmf backup now x230-28GSv2` writes `usb:/atmf/Enterprise-AMF/nodes/x230-28GSv2/flash/`
  (= T46810's Q1 reading), then inside `locate`: `copy usb:/atmf/Enterprise-AMF/nodes/x230-28GSv2/flash/<rel> ./<rel>`
  and the same for `tb470-bench.cfg`; (b2) a person pulls the USB stick, drops `x230v2_28GS-awplus_main-20261019-75.rel`
  on it from a PC, replugs (person step; the file is on the x230's flash only, and in the build tree); (b3) a host link
  (bench-level: cable tb470 eth3 -> 4050 `port1.0.1` and give eth3 an address in 10.38.215.64/27; then the x230 would
  still need a path of its own) — not recommended. (b1) adds ~20 min (link ~1–2 min, backup ~3–5 min) and needs the
  u1-joins setup below.
- **(c) extend to the real provisioning of the x230** (38479 steps 3–6: `interface port1.0.2` / `atmf provision
  future_node` on the master with the port SHUT first (`% Cannot provision an active ATMF link`), `atmf cleanup` on the
  x230, `no shutdown`, watch recovery) — **only with (b)**, and the provisioned node name must then be the one the
  x230 will recover as (38479 used the DUT's real hostname, so `future_node` would have to become `x230-28GSv2`, which
  then collides with its own backup → `atmf backup delete x230-28GSv2` first, 38479 trap 2). What `atmf cleanup` does to
  the x230: it is an alias of `erase factory-default` (wiki) — erases NVS and all of flash EXCEPT the boot `.rel` + its
  release-setting file, licence files and the latest GUI file, then reboots. So `tb470-bench.cfg`, `default.cfg`,
  `burnin.log`, `log/` go; its 36.7 MB `.rel` stays. The x230 gets its config back ONLY from the master's file-set via
  recovery (`atmffsd: File recovery from master node succeeded. Node will now reboot` → second reboot, ~7–8 min end to
  end in 38479), and its `.rel` back the same way (a same-named `.rel` is already on flash; a differently named one
  needs 36.7 MB of the 60.5 MB free: fits). There is NO bootloader/TFTP fallback today (eth1/2/3 down). If recovery
  fails the x230 is left factory-default on its own `.rel` with no `tb470-bench.cfg`: the restore is then by hand from
  the capture (`bench-setup/captures/2026-10-20T194059Z/u1.show_running-config.txt`) + `copy running-config
  flash:/tb470-bench.cfg` + `boot config-file`. The x230's baseline `atmf network-name Enterprise-AMF` is in that cfg,
  so a successful recovery rejoins (unlike 38479). Est. +45–60 min, two x230 reboots (~165 s each) + recovery.
  **Recommendation: not in T28218's scope; run it only if the Test Engineer asks for it by name.**

**Q3 — AMF network name and `device`.** Default: `Enterprise-AMF` on the 4050, matching the x230's baseline, so the
x230's config is never touched (its `atmf management vlan 3500` / `atmf domain vlan 1234` are non-default: if the x230
must join (b1/c), the 4050 also gets `atmf management vlan 3500` + `atmf domain vlan 1234` — the wiki says these take
effect immediately, no reboot — and `interface port1.0.2` → `switchport mode trunk` + `switchport atmf-link`; VLAN 10
on that port (the `10.10.10.0/27` transit SVI) is run-only displaced and restored after). Any other name means
changing the x230's baseline config, which is a bench-level change. `device x530`: default = omit (an x530 file-set is
meaningless here; the real token for this DUT would be read from `show atmf nodes` once it joins).

**Restore recipe (u0; all within the test):** `atmf provision node future_node` → `delete` (the wiki lists `delete
(amf-provision)`; removes the node's directory from `usb:`); `atmf backup delete x230-28GSv2` if (b1) ran (the Sep-21
`usb:/atmf/tb470/` tree is pre-existing and stays); `no atmf master`, `no atmf network-name` (bare form only),
`no atmf management vlan`, `no atmf domain vlan`, `interface port1.0.2` → `no switchport atmf-link`, `switchport mode
access`, `switchport access vlan 10`; verify `show atmf` → Network Name Not Set, `show running-config` identical to
the capture, `show boot` unchanged. The wiki notes a node "retains its node depth of 0 until the network is rebooted"
after `no atmf master`: if any AMF residue shows, `reload` the 4050 (allowed; boots `tb470-bench.cfg`; est. 3–4 min).
After-run probe must be MATCH. Est. 10 min, 15 with a reload.

**Time estimate:** T28218 as written, default (a): **~45 min** (gate + pre-capture 5, setup 10, steps 10, show + `.cfg`
save + working log 10, restore + post-probe 10); no reload. With (b1): ~65 min. With (c): ~2 h, and reboot-heavy
(reloads allowed today per the constraints). T46810 under the Q1 reading: ~40 min on top of the shared setup, or ~25
min if run in the same AMF session as T28218(b1).

**Open questions carried to the Test Engineer (answers unblock; none blocks T28218 default (a)):**
Q1 T46810 definition (proposal above). Q2 T28218 file-set: (a) 4050's own files [default] / (b1) x230's via backup /
(c) also provision the x230 for real. Q3 network name `Enterprise-AMF` + omit `device` [default]. Also to note: the
run `.setup` is the deployed `tb470.setup` as is (it declares only u0/u1, the two units the run uses); no framework
script is involved (manual CLI via `tools/tb ckcon|cfg`), so pt_preflight does not apply.

## Run, group 1 (atmf-2026-10-21T0835) -- bench setup and restore recipe (bench-runner, written 09:2x before the first device change)

Gate: the 08:40 triage gate stands (precheck CLEAR bar the two known stale locks; peek u0/u1 at exec; `/nfsHome`
mounted; probe `2026-10-20T194059Z` MATCH; both units boot `flash:/tb470-bench.cfg`). Group baseline = that capture's
`u0/u1.show_running-config.txt` plus this group's own pre-run reads `46810/work/prerun-u0.out`, `prerun-u1.out`
(running-config, boot, system, health). Scratch on tb470: `/tmp/atmf-0835/` (transcripts `console-u0.log`,
`console-u1.log`). **No `write` on either unit. The x230 (u1) is never configured.** Run order: T46810, then T28218,
in ONE AMF session; restore ONCE after both. Tools: `tools/console.py` now matches the `[atmf-provision]#` prompt and
leaves it with `exit`; `tools/tb` forwards `CKTO` (committed with this recipe).

**Setup (u0 = 4050, running-config only), in this order:**
```
configure terminal
 atmf network-name Enterprise-AMF      <- the x230's baseline network
 atmf management vlan 3500             <- the x230's baseline values (defaults are 4092/4091); wiki: immediate, no reboot
 atmf domain vlan 1234
 atmf master                           <- AMF-MASTER-20..250 on the FULL licence (show license brief 08:41)
 interface port1.0.2                   <- the one lead to x230 port1.0.1 (trunk, atmf-link in the x230's baseline)
  switchport mode trunk
  switchport atmf-link
end
```
Gate before step 1 of T46810: `show atmf` Role Master / Network Enterprise-AMF; `show atmf nodes` lists
`x230-28GSv2` (poll up to 180 s); `show atmf backup` → `Backup Media: USB (Total … Free …)`.

**T46810 (assumed reading, Test Engineer: "the backup should be with the provisioned node"):** `atmf backup now
x230-28GSv2` → poll `show atmf backup` to status `Good` → `dir usb:/atmf/Enterprise-AMF/nodes/x230-28GSv2/flash/`
must list `x230v2_28GS-awplus_main-20261019-75.rel` (36,747,551 B) and `tb470-bench.cfg` (1914 B).
**T28218 (as written, 5 steps, `future_node`, no `device`):** `atmf provision node future_node` → `create` → `locate`
→ `copy usb:/atmf/Enterprise-AMF/nodes/x230-28GSv2/flash/x230v2_28GS-awplus_main-20261019-75.rel
./x230v2_28GS-awplus_main-20261019-75.rel` → `configure boot system x230v2_28GS-awplus_main-20261019-75.rel` →
`copy usb:/atmf/Enterprise-AMF/nodes/x230-28GSv2/flash/tb470-bench.cfg ./tb470-bench.cfg` → `configure boot config
tb470-bench.cfg` → `exit` → `show atmf provision nodes`. **Never** `atmf provision future_node` on an interface,
never `atmf cleanup` on the x230 (option (c), out of scope).

**Restore (u0), in this order, after both cases:**
```
atmf provision node future_node
 delete                               <- removes usb:/atmf/Enterprise-AMF/nodes/future_node/ (answer y if asked)
 exit
atmf backup delete x230-28GSv2        <- this run's backup only; the Sep-21 usb:/atmf/tb470/ tree STAYS
configure terminal
 interface port1.0.2
  no switchport atmf-link
  switchport mode access
  switchport access vlan 10
 no atmf master
 no atmf network-name                 <- bare form only
 no atmf management vlan
 no atmf domain vlan
end
```
Then `show atmf` → Network Name Not Set; `tools/rcdiff.py` of `show running-config` against the pre-run read, both
units (the x230's must be empty without any restore); `show boot` both `flash:/tb470-bench.cfg (file exists)`; health
reads; `terminal no monitor`, consoles at exec. If `show atmf` still shows master/depth residue: `reload` the 4050
(allowed today; boots tb470-bench.cfg, ~3-4 min; `write` never). Post-run probe with the triage facts must be MATCH.
**If the tester dies mid-group:** apply the restore block above on u0 exactly as written (the x230 needs nothing),
then rcdiff; a provisioned node or backup left on `usb:` is removed by the same two commands.

- **After the group (09:32-09:37):** RESTORE (group, after both cases; u0 only, the x230 untouched) -- 09:32:42-09:32:59 (tools/tb ckyn, the local process was killed at 09:33 by the sentinel restart, so work/restore-u0.out holds the 09:34 VERIFICATION reads instead; the applied commands are in /tmp/atmf-0835/console-u0.log): `atmf provision node future_node` / `delete` / `exit`; `atmf backup delete x230-28GSv2`; `configure terminal` / `interface port1.0.2` / `no switchport atmf-link` / `switchport mode access` / `switchport access vlan 10` / `no atmf master` / `no atmf network-name` / `no atmf management vlan` / `no atmf domain vlan` / `end`. No (y/n) prompt appeared. Verified 09:34-09:37 (28218/work/restore-u0.out, restore-u1.out, restore-u0-dir.out, restore-u0-rmdir.out, final-u*.out): u0 `show atmf` Network Name Not Set / Role Member / nodes 1, no `atmf` line in running-config, `show atmf backup` -> "% Error: ATMF is not configured."; usb:/atmf/Enterprise-AMF/nodes/ had lost x230-28GSv2/ (backup delete) and future_node/flash/ (provision delete) but kept an EMPTY future_node/ directory (dir 09:32:32 on the 4050 clock) -> `rmdir usb:/atmf/Enterprise-AMF/nodes/future_node` 09:36:28 "Successful operation"; nodes/ now empty. Left on the stick, deliberately: usb:/atmf/Enterprise-AMF/{info,logs,nodes,areas,guests}/ (AMF housekeeping dirs created 09:25, no node data) beside the pre-existing Sep-21 usb:/atmf/tb470/ tree. u1 (x230): `show atmf` Enterprise-AMF / Member / nodes 1 (back from 2), its baseline atmf lines + port1.0.1 atmf-link intact, `show atmf links` 1.0.1 Downlink Up Incompatible 4050-5g Blocking (dynamic state: the 4050 now has no network name; was OneWay/stale before the run). Running-config of BOTH units byte-identical to the pre-run capture 2026-10-20T194059Z (plain diff after dropping the header comment lines: u0 111/111, u1 116/116 lines, IDENTICAL; tools/rcdiff.py of prerun-u*.out vs restore-u*.out empty). `show boot` both: Current boot config flash:/tb470-bench.cfg (file exists). Reboot history after: 4050 newest 2026-10-15 15:01:55, x230 newest 2026-10-19 22:30:23 -> NO new Unexpected System reboot; x230 exception log None. Post-run probe `tools/tb probe tb470 --consoles 0,1 --baud 115200 --no-prompt --pdu 10.36.150.14 --outlet u0=3 --outlet u1=4 --name u0=swi_e --name u1=swi_f` exit 0 MATCH, capture 2026-10-20T203651Z (09:36 NZDT). Consoles: u0 closed 09:37:21 at `4050-5g#` after `terminal no monitor`; u1 closed 09:37:34 at `x230-28GSv2#` after `terminal no monitor` (transcript tails). No reload, no PDU cycle, no write anywhere.
