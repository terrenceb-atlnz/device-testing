# T33235 "(3) Port - Fixed port Speed" — validation review (Ask-CK run 2026-10-13T1223-val-3ede)

Reviewer: the sentinel session, /test-mode §11 step 2, 2026-10-13 ~13:50 NZDT. This is analysis only: **the framework's
verdict stands** (PASS, 12 PASS / 2 UNSUPPORTED / 0 FAIL of 14 TestCases, rc 0), and no Results row changes here (memory
`grading-authority-tier-list`).

**Inputs:**
- `work/run1.log`: the tester's working log, verdict PASS.
- `work/framework-run1/test-9001.33235.log` and `run.log`.
- The case payload `ask-ck/functions/generator/refined-cases/Port/AWPTCM-T33235/zephyr_payload.json` (11 steps).
- The script copy `work/test-9001.33235.py`: unedited, sha1 f04ea359…, Test-cases ef53cea. This is the grouped version:
  14 framework TestCases instead of 33, and step 29 runs without confCheck.
- The previous review, `tb470/IE520/port-2026-10-13T0626/33235/review.md`: same case, previous script version, x230 as
  the partner. Its findings are referred to below as 0626-A1…A4 and 0626-c1…c7.

**What the script bound to** (DUT = IE520 stack `stk_a` via swi_a/u2; every partner is the IE520-sa `swi_b`):
- **Copper test port:** port1.0.10 (AT-SPTXc 1000BASE-T) ↔ sa port1.0.2 (AT-SPTXc). This is link C.
- **Monitored copper-SFP port:** port1.0.6 (AT-SP10TM 10GBASE-TM) ↔ sa port1.0.14. This is link M, in VLAN 106.
- **Fibre test port:** port4.0.26 (AT-SPSX) ↔ sa port1.0.26 (AT-SPSX), in VLAN 4000.
- **Setup:** none was needed; both links were recabled and saved by the Test Engineer before the run.

**Was the run clean?** Yes, by Terrence's definition.
- No exception, no Python error, no refused setup, defaulting or tear-down command, and no missed config step.
- Every `%` line answers a deliberate sweep or negative step. The exceptions are the framework's own
  `show wireless apteryx info` probe, once per device, and an information-only `% Already logged onto stack member 3`.
- 0 PDU cycles and 1 planned whole-stack reload (TC31_to_33).
- No repair was needed. `repairs.md` R1, the pre-run exception-log check, found nothing to clear.
- So the script needs no repair: there is no `REPAIRED` line.

---

## (a) The logs — false positives and false negatives

### A1. Link-up is still judged only from the status display; this run shows no false PASS, but the gap remains
- Every "link re-established" check reads only the status row, `show interface` and running-config. That covers
  TC1_to_7, TC8_to_12, TC13, TC22_to_24, TC25, TC26_to_27, TC30 and TC31_to_33. 0626-A1 showed why that is weak:
  - On this build an AT-SPSX forced to `speed 100` read `connected … 100` while passing no traffic. That was stack port1.0.3
    against the x230, and T47209 on 2026-10-09.
  - So TC8 was a likely false PASS there.
- **Today TC8 cannot repeat that false PASS.** Both SX ends **refused** `speed 100`. The DUT kept configured speed auto and
  current speed 1000, so STEP 9 recorded a rejection, and that PASS is real.
  - **New DUT observation, the same build (awplus_main-20261008-57), the same module type (AT-SPSX), and opposite answers:**
    - stack port1.0.3 on member 1 *accepted* `speed 100` in 0626;
    - stack port4.0.26 on member 4 *rejected* it today, as did the IE520-sa's port1.0.26.
  - Whether a 1000BASE-SX port takes `speed 100` should not depend on the port. Worth raising with the IE520 owner. It
    could be a per-port PHY or front-port-group difference, or the earlier acceptance was the defect. That would square
    with T47209, where the port accepted it and then passed no traffic.
- The copper links this run did link at 100 and 1000 with an IE520 partner. I have no reason to doubt those PASSes.
- **0626-c1 still applies:** add a traffic or liveness check to every link-up assertion. Any one of these would do:
  - an LLDP neighbour seen on the partner;
  - a ping or ARP across the link's VLAN;
  - rx/tx counter deltas on both ends.

  Then a port that reads "connected" but passes nothing becomes a FAIL instead of a PASS. It is still a clean run, because
  the defect is the DUT's.

