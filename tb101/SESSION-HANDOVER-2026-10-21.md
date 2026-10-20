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

Measured: [bench-setup/tb101/bench-state.md](../bench-setup/tb101/bench-state.md) (capture `2026-10-20T203815Z`,
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
4. Handover placement: this and the 2026-10-20 file live at `tb101/` (no `<FAMILY>/` level, unlike orient-dt §0's
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
