# Session handover — 2026-10-27 (08:01–12:45 NZDT): tb470, the previously-UNSUPPORTED x230v2 cases re-run after a FULL licence (1 PASS, 3 UNSUPPORTED), final logs created, campaign-review savings implemented

Session `3f3fd9c9…` (VS Code, `device-testing-13`), Test Engineer terrenceb@terrenceb-dl. `/orient-dt` (tb470, last test bench
run), `/test-mode T30403 T31863 T31866 T28218`, `/create-logs`, "implement the savings plans", and this wrap.

## Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u0,u1 (u0 = AR4050S swi_e; u1 = x230v2-28GS swi_f, the DUT; both 115200)
PDU: "10.36.150.14 u0=3 u1=4" (declared; nothing was power-cycled)
Constraints: "Reloads allowed" (the x230 and the 4050 may reload as the cases need, during office hours) + "None beyond reloads allowed". Host: VS Code.

## TL;DR
- **Bench is whole, both consoles logged out, box CLEAR** (12:36). Wrap probe `2026-10-26T233815Z` = **MISMATCH on the
  2026-10-22 recable only** (4050 1.0.3 <-> x230 1.0.3, eth2 -> x230 port1.0.10); no Advisories. **`apply` is still yours.**
- **Terrence installed a FULL licence on the x230v2** (S/N A10783G262900002) ~08:46 and rebooted it (08:48). Re-run of every
  case previously UNSUPPORTED on it: **T28218 (x230 as AMF master) PASS; T31863 BIST, T31866 PRBS, T30403 static mroutes
  still UNSUPPORTED** -- the platform/build lacks them; the licence was never the gap.
- **The AR4050S's 31 GB USB stick is now IN THE x230** (Terrence moved it for T28218). The 4050 has no `usb:` until it goes
  back (OPEN 1).
- **Final logs CREATED** (`55c43d8`, `734918f`, `1ebb382`); no `work/` remains.
- **Savings implemented** (`31006a5`): health.py no longer flags pre-existing log lines, `ckcon --verbatim`, ckcase.py finds
  ck.db itself, new `startjobs.py` and `atmf_provision.py`, bench-runner quick kit, test-mode dispatch line ranges.
- **Sentinel stood down** (Monitor expired and not re-armed after the campaign; cron `8a4c06a7` deleted at the wrap; no
  `sentinel.sh` of this session; all three testers finished, last 11:25).

## Bench state at the wrap (read 12:37–12:40 on u0/u1, then probe 233815Z)
| unit | console | build | boot image / config | notes |
| --- | --- | --- | --- | --- |
| AR4050S swi_e S/N A10401G214000005 | u0, 115200 | awplus_main-20261008-57 (Wed Oct 7 23:56:11 UTC 2026) | `flash:/AR4050S-awplus_main-20261008-57.rel (file exists)` / `flash:/tb470-bench.cfg (file exists)` | up 11 d 21 h; newest reboot 2026-10-15 15:01:55 (none new); **`usb:` Avail N (its stick is in the x230)**; AMF Network Name Not Set, Member; running = startup. Not configured by this session |
| x230v2-28GS swi_f S/N A10783G262900002 | u1, 115200 | awplus_main-20261019-75 (Mon Oct 19 08:39:33 UTC 2026), bootloader 6.2.40 | `flash:/x230v2_28GS-awplus_main-20261019-75.rel (file exists)` / `flash:/tb470-bench.cfg (file exists)` | **licences Base + ACCESS + FULL**; up 1 h 24 m (last reload 2026-10-26 22:11:30 UTC = T28218's restore); `usb:` 28.9G / 28.6G free (the 4050's stick); AMF Enterprise-AMF, Member, Restricted login Enabled; admin down AND saved: port1.0.7, 1.0.16, 1.0.26 (as before); **running = startup** (no `write` by anyone this session) |