### A2. TestCase_20/21 UNSUPPORTED is still a coverage gap, not a platform limit (0626-A2, not fixed in ef53cea)
- At 12:46:32 the pre-mark reads "the sweep recorded speed 10=False, speed 100=True on port1.0.10; step 21 needs the DUT
  to accept both". STEP 21 still hard-wires the incompatible pair as **DUT 100 / partner 10**.
- This bench had a valid incompatible pair all along: **1000 / 100**. Both ends accepted both values in the copper sweep
  (TC3 `speed 100`, TC4 `speed 1000`), in S = 1000 (TC13) and in S2 = 100 (TC30).
- So payload step 7 was testable here and went unmeasured because of the script's choice of pair. It is the only payload
  step with no result in this run (see (b)).
- **Recommendation, unchanged:**
  - choose the pair from `speedMap`: any two fixed speeds that both ends accepted, the DUT at one and the partner at the
    other;
  - mark UNSUPPORTED only when fewer than two common fixed speeds exist.

  That turns 2 UNSUPPORTED into 2 measured cases on this bench and on the 0626 bench.

### A3. A rejection counts as "clear" whatever the error text says (0626-A3, unchanged)
- `speed 5` returns `% port1.0.10: Speed or duplex must be auto port1.0.10` (TC18). The script accepts any `%` line, so
  the payload's "rejected with a clear error" is not judged.
- The message is misleading for an out-of-range value: it reads like a duplex conflict. That is a possible minor DUT UX
  finding.
- `speed 200000` and `speed 10000` gave the clearer `Unsupported speed/duplex combination`, and `speed fast` gave `% Invalid`.
- **Recommendation:** grade the error text against an expected pattern, if the case owner wants "clear" judged.
  - TC18's PASS lines already carry the raw console reply.
  - TC17 records only the indicator tokens (`['%', 'Invalid']`).

### A4. "Auto-negotiation disabled" is still inferred from the missing `a-` prefix (0626-A4, unchanged)
- This held on every row this run: `a-full a-1000` changed to `full 1000` in TC13, TC14, TC24 and TC33, and back again in
  TC25 and TC27.
- It is acceptable, but indirect: IE520 `show interface` has no explicit auto-negotiation field.
- A change in the status-row format would read as a FAIL, never as a false PASS.

### A5. New, minor: the S2 candidate list ignores the sweep's own record (TC30, STEP 31)
- At 13:12:15 the log reads "S2 candidates for port1.0.10 (excluding S = 1000): ['100', '10']", although the copper sweep
  had recorded `speed 10` as rejected on that port.
- The code (`TestCase_30`, around line 5785) builds the list from a fixed table filtered only by `< S1` and `!= S`. The
  comment above it says S2 uses "the same accept/link criterion the steps 3-8 sweep records", but `speedMap` is never read.
- No effect today, because 100 was tried first and linked.
- On a bench where the higher candidate fails to link, the loop would go on to send a speed the sweep already knows is
  refused, on both partner and DUT. That would add a `%` line and an extra reconfigure. It would not give a wrong verdict.
- **Fix:** filter `candidateSpeeds` by `speedMap[...] is True`.

### No false negatives found
- **Negative steps:** every one checked the rejection **and** that running-config, configured speed and link state were
  unchanged afterwards. These are TC2, TC5–7, TC9 (SX 100), TC10–12, TC17, TC18 and TC19.
- **The partner rejecting first:** in TC8 the partner refused SX `speed 100` before the DUT was tried. The script logged
  "judging only the DUT, link-up not asserted" and judged the DUT on its own answer. That is correct.
- **Return to auto:** TC25 (`no speed`) and TC27 (`speed auto`) each got the `a-` prefix back and matched the step-2
  baseline of 1000/full.
- **Other ports unaffected:** in TC29 and TC30 the monitored ports port1.0.6 and port4.0.26 kept identical rows and current
  values, and `show log` had no link event for them.

## (b) Objective and steps vs the script

