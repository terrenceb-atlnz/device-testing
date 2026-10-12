# Session handover — 2026-10-09: x230v2-28GS AWPTCM campaign (18:00 run), Ask-CK campaign support

Session `50f164f5` (VS Code, desktop). The morning's image update and IE520 bench wrap are in
[../IE520/SESSION-HANDOVER-2026-10-09.md](../IE520/SESSION-HANDOVER-2026-10-09.md). This file covers the
x230 campaign: triage, the scheduled 18:00 run, and the Ask-CK support work done with the peer session
`test-cases-2b` in the afternoon. Wrapped at ~20:40 NZDT on the Test Engineer's instruction:
*"/wrap-dt after everything is done between sessions"*.

## Update 2026-10-12 (same session): final logs created; x230 boots its own config

- **Final logs created** for all 23 cases (`/create-logs`, commits `148d7a4` secure, `948349d` platform,
  `c7fed2d` l2l3, `a6fcbf5` ports); no `work/` left. `tools/case_tokens.py` fix `c83a7d1`.
- **Decisions 1 and 2 below are resolved** (Terrence: *"make a new .cfg and set it up how you want, write it to
  memory, and then set the default boot config to that new config"*), 14:09-14:18 NZDT on u0 only:
  - `copy running-config flash:/tb470-bench.cfg` (967 B: the isolation VLAN 103/104/105 on port1.0.3/1.0.4/1.0.5 +
    `lldp run`, otherwise the original default.cfg content) and `boot config-file flash:/tb470-bench.cfg`.
  - `show boot`: `Current boot config: flash:/tb470-bench.cfg (file exists)`; `Default boot config:
    flash:/default.cfg` (untouched, the fallback).
  - `service password-encryption` is obsolete on this build ("Password encryption is already always enabled"), so
    default.cfg's missing line was never a difference.
  - **Verified by one reload** (Terrence: *"verification reload now, once"*): CLI `reload` 14:14:19, login after 166 s,
    VLAN 103/104/105 present with no re-apply, running-config = the file, exception log None. Probe
    `2026-10-12T011811Z` (u0-u5, precheck CLEAR) **MATCH**.
  - **The "re-apply the isolation after every x230 reload" recipe below is no longer needed.**

## Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: "u0-u5 all" (u0 = x230v2-28GS DUT; u1 AR4050S, u2/u4/u5 IE520 stack, u3 IE520-sa as partners)
PDU: "10.36.150.14 per tb470.static" (u0=1, u1=7, u2=6, u3=8, u4=4, u5=5)
Constraints: "Triage only for now", lifted ~12:0x for the 18:00 NZDT run, scope "18 + after-hours reloads" (23 cases)

## TL;DR
- **Campaign complete: 37 cases, 23 run → 19 PASS, 1 FAIL, 1 PARTIAL, 2 UNSUPPORTED; 14 NOT TESTED.**
  Results table: [CAMPAIGN-QUEUE-2026-10-09T0845.md](CAMPAIGN-QUEUE-2026-10-09T0845.md) `## Results`.
- **Final logs NOT created yet: 23 cases still hold `work/`.** Run
  `/create-logs tb470/x230v2-28GS/CAMPAIGN-QUEUE-2026-10-09T0845.md` after review.
- **One real defect:** T47209, the x230 (and IE520) 1000BASE-SX port accepts `speed 100` and passes no traffic.
- **Bench is whole:** final probe `2026-10-09T073433Z` (20:34 NZDT) **MATCH**, all six consoles at exec,
  occupancy CLEAR. Two things on the x230 are running-only or changed; see "Decisions for the TE".
- **Committed, NOT pushed** (72 commits since `83c0880`; push is yours: `git push origin main`).

## Bench state at the wrap (read, not recalled)
- Probe `2026-10-09T073433Z` MATCH; bench-state.md regenerated. One advisory (long-standing): eth1 learned on
  swi_c port3.0.13 AND swi_f port1.0.2, because x230 port1.0.2 shares the stack's VLAN 1.
- All six units on awplus_main-20261008-57, flash boot, boot image `(file exists)`. Stack stk_a Normal:
  member 3 (swi_c, u5) Active Master, members 1 and 4 Backup.
- **x230 (u0):** secure mode OUT; boot config `flash:/default.cfg (file exists)`; running-config has the
  VLAN 103/104/105 isolation and `lldp run` (running-only). Reloaded 7 times tonight by CLI `reload` (5 in run 1, 2 in run 4).
  **No PDU cycle anywhere; no `write` on any unit other than the x230 (T47114/T47115).**
- **AR4050S port1.0.2** is admin-shut (as since 09-03); the tester opened it only inside T47208/T47210.
- tb470: no tool processes, no root changes, no host routes/addresses changed.
- Verify in one go (from the repo root):
  `tools/tb precheck tb470 0-5 && tools/tb probe tb470 --consoles 0-5 --no-prompt --pdu 10.36.150.14 --outlet u0=1,u1=7,u2=6,u3=8,u4=4,u5=5 --baud 115200`

## Decisions for the Test Engineer (nothing below was decided by this session)
1. **x230 startup config is not byte-identical to the pre-run file.** The x230 refuses every copy/delete
   onto `flash:/default.cfg` (memory `awplus-default-cfg-cannot-be-overwritten`), so after secure mode it
   was restored by `write`. Differences: new saved-on header; **`service password-encryption` missing**;
   `security-password minimum-length 8` and `history 1` added (678 B vs 643 B). The pre-run file is in
   [secure-2026-10-09T0845/47114/work/default.cfg.pre-secure.txt](secure-2026-10-09T0845/47114/work/default.cfg.pre-secure.txt).
   Options: accept as is; add `service password-encryption` and `write`; or a byte-exact restore via
   `start-shell` + `cp` (not tried).
2. **The x230 VLAN 103/104/105 isolation is still running-only.** Keep it running-only (re-apply after
   every x230 reload, recipe below), or `write` it into default.cfg, or recable. An x230 reload drops it;
   the stack side keeps the loop broken, but eth3 then shares eth1's domain.
3. **Re-grade candidates** (the tester's suggestions; verdicts unchanged):
   T47208 PASS → PARTIAL? (SPTX at 10 Mb/s not measurable); T31853 PASS (no `gui-userdata/`, used unit).
4. **T47114 release-verification warning:** the secure-mode boot logged
   `Verification of the release file has failed, please verify it.` Dev build, no SHA256 to verify against.
5. **T20358 recable** to re-run it: move the AT-SPSX from stack port3.0.7 into x230 port1.0.6 and the
   AT-SPSX from stack port4.0.7 into x230 port1.0.7, then one multimode LC-LC lead x230 port1.0.6↔1.0.7
   (or a hub with two x230 ports); then `bench_probe.py apply`.
6. **NOT TESTED rows** need a person, your decision, or setup (list in the queue's Results; summary posted
   at 20:3x).
7. **`tb999/NO-FAMILY/`** (commit `0b5cc3e`): left by `test-cases-2b`'s deliberate 14:10 test against a
   nonexistent box. Keep or delete; this session did not touch it.

## What was accomplished (10-09, afternoon and evening)
1. **Ask-CK campaign support** with `test-cases-2b` (Terrence: *"work with the other peer session"*):
   `tools/tb` wrapper and the campaign settings file (approved by Terrence, commit `c4ccd0c`); test-mode
   reads the Ask-CK hand-off (`df4b009`, `e334e89`), ends with `ASKCK-DONE` (`df4b009`), Validation repair
   loop + review + `PROBE` marker (`da37c2d`); bench-runner reads console state from the transcript
   (`fe5ad02`). The peer released tb470 at 13:59 and was "completely done" at 14:12.
2. **18:00 run** (cron, this session as sentinel, four bench-runner dispatches): run 1 platform 18:02–18:38,
   run 2 ports 18:40–19:27, run 3 L2/L3 19:29–20:04, run 4 secure 20:07–20:31.
3. **Tools added by the testers:** `@sleep`/`@poll` in [tools/ckcon.py](../../tools/ckcon.py),
   [tools/snmpwalk.py](../../tools/snmpwalk.py) (new), five options in [tools/linerate.py](../../tools/linerate.py);
   all in [tools/README.md](../../tools/README.md).
4. **New platform file** [platforms/x230v2-28GS.md](../../platforms/x230v2-28GS.md).

## Results — clean, final logs NOT created
All 23 runs **clean** (no confounding: no PDU cycle, every case's config diff empty, isolation intact).
Per group: platform 9 PASS / 2 UNSUPPORTED; ports 3 PASS / 1 PARTIAL / 1 FAIL; L2/L3 5 PASS; secure 2 PASS.
**Final logs NOT created yet: 23 cases hold `work/`.** `find tb470/x230v2-28GS -path '*0845*' -name work -type d`.

## Findings
**Measured** (details and rows in [platforms/x230v2-28GS.md](../../platforms/x230v2-28GS.md)):
- T47209: SX port accepts `speed 100`, reports `connected a-full 100`, passes nothing; IE520 same.
- BIST and PRBS offered by the parser, refused at run time.
- `flash:/default.cfg` cannot be overwritten or deleted from the CLI; `write` still updates it.
- A boot updates default.cfg's mtime without a save.
- Secure-mode boot ≈ 265 s vs ≈ 165 s.
- `no exec-timeout` leaves `exec-timeout 0 0` until a reload.
- Routed line rate (IPv4 and IPv6) and aggregated trunks (static and LACP) at line rate with 0 loss.
**Inferred:** the SX `speed 100` defect is shared AW+ code (same on IE520); not proven.

## Process notes (for the tester agent)
- Two tester slips in `@poll` (19:04 `do show …` at exec on the 4050; 19:50 `\s` in the command field):
  each only wasted a poll; the sentinel sent a one-line correction.
- T47114's log first omitted the release-verification warning; corrected in `3bcd790`, verdict untouched.

## Recipes
- **Re-apply the x230 isolation after any x230 reload** (running-only, no `write`):
  `configure terminal` / `vlan database` / `vlan 103,104,105` / `interface port1.0.3` /
  `switchport access vlan 103` / `interface port1.0.4` / `switchport access vlan 104` /
  `interface port1.0.5` / `switchport access vlan 105` / `exit` / `lldp run` / `end` / `show vlan brief`.
- **Undo a test's startup-config change on the x230:** make running-config equal the original, then `write`
  (copy-back is refused). Check `show boot` reads `flash:/default.cfg (file exists)`.

## Sentinel
Stood down at the wrap: Monitor stopped, the 15-min backstop cron deleted, no `sentinel.sh` left.
The 18:00 one-shot cron fired at 17:58 and is gone.

## Pointers
- Queue and results: [CAMPAIGN-QUEUE-2026-10-09T0845.md](CAMPAIGN-QUEUE-2026-10-09T0845.md)
- Bench: [../../bench-setup/bench-state.md](../../bench-setup/bench-state.md)
- Platform facts: [../../platforms/x230v2-28GS.md](../../platforms/x230v2-28GS.md)
- Ask-CK plan records: Test-cases `ask-ck/plans/PLAN-agent-sessions.md`, `PLAN-test-validation.md`
