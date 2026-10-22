# Session handover — 2026-10-22 (12:33–15:3x NZDT): tb470 recabled, x230 storm stopped, campaign 2026-10-22T1320 taken over and finished (2 FAIL, 1 PARTIAL, 3 NOT TESTED), final logs created, probe fixed

Session `f7014de7…` (VS Code, `device-testing-c9`), Test Engineer terrenceb@terrenceb-dl. `/orient-dt` (tb470, named),
a loop fix on the Test Engineer's OK, then a takeover of the `/test-mode` campaign another session of his
(`device-testing-43`) had started and lost, `/create-logs`, and this wrap.

## Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u0,u1 (u0 = AR4050S swi_e, the link partner; u1 = x230v2-28GS swi_f, the DUT; both 115200)
PDU: "10.36.150.14 u0=3 u1=4" (declared; nothing was power-cycled)
Constraints: "no reboots" (campaign 2026-10-22T1320) + "None beyond no reboots". Host: VS Code.

## TL;DR
- **Bench is whole, both consoles logged out, box CLEAR.** Wrap probe `2026-10-22T022318Z` (15:23 NZDT) = **MISMATCH on the
  real recable only** (the new 4050 1.0.3 <-> x230 1.0.3 link, and eth2 on x230 port1.0.10). The fence is now correct;
  **`apply` is yours** (OPEN 1). No new reboot on either unit; both boot `flash:/tb470-bench.cfg (file exists)`.
- **The x230 had a live broadcast storm at 12:45** from your 12:40 recable: two self-loops (copper port1.0.15<->1.0.16,
  SX fibre port1.0.25<->1.0.26) all untagged vlan1 with spanning tree off (CPU 68%, exfx 97%). On your OK port1.0.16 and
  port1.0.26 were shut (12:49, CPU -> 1%), and **on your OK at this wrap they are now SAVED** (`write`, 15:20,
  `flash:/tb470-bench.cfg`). A reload no longer reopens them.
- **Campaign 2026-10-22T1320 complete:** T47209 FAIL, T47228 FAIL, T45543 PARTIAL; T44179, T47119, T47121 NOT TESTED
  (blocked by "no reboots"). **Final logs CREATED** (`5117f28`, `b098bea`). No `work/` remains.
- **`bench_probe.py` fixed** (your "fix the probe first"): host-NIC edges skip LLDP link ports, self-loops are an Advisory.
- **Sentinel stood down** (Monitor stopped 14:49, cron deleted at the wrap, no `sentinel.sh` of this session, both testers finished).
- **Committed, NOT pushed** (push is yours): see Git.

## Bench state at the wrap (read 15:12–15:23 on u0/u1, then probe 022318Z)
| unit | console | build | boot image / config | notes |
| --- | --- | --- | --- | --- |
| AR4050S swi_e S/N A10401G214000005 | u0, 115200 | awplus_main-20261008-57 (build Wed Oct 7 23:56:11 UTC 2026), bootloader 5.2.8 | `flash:/AR4050S-awplus_main-20261008-57.rel (file exists)` / `flash:/tb470-bench.cfg (file exists)` | up 7 d; flash 3.4 GB free; USB 28.6 GB free; newest reboot 2026-10-15 15:01:55 (none new). port1.0.3 is access vlan10 + `static-channel-group 1` (sa1) -- found so, not ours |
| x230v2-28GS swi_f S/N A10783G262900002 | u1, 115200 | awplus_main-20261019-75 (build Mon Oct 19 08:39:33 UTC 2026), bootloader 6.2.40 | `flash:/x230v2_28GS-awplus_main-20261019-75.rel (file exists)` / `flash:/tb470-bench.cfg (file exists)`, **saved 2026-10-22 02:20:14 UTC** | up 2 d 03 h; flash 60.5 MB free; exception log None; newest reboot 2026-10-20 08:05:54 (none new). Admin down AND saved: port1.0.7 (as before), **port1.0.16, port1.0.26** (the loop legs). Running = startup |