| payload step | script (framework TestCase) | verdict |
| --- | --- | --- |
| 1 baseline: link up, negotiated speed, duplex, autoneg | TC1_to_7 (STEP 2) | covered |
| 2 each fixed speed on copper and fibre; link re-establishes; speeds match | TC1_to_7 copper (100 ✓, 1000 ✓; 10, 2500, 5000, 10000 refused), TC8_to_12 fibre (1000 ✓; 100, 10000, 40000, 100000 refused) | covered for the test ports' modules; link-up is judged from the status display only (A1) |
| 3 autoneg reported disabled with a fixed speed | TC14_to_18 (TC14) | covered (A4) |
| 4 configured vs operational; status and running-config agree | TC14_to_18 (TC15, TC16) | covered |
| 5 `no speed` and, separately, `speed auto` → autoneg enabled again | TC25; TC26_to_27 | covered |
| 6 invalid, out-of-range, and unsupported-on-this-media values rejected; state unaffected | TC14_to_18 (TC17, TC18), TC19, plus the sweep's rejections | covered (A3) |
| 7 incompatible fixed speeds → no link over a sustained period; compatible → link returns | TC20, TC21 | **not measured** (A2) |
| 8 shutdown / no shutdown keeps the fixed speed | TC22_to_24 | covered |
| 9 save and restart; the fixed speed is reapplied | TC31_to_33 | covered (whole-stack reload, 13:15–13:18) |
| 10 other ports unaffected; repeat with a changed speed | TC28 (baseline, no confCheck), TC29, TC30 (S2 = 100) | covered, including `show log` for link flaps |

The script makes sense for the objective. One coverage note on step 2's "each speed supported by the port":
- The copper test port is the role-bound 1000BASE-T SFP, so only 100 and 1000 can be exercised.
- On this bench the *monitored* port (link M) holds an AT-SP10TM (10GBASE-TM). It is likely multi-rate (2.5G, 5G and
  10G are plausible; **not measured**: the CLI's `speed` help lists 10–400000 on every port whatever the module). The
  script never sweeps it, because the cusfp role is monitor-only.
- Whether the case owner wants a multi-rate copper module swept as a second copper test port is their call. It would add
  real coverage (2.5G and 5G fixed speeds) wherever such a module and a matching partner exist. Here both ends of link M
  are SP10TM.

## (c) Improvements and outdated tests

1. **The grouping in ef53cea works and pays off.**
   - Framework time was 38 min 49 s (12:40:56–13:19:45), against 56 min for the 33-TestCase version in 0626. That saves
     about 17 min per run with the same checks: 256 checks passed here.
   - Step 29 without confCheck worked. This also covers 0626-c3, merging the read-only TC14–16.
   - The cost of grouping is that a failing step now power-cycles once for the whole group rather than once for that
     step. That is the right trade while the groups pass.
2. **Traffic or liveness check on link-up assertions** (A1, 0626-c1). Still the highest-value change.
3. **Derive the incompatible pair from `speedMap`** (A2, 0626-c2). This restores payload step 7.
4. **S2 candidates from `speedMap`** (A5). A one-line filter.
5. **Record and, optionally, grade the rejection text** (A3).
6. **Framework, not script:**
   - The per-TestCase `<dev>_9001_33235_<N>.cfg` files and their stack-member copies are left behind for the restore to
     delete (0626-c5).
   - The `show wireless apteryx info` probe errors on every IE520 (0626-c6).
   - Both are unchanged and harmless to verdicts.
7. **Outdated tests:** none.
   - The 056114d pre-mark worked again: TC20 and TC21 were skipped with no PDU cycle.
   - The 3454bc0 fibre-exclusion gate correctly did *not* fire, because a fibre link was present.

## Bench and run facts worth carrying

- **Software:** awplus_main-20261008-57 on all four IE520s.
- **Stack roles:** 1 Backup / 3 Active Master / 4 Backup.
- **Partner:** the IE520-sa for every role. There is no x230 or AR4050S in this run (the session constraint).
- **Expected tally on this bench as wired today:** 12 PASS / 2 UNSUPPORTED / 0 FAIL, 0 PDU cycles, 1 stack reload,
  about 39 min framework time, plus about 3 min of pre-run checks and about 7 min of restore and probe.
- **Links C and M are not yet in the deployed `tb470.setup`.** Recording them is the Test Engineer's `bench_probe.py
  apply`. Until then this case runs from the run .setup `port-2026-10-13T1223/tb470-u2u5.setup`.
