# T33234 "Port - Auto MDI/MDI-X" -- validation review (Ask-CK 2026-10-12T1455-val-0210)

Reviewed 2026-10-12 by the sentinel (/test-mode §11 step 2), in context, from:
- `work/run1.log` and `work/framework-run1/`;
- the script as run, `work/test-9001.33234.py` (byte-identical to Test-cases
  `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33234.py`, sha1 66c23163, d9a08dd), and
  `work/library_9001.py`;
- the case text, `ask-ck/functions/generator/refined-cases/Port/AWPTCM-T33234/zephyr_payload.json`.

**Analysis only. The framework's verdict stands:** UNSUPPORTED, graded by the tester (memory
`grading-authority-tier-list`). Nothing here changes a Results row.

Run under review: run 1, 15:04:25-15:07:15 NZDT, rc 0, **clean**, 0 power cycles, no repairs. Bench: tb470,
DUT `swi_a` = IE520-28GSX stack `stk_a` (awplus_main-20261008-57).

---

## (a) The logs: false positives / false negatives

**This run: none found.** The verdict rests on printed output, not inference:
- Discovery printed the media of every data link on the DUT, read from the DUT itself:
  `cusfp=port1.0.17,port1.0.2,port3.0.2,port4.0.2; fibre=port1.0.3,port4.0.26; tb=port3.0.13`.
- The live `show system pluggable` agrees: every twisted-pair data port is a cage holding AT-SPTXa or AT-SP10TM.
  The IE520-28GSX has no RJ45 front port (platforms/IE520.md §3).
- So `has_fixed_copper_port = False`, and the framework's marking pass printed 14/14 "marked as unsupported
  ... without property has_fixed_copper_port, for device swi_a".
- UNSUPPORTED is the right verdict under Terrence's 2026-09-29 ruling (MDI/MDI-X applies to fixed copper
  switchports only). It is not a missed enable step: polarity has no enable.
- The only `% ` lines answer the framework's own commands, not the script's: `show wireless apteryx info`
  (capability probe) and `remote-login 3` ("Already logged onto stack member 3"). They are noise, not
  findings.

**Latent: a false FAIL on a bench that does have fixed copper.** This run could not show it, because no
TestCase body ran.
- **Operator prompts.** `yesNo()` (library_9001.py:305) asks for physical cable swaps 5 times: lines 753 and
  788 (TestCase_3), 1228 and 1267 (TestCase_7), 1340 (TestCase_8 configure). An unattended framework run (Ask-CK,
  `tools/tb fw` under `sudo -n`, no tty) gets EOF, so `yesNo` returns False and the case calls `failed()`.
  - Under logged-output.md §1, a physical precondition that could not be met is **PARTIAL**, not FAIL.
  - Each such FAIL also costs a full-bench power cycle (STANDING-ORDERS §6, about 4 min on tb470).
  - TestCase_4/5/6 then run against a straight-through cable while expecting a crossover. Their
    "inverse resolution" checks fail for a bench reason, not a product reason.
  - So an unattended run on a fixed-copper DUT would be a systematic failure: at least 5 TestCases, about 5
    power cycles, and a misleading FAIL verdict.
- **Fix (mechanics, not a loosened check):** when no operator is attached (`not sys.stdin.isatty()` or an
  explicit run flag), mark the cable-swap TestCases UNSUPPORTED or skip them with a "needs operator for
  recable" reason, instead of failing them. Better still, move them into their own operator-attended
  TestSet (STANDING-ORDERS §6: a case that needs a different physical setup is a different TestSet).

## (b) Objective and steps against the script

The payload has 1 note step and 11 action steps (2-12). The script has 14 TestCases, which log STEP 2-15, plus
a suite STEP 1 (the defaulting commands). How they map:

| payload step | script | meets it? |
| --- | --- | --- |
| 2 straight-through, auto, roles opposite | TestCase_1 (STEP 2) | yes. Exact-token parse of `current polarity`, link UP, `a-` duplex, opposite roles |
| 3 crossover, compare with straight | TestCase_3 (STEP 4, swap) + TestCase_4 (STEP 5, compare) | yes, **operator-dependent** (see (a)) |
| 4 auto is the default on a never-configured port | TestCase_2 (STEP 3) | **partly.** Suite `configure()` and TestCase configures send `polarity auto` first, so the port HAS been explicitly configured (to the default value) before TestCase_2 reads it. The running-config looks the same, but "never explicitly configured" is not literally what is tested |
| 5 force MDI / MDI-X on both cable types | TestCase_5, _6 (crossover), _7 (swap back), _8, _9 (straight) | yes. The partner is forced to the non-pairing role so the negative case can go DOWN (`force_partner_polarity`). Operator-dependent through TestCase_7/_8 |
| 6 return to auto | TestCase_12 (STEP 13) | yes |
| 7 copper SFP | **none: stripped** (ruling 2026-09-29) | n/a by ruling. The payload's objective bullet 4 still asks for it |
| 8 fibre SFP "not applicable" | **none: stripped** (ruling 2026-09-29) | n/a by ruling. See "outdated" below |
| 9 invalid values rejected | TestCase_10 (STEP 11): `polarity mdi-x`, `crossover`, `1`, bare `polarity` | yes on a copper port. But it is gated on `has_fixed_copper_port` like everything else, although a parser-rejection check needs no copper link |
| 10 shutdown / no shutdown keeps role | TestCase_13 (STEP 14) | yes |
| 11 forced polarity across a **port reset**, "rather than an administrative cycle" | TestCase_11 (STEP 12) | **no, not as written.** It issues `shutdown` / `no shutdown`, the same administrative cycle as TestCase_13, so the step's distinguishing condition is not exercised. Its own STEP text admits the substitution ("e.g. shut/no shut driven as a port reset") |
| 12 polarity + duplex combinations with a shutdown | TestCase_14 (STEP 15) | yes |

