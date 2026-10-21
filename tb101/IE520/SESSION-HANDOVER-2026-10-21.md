# Session handover — 2026-10-21 (10:45–15:10 NZDT, second session continued): T17584 LACP campaign PASS, logs created, bench whole

Session `b5b3ec8b…` (VS Code), Test Engineer terrenceb@terrenceb-dl. After the 10:40 read-only wrap below, Terrence moved
the tb101 handovers to `tb101/IE520/` and ran `/test-mode T17584`, then `/create-logs`, then this `/wrap-dt`. This
section supersedes the 09:50–10:40 one below for the bench state.

## Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb101
Consoles: u0,u1,u2,u3 (= stack members 1,2,3,4; all 115200)
PDU: none (nothing is power-cycled; the framework's post-failure cycle silently does nothing)
Constraints: none ("Confirm as stated"). Run window: "Reloads now, stand down at end of run, stay in VS Code". Root on tb101: "Tester may use sudo -n for the bond and its restore"; root traffic tools: "Yes, that reading" (traffic tools under sudo -n are test traffic; root CHANGES limited to the bond).

## TL;DR — bench is WHOLE and back to its template

- **T17584 "LACP - Startup stable with heavy traffic": PASS** (1 case, graded by the tester, final log created).
- Wrap probe `2026-10-21T020410Z`: **MATCH** vs `/home/st-art/configs/tb101.setup`, advisories none, only the stamp changed.
- Read on u0 at 15:03: one stack, Normal operation, all four Ready, **member 1 (u0) Active Master**, VMAC
  0000.cd37.0d6f. Boot image `flash:/IE520-awplus_main-20261019-75.rel (file exists)`, boot config
  `flash:/tb101-bench.cfg (file exists)` on every member. `show etherchannel` LAG count 0. Running-config matches
  `tb101-bench.cfg` (no `write` this session; `tb101-bench.cfg` still 1771 B, Oct 20 20:33:07). Build
  `awplus_main-20261019-75` / bootloader 9.2.0 on all four, uptime 01:14 (since the case's whole-stack reload).
- `show reboot history` newest per member: all `2026-10-21 00:50:12-13 Expected User Request` (UTC) = the case's
  whole-stack reload at 13:48 NZDT. Also new today: member 1 00:14:14, member 2 00:27:05, member 4 00:37:37 = the
  case's three member reloads. **No unexpected reboot.**
- Host: eth2 10.37.101.1/27, eth3 10.37.101.33/27, eth4 10.37.101.65/27 (+ their fd32:…::1/64), carrier up, original
  MACs, no bond interface. The `bonding` kernel module stays loaded (harmless). No NIC pinning was ever set.
- Consoles u0–u3 at `IE520#` with `terminal no monitor`. Nothing of ours runs on tb101. Scratch `/tmp/lacp-1222/`,
  `/tmp/orient/`, `/tmp/wrap/` are tmpfs; losing them is correct.
- Sentinel stood down: Monitor stopped 14:23:57, cron deleted at this wrap, no own `sentinel.sh` left.

Verify from the dev host, repo root:
```bash
tools/tb precheck tb101 0-3                                   # all four free; ser2net FOUND is normal
tools/tb probe tb101 --consoles 0-3 --baud 115200 --no-prompt # expect MATCH
```

## What was done, in order
1. **10:45** Handovers `git mv`'d to `tb101/IE520/` (Terrence: "handovers should be tb101/IE520/"); memory pointer fixed (`e20e7f2`, rebased to `d26deef`).
2. **12:22** `/test-mode T17584`: queue [CAMPAIGN-QUEUE-2026-10-21T1222.md](CAMPAIGN-QUEUE-2026-10-21T1222.md); Terrence chose the fit: host
   bond0 (eth3+eth4, 802.3ad) ↔ po1 (port1.0.1 member 1 + port2.0.1 member 2), far side eth2 ↔ port3.0.1 (member 3).
3. **12:28–12:35** TRIAGE (bench-runner): 1 runnable / 0 blocked; probe MATCH.
4. **12:45–14:11** RUN (bench-runner): baseline, setup, E0 traffic, E1/E2 leg shutdowns, E3/E4/E5 member reloads
   (masters 1 → 4 → 1), E6 whole-stack reload booting the LAG config, control flows, health twice, full restore,
   probe MATCH. Commits 5cdad39, bc55eec, 23e8a95, 4cd00db.
5. **14:4x** `/create-logs` (Terrence confirmed): final log, README, reviews; `work/` deleted (`192089f`).

## Results (from the queue's Results table)
| case | verdict | graded | final log |
| --- | --- | --- | --- |
| T17584 | PASS | tester | [17584.log](lacp-2026-10-21T1222/17584/17584.log) + IE520.cfg — **final logs created** (`192089f`) |

Run label: **clean** (both health samples clean against the 10-20 baseline; every new reboot entry matched to a reload
the case issued). The 4-device / 4-route step is NOT MEASURABLE on tb101 (one switch, three host edges) and is
reported, not failed.

## Findings
- **Measured:** `show lacp sys-id`, the LACPDUs on the wire and the bond's partner MAC stay the VMAC through two master
  failovers and a whole-stack reboot. Outage: 770 ms when the reloading master carries a LAG leg, ≤ 30–40 ms
  otherwise, 202.5 s for the whole-stack reboot. Now in `platforms/IE520.md` §3.
- **Measured:** `boot config-file` on a stack copies the file to every member (> 60 s first time); restore must delete
  it on each `IE520-N/flash:`. Now in `platforms/IE520.md` §3.
- **Measured (tb101 host):** tcpreplay ~700 Mbps one way; igb `rx_fifo_errors` under concurrent load, so grade DUT
  loss on DUT counters; networkd re-applies addresses to bond slaves. Now in memory `tb101-ie520-bench-map`.
- **Observed, cause inferred (O-1):** 4 broadcast frames duplicated in one ~30 ms window at each member rejoin.
- **Observed, cause unknown (O-2):** `show lacp-counter` port1.0.1 `Pckt err Sent 2` after member 1 became master.
- **Process:** two concurrent `/test-mode` sessions on this host killed each other's `sentinel.sh` at 13:25 (the kit's
  sweep matched every `sentinel.sh`). Fixed: the sweep now matches only this session's `SCRATCH`
  (`ddcc0c6`, memory `sentinel-sweep-kills-peer-sentinels`); the tb470 session (`device-testing-77`) was told.

## OPEN
1. ~~Should `bondctl` stay in `tools/tb`'s `SUDO_TOOLS`?~~ **Terrence 2026-10-21: "yes, save it in tools".** It stays
   in `tools/` and on the wrapper's root-tool list. Each LAG case still needs his OK for the bond (STANDING-ORDERS §4);
   `tools/tb`, `tools/README.md` and memory `tb101-ie520-bench-map` say so.
2. ~~O-1 and O-2: a developer or a follow-up measurement?~~ **Terrence 2026-10-21: "no".** They stay recorded in
   `platforms/IE520.md` §3 as observations; nothing is scheduled.
3. ~~Build the proposed tools?~~ **Terrence 2026-10-21: "yes, all". Built the same afternoon:** `tools/eventwin.py`
   (new), `l2flows.py --per-link` (+ `flowstat.py`/`loopwin.py` read sub-flows), `rcdiff.py` fix. Tested offline
   (fake socket layer, stub-tool harness) and by a regression on tb101's E3 flow files (identical output); **not yet
   run on hardware** — the first traffic case that uses them is their hardware test. README entries in `tools/README.md`.
4. Unchanged from 10-20: `port4.0.26`'s far end; flash housekeeping on the master (old cfgs, a 242 KB debug tgz);
   `/nfsHome` fstab line on tb101.

## Next steps
1. Terrence: `git push origin main` (count in the brief).
2. Attach `lacp-2026-10-21T1222/17584/17584.log` + `IE520.cfg` to AWPTCM-T17584 in Zephyr.
3. Next session: `/orient-dt tb101`; expect precheck CLEAR (ser2net FOUND) and probe MATCH.

## Recipes
Host bond for a LACP partner (root, only with the Test Engineer's say-so):
```bash
tools/tb scratch tb101 <scratch>
tools/tb sudotool tb101 <scratch> bondctl up bond0 /tmp/<scratch>/bond-state.json eth3 eth4
tools/tb sudotool tb101 <scratch> bondctl status bond0       # Partner Mac Address = the stack VMAC
tools/tb sudotool tb101 <scratch> bondctl down bond0 /tmp/<scratch>/bond-state.json   # re-run until "RESTORE DIFF: empty"
```

## Pointers
- Campaign: [CAMPAIGN-QUEUE-2026-10-21T1222.md](CAMPAIGN-QUEUE-2026-10-21T1222.md); group [README](lacp-2026-10-21T1222/README.md) and [REVIEW](lacp-2026-10-21T1222/REVIEW.md).
- Measured state: [bench-setup/tb101/bench-state.md](../../bench-setup/tb101/bench-state.md) (capture `2026-10-21T020410Z`).

---

# Session handover — 2026-10-21 (09:50–10:40 NZDT, second session): orient + wrap only, tb101 read-only, bench whole

Session `b5b3ec8b…` (VS Code), Test Engineer terrenceb@terrenceb-dl. `/orient-dt tb101` then `/wrap-dt`, no task given
in between. No test case ran, no sentinel (none needed: no campaign). Nothing on the DUTs or the box was changed.

## Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb101
Consoles: u0,u1,u2,u3 (all 115200)
PDU: none
Constraints: none stated

## TL;DR — bench is WHOLE, unchanged since the 09:45 wrap below

- Git at orient (09:52): 2 ahead of `origin/main`, 0 behind, nothing to pull; dirty tb470 probe files belong to
  another session and were left alone.
- Orient probe `2026-10-20T205250Z` and wrap probe `2026-10-20T213624Z`: both **MATCH** vs
  `/home/st-art/configs/tb101.setup`, advisories none; the only diff is the capture stamp.
- Read on u0 at 09:53 (`tools/tb ckcon tb101 orient u0 115200 …`): `show reboot history` — newest entry on all four
  members is still `2026-10-20 20:30:19 Expected User Request` (UTC, the 09:29 reload), no new entries; free flash
  64.9 / 64.7 / 64.6 / 59.2 MB (members 1–4); `show stack detail` 8/8 stackports learnt (ring); boot image and boot
  config both `(file exists)`; build `awplus_main-20261019-75`, bootloader 9.2.0, identical on all four. Member 1
  (u0) Active Master.
- Consoles u0–u3 left at the manager exec prompt (ckcon's `end` preamble; no `configure terminal` sent).
- Box: only `/tmp/orient/tools/` created (tmpfs scratch, a copy of the repo's `tools/`); losing it is correct.
- Measured state: [bench-setup/tb101/bench-state.md](../../bench-setup/tb101/bench-state.md) (capture `213624Z`).

## Restored / kept / skipped
- Restored: nothing to restore (read-only session).
- Kept: everything as the 09:45 handover below left it.
- Skipped: the OPEN items below (port4.0.26 far end, flash housekeeping, /nfsHome fstab; handover placement CLOSED 10:45, moved to tb101/IE520/) —
  not asked for. The ser2net daemon is the only `precheck` FOUND item, as before (holds no console).

## Next steps
1. Terrence: `git push origin main` (count in the brief).
2. Next session: `/orient-dt tb101`; expect precheck CLEAR (ser2net FOUND is normal) and probe MATCH.
3. OPEN items are unchanged from the section below.

---

# Session handover — 2026-10-21 (08:15–09:45 NZDT): tb101 4-stack applied, cable fixed, reloaded, member 1 master; git re-synced with origin; orient-dt §0a

Session `f1aa8110…` (VS Code), Test Engineer terrenceb@terrenceb-dl. No test case ran, no sentinel (none needed:
no campaign). Started as a status relay from the 2026-10-20 session (peer `device-testing-e8`), became the
follow-up that closed that handover's open items 1–3.

## Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb101
Consoles: u0,u1,u2,u3 (all 115200)
PDU: none
Constraints: none stated

## TL;DR — bench is WHOLE and matches its template

One 4-member stack `IE520` on **awplus_main-20261019-75** (build Mon Oct 19 08:37:01 UTC 2026, identical on all
four), bootloader 9.2.0 on all four, each booting `flash:/IE520-awplus_main-20261019-75.rel (file exists)` with boot
config `flash:/tb101-bench.cfg (file exists)`. **Member 1 (u0, S/N 264A23061, swi_a) is Active Master** since the
09:29 reload; members 2–4 Backup. All eight stackports up (`Learnt neighbor …`), `Operational Status: Normal
operation` = a ring, not a chain. Free flash 64.9 / 64.7 / 64.6 / 59.2 MB (members 1–4). Three host NICs proven
(eth2↔port3.0.1, eth3↔port2.0.1, eth4↔port1.0.1). Nothing is shut, nothing is running-only, nothing powered off.

Measured: [bench-setup/tb101/bench-state.md](../../bench-setup/tb101/bench-state.md) (capture `2026-10-20T203815Z`,
MATCH vs the deployed `/home/st-art/configs/tb101.setup`, advisories none).

Verify from the dev host, repo root:
```bash
tools/tb precheck tb101 0-3                                   # expect all four free (ser2net FOUND is normal, holds no console)
tools/tb probe tb101 --consoles 0-3 --baud 115200 --no-prompt # expect MATCH; tools/tb picks python3.8 on tb101
```

## What was done, in order
1. **08:20** Relayed the 2026-10-20 session's end-of-session status (peer `device-testing-e8` replied by SendMessage;
   everything done except the `apply`, hard-denied for sessions).
2. **08:22** Terrence ran `bench_probe.py --box tb101 apply` (worked: `/home/st-art/configs/tb101.setup`, 729 B; an
   empty `backups/2026-10-20T192223Z.tb101.setup` because no .setup existed before). His `tools/tb probe` then
   FAILED: tb101's `/usr/bin/python3` is 3.6.9 and bench_probe.py uses `subprocess.run(capture_output=…)` (3.7+); it
   died in the precheck, leaving an empty capture dir (removed). **Fix:** `tools/tb` `BOX_PY` now maps tb101 →
   python3.8 (as tb105, tb277). His re-run: probe `192814Z` MATCH.
3. **Git re-sync (Terrence's instruction).** Local main was 5 ahead / 231 behind origin (tb277 x960 campaigns from
   another seat). Peer put on hold, `git rebase --autostash origin/main`, three conflicts merged keeping both
   sides (MEMORY.md index line extended at both ends; `tools/tb` BOX_PY tb277 ∪ tb101; `.gitignore` duplicate
   comment dropped). A THIRD session, invisible to `ListAgents`, was committing and probing tb470 in the same
   working tree meanwhile (queue `tb470/x230v2-28GS/atmf-2026-10-21T0835`); its dirty files were left alone.
4. **orient-dt §0a "Git first"** written (fetch → ff-pull / rebase with peers on hold / stop on a half-done op; both
   sides' facts in conflicts; `Git:` line in the brief); wrap-dt §6 reports `<n> to push, <m> behind`; memory
   `shared-working-tree-git-sync-first`.
5. **Terrence: `stack 1 priority 1` KEPT; cable reseated** (port4.0.28 ↔ port1.0.27). 09:28 `show stack detail`:
   8/8 stackports learnt, Normal operation.
6. **09:29 whole-stack `reload`** from u0 (`tools/tb reloadc`, transcript `/tmp/relcbl/console-u0.log` on tb101,
   tmpfs); login back 09:33 (~65 s of console output after `Starting AWPlus`). 09:34: member 1 Active Master,
   boot pointers valid. Probe `203454Z` MATCH. Reboot history on every member: `2026-10-20 20:30:19 Expected User
   Request` (UTC) = this reload; member 4 also shows the 2026-10-20 merge reboots (`VCS duplicate member-ID`).
7. **Wrap probe `203815Z`** MATCH, no advisories; only the stamp changed.

## Restored / kept / skipped
- **DUT config:** nothing changed this session (reload only). Kept as found: `tb101-bench.cfg` incl. `stack 1
  priority 1` (Terrence's decision 2026-10-21).
- **Consoles u0–u3** are left at the manager exec prompt (`line con 0 exec-timeout 0 0`), as the probe always
  leaves them; tb101 is not a shared box. No `configure terminal` was entered.
- **Box:** no NIC pinning, IPs, routes or rules touched. Scratch `/tmp/relcbl/` (tmpfs) left; losing it is correct.
- **Skipped:** flash housekeeping (old tb470 `.cfg`, merge debug tarballs, `tb101-prep.cfg`), `/tftproot/tb101-bench.cfg`,
  `/tmp/relup/` — all still as the 2026-10-20 handover lists them; not asked for.

## Findings
- **Measured:** tb101 python3 = 3.6.9 (python3.8 present); bench_probe.py needs 3.7+. A `tools/tb probe` on a box
  not in `BOX_PY` fails in the precheck with an empty capture dir as the only trace.
- **Measured:** after the cable reseat the ring formed without a reload; the reload was for mastership (priority
  has no pre-emption) and it took ~4 min console-to-login.
- **Inferred:** the empty 0-byte `backups/…tb101.setup` from `apply` is the "snapshot of the outgoing pair" when
  there was no outgoing file — harmless, kept as the record of the first apply.

## OPEN
1. **`port4.0.26` (member 4, copper SFP, `connected`, vlan1): what is on the other end?** Evidence: not in the
   probe's links (no LLDP neighbour, no host MAC learned). Unchanged since 2026-10-20.
2. Flash housekeeping on the members, if wanted (see 2026-10-20 handover, "Flash leftovers").
3. `/nfsHome` fstab line on tb101 (optional root change; the `remote_path()` fallback makes it unnecessary).
4. ~~Handover placement~~ CLOSED 2026-10-21: Terrence ruled `tb101/IE520/`; both files moved there (git mv). Was: live at `tb101/` (no `<FAMILY>/` level, unlike orient-dt §0's
   `<TB>/<FAMILY>/` pattern). Decide: move both to `tb101/IE520/` or record tb101 as single-family.

## Next steps (ordered)
1. Terrence: `git push origin main` (see brief for the count).
2. Next session on tb101: `/orient-dt tb101` — expect a `Git:` line first (§0a), then precheck + probe MATCH.
3. Answer OPEN 1 before any campaign uses member 4's front ports.

## Pointers
- Previous handover (image update, re-form, clean config, flash leftovers, IXIA addressing):
  [SESSION-HANDOVER-2026-10-20.md](SESSION-HANDOVER-2026-10-20.md)
- Bench map memory: `.claude/memory/tb101-ie520-bench-map.md`; git lesson: `.claude/memory/shared-working-tree-git-sync-first.md`
- Image update procedure (tb101 run notes): `.claude/memory/ie520-image-update-procedure.md`