Reboots on the x230 today (all expected, all CLI): 08:48 (Terrence, licence), 09:23, 09:32 (T31863), 09:37, 09:45 (T31866),
11:11 (T28218 restore) NZDT. Each boot 168-169 s to login.

Host: no change by this session (no IP, route, ethtool). Scratch on tb470 (tmpfs): `/tmp/o1027`, `/tmp/triage-0855`,
`/tmp/plat-1027`, `/tmp/mc-1027`, `/tmp/atmf-1027`, `/tmp/tools1027`, `/tmp/wrap1027`.

Verify in one go (repo root):
```
tools/tb precheck tb470 0,1; tools/tb probe tb470 --consoles 0,1 --baud 115200 --no-prompt --pdu 10.36.150.14 --outlet u0=3 --outlet u1=4 --name u0=swi_e --name u1=swi_f
tools/tb scratch tb470 v1028; CKTO=20 tools/tb ckcon tb470 v1028 u1 115200 "show license brief" "show file systems" "show boot" "show interface brief" "exit"
CKTO=10 tools/tb ckcon tb470 v1028 u0 115200 "exit"      # the probe leaves u0 logged in
```

## What was accomplished
1. **Orient (08:01):** git 3 ahead / 28 behind, no peers, clean rebase (Terrence then pushed). tb470 from the 10-22 record.
   Probe 08:02 MISMATCH = the 10-22 recable.
2. **Scope (08:5x):** every x230v2 case recorded UNSUPPORTED -> T30403, T31863, T31866 plus T28218 with the x230 as master;
   T33234 (MDI/MDI-X) left out on your ruling (hardware). Your minicom held u1 until 09:02; nothing touched it.
3. **/test-mode** (queue `CAMPAIGN-QUEUE-2026-10-27T0855.md`): triage 09:03-09:12 (3 runnable, T28218 blocked on backup
   media), group 1 09:20-09:54, group 2 09:55-10:10, stick moved by you, group 3 10:57-11:25 (held at gate 1 on a minicom on
   u2, outside the session; your answer "dont touch u2, its irrelevant").
4. **/create-logs (~12:00):** 4 final logs, 3 READMEs, reviews; `work/` deleted.
5. **Savings (12:10-12:30):** see Findings / Recipes; verified on u1 read-only (refused `show ip mroute` / `ip mroute`,
   two health samples), u1 logged out after.
6. **Wrap:** memory `review-feature-docs-before-testing` re-pointed to the website FoG list (your 12:4x answer), platform
   file rows, AMF memories.

## Results (queue `## Results`) — final logs CREATED: `55c43d8` (platform), `734918f` (mcast), `1ebb382` (atmf)
| case | verdict | run label | one line |
| --- | --- | --- | --- |
| T31863 FactoryRunup-BIST | UNSUPPORTED (tester) | clean | `platform bist instance all|0|all full` -> `% BIST test not supported.`; BIST is not a licensed feature |
| T31866 FactoryRunup-PRBS | UNSUPPORTED (tester) | clean (health.py false DIRTY on a pre-existing boot line; you confirmed clean) | every `platform prbs` form, incl. the case's `all`, -> `% PRBS not supported on this platform` |
| T30403 static mroutes (IPv4) | UNSUPPORTED (tester) | clean (same health.py false positive; confirmed clean) | PIM/PIM6/L3-MC-ROUTE licensed and enabled, every multicast-routing command still refused; X220 TPS = NO; build target `mcast-ip-cmd = no` |
| T28218 ATMF provisioning, x230 as master | PASS (tester) | clean | `atmf master` + all 5 provisioning steps on the USB stick; restored with one x230 reload for Restricted-login residue |