**Does the script make sense for the objective?** Yes, for a fixed-copper DUT. Discovery reads the media from
the DUT. Verdicts use exact tokens (`mdix` can never satisfy `mdi`). Defaulting uses `polarity auto`, never the
refused `no polarity` (b734b40). Configure/teardown send nothing when no copper link is bound, which is why this
run cost no power cycle.

## (c) Improvements and outdated tests

1. **Unattended mode for the cable-swap cases.** This is the most valuable change; see (a). Without it,
   Ask-CK cannot validate T33234 on any fixed-copper bench without someone at the bench.
2. **TestCase_11 "port reset".** Find a reset that is not `shutdown` / `no shutdown` (check the AW+ CLI wiki
   on the share; memory `awplus-cli-wiki-on-the-share`, no IE520 pages, so read x230). If none exists on the
   target platform, say so in the step and grade that part UNSUPPORTED. Do not label an administrative cycle
   a reset. At present TestCase_11 is TestCase_13 with forced polarity.
3. **Ungate TestCase_10 (invalid values)?** A CLI-parser rejection test runs on any switchport. But the
   09-29 ruling says polarity does not apply to cages, so running it on a cage is **Terrence's call**, not
   a mechanics fix. If allowed, it would give a real measurement on the IE520 instead of UNSUPPORTED.
4. **Dead code left by the 09-29 strip.** `NOT_APPLICABLE_MARKERS`, `cli_refused_for_media`,
   `assert_role_media_now`, `FIBRE_TYPE_RE` and `COPPER_TYPE_RE` are defined but never called (one reference
   each, the definition; the markers tuple is used only by the unused function). The 20-line comment about
   "step 19" (lines 81-87) describes a fibre case that no longer exists. Removing them shortens a 2448-line
   script and stops a reader looking for a fibre check that is not there. The optional `tb` binding
   (line 375) is also unused by every TestCase.
5. **STEP numbering.** Script STEP n is payload step n-1 for the first few, then the mapping diverges (payload
   5 spans STEP 6-10). Tag each TestCase's log line with the payload step it serves (e.g. `STEP 6 (case step
   5a)`) so a reviewer can trace a FAIL back to the Zephyr step without this table.
6. **TestCase_2 precondition.** To test "never explicitly configured", read the port BEFORE the suite's
   defaulting, or pick a port whose running-config has no `polarity` line at the start of the run, and
   record that it does. Otherwise reword the step to "after returning to default".
7. **Outdated case text (Test-cases side, not this repo's to edit):**
   - Objective bullets 4 (copper SFP) and 5 (fibre "reported as not applicable") and payload steps 7-8 are
     out of scope by the 2026-09-29 ruling, but the payload does not say so.
   - Step 8's expectation also contradicts measured IE520 behaviour: the CLI accepts `polarity` on fibre /
     cage ports with no error (platforms/IE520.md §3). So if it were ever reinstated it would FAIL on the
     IE520 for a reason the ruling already settled.
   - Suggest updating the Zephyr case (or the refined case) to record the ruling and drop or re-scope those
     steps.
8. **Framework side effect worth knowing.** Even an all-UNSUPPORTED run rewrites the boot config on every
   bound device (`boot conf <dev>_9001_33234.cfg`), so a restore is always needed. On the IE520 stack that
   took 64 s of SPIFlash sync. That is not the script's doing; it is noted so the restore recipe is never
   dropped "because nothing ran".
9. **Tooling (device-testing side):** `tools/tb fw` did not detach after "started". Its ssh stayed open for
   the whole run (first use). The run was unaffected, but the README's "never run" status for `fw` / `fwprep`
   should be updated, and the detach fixed.

**Bottom line:** for the bench Ask-CK targeted (tb470, IE520 stack), the script is correct and runs clean to a
genuine platform UNSUPPORTED with no bench cost. For a fixed-copper DUT, item 1 is the blocker to an unattended
validation, and item 2 is the one place where the script does not test what the step says.
