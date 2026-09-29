# Port group — IE520 stack, tb470, 2026-09-29

Queue: [../CAMPAIGN-QUEUE-2026-09-29.md](../CAMPAIGN-QUEUE-2026-09-29.md). Scripts: Ask-CK
generated `9001_Port/test-9001.33234.py` (+ `library_9001.py`, `ck_media.py`), run through
`/test-mode` with the bench-runner agent as tester (Terrence at the bench with a crossover cable).

| case | title | log | verdict |
| --- | --- | --- | --- |
| T33234 | Port — Auto MDI/MDI-X | [33234-unsupported.log](33234-unsupported.log) | **UNSUPPORTED** (run 3, 13:38–13:40, Test-cases d9a08dd): the IE520-28GSX has no fixed copper switchport (every front port is an SFP cage) and Terrence ruled MDI/MDI-X does not apply to pluggables (I-5); the framework marked all 14 cases unsupported on `swi_a` (`has_fixed_copper_port` missing), ran none, power-cycled nothing; bench restored, probe MISMATCH = only the pending SX link. Nothing on tb470 unblocks it. Earlier: run 2 FAIL (script defect `no polarity`, fixed b734b40; the `current polarity auto` reading that led to the ruling) — evidence in framework-run2/ |
| T33235 | (3) Port — Fixed port speed | [33235-partial.log](33235-partial.log) | **STOPPED — partial** (run 1 12:17–12:57, stopped on Terrence's instruction: "useless" without a fibre link). Cases 1–7 copper sweep on stack port1.0.9 ↔ x230 port1.0.4 PASS: `speed 10` rejected (`% Unsupported speed/duplex combination`), 100 and 1000 accepted and linked fixed, 2500/5000/10000 rejected at both ends; cases 8–12 fibre sweep `!!FAIL: … not applicable` = script grading (no fibre link on the bench), each followed by a full-bench power cycle (five); cases 13–30 not run. Bench restored, configs IDENTICAL, probe 13:08 MATCH. Re-run after fibre cabling (stack port1.0.25 ↔ IE520-sa port1.0.25) on Test-cases 3454bc0 |

## What is in this directory
- `33234-unsupported.log` — the case log (run 3, UNSUPPORTED): what the case needs, what the bench
  lacks, the ruling, the verbatim marking-pass lines, the framework's boot-config touch and its
  restore, the after-run probe; plus a pointer to the run-2 evidence. (Its git history holds the
  run-2 FAIL text: gate, LAG isolation, the two failures, the two power cycles.)
- `framework-run3-unsupported/` — run 3's framework output: `run.stdout`, `run.start`/`run.end`,
  `swi_*_33234.log` / `stk_a_33234.log`, `setup_33234.log`, `tb470.setup.asrun`,
  `probe-pre-run3.log`, `restore3.sh`.
- `console-u0/u1/u3/u5-33234-run3.log` — the run-3 restore transcripts (boot pointer + frame
  cfg deletion on the x230, 4050, IE520-sa and the stack master).
- `pre-test-configs/u0..u5.show_running-config.txt` — from the 08:36 `bench_probe.py run`
  capture (`bench-setup/captures/2026-09-28T193600Z`), the baseline every restore is diffed against.
- `framework-run2/` — the framework's own output for the run that produced the verdict:
  `run.stdout`, `swi_*_33234.log` / `stk_a_33234.log` console logs (binary-ish: `grep -a`),
  per-case `*-tags.log`, PDU logs, `tb470.setup.asrun`.
- `framework-run1-aborted/` — run 1's stdout (bound the copper role to a LAG member; stopped
  3 s into configure(), nothing saved).
- `console-u2.log`, `console-u0.log` — my own console.py transcripts on the stack (u2) and the
  x230 (u0): the pre-run reads, the LAG/VLAN isolation and the restore.
- `33235-partial.log` — the T33235 case log: gate, the loop found at 12:09 and broken, the
  two-leg isolation, cases 1–7 with raw output, the five fibre-case FAILs and their power cycles,
  the stop, the login/restore/diff/probe.
- `framework-run1-stopped/` — the framework's own output for T33235 run 1: `run.stdout`,
  `run.start`/`run.end`, `swi_*_33235.log` / `stk_a_33235.log` (grep -a), per-case `*-tags.log`,
  PDU logs, `tb470.setup.asrun`, plus `login-after-cycle5.log` (the six passive login watchers).
- `console-u0-33235.log`, `console-u1-33235.log`, `console-u2-33235.log`, `console-u3-33235.log` —
  console.py transcripts for T33235: the 12:13 loop-break and isolation (u0/u2), the post-stop
  reads and the restore on all four.

## Bench facts learned (candidates for orient-dt / memory, not yet folded)
1. The frame (Test-cases 4ef0dc4) sorts non-LAG links first and binds `cusfp` BEFORE `copper`,
   so on tb470 — where every stack partner link is a copper SFP in a LAG — a tester must free
   TWO links from their aggregator for the copper role to land on a non-LAG port.
2. Removing the last member of a static-channel-group auto-deletes `interface saN` and its
   lines on both the IE520 and the x230; the restore must recreate them (x230 sa2 carried
   `switchport access vlan 100`).
3. `no polarity` is not a command on either platform; `polarity auto` is the negation.
4. A linked IE520 copper-SFP port shows `current polarity auto` — the platform exposes no
   resolved mdi/mdix role on a pluggable copper PHY (measured on AT-SPTXa 1.0.2 and AT-SPTXc 1.0.9).
5. The framework power-cycles every bound device via the PDU after ANY failed TestCase
   ("Setup is no longer reliable"), ~3.5 min each — budget for it, or fix the failing step first.
6. (T33235) A frame role declared OPTIONAL at init ("the cases needing it report UNSUPPORTED")
   still graded `!!FAIL: … not applicable` in every case that needed it — five full-bench cycles
   for nothing. Check how a script grades an ABSENT optional role before launching on a bench
   that lacks it (Test-cases 3454bc0 excludes those cases up front).
7. (T33235) The x230-10GP's fixed copper ports reject `speed 2500/5000/10000` exactly as the
   IE520 copper SFP does, so a "partner accepts, DUT rejects" split never occurs on this pair;
   after a rejected DUT speed the frame's `duplex full` still lands (running-config keeps it)
   and the link drops until the partner is put back to auto.
8. Waking six consoles after a framework power cycle: open the port, send NOTHING until a
   banner or 20 s of silence, then one bare CR; `login:` -> `manager` -> `friend` -> `enable`.
   Six clean logins, zero `Login incorrect` (framework-run1-stopped/login-after-cycle5.log).
