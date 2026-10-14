# Session handover — 2026-10-15: IE520 stack rebuilt as 1/2 on the Aug `-42` build; corosync flow-control defect NOT reproduced (2 rows)

Session `95bc60b5` (VS Code, desktop), 06:3x–10:4x NZDT. Oriented on u0/u1 (read-only, the x230 campaign's bench),
then worked the IE520 stack on **u4/u5** at the Test Engineer's direction. Wrapped ~10:40 on `/wrap-dt`.

## Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u4,u5 (the IE520 stack: u5 = S/N 264A23066, u4 = S/N 264A23052); u0,u1 read-only at orient only
PDU: 10.36.150.14; outlets u4=4, u5=5 (u0=1, u1=7 for the orient read)
Constraints: "Now" (office hours; ~1 Gb/s of DLF per host NIC accepted; no reloads beyond the one config reload already done)

## TL;DR
- **The IE520 stack is whole and deliberately OFF-TEMPLATE.** Members **1 = u5 (264A23066, Backup)** and
  **2 = u4 (264A23052, Active Master, `stack 2 priority 1`)**, both `tomahawk_ie520-20260825-42`, both bootloaders 9.2.0
  **forced to `flash:IE520-tb470.rel`** (the Test Engineer's Boot Menu procedure), two stack links up, `Normal operation`.
  It boots **`flash:/coro-repro.cfg`** = the defect reporter's config, adapted (hostname `IE520`, chassis-id 2662,
  `no lldp run`, sa1 on the empty cages port1.0.1/2.0.1, sa2 = port1.0.2+2.0.2 in VLAN 100 to the AR4050S, VLAN 100/200/1000,
  `vlan1000` 10.38.29.15/27; our `manager` user, `exec-timeout 0 0`, port1.0.13/2.0.13 in VLAN 100 as injection ports).
  **Running = startup.** The bench config for this stack is saved beside it: **`flash:/tb470-bench.cfg`** (IDs 1/2,
  written 07:17) — going back is `boot config-file flash:/tb470-bench.cfg` + one stack reload (OPEN 1).
- **Corosync `coroipcs … flow control` defect: NOT reproduced**, two rows, both PASS (not reproduced): line-rate DLF across
  the stack link (row 1) and CPU-bound traffic that loaded the master's CPU at the punt cap (row 2). Final logs NOT created.
- **bench-state.md and the deployed `tb470.setup` are STALE** (still the 1/3/4 stack on `-57`, x230 eth3 link): this session
  changed u4/u5 only and never had u2/u3, so no full probe/apply was possible (OPEN 2).
- **Outside our sessions:** on 10-14 (09:00–16:06 NZDT) someone reloaded the stack repeatedly and loaded
  `tomahawk_ie520-stephenh` (13 Oct dev build) as `IE520-tb470.rel`; `stephenh.cfg` appeared in both members' flash
  (left there). That build was deleted from both members today (the Test Engineer's "delete the old .rel" step).
- Sentinel stood down (Monitor stopped, cron deleted, no strays). Nothing of this session runs on tb470.
- Commits `9fbe1ed`…this wrap commit are **committed, NOT pushed** (push is yours: `git push origin main`).

## Bench state at the wrap (read 10:3x NZDT on u4; u0–u3 NOT read at the wrap)
| unit | console | stack | build | boot image / config | flash free | notes |
| --- | --- | --- | --- | --- | --- | --- |
| IE520 264A23066 | u5, 115200 | **ID 1**, Backup, Ready | `-42` (Aug 25) | `flash:/IE520-tb470.rel` (exists) / `flash:/coro-repro.cfg` (exists) | 58.9 MB | banner `IE520-1 login:`; only `.rel` in flash |
| IE520 264A23052 | u4, 115200 | **ID 2**, Active Master, Ready | `-42` | same | 64.4 MB | hostname `IE520` |

- Stack links port1.0.27↔2.0.28 and port1.0.28↔2.0.27 both up (10G, 0 drops). Virtual MAC `0000.cd37.0a66`.
- Live links (reporter's config): sa2 (port1.0.2+2.0.2, VLAN 100) to the AR4050S u1; **tb470 eth1 → port1.0.13** and
  **eth3 → port2.0.13** (the Test Engineer's recable this morning, so the **x230 u0 has lost its eth3 link**; the deployed
  `.setup` still says `tb-swi_f eth3-port1.0.5`); port2.0.26 (SX) to the IE520-sa u3, VLAN 1. sa1 down (empty cages).
- Reboot history: last entries 2026-10-14 19:00:16 UTC on both (= 08:00 NZDT, this session's coro-repro reload); nothing since.
- Exception logs None on both. Both consoles left logged in at `IE520#`, terminal monitor off.
- Host: eth1/eth2/eth3 carrier up, addresses unchanged, no ethtool/IP/route change by this session. Scratch `/tmp/orient1015`,
  `/tmp/coro1015` are tmpfs.
- Wrap probe (u4/u5, read-only, to scratch): `captures/2026-10-14T233024Z`, **MISMATCH (26)** = the expected off-template set
  (u0–u3 absent from a two-console read; `[stack] stk_a` bench `{swi_c, swi_d}` vs template `{swi_a, swi_c, swi_d}`; port
  renames), **no USER-CONFLICT**. bench-state.md was NOT rewritten (a u4/u5 probe writes a two-unit file).

Verify in one go (repo root):
```
tools/tb precheck tb470 4,5 && tools/tb ckcon tb470 w1015 u4 115200 "show stack" "show boot" "show system" "show exception log"
tools/tb probe tb470 --consoles 4,5 --no-prompt --read-only --pdu 10.36.150.14 --outlet u4=4,u5=5 --baud 115200 --out /tmp/w1015/bs.md
```
(`--read-only`: the reporter's config has `no lldp run`; a writing probe would switch it on. Never `apply` from a u4/u5 probe.)

## What was accomplished
1. **Orient** on u0/u1 (x230 + AR4050S): whole, no change. Ruling recorded: **a run's `.setup` declares only the units the run
   uses** (closes the 10-13 OPEN 6; STANDING-ORDERS §6, bench-runner gate 5; `9fbe1ed`).
2. **Stack checked, then rebuilt** at the Test Engineer's direction ("members 1 and 2, no provisioned members, the August 42
   build, second stack link added"): `stack 3 renumber 1` / `stack 4 renumber 2`, port3→port1 / port4→port2 config translated in
   place from the CLI, `no switch 3/4 provision`, `write` → `tb470-bench.cfg`; TFTP of `/tftproot/IE520-tb470.rel`
   (`IE520-tomahawk_ie520-20260825-42.rel`, 41,104,007 B, sha256 verified) to the master, `boot system` sync, Boot Menu park of
   both units on that file, `9` together; old `-57` and the stephenh `.rel` deleted from both members (`576a5f2`).
   - The first reload **split the stack**: member 4's bootloader was forced to `IE520-tb470.rel` = the stephenh build, so it
     came up `Disabled Master` / `Neighbor incompatible`. Fixed by parking it on `-57`, then the full image procedure.
     Recorded in `platforms/IE520.md` §2.
3. **Corosync check** after the rebuild: no `corosync`/`totem` lines in any log; the only `CMSG` errors were boot/reload-time
   `cmsg_sld`/`stkd` lines from 10-14 and the split reload.
4. **Reporter's config loaded** (adapted, decision "Adapted load"; boot config `coro-repro.cfg`, one reload, 07:59).
5. **Campaign `2026-10-15T0755`** (`/test-mode` shape A, this session = sentinel, bench-runner = tester), two rows — Results below.
6. **Tool fix:** `tools/tb killmine` now accepts the console tools `tb` itself launches (bare `python3 <tool>.py`, cwd
   `/tmp/<x>/tools`) and sends SIGINT before SIGTERM; tested live (`d425f0b`). Queue issue I-1 closed.
7. **Records:** memory `ie520-4stack-flashprep` (CLI-only renumber recipe), memory `ie520-is-marvell-cpu-queues` (measured
   queues on `-42`), `platforms/IE520.md` (forced-file split; punt cap + queues row), the 10-15 x230 handover's OPEN 2 answered.

## Results (queue `CAMPAIGN-QUEUE-2026-10-15T0755.md` `## Results`) — both runs clean; **final logs NOT created yet: 2 cases hold `work/`. Run `/create-logs tb470/IE520/CAMPAIGN-QUEUE-2026-10-15T0755.md` after review.**
| case | verdict | what it proved | working log |
| --- | --- | --- | --- |
| coro-dlf | PASS (not reproduced) | 3.5-min baseline + 5 min line-rate DLF into member 1 (24.67 M frames, 100 % across the stack) + 5 min into both members (24.50 M + 24.07 M, 100 % / 99.99998 %): no corosync line on either console (terminal monitor, debugging) or in any log; **CPU sdma unchanged (~24 pps)** — the flood never reached a CPU | `corosync-dlf-2026-10-15T0755/coro-dlf/work/run1.log` |
| coro-cpu | PASS (not reproduced) | Injection ports moved into the reporter's `vlan1000` (running-only, restored, diff identical). Four 5-min runs: to-me unicast (stack MAC + 10.38.29.15) into the backup / the master / both; subnet broadcast into both. **5.1–5.7 M frames punted to the master's CPU per run (~17–19 kpps, the device's punt cap; master CPU 31–39 %, `exfx` ~50 %, interrupts ~30 %; backup CPU untouched)**, every punted frame crossing the stack link in R1/R3/R4: no corosync line anywhere | `corosync-dlf-2026-10-15T0755/coro-cpu/work/run1.log` |

Both graded `tester`; the sentinel verified each VERDICT line against the committed log and the traffic proof (interface
counters at both ends). Older campaigns still hold `work/` too (port-2026-10-12/13 Ask-CK rows, kept by `--auto` by design;
`vlan-2026-10-05T1052/27887`): not this session's.

## Findings
**Measured (2026-10-15):**
- The reported `corosync[…] coroipcs.c:383/373 Enabling/Disabling flow control for 705` lines did not appear under line-rate
  DLF across the stack link, nor under CPU-bound traffic at the punt cap, on `-42` with the reporter's config, 1G NICs,
  1500-byte frames, 5 min per run (6 runs).
- On `-42`: to-me unicast is punted to the **master** on `rxDmaPcktCnt[1]`, broadcast copies on `[2]`; q0/q6 flat; the punt
  rate-limiter caps at ~17–19 k packets/s (per packet, so smaller frames would not raise it).
- A member's **forced bootloader file is invisible from the CLI** (`show boot` showed `-57` while the bootloader was set to
  `IE520-tb470.rel`), and a mismatch between members splits the stack on reload (`Neighbor incompatible`).
- `stack N renumber` works with a Provisioned absent member present; `no switch N provision` removes the phantom and its port
  config without a prompt.
- The stack's own `IMI: Writing unsaved config changes to temporary memory` + `stk_file_sync_by_node … /var/spool/.saved.cfg`
  lines are periodic housekeeping of the UNSAVED running config, not a flash write.
- `Command [end] failed` log lines are the tools' exit path sending `end` at exec (cosmetic).
- `tools/tb killmine` refused the wrapper's own tools (fixed `d425f0b`).
**Inferred:** the reporter's trigger is something this bench did not offer — another punt reason (ARP storm, TTL expiry,
management-protocol floods), a longer soak, 10G ingress, or their exact build. Not established.

## OPEN (Test Engineer)
1. **Return the stack to the bench config?** `configure terminal` / `boot config-file flash:/tb470-bench.cfg` / `end` /
   `reload` (`y\r`), ~3 min; then `show stack` 1 Backup / 2 Master… — note `stack 2 priority 1` is NOT in `tb470-bench.cfg`,
   so after that reload member 1 (u5) becomes master again (election: equal priority, lowest MAC …0740). Or keep the
   reporter's config for more repro work.
2. **bench-state.md + `tb470.setup` are stale** (1/3/4 stack, `-57`, x230 eth3): a full u0–u5 probe (needs u2/u3, not this
   session's) and your `apply`. Also decide the x230's eth3: it now has no host NIC (eth3 → stack port2.0.13).
3. `/create-logs tb470/IE520/CAMPAIGN-QUEUE-2026-10-15T0755.md` after reviewing the two Results rows.
4. More repro variants, if wanted: ARP-request storm into the backup, TTL-1 traffic, `ping -f` from the 4050 to 10.38.29.15,
   a 30–60 min soak, the reporter's exact build; or ask the reporter which Ixia frame type they used.
5. `stephenh.cfg` (13.8 KB) sits in both members' flash; `u2-standalone.cfg`, `tb470-oldstack.cfg`, `stk_a_9001_33234_*.cfg`
   are older leftovers. Delete or keep: yours.
6. u2 (IE520 264A23061, old member 1, now outside the stack) was not read this session; its state is unknown here.
7. Push: `git push origin main`.

## Next steps
1. Decide OPEN 1 (bench config vs reporter's config), then OPEN 2 (full probe + apply).
2. Push.
3. `/create-logs` (OPEN 3).

## Recipes
- **Image update (the Test Engineer's procedure, as run today):** re-read `/tftproot/IE520-tb470.rel{,.info,.sha256sum}`;
  `tools/tb tftp_copy tb470 <scr> u<master> 10.38.215.1 IE520-tb470.rel <bytes> IE520-tb470.rel --baud 115200 --timeout 1800 --log /tmp/<scr>/tftp.log`;
  `configure terminal` / `boot system flash:/IE520-tb470.rel` / `end` (waits for "File synchronization with stack member N
  successfully completed"); member: `tools/tb bootmenu_park tb470 <scr> u<member> IE520-tb470.rel --baud 115200 --transcript … --watch 600`
  in the background, then `tools/tb ckyn tb470 <scr> u<master> 115200 "YN:reload stack-member N"`; master:
  `bootmenu_park … --reload`; then `tools/tb bootmenu_escape tb470 <scr> u<N> --baud 115200 --boot-wait 480` on both;
  delete the old `.rel` on both (`delete flash:/<old>`, `delete IE520-stk-N/flash:<old>`, `YN?:`).
- **CLI-only renumber:** memory `ie520-4stack-flashprep` (2026-10-15 paragraph).
- **CPU-bound traffic:** `tools/tb sudotool tb470 <scr> linerate --tx eth1 --dst-mac 00:00:cd:37:0a:66 --dst-ip 10.38.29.15 --dport 9001 --rate top --secs 300 --rx eth3`
  with port1.0.13/2.0.13 in VLAN 1000 (running-only); sdma on the master before/after (`show platform counter sdma`,
  clear-on-read); `show cpu`.
- **Corosync log check:** `show log | include orosync|otem|CMSG|coroipcs|flow control`, `show log permanent 1|2 | include …`,
  with `show log | include VCS` as the positive control.

## Pointers
- Queue + results: [CAMPAIGN-QUEUE-2026-10-15T0755.md](CAMPAIGN-QUEUE-2026-10-15T0755.md)
- Run folders: [corosync-dlf-2026-10-15T0755/](corosync-dlf-2026-10-15T0755/)
- Platform facts: [../../platforms/IE520.md](../../platforms/IE520.md) (§2 forced-file split; §3 punt cap row)
- Previous IE520 handover: [../../IE520/SESSION-HANDOVER-2026-10-05.md](../../IE520/SESSION-HANDOVER-2026-10-05.md)
  (the earlier 1/2 rebuild and its way back); today's x230 wrap: [../x230v2-28GS/SESSION-HANDOVER-2026-10-15.md](../x230v2-28GS/SESSION-HANDOVER-2026-10-15.md)
- Bench (STALE for u2–u5 until OPEN 2): [../../bench-setup/bench-state.md](../../bench-setup/bench-state.md)
