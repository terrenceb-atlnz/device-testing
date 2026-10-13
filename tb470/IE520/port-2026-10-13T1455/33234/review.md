# T33234 "Port - Auto MDI/MDI-X" -- validation review (Ask-CK 2026-10-13T1454-val-43dd)

Reviewed 2026-10-13 by the sentinel (/test-mode §11 step 2), in context, from:
- `work/run1.log`, `work/framework-run1/` and `work/repairs.md` (none);
- the script as run, `work/test-9001.33234.py` (byte-identical to Test-cases
  `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33234.py`, sha1 66c23163, d9a08dd);
- the case text, `ask-ck/functions/generator/refined-cases/Port/AWPTCM-T33234/zephyr_payload.json` (unchanged since 2026-09-17);
- the previous validation of the same script, `tb470/IE520/port-2026-10-12T1456/33234/review.md` ("the 10-12 review").

**Analysis only. The framework's verdict stands:** UNSUPPORTED, graded by the tester (memory
`grading-authority-tier-list`). Nothing here changes a Results row.

Run under review: run 1, framework 15:02:19-15:03:57 NZDT (1 min 38 s), rc 0, `run.exit` 0, **clean**, 0 power
cycles, 0 reloads, no repairs. Bench: tb470 consoles u2-u5 only, run .setup `port-2026-10-13T1455/tb470-u2u5.setup`
(stk_a + swi_b, no x230 / AR4050S), DUT `swi_a` = IE520-28GSX stack `stk_a` (awplus_main-20261008-57), partner the
IE520-sa (swi_b) over the recabled links C (port1.0.10-port1.0.2, AT-SPTXc) and M (port1.0.6-port1.0.14, AT-SP10TM).

**What is new against 10-12:** the script and case text are the same; the bench is not. The 10-12 run had the
x230 (which does have RJ45 ports) declared as a partner, and the DUT's copper-SFP links went to it. Today the only
partner is another all-SFP IE520 and two fresh copper-SFP links were cabled. The verdict is the same, so the
`has_fixed_copper_port` gate is shown to depend on the DUT's own media only, not on the partner or on which
copper SFPs are linked.

---

## (a) The logs: false positives / false negatives

**None found.** The verdict rests on printed, DUT-read evidence:
- `topology discovered on swi_a: tb=port3.0.13<->tb.eth1; cusfp=port1.0.6<->swi_b.port1.0.14,port1.0.10<->swi_b.port1.0.2;
  fibre=port4.0.26<->swi_b.port1.0.26` (15:02:24). Both recabled twisted-pair links classify as `cusfp`, including
  the 10GBASE-TM module on link M (`ck_media` maps `BASE-T[A-Z0-9]*$` to twisted pair, and `show system pluggable`
  lists the port, so it is a cage). No `copper` entry, so `has_fixed_copper_port = False`.
- The script's own line states the ruling: "UNSUPPORTED: no copper switchport on DUT; polarity does not apply to
  pluggable/fibre ports - every test case will be marked unsupported (data links discovered: 1 tb, 2 cusfp, 1 fibre)",
  then "suite setup skipped" (15:03:22), then the framework marked TestCases 1-14 unsupported for `swi_a`.
- That is the correct verdict under Terrence's 2026-09-29 ruling (memory `sfp-is-not-a-fixed-copper-port`;
  platforms/IE520.md "MDI/MDI-X polarity is UNSUPPORTED"). It is not a missed enable step: polarity has no enable.
- The only `% ` lines answer the framework's own commands (`show wireless apteryx info` capability probe;
  `remote-login 3` "Already logged onto stack member 3"), as on 10-12. Noise, not findings.
- Cosmetic: the framework's marking line reads "marked as unsupported on .* platform without property ..." -- the
  literal `.*` is the platform regex printed unformatted (framework side, harmless, also on 10-12).

