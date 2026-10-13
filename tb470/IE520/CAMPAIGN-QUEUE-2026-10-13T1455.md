# Campaign queue — tb470, IE520 stack (`stk_a`) as the DUT, 1 AWPTCM script case (Ask-CK validation), from 2026-10-13 14:55 NZDT

The ask, 2026-10-13 14:55 NZDT (`/test-mode --from-ask-ck`, Ask-CK's launcher):
*"/test-mode --from-ask-ck /home/terrenceb/.local/share/ck-agent/runs/2026-10-13T1454-val-43dd/2026-10-13T1454-val-43dd.json AWPTCM-T33234"*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-13 14:55 NZDT, word for word from the Ask-CK hand-off `2026-10-13T1454-val-43dd.json`
(schema 1, run_id `2026-10-13T1454-val-43dd`, kind `validation`, seat `10.33.22.17`, created 2026-10-13T14:54:46+13:00):
Test Engineer: terrenceb@terrenceb-dl
Driver: ask-ck (2026-10-13T1454-val-43dd)
Testbox: "tb470"
Consoles: "u2-u5"
PDU: {"ip": "10.36.150.14", "outlets": {}}
Constraints: "do not attempt to use the 4050 or x230 for this run; recabled: stack port1.0.10–IE520-sa port1.0.2 (link C, VLAN 1); stack port1.0.6–IE520-sa port1.0.14 (link M, both ends in VLAN 106 \"link-m\", saved in tb470-bench.cfg)"

Hand-off case entries:
- AWPTCM-T33234 — kind `script`, script_rel `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33234.py`
  (resolved: `claude/Test-cases/ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33234.py`, read-only;
  sha1 66c2316363f8…, last changed Test-cases d9a08dd 2026-09-29 — **the same script as the 2026-10-12T1456 validation**),
  case_payload_rel `ask-ck/functions/generator/refined-cases/Port/AWPTCM-T33234/zephyr_payload.json`.

Sentinel's reading of the facts (not a session fact):
- "u2-u5" on tb470 = u2 swi_a, u3 swi_b (IE520-sa), u4 swi_d, u5 swi_c — the IE520 stack and the IE520-sa.
  u0 (x230, swi_f) and u1 (AR4050S, swi_e) are outside the session and, per the constraint, not used.
- The hand-off gives no outlets, so a power cycle takes outlets from `bench-setup/tb470.static` (STANDING-ORDERS §1)
  **for the session's units only**: u2 swi_a 6, u3 swi_b 8, u4 swi_d 4, u5 swi_c 5. Outlets 1 (x230) and 7 (AR4050S)
  are never cycled by this run.
- The constraint is the one the 2026-10-13T1223 campaign ran under (same words); its run .setup
  `tb470/IE520/port-2026-10-13T1223/tb470-u2u5.setup` (stk_a + swi_b only) is the starting point for this run's .setup.
- `<FAMILY>` = IE520 (the script's DUT is the IE520 stack `stk_a`).

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  This is a `Driver: ask-ck` campaign: at completion the sentinel runs `/create-logs --auto` (manual
  cases only; T33234 is a script case, whose framework log is already final).
- `STANDING-ORDERS.md` applies, tightened by the constraint: **the x230 (u0) and the AR4050S (u1) are not used** —
  not opened, configured, declared in the run's `.setup`, or power-cycled. §6: the framework's post-failure power
  cycle is accepted only over outlets 4, 5, 6, 8.
- `/test-mode` §10 applies: nothing stops to wait. Every question becomes a `NOTIFY` line plus an
  entry in `## Issues`. §11 applies (`kind: validation`): repair loop on a COPY in
  `<group dir>/33234/work/`, `repairs.md`, ≤5 runs, then `review.md`.
- Ruling carried (memory `sfp-is-not-a-fixed-copper-port`, platforms/IE520.md row "MDI/MDI-X polarity is UNSUPPORTED"):
  the IE520 has no fixed RJ45 switchport, so T33234 is UNSUPPORTED on it; the copper-SFP links C and M do not change
  that, and no legacy copper-SFP polarity script is a substitute. The validation checks that the Ask-CK script itself
  reaches that verdict cleanly (its `has_fixed_copper_port` gate).
- Recorded history (not a verdict for this campaign): 2026-10-12T1456 validation of the same script (sha1 66c23163) on
  the full u0-u5 bench: clean run 1, 14/14 TestCases UNSUPPORTED, 0 power cycles, rc 0. Re-verify on the u2-u5 setup;
  do not inherit.
- Office hours (memory `reboot-heavy-runs-after-hours`): starts 14:55 on a weekday (Tuesday); expected 0 power cycles.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | port (script, validation): T33234 | tb470/IE520/port-2026-10-13T1455/ | TRIAGE | kind `script`, script_rel `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33234.py` (sha1 66c23163) |

## Setup and restore recipe — group 1

(Written by bench-runner at TRIAGE, before the first run.)

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

- **I-0 (campaign) precheck CLEAR, 2026-10-13 14:55.** `tools/tb precheck tb470 u2-u5`: u2-u5 free, no holder, lock
  file, screen/tmux/minicom-type session or python script on the box; only the Test Engineer's own ssh logins.
