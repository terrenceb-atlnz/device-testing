# T33234 process review -- mdix-2026-10-13T0949
Reviewed 2026-10-13 by /create-logs from `agent-a56f1efcb6f6b0267.jsonl` (tool inputs and result
sizes only) and the working files. Group-wide findings: [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 55 | 110 | 74,665 | 8,739,869 | 2,718 | 56 | 1,275 s | 59,244 chars |

Span: transcript calls #25-#80 (22:45:52Z-23:07:08Z = 11:45:52-12:07:08 NZDT). Two framework
TestSets ran for 6 min of the 21 min; most of the rest went on pre-launch checks and on polling.
Cache read (8.7 M) is high for a case that is UNSUPPORTED by definition: 55 calls each re-read a
~160k context.

## Process taken
1. #25-#29 copied the three ck.db scripts and the case setup into the case folder; offline
   preflight; `tools/tb fwprep` for 0004; three greps of the framework's `ATTestSet.py` on tb470
   (power-cycle and `--include-test-cases` behaviour).
2. #30 group baseline on u0/u1 (`prerun-u*.out`, 5,035 chars back); #31-#32 `tools/tb qmark`
   for polarity/speed/duplex on both units; #33 VLAN read-back from the baseline file.
3. #34 setup (u1 port1.0.2 up, u0 vlan 101).
4. #35-#39 pre-launch checks: x230 `polarity mdix` refused, 4050 forced mdi, link stays up;
   x230 mdi/mdix refused on both ports; 1000/half and 100/half by hand; restore.
5. #40 grep for the `--include-test-cases` flag handling; #41-#42 NEEDS TEST ENGINEER to the
   sentinel (the forced-polarity TestCases proposed UNSUPPORTED).
6. #43 after-setup configs; #44-#45 queue edits; #46 `dir *.cfg` pre; #47 run1.log started;
   #48 PDU status.
7. #49 0004 launched (`--include-test-cases 1 6`); #50-#54 and #59 six calls hunting for the
   result lines in `run.log`/`test-5000.0004.log`; #55-#58 four calls into the IE520
   `port-2026-10-12T1456/33234/work/` run for the result format; #60-#61 framework logs copied
   and grepped (4,809).
8. #62 0003 prepped and launched (`1 6 7 8 11`; the local call was cut by a 20 s timeout);
   #63 `ps` proof of one run; #64 answer to the sentinel (u2-u5 not opened); #65-#70 six
   wait/tail calls; #71 framework logs copied and grepped (11,743).
9. #72-#76 restore: boot pointers, 9 framework `.cfg` files deleted per unit, `rcdiff` clean.
10. #77 post-run probe; #78 logged-output ranges re-read; #79 run1.log finished; #80 RESULT
    (PASS).

## Wasted input
- #71 (11,743 chars) and #61 (4,809): after copying the framework logs, a broad
  `grep -aE '^>>|^<<|LOG /dev|admin up|current |configured |^%|RESULT|...'` printed every
  TestCase's detail. The results needed `grep -aE '^<<|^% |Skipping|TESTSET FINISHED'`
  (~1.2k for both). The detail sits in the copied file for the write-up.
- #51-#54, #59 (5,707 together): five greps on tb470 guessing the result format (`PASSED|FAILED`,
  `TestCase|TESTCASE`, `[Pp]ass|[Ff]ail`). The framework's per-TestCase line is always
  `<< test-<set>.<n>: PASS|FAIL (numPassed: N numFailed: M)`; one `grep '^<<'` does it.
- #30 (5,035): the baseline printed its full output back. Redirect-only plus one `grep` for
  `Current boot config|current |configured |admin up` (~800 chars) would have done.

