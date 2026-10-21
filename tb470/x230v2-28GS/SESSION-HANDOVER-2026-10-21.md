# Session handover — 2026-10-21 (08:20–12:3x NZDT): x230v2-28GS ATMF campaign (2 cases, 2 PASS), final logs created, bench whole

Session `db650952…` (VS Code, `device-testing-e5`, re-attached after a 09:33 process restart as `device-testing-d7`), Test
Engineer terrenceb@terrenceb-dl. One `/test-mode` campaign on tb470 (this session = sentinel, one bench-runner subagent as
tester), then `/create-logs`, then this wrap. A parallel session worked on tb101 all day; it is out of this session's scope.

## Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u0,u1 (u0 = AR4050S swi_e, the AMF master; u1 = x230v2-28GS swi_f, the DUT). No other console exists on tb470 today (u2-u9 absent).
PDU: 10.36.150.14, u0=3, u1=4 (per tb470.static, applied by the Test Engineer 2026-10-21 08:3x)
Constraints: "Reloads allowed now" (office hours); sentinel stand-down "When the run ends"; host "Stay in VS Code"; the 4050 is the ATMF master; the parallel session on tb101 is out of scope.

## TL;DR
- **Campaign 2026-10-21T0835 complete: T46810 ATMF Backup PASS (reading confirmed by the Test Engineer, 2026-10-21 afternoon), T28218 ATMF provisioning PASS.**
  Final logs CREATED (`04bc3ce` after the rebase; was `297190c`): [atmf-2026-10-21T0835/README.md](atmf-2026-10-21T0835/README.md). No `work/` remains.
- **Bench is whole.** Wrap probe `2026-10-20T231844Z` (12:18 NZDT, u0/u1) **MATCH** against the template the Test Engineer
  applied at 08:3x (`backups/2026-10-20T192905Z.*`); no advisories. Both units at exec, logged out of nothing (consoles
  closed after `terminal no monitor`). No reload, no PDU cycle, no `write` by any case; both running-configs byte-identical
  to the pre-run capture; AMF is off on the 4050 again; the x230's saved config was never changed.
- **No new `Unexpected System reboot` on either unit all day** (4050 newest 2026-10-15 15:01:55; x230 newest 2026-10-19
  22:30:23 on its UTC clock, your own unplugging). The Test Engineer asked to be told of any new one: there was none.
- **Sentinel stood down** at 09:5x (Monitor stopped, both cron jobs deleted, no stray `sentinel.sh`, no tester subagent running).
- **Committed, NOT pushed** (push is yours). Git state at the wrap: see "Git" below.

## Bench state at the wrap (read 12:17–12:18 on u0/u1, then probe 231844Z)
| unit | console | build | boot image / config | AMF | notes |
| --- | --- | --- | --- | --- | --- |
| AR4050S swi_e S/N A10401G214000005 | u0, 115200, outlet 3 | awplus_main-20261008-57, bootloader 5.2.8 | `flash:/AR4050S-awplus_main-20261008-57.rel (file exists)` / `flash:/tb470-bench.cfg (file exists)` | Network Name Not Set, Role Member, 1 node; `show atmf backup` → `% Error: ATMF is not configured.`; no `atmf` line in running-config | up 5 d 21 h; flash 3.4 GB free; USB stick present: `usb:/atmf/Enterprise-AMF/` (empty housekeeping dirs from this run, see OPEN) beside the pre-existing Sep-21 `usb:/atmf/tb470/` |
| x230v2-28GS swi_f S/N A10783G262900002 | u1, 115200, outlet 4 | awplus_main-20261019-75, bootloader 6.2.40 | `flash:/x230v2_28GS-awplus_main-20261019-75.rel (file exists)` / `flash:/tb470-bench.cfg (file exists)` | Enterprise-AMF, Member, 1 node; `show atmf links` 1.0.1 Downlink Up **Incompatible** 4050-5g 0 Blocking (dynamic: the 4050 has no network name; before the run it read OneWay to a stale "A2-core-x950") | up 1 d 0 h; flash 60.6 MB free; exception log None; port1.0.7 `shutdown` (saved, as before) |