**Latent false FAIL on a fixed-copper bench: still open, unchanged** (10-12 review (a)). The five `yesNo()` cable-swap
prompts (TestCase_3, _7, _8) fail unattended and cost a power cycle each. Today's triage recorded this as a MANUAL-ONLY
row (MANUAL-ONLY.md, 2026-10-13), so an unattended device-testing campaign will no longer schedule those steps; the
script itself still fails them rather than reporting them as needing an operator.

## (b) Objective and steps against the script

Unchanged from the 10-12 review (b); the script and payload are byte-for-byte the same. In short:
- payload steps 2, 5, 6, 9, 10, 12 are met on a fixed-copper DUT (steps 3 and 5 operator-dependent);
- step 4 is met only "after returning to default", not "never explicitly configured" (the suite sends
  `polarity auto` first);
- step 11 is **not met as written**: TestCase_11 uses `shutdown`/`no shutdown`, the same administrative cycle as
  TestCase_13, not a port reset;
- steps 7 (copper SFP) and 8 (fibre "not applicable") are stripped by the ruling, while the payload's objective
  bullets 4 and 5 still ask for them.

For the bench Ask-CK targeted, the script makes sense: it reads media from the DUT, sends nothing when no copper
link is bound, and exits clean with no bench cost.

## (c) Improvements and outdated tests

Carried from the 10-12 review (c), still open, in priority order:
1. **Unattended handling of the cable-swap TestCases** (mark them needs-operator / UNSUPPORTED, or move them to an
   operator-attended TestSet) instead of failing on `yesNo` EOF.
2. **TestCase_11 "port reset"**: find a real reset or say UNSUPPORTED for that part; do not relabel shut/no shut.
3. **TestCase_10 (invalid values)** needs no copper link to test the parser; whether it may run on a cage is
   Terrence's call under the ruling, not a mechanics fix.
4. **Dead code from the 09-29 strip** (`NOT_APPLICABLE_MARKERS`, `cli_refused_for_media`, `assert_role_media_now`,
   `FIBRE_TYPE_RE`, `COPPER_TYPE_RE`, the "step 19" comment, the unused `tb` binding).
5. **STEP numbering** traceable to payload steps.
6. **TestCase_2 precondition** ("never explicitly configured").
7. **Outdated case text** (Test-cases side): record the ruling in the refined case / Zephyr and drop or re-scope
   objective bullets 4-5 and payload steps 7-8.

New from this run:
8. **pt_preflight is media-blind and says RUNNABLE for this case on an all-SFP DUT.** At triage it reported the
   copper role "can take port1.0.10-port1.0.2", but that port is an AT-SPTXc cage. For T33234 specifically, a
   preflight that can read `show system pluggable` from the latest bench capture (or the generated bench-state.md)
   could report "UNSUPPORTED expected: no fixed copper" before launch. Ask-CK's own pre-run check would then not
   show a green RUNNABLE for a case that cannot run on this platform.
9. **An all-UNSUPPORTED run still costs a restore.** The script logs "suite setup skipped", yet the framework still
   rewrote the boot config on stk_a and swi_b (`boot config-file <dev>_9001_33234.cfg`, plus the files on stack
   members 1 and 4). The restore recipe is still needed even though nothing ran (as on 10-12 item 8). If the case
   could be decided UNSUPPORTED before the framework's per-device save (for example, a class-level property check
   before `init_all_devices`), a run on an all-SFP DUT would leave the bench untouched.
10. **Residue from an older run.** Stack members 1 and 4 still hold `stk_a_9001_33234_1.cfg` / `_2.cfg` from
    2026-09-28 (queue I-2, NOTIFY sent). They are not this run's. They show that the 09-28 restore cleaned the master
    only; today's recipe deletes on the backups too (memory `stack-refused-command-lands-on-backups` describes the
    same "master is not the whole stack" pattern).

**Bottom line:** two validations on two different partner sets now show that the script runs clean to a genuine
platform UNSUPPORTED on the IE520, with no bench cost beyond the boot-config restore. Nothing needed repair. The
open work is for a fixed-copper DUT (items 1-2), the case text (7), and making the UNSUPPORTED outcome visible
before launch (8-9).