## Repetition
- Waiting on the framework took 14 calls (#49-#54, #59, #62-#63, #65-#70): one `waitfor` with a
  30 s limit, then repeated tails and greps, the same again for 0003 with a 540 s and a 500 s
  `waitfor`. A single blocking call per TestSet (proposed below) replaces them.
- The result-format search was done once per TestSet (0004 at #51-#59, 0003 at #67-#69).
- #55-#58 opened another campaign's working files to learn the framework's result format,
  a fact that belongs in a reference (below).

## Accuracy risks
- **The verdict.** The tester graded PASS on the copper-SFP framework TestCases. The Test
  Engineer's ruling (2026-09-29, `IE520/port-2026-09-29/33234-unsupported.log`): an SFP is not
  a fixed copper port for MDI/MDI-X, so an all-SFP DUT makes this case UNSUPPORTED before
  anything runs. The case was re-graded UNSUPPORTED. The tester read another campaign's T33234
  run (#55-#58), but only for the result format, and neither the triage nor the run read the
  earlier verdict of the same case id. That ruling is now in
  `.claude/memory/sfp-is-not-a-fixed-copper-port.md` and `platforms/x230v2-28GS.md` §2.
- **The working log contradicts the Results table.** `run1.log` still ends `Run: CLEAN` /
  `VERDICT: PASS`; the final log follows the Results table (UNSUPPORTED, Test Engineer re-grade).
- **"All 28 ports are SFP cages" is not printed by this run.** `show system pluggable` lists
  only the populated cages 1.0.1-1.0.8; the final log states the rest as the platform fact the
  ruling rests on. A `show interface port1.0.9` (or any empty cage) in the baseline would close
  it, or one quote of the platform doc in `platforms/x230v2-28GS.md`.
- **The DUT's resolved MDI/MDI-X role is never visible**: the x230 reports
  `current polarity auto` on both copper SFPs in every reading. STEP 1.2's "the DUT end adapted"
  is inferred from the link coming up, and the partner's `current polarity` is the only
  observed role.
- **TC9/TC10 rest on a ruling, not a refusal.** The parser offers `speed auto 10` (qmark) and no
  10 Mb/s command was sent, so "not supported" has no device line in this run.
- **Unsourced and left out of the final log:** the run log's "(the SFP end auto-crosses)" and
  "the PHY is in the module" (inferences, no device line); the AW+ `polarity` usage note quoted
  in the IE520 log (not in this run's files). The 4050 port1.0.5 VLAN was never read, so
  TOPOLOGY omits it.

## Next run: expected outputs
A DUT with no fixed RJ45 switchport: grade UNSUPPORTED at triage and run nothing
(`platforms/x230v2-28GS.md` §2). If the case is ever run on the copper SFPs for evidence again:

| check | this bench gave |
| --- | --- |
| x230 `polarity mdi` / `polarity mdix` on port1.0.1 or port1.0.8 | `% Polarity set failed port1.0.N`; log `EXFX[691]: DBG:exfx_port_polaritySet 1859: Polarity mode not supported on this interface.` |
| x230 `polarity auto` | accepted; `current polarity auto` always |
| 4050 port1.0.5 `polarity mdi`, x230 auto, crossover | link down/up in 3 s, then running 1000/full, 4050 `current polarity mdi` |
| auto both ends, crossover | 1000/full, 4050 `current polarity mdix` |
| auto both ends, straight | 1000/full, 4050 `current polarity mdi` (0003 TC1) or `mdix` (TC11) |
| `speed auto 1000` + `duplex half` (both units) | `% Cannot set speed 1000 and half duplex port1.0.N` |
| `speed auto 100` + `duplex half` / `full` | link up, current 100 half / full both ends |
| framework result line | `<< test-5000.000N.<tc>: PASS (numPassed: 5 numFailed: 0)` |

## Next run: scripts
- Existing: `tools/tb ckcon`, `tools/tb qmark` (the defaulting-command check took one call per
  unit), `tools/rc2cfg.py`, `tools/rcdiff.py`.
- Proposed: `tools/tb fw ... --wait <s> --summary <local dir>`: launch, block until `run.exit`,
  copy `run.log run.exit test-*.log setup_*.log swi_*_*.log` into `<local dir>`, print only
  `^<<|^% |Skipping TestCase|TESTSET FINISHED`. Replaces #49-#54, #59-#71 (about 20 calls).
- Proposed: `tools/fwclean.py --box tbNNN --units u0,u1 --set 5000_0003,5000_0004`: reset the
  boot pointer and delete the framework's `swi_X_<set>[_N].cfg` and `TestCase_tear_down.cfg`
  files (the #72-#75 restore, the same after every `--nodefaultcfg` run).

## Next run: references
- `platforms/x230v2-28GS.md` §2, rows "All 28 ports are SFP cages" and "Copper SFPs refuse
  forced polarity": the verdict and the evidence, read at triage.
- `.claude/memory/sfp-is-not-a-fixed-copper-port.md`: the ruling and its scope (MDI/MDI-X only).
- The framework result line format (`<< test-...: PASS (numPassed ...)`): proposed for
  `tools/README.md` under `tb fw`, so no tester greps another campaign for it.