Cabling (probe 022318Z, LLDP both ends; the two self-loops are not in it, see Findings):
- tb470 eth1 -> x230 port1.0.2 (AT-SPTXc, vlan1000); **tb470 eth2 -> x230 port1.0.10** (AT-SPTXc, vlan1); tb470 eth3 -> 4050 port1.0.1 (vlan1)
- 4050 port1.0.2 (vlan10) <-> x230 port1.0.1 (trunk, `switchport atmf-link`); **4050 port1.0.3 (vlan10, sa1) <-> x230 port1.0.3 (vlan103)** (new)
- x230 self-loops: copper 1.0.15 (AT-SPTXa) <-> 1.0.16 (AT-SPTXa, shut); SX 1.0.25 (AT-SPSX) <-> 1.0.26 (AT-SPSX, shut)
- No host change by this session (no IP, route, ethtool). Scratch on tb470 (tmpfs): `/tmp/o1022`, `/tmp/x230p1022`, `/tmp/mgmt1022`, `/tmp/wrap1022`.

Verify in one go (repo root):
```
tools/tb precheck tb470 0,1; tools/tb probe tb470 --consoles 0,1 --baud 115200 --no-prompt --pdu 10.36.150.14 --outlet u0=3 --outlet u1=4 --name u0=swi_e --name u1=swi_f
tools/tb scratch tb470 v1023; tools/tb ckcon tb470 v1023 u1 115200 "show interface brief | include admin down" "show boot" "show reboot history"
tools/tb ckcon tb470 v1023 u1 115200 "terminal no monitor" "exit"      # leave it logged out
```