## Findings
**Measured (2026-10-27, tb470, x230v2 awplus_main-20261019-75 with FULL):**
- FULL makes the x230v2 a working AMF master; it does not add BIST, PRBS or IPv4 multicast routing (platforms/x230v2-28GS.md §2).
- `show platform bist` writes ~96 `local7.err EXFX ... illegal devGroup 99` debug lines per call (developer interest, not graded).
- poefw / TPM2 / iptables / Stack Election start jobs on every normal boot, same before the licence (2026-10-06 logs).
- Provisioning a node rewrites `usb:/atmf/<net>/info/backup_<node>.info`; the file survives `delete` + `rmdir`.
- `tools/health.py` flagged pre-existing boot-time lines as DIRTY (fixed in `31006a5`, verified).
**Inferred:** none.

## OPEN (Test Engineer)
1. **The 4050's USB stick is in the x230.** Move it back when you want the 4050's `usb:` (its 09-21 and 10-21 `usb:/atmf`
   trees are on it, untouched; `info/backup_future_node.info` was rewritten by T28218).
2. **`apply` the corrected fence** (carried from 10-22 OPEN 1; still the same two lines).
3. **The 4050's port1.0.3 config** (vlan10 + sa1) -- carried from 10-22 OPEN 2.
4. **Feature Overview Guides:** the local folder is gone; the memory now points at
   https://www.alliedtelesis.com/nz/en/resource/alliedware-plus-feature-overview-and-configuration-guides/ -- tell a session
   when the local copies are back.
5. **`tools/atmf_provision.py` is not yet run on hardware**; the next AMF provisioning case should use it and update its README status.
6. **Carried from 10-22:** T44179 (needs MTU 9216 on eth1/eth2, yours) and T47119 / T47121 (need a secure-mode reference
   device) -- reloads are allowed now, so T44179 is closer to runnable.
7. **Git:** below.

## Next steps
1. Push (`git push origin main`).
2. OPEN 1 (stick), then OPEN 2 (`apply`).
3. If wanted: T44179 / T47119 / T47121 in a reload-allowed session.

## Recipes
- **x230 as AMF master (T28218):** needs `AMF-MASTER` in `show license brief` and a stick (`usb:` Avail Y). One call:
  `CKTO=600 tools/tb atmf_provision tb470 <run> u1 115200 --node future_node --set-master --rel x230v2_28GS-awplus_main-20261019-75.rel --cfg tb470-bench.cfg`
  then `tools/tb ckreload tb470 <run> u1 115200 400` to clear the Restricted-login residue. Hand sequence: the case log
  `atmf-2026-10-27T0855/28218/28218.log`.
- **A "does the platform support it?" case:** licence -> `qmark` -> `ckcon --verbatim` -> TPS / "<Platform> Features" on the
  lab wiki via `tools/tb tool <TB> <run> httpq "<raw URL>"` (bench-runner "Running").
- **Boot start jobs after a reload:** `tools/tb tool tb470 <run> startjobs /tmp/<run>/console-u1.log`.

## Git
Fetched 08:01: 3 ahead / 28 behind; rebased clean (no conflicts, no peers); Terrence pushed. This session's commits since:
`1ebd615` .. `31006a5` (queue, testers, results, `/create-logs`, savings) and the wrap commit that follows this file.
Final count: see the brief.

## Pointers
- Queue and results: [CAMPAIGN-QUEUE-2026-10-27T0855.md](CAMPAIGN-QUEUE-2026-10-27T0855.md)
- Final logs and reviews: [platform-2026-10-27T0855/](platform-2026-10-27T0855/), [mcast-2026-10-27T0855/](mcast-2026-10-27T0855/), [atmf-2026-10-27T0855/](atmf-2026-10-27T0855/)
- Bench: [../../bench-setup/bench-state.md](../../bench-setup/bench-state.md) (stamp 2026-10-26T233815Z)
- Platform facts: [../../platforms/x230v2-28GS.md](../../platforms/x230v2-28GS.md)
- Previous tb470 handover: [SESSION-HANDOVER-2026-10-22.md](SESSION-HANDOVER-2026-10-22.md)
