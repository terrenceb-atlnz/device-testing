# Port group — IE520 stack, tb470, 2026-09-29

Queue: [../CAMPAIGN-QUEUE-2026-09-29.md](../CAMPAIGN-QUEUE-2026-09-29.md). Scripts: Ask-CK
generated `9001_Port/test-9001.33234.py` (+ `library_9001.py`, `ck_media.py`), run through
`/test-mode` with the bench-runner agent as tester (Terrence at the bench with a crossover cable).

| case | title | log | verdict |
| --- | --- | --- | --- |
| T33234 | Port — Auto MDI/MDI-X | [33234-fail.log](33234-fail.log) | **FAIL** — case 1: script defect (`no polarity` is `% Invalid input` on IE520 and x230; use `polarity auto`); case 2: REAL FINDING — a linked IE520 copper-SFP port reports `current polarity auto`, no resolved mdi/mdix role; cases 3–18 not run (framework power-cycled the whole bench after each failed case, twice; run stopped) |
| T33235 | Port — Fixed port speed | — | not run in this session (queue row 2) |

## What is in this directory
- `33234-fail.log` — the case log: gate, topology binding, the LAG isolation made for the run,
  the two failures with raw output, the two full-bench power cycles, the restore and its diff,
  the after-run probe.
- `pre-test-configs/u0..u5.show_running-config.txt` — from the 08:36 `bench_probe.py run`
  capture (`bench-setup/captures/2026-09-28T193600Z`), the baseline every restore is diffed against.
- `framework-run2/` — the framework's own output for the run that produced the verdict:
  `run.stdout`, `swi_*_33234.log` / `stk_a_33234.log` console logs (binary-ish: `grep -a`),
  per-case `*-tags.log`, PDU logs, `tb470.setup.asrun`.
- `framework-run1-aborted/` — run 1's stdout (bound the copper role to a LAG member; stopped
  3 s into configure(), nothing saved).
- `console-u2.log`, `console-u0.log` — my own console.py transcripts on the stack (u2) and the
  x230 (u0): the pre-run reads, the LAG/VLAN isolation and the restore.

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