## What was accomplished
1. **Orient (12:33):** git 12 ahead / 50 behind; peer `device-testing-5e` (tb101 T17509) held git; rebase onto `fdaded7`,
   one conflict in `tools/README.md` (both sides' new sections kept). Bench named tb470 by you. Probe 12:34 MISMATCH on
   the new host links.
2. **Storm (12:45-12:50):** after your recable and 12:44 `apply` (`backups/2026-10-21T234445Z.*`), the read found the
   two vlan1 self-loops with STP off; on your OK `shutdown` port1.0.16 and 1.0.26 (running-config); CPU 68% -> 1%.
3. **Triage answers for you:** which x230 cases ran before, and the list of PARTIAL / FAIL / never-run cases.
4. **Peer brief (13:1x):** told `device-testing-43` the bench facts (eth2 misattribution, the shut legs, the reboot needs).
5. **Takeover (14:03):** `device-testing-43` had exited mid T47209; its tester died with it, nothing committed. Proved no
   copy alive, `/test-mode --resume` here, sentinel armed on this session, fresh tester rebuilt R2-R6 from the row files
   and finished the case; then Group 2 (memory `test-mode-takeover-after-dead-session`).
6. **`/create-logs` (15:0x):** three final logs, two group READMEs + REVIEWs, per-case reviews; `work/` deleted.
7. **Wrap:** x230 running vs startup diffed (only the two shutdowns differed) and `write` on your OK; `bench_probe.py` fixed
   and verified; platform file, memories, this handover.

## Results (queue `## Results`) — final logs CREATED: `5117f28` (ports), `b098bea` (mgmt)
| case | verdict | run label | one line |
| --- | --- | --- | --- |
| T47209 Fibre pluggable with supported speeds | FAIL (tester) | clean (resumed mid-case after the first tester died; R2-R6 from its row files, R6 re-run as R6b) | AT-SPSX accepts `speed 100`/`speed auto 100`, reads connected 100, 0/100 frames; 10/2500/10000/half refused; auto, 1000, 1000+full both ends 100/100 |
| T47228 API enable/disable interface, add/delete VLANs | FAIL (tester) | clean | RESTCONF PUT disables/enables port1.0.3 on both models; no VLAN add or delete through RESTCONF (403/404/204-phantom); PATCH 204 no-op |
| T45543 TPM Support | PARTIAL (tester) | clean | steps 1-2 PASS; step 3 (idevid) MANUAL-ONLY |
| T44179 Jumbo Frames | NOT TESTED | — | `platform jumboframe` = write + 2 x230 reloads ("no reboots") + root MTU 9216 on tb470 eth1/eth2 |
| T47119 / T47121 secure-mode SSH / TLS | NOT TESTED | — | write + 2 reloads per unit ("no reboots"), and no secure-mode reference device (the 4050 rejects `show secure-mode`) |

Health CLEAN in all three attempted cases; no reload, no PDU cycle, no `write` by any case.

## Findings
**Measured (2026-10-22, tb470, x230v2 awplus_main-20261019-75; 4050 awplus_main-20261008-57):**
- The SX `speed 100` defect and the RESTCONF VLAN/PATCH defects are unchanged on -20261019-75 (`platforms/x230v2-28GS.md` §2 rows updated).
- SX fibre: one end `speed 1000` + `duplex full` against an auto end -> fixed end `connected full 1000`, auto end `notconnect`, 0 frames. Not graded.
- RESTCONF: a GET of a nonexistent interface answers 200 `{}`; an IETF PUT of vlanN with a type answers 403.
- `show system pluggable diagnostics port1.0.N` is `% Invalid input` on the x230.
- Two vlan1 self-loops with STP off storm the x230 within seconds (CPU 68%, exfx 97%, port1.0.25 input peak 1.01 Gbps).
- `bench_probe.py` put a host NIC on an inter-switch port and could not see self-loops (fixed, below). **A self-loop with
  one leg shut has no LLDP neighbour, so the probe cannot see it**: today's two loops are recorded only here.
**Inferred:** none.

## OPEN (Test Engineer)
1. **`apply` the corrected fence?** Probe `022318Z` MISMATCH = exactly the recable (adds `port1.0.3-port1.0.3` and
   `tb-swi_f eth2-port1.0.10`). Any framework run that binds `tb470.setup` needs it. `tools/tb`/`bench_probe.py apply` on tb470.
2. **The 4050's port1.0.3 config** (`switchport access vlan 10`, `static-channel-group 1` = sa1) was found so; whose is it, keep it?
   It bridges x230 vlan1 (via the 1.0.1 trunk) into x230 vlan103 through the 4050. Not changed.
3. **Review `/create-logs`' three points**: T47209's R9 "connected with 0 frames" (developer opinion?), its late `swi_f.cfg`
   (14:18, header says so), and whether to file the SX and RESTCONF defects again on -20261019-75.
4. **T44179, T47119, T47121** need a session that allows reboots (and, for T44179, MTU 9216 on eth1/eth2 by you; for
   T47119/T47121, a named secure-mode reference device).
5. **Git:** below.

## Next steps
1. Push (`git push origin main`).
2. OPEN 1 (`apply`), then OPEN 2.
3. If wanted: a reboot-allowed session for T44179 / T47119 / T47121.

## Recipes
- **Self-loop cases on the x230** (T20358 copper 1.0.15/1.0.16, T47209 SX 1.0.25/1.0.26): put each loop end in its OWN
  VLAN before `no shutdown` on the shut leg, prove it with `show vlan brief`, and shut that leg FIRST in the restore.
  Group 1's exact recipe is in [CAMPAIGN-QUEUE-2026-10-22T1320.md](CAMPAIGN-QUEUE-2026-10-22T1320.md) "Group 1".
- **RESTCONF from tb470:** temporary `interface port1.0.10` / `switchport access vlan 105`, `interface vlan105` /
  `ip address 10.38.215.35/27`, then `tools/tb tool tb470 <run> restconf ...` over eth2; restore per the queue's "Group 2".
- **Taking over a dead `/test-mode` session:** memory `test-mode-takeover-after-dead-session`.

## Git
Fetched 12:33: 12 ahead / 50 behind; rebased (1 conflict, merged keep-both); Terrence pushed ~13:00. This session's
commits since: `621db11`, `2ea6b70`, `b39c4cf` (Results rows), the testers' `298c54d`, `e4dbe5f`, `052a948`, `/create-logs`
`5117f28`, `b098bea`, and the wrap commit that follows this file. Final count: see the brief.

## Pointers
- Queue and results: [CAMPAIGN-QUEUE-2026-10-22T1320.md](CAMPAIGN-QUEUE-2026-10-22T1320.md)
- Final logs and reviews: [ports-2026-10-22T1320/](ports-2026-10-22T1320/), [mgmt-2026-10-22T1320/](mgmt-2026-10-22T1320/)
- Bench: [../../bench-setup/bench-state.md](../../bench-setup/bench-state.md) (stamp 2026-10-22T022318Z)
- Platform facts: [../../platforms/x230v2-28GS.md](../../platforms/x230v2-28GS.md)
- Previous tb470 handover: [SESSION-HANDOVER-2026-10-21.md](SESSION-HANDOVER-2026-10-21.md)