- Link: 4050 port1.0.2 (access VLAN 10) <-> x230 port1.0.1 (trunk, `switchport atmf-link`, saved baseline), LLDP both ends. The only link.
- tb470: eth1/eth2/eth3 carrier DOWN all day (no host link to either unit); no host change by this session (no IPs, routes, ethtool).
  Scratch `/tmp/orient1021/` and `/tmp/atmf-0835/` are tmpfs (console transcripts of the run live there until the box reboots).
- Stale lock files `/run/lock/LCK..u0` and `LCK..u1` (2026-10-20 08:44, PIDs 2717/2735 dead, no fuser holder) are still on tb470:
  `tools/tb precheck` reports FOUND on them every time. They are yours; the two sessions today proceeded over them on your word.
- Clocks: the x230 logs in UTC (13 h behind the 4050's NZDT); both units within 15 s of the box.

Verify in one go (repo root):
```
tools/tb precheck tb470 0,1; tools/tb probe tb470 --consoles 0,1 --baud 115200 --no-prompt --pdu 10.36.150.14 --outlet u0=3 --outlet u1=4 --name u0=swi_e --name u1=swi_f
tools/tb ckcon tb470 wrap1021 u0 115200 "show atmf" "show boot" "show reboot history"      # after: tools/tb scratch tb470 wrap1021
tools/tb ckcon tb470 wrap1021 u1 115200 "show atmf" "show atmf links" "show boot" "show reboot history"
```

## What was accomplished
1. **Orient (08:2x):** tb470's consoles had moved (u7/u8 → u0/u1; u2-u9 absent); probe MISMATCH on exactly that; the Test
   Engineer ran `apply` (08:29, `backups/2026-10-20T192905Z.*`) and the next probe read MATCH. The brief wrongly said there was no
   platform file for the x230v2-28GS: `platforms/x230v2-28GS.md` has existed since 10-09 (corrected in the session).
   Before the Test Engineer narrowed the scope to tb470, this session also ran one probe on tb101 (MATCH, read-only effect).
2. **Campaign 2026-10-21T0835** ([CAMPAIGN-QUEUE-2026-10-21T0835.md](CAMPAIGN-QUEUE-2026-10-21T0835.md)): setup questions,
   queue file, sentinel armed, TRIAGE (08:37–08:47: 1 runnable / 0 topology / 1 blocked otherwise, three questions), the
   Test Engineer's answers (09:0x), RUN (09:19–09:32: T46810 then T28218 in one AMF session), group restore (09:32–09:37,
   finished after the restart), hand-back 09:39.
3. **Session restart at 09:33** (the VS Code process died mid-restore). The tester subagent was resumed by name with its
   context intact; the device had already taken every restore command (transcript), so only the verification was redone.
4. **`/create-logs` (10:3x–10:4x, `04bc3ce`, was `297190c`):** two final logs with `.cfg` files, group README, per-case and group reviews.
5. **Records at this wrap:** this handover; two rows added to `platforms/x230v2-28GS.md`; memory `x230v2-atmf-campaign-2026-10-21`.

## Results (queue `## Results`) — final logs CREATED, commit 04bc3ce (was 297190c before the rebase)
| case | verdict | run label | one line |
| --- | --- | --- | --- |
| T46810 ATMF Backup | PASS (tester; reading **confirmed** by the Test Engineer 2026-10-21 afternoon: ck.db has no steps) | clean | 4050 master backed up the x230 member to its USB in 32 s, status Good; the .rel (36,747,551 B), tb470-bench.cfg (1914 B) and default.cfg on usb: at flash sizes |
| T28218 ATMF provisioning | PASS (tester) | clean | all 5 steps on the 4050: `future_node` created on usb:, the x230's .rel + tb470-bench.cfg copied from its backup and set as boot system/config, `show atmf provision nodes` matches the expected block field for field (USB media, not a file server) |

Both runs clean: no reload, no PDU cycle, no `write`, running-config diffs empty after the restore, no new reboot.

## Findings
**Measured (2026-10-21, tb470, 4050 awplus_main-20261008-57 as master, x230v2 awplus_main-20261019-75 as member):**
- The AR4050S is a working AMF master with the USB stick as backup media (`Backup Media .......... USB`); the x230 joined
  within 1–2 s of `switchport atmf-link` on the 4050 (log `x230-28GSv2 has joined. 2 members in total.`). `atmf management vlan`
  / `atmf domain vlan` took effect without a reboot.
