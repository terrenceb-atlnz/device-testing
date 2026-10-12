# T33235 "(3) Port - Fixed port Speed" — validation review (Ask-CK run 2026-10-13T0626-val-fbe9)

Reviewer: sentinel session, /test-mode §11 step 2, 2026-10-13 ~07:45 NZDT. Analysis only: **the framework's verdict stands**
(PASS, 31 PASS / 2 UNSUPPORTED / 0 FAIL, rc 0) and no Results row changes here (memory `grading-authority-tier-list`).

Inputs: `work/run1.log` (tester's working log, verdict PASS), `work/framework-run1/test-9001.33235.log`, the case payload
`ask-ck/functions/generator/refined-cases/Port/AWPTCM-T33235/zephyr_payload.json` (11 steps), the script copy
`work/test-9001.33235.py` (unedited, sha1 b044d695…, Test-cases 056114d), and the sentinel's live console feed of the run.

Bench binding for this run (IE520 stack `stk_a` via swi_a/u2; partner x230v2-28GS `swi_f`): copper test port **port1.0.17
(AT-SPTXa) ↔ x230 port1.0.3 (AT-SPTX)**, monitored copper-SFP port1.0.2 ↔ x230 port1.0.2, fibre test port **port1.0.3 (AT-SPSX
1000BASE-SX) ↔ x230 port1.0.4 (AT-SPSX)**. Setup: stack port1.0.2 out of sa2 (the one-leg isolation); restored after.

**Run clean?** Yes, by Terrence's definition: no exception, no Python error, no refused setup/defaulting/tear-down command, no
missed config step. Every `%` line answers a deliberate negative step. 0 PDU cycles, 1 planned whole-stack reload (TC33).
No repair was needed; repairs.md R1 (clear pre-run exception history) was checked and was a no-op (all logs `None`).

---

## (a) The logs — false positives and false negatives

### A1. TestCase_8 PASS is a likely false positive (fibre `speed 100` on 1000BASE-SX) — **most important finding**
- Both SX ends accepted `speed 100`; the DUT row read `connected 104 full 100 1000BASE-SX` and `current speed 100`, so the script
  graded PASS (5 checks, all on the status row / `show interface` / running-config).
- 1000BASE-SX optics cannot physically run 100 Mb/s. On this build (awplus_main-20261008-57) an SX port forced to 100 reports
  connected **while passing no frames** — measured on this same stack port 1.0.3 and on the x230 in T47209 (2026-10-09, FAIL).
- So the PASS proves "the CLI accepted it and the row says connected", not "the link re-established at 100" (payload step 2).
  It is at best unproven, and given T47209 most likely a **DUT defect masked by the test**: the DUT should either reject
  `speed 100` on an SX module or show the link down.
- Recommendation: add a traffic/liveness check to every link-up assertion in the fibre sweep (TC8–12) and ideally the copper sweep —
  e.g. LLDP neighbour on the partner, or a ping/ARP across the link's VLAN, or rx/tx counter deltas on both ends over a few seconds.
  With that check TC8 would read FAIL (real DUT finding, still a clean run) and would cost one PDU cycle.

### A2. TestCase_20/21 UNSUPPORTED is a coverage gap, not a platform limit
- Payload step 7: "fix the DUT at one supported speed and the partner at a different, incompatible speed; confirm no link over a
  sustained period; then set a compatible speed and confirm the link returns."
- The script hard-wires the incompatible pair as **DUT 100 / partner 10** (STEP 21, l.3886) and gates TC20/21 on the DUT accepting
  both `speed 10` and `speed 100`. The AT-SPTXa rejects `speed 10`, so both read UNSUPPORTED (pre-marked by TC3, skipped cleanly).
- But this bench had a valid incompatible pair the whole time: **DUT 1000 / partner 100** (both ends accepted both in TC3/TC4/TC30).
  The objective was testable; the script's choice of pair made it untestable.
- Recommendation: pick the pair from the sweep's own record (`speedMap`): any two speeds both ends accepted, DUT at one, partner at
  the other. Mark UNSUPPORTED only when fewer than two common fixed speeds exist. That turns 2 UNSUPPORTED into 2 measured cases here.

### A3. TestCase_18 grades "a clear error" loosely
- `speed 5` → `% port1.0.17: Speed or duplex must be auto port1.0.17`. That is an error, but not a clear one for an out-of-range
  value (it reads as a duplex problem). The script accepts any `%` line (its PASS evidence string is just the echoed command).
- Not a false PASS by the script's own rule, but the payload's "rejected with a clear error" is not really judged. Possible minor
  DUT UX finding (misleading message). Recommendation: record the error text in the PASS line and, if the case owner wants it,
  grade it against an expected pattern (`Unsupported speed`, `Invalid input`, out-of-range).

### A4. "Auto-negotiation reported as disabled" is inferred from a display prefix
- TC14/TC24/TC33 use "no `a-` prefix in the status row" as the evidence that auto-negotiation is disabled. On AW+ this is the
  established convention and it held consistently in this run (a-full/a-1000 ↔ full/1000), so no false result here.
- It is indirect: the IE520 `show interface` output has no explicit auto-negotiation field. Acceptable; worth a comment in the
  script so a future build that changes the status-row format is caught (a format change would read as a FAIL, not a false PASS).

### No false negatives found
- Every negative step (TC2, TC5–7, TC10–12, TC17–19) checked rejection **and** that running-config, configured speed and link state
  were unchanged afterwards — the full payload step 6 wording.
- TC25 and TC27 cover both `no speed` and `speed auto` as payload step 5 asks, each with the a- prefix back and the step-2 baseline
  (1000/full) matched.

## (b) Objective and steps vs the script

| payload step | script | verdict |
| --- | --- | --- |
| 1 baseline (link up, negotiated speed/duplex/autoneg) | TC1 (STEP 2) | covered |
| 2 each fixed speed, copper and fibre, link re-establishes, speeds match | TC2–7 copper, TC8–12 fibre | covered, but link-up is status-only (A1) |
| 3 autoneg reported disabled with fixed speed | TC14 | covered (A4) |
| 4 configured vs operational, status and running-config agree | TC15, TC16 | covered |
| 5 `no speed` and separately `speed auto` → autoneg enabled again | TC25, TC26 (re-force), TC27 | covered |
| 6 invalid / out-of-range / unsupported-on-this-port values rejected, state unaffected | TC17, TC18, TC19 (+ sweep rejections) | covered (A3) |
| 7 incompatible fixed speeds → no link, sustained; compatible → link returns | TC20, TC21 | **not measured** (A2) |
| 8 shutdown / no shutdown keeps fixed speed | TC23, TC24 | covered |
| 9 save + restart, fixed speed reapplied | TC32, TC33 | covered (whole-stack reload, 3 min) |
| 10 other ports unaffected; repeat with a changed speed | TC28, TC29, TC30 (S2 = 100) | covered, incl. `show log` for link flaps |

The script makes sense for the objective. Its 33 TestCases are a finer split of the 11 payload steps (one TestCase per sweep value);
that granularity is what makes a failing value cost exactly one PDU cycle, so it is worth keeping.

## (c) Improvements (structure / efficiency, without lowering output quality) and outdated tests

1. **Traffic check on link-up assertions** (A1). Highest value; changes a likely false PASS into a real result.
2. **Derive the incompatible pair from `speedMap`** (A2). Restores payload step 7 coverage on this and most benches.
3. **Merge TC14 + TC15 (+ TC16)**: three back-to-back read-only TestCases reading the same `show interface`/status/running-config with
   S in effect. Each TestCase costs ~70–80 s of framework overhead here (config snapshot, per-device tag analysis, boot-config save and
   stack sync, tear-down config diff). Merging saves ~2.5 min per run with identical checks.
4. **Stack boot-config sync dominates run time.** The framework writes `<dev>_9001_33235_<N>.cfg` and runs `boot conf` for every
   TestCase on every device; on the 3-member stack each `boot conf` sync took 3–60 s (several at 40–60 s; TC6/TC7/TC13/TC25/TC32), and
   one happens again in tear-down. That is roughly a third of the 56-minute run. Framework behaviour, not the script's — raise with the
   framework owner if run time matters (e.g. save once per TestSet when the case changes no startup state).
5. **Framework leaves per-TestCase .cfg files behind** — 33 per device, and the stack's backup members keep their own synced copies that a
   delete on the master does not remove (68 deleted by member path at restore). Recipe now covers it; the framework should clean up its
   own files. Also still on members 1/4 and not this case's: `stk_a_9001_33234.cfg` (2026-10-12) and `stk_a_9001_33234_1/_2.cfg`
   (2026-09-28), from earlier T33234 runs.
6. **Framework noise, harmless**: `show wireless apteryx info` returns `% Invalid input` on every IE520 at every TestCase start (framework
   probe, not the script); the tag analyser once logged a stray console escape `'!\x1b[K'` as an "unprocessed command" (TC24 stk_a).
   Neither affected a verdict.
7. **Outdated tests**: none. The 056114d change (pre-marking not-applicable cases before they run) worked on hardware for the first time
   here: TC20/21 skipped with no PDU cycle. Keep it.

## Bench/run facts worth carrying

- Software: awplus_main-20261008-57 on all four units; bootloader 9.2.0 on the IE520s. Stack 1 Backup / 3 Active Master / 4 Backup.
- Expected tally on this bench as wired today: 31 PASS / 2 UNSUPPORTED / 0 FAIL, 0 PDU cycles, 1 stack reload, ~56 min framework time
  (06:35:03–07:31:15) plus ~5 min setup and ~6 min restore.
- The one-leg isolation (stack port1.0.2 out of sa2) remains required; without it the copper role binds to an aggregator member and
  every DUT speed command is refused.
