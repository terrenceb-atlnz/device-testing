# Campaign queue — tb470, IE520 stack (`stk_a`) as the DUT, 1 AWPTCM script case (Ask-CK validation), from 2026-10-13 12:23 NZDT

The ask, 2026-10-13 12:23 NZDT (`/test-mode --from-ask-ck`, Ask-CK's launcher):
*"/test-mode --from-ask-ck /home/terrenceb/.local/share/ck-agent/runs/2026-10-13T1223-val-3ede/2026-10-13T1223-val-3ede.json AWPTCM-T33235"*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-13 12:23 NZDT, word for word from the Ask-CK hand-off `2026-10-13T1223-val-3ede.json`
(schema 1, run_id `2026-10-13T1223-val-3ede`, kind `validation`, seat `10.33.22.17`, created 2026-10-13T12:23:26+13:00):
Test Engineer: terrenceb@terrenceb-dl
Driver: ask-ck (2026-10-13T1223-val-3ede)
Testbox: "tb470"
Consoles: "u2-u5"
PDU: {"ip": "10.36.150.14", "outlets": {}}
Constraints: "do not attempt to use the 4050 or x230 for this run; recabled: stack port1.0.10–IE520-sa port1.0.2 (link C, VLAN 1); stack port1.0.6–IE520-sa port1.0.14 (link M, both ends in VLAN 106 \"link-m\", saved in tb470-bench.cfg)"

Hand-off case entries:
- AWPTCM-T33235 — kind `script`, script_rel `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py`
  (resolved: `claude/Test-cases/ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py`, read-only;
  sha1 f04ea35931e4…, last changed Test-cases ef53cea 2026-10-13 11:40 "14 TestCases instead of 33 (steps with the same
  gates run as one); step 29 without confCheck" — **NOT the script of the 0626/0954 campaigns** (b044d695…)),
  case_payload_rel `ask-ck/functions/generator/refined-cases/Port/AWPTCM-T33235/zephyr_payload.json`.

Sentinel's reading of the facts (not a session fact):
- "u2-u5" on tb470 = u2 swi_a, u3 swi_b (IE520-sa), u4 swi_d, u5 swi_c — the IE520 stack and the IE520-sa.
  u0 (x230, swi_f) and u1 (AR4050S, swi_e) are outside the session and, per the constraint, not used.
- The hand-off gives no outlets, so a power cycle takes outlets from `bench-setup/tb470.static` (STANDING-ORDERS §1)
  **for the session's units only**: u2 swi_a 6, u3 swi_b 8, u4 swi_d 4, u5 swi_c 5. Outlets 1 (x230) and 7 (AR4050S)
  are never cycled by this run.
- The recable is the one `CAMPAIGN-QUEUE-2026-10-13T0954.md` § Triage asked for, option (a) for link M, with link M in
  VLAN 106 rather than the suggested 105. It is a Test Engineer's change to the standing bench (saved in
  tb470-bench.cfg); the deployed `tb470.setup` is not known to carry it yet — triage's probe will say.
- The x230 campaign (`tb470/x230v2-28GS/CAMPAIGN-QUEUE-2026-10-13T0949.md`) shows both groups DONE by 12:06.
- `<FAMILY>` = IE520 (the script's DUT is the IE520 stack `stk_a`).

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  This is a `Driver: ask-ck` campaign: at completion the sentinel runs `/create-logs --auto` (manual
  cases only; T33235 is a script case, whose framework log is already final).
- `STANDING-ORDERS.md` applies, tightened by the constraint: **the x230 (u0) and the AR4050S (u1) are not used** —
  not opened, configured, declared in the run's `.setup`, or power-cycled. §6: the framework's post-failure power
  cycle is accepted only over outlets 4, 5, 6, 8.
- `/test-mode` §10 applies: nothing stops to wait. Every question becomes a `NOTIFY` line plus an
  entry in `## Issues`. §11 applies (`kind: validation`): repair loop on a COPY in
  `<group dir>/33235/work/`, `repairs.md`, ≤5 runs, then `review.md`.
- Office hours (memory `reboot-heavy-runs-after-hours`): the campaign starts 12:23 on a weekday (Tuesday). The 0954
  triage estimated 1 reload (TC33) and 0-2 four-unit PDU cycles: not reboot-heavy. See `## Issues`.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | port (script, validation): T33235 | tb470/IE520/port-2026-10-13T1223/ | QUEUED | kind `script`, script_rel `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py` (sha1 f04ea359). Expected binding after the recable: cusfp = link M (stack 1.0.6 <-> sa 1.0.14), copper = link C (stack 1.0.10 <-> sa 1.0.2), fibre = stack 4.0.26 <-> sa 1.0.26 |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