- `atmf backup now <node>` returns at once (`Backup successfully initiated`); the job ran 32 s for 36.7 MB; poll
  `show atmf backup` for the node row `Yes Yes Good`.
- Provision-mode `delete` removes `<node>/flash/` but leaves an EMPTY `usb:/atmf/<net>/nodes/<node>/` directory; `rmdir` clears it.
- The x230's `show cpu` prints busy averages (1 s / 20 s / 60 s), not an idle figure.
- `tools/console.py` now recognises the `host[atmf-provision]#` prompt and leaves it with `exit`; `tools/tb` forwards `CKTO` (b29652b).
**Inferred:** T46810's folder ("ER-7243 Increase the number of managed devices by AMF Plus of ARX200S-GTX") suggests a scale
test that this bench cannot run; the functional reading used here is the sentinel's, confirmed by the Test Engineer only as
"the backup should be with the provisioned node".

## OPEN (Test Engineer)
1. ~~**T46810's definition.**~~ CLOSED 2026-10-21 afternoon: the Test Engineer confirmed the functional reading (member backed up to the master's USB media); the PASS stands.
2. ~~**`usb:/atmf/Enterprise-AMF/`**~~ CLOSED 2026-10-21 afternoon: the Test Engineer said KEEP the five empty housekeeping
   directories (info, logs, nodes, areas, guests) on the 4050's stick beside `usb:/atmf/tb470/`. They stay; nothing to remove.
3. ~~**Stale lock files**~~ CLOSED 2026-10-21 afternoon: removed on the Test Engineer's instruction (terrenceb-owned, PIDs dead); `tools/tb precheck tb470 0,1` reads CLEAR.
4. **Option (c)**, the real provisioning of the x230 (`atmf cleanup` + recovery from `future_node`), was out of scope and not run.
   The recipe and its risks (no TFTP fallback: eth1/2/3 down) are in the queue's Triage section if it is ever wanted.
5. **Git:** see below.

## Next steps
1. Push (`git push origin main`).
2. Decide OPEN 1–3.

## Recipes
- **AMF setup / restore for this pair** (run-only, no `write`): the queue file's "Run, group 1" recipe and its "After the group"
  summary. Setup on the 4050: `atmf network-name Enterprise-AMF` / `atmf management vlan 3500` / `atmf domain vlan 1234` /
  `atmf master` / `interface port1.0.2` / `switchport mode trunk` / `switchport atmf-link`. Restore: `atmf provision node <n>` /
  `delete` / `exit`; `atmf backup delete <node>`; `rmdir usb:/atmf/Enterprise-AMF/nodes/<n>`; `interface port1.0.2` /
  `no switchport atmf-link` / `switchport mode access` / `switchport access vlan 10`; `no atmf master` / `no atmf network-name` /
  `no atmf management vlan` / `no atmf domain vlan`.
- **Resuming a tester after a sentinel restart:** `SendMessage` the subagent by its id with what the queue and the box
  transcripts show completed; its context survives the parent's restart (worked 09:34).

## Git
Fetched 12:19: local main was 5 ahead / 4 behind origin/main (the behind side = tb277 and bench_probe.py work). At 12:3x,
with both peer sessions holding, `git rebase --autostash origin/main` finished with no conflicts; the dirty bench-setup files
(your 08:29 apply's `.current` files and `backups/2026-10-20T192905Z.*`) were carried across uncommitted. Hashes changed in the
rebase: create-logs `297190c` is now `04bc3ce`; this wrap's records commit is the one that follows it. Final state: 6 to push,
0 behind. Push is yours: `git push origin main`.

## Pointers
- Queue and results: [CAMPAIGN-QUEUE-2026-10-21T0835.md](CAMPAIGN-QUEUE-2026-10-21T0835.md)
- Final logs and reviews: [atmf-2026-10-21T0835/](atmf-2026-10-21T0835/) (README, REVIEW.md)
- Bench: [../../bench-setup/bench-state.md](../../bench-setup/bench-state.md) (stamp 2026-10-20T231844Z)
- Platform facts: [../../platforms/x230v2-28GS.md](../../platforms/x230v2-28GS.md)
- Previous handover: [SESSION-HANDOVER-2026-10-15.md](SESSION-HANDOVER-2026-10-15.md)
