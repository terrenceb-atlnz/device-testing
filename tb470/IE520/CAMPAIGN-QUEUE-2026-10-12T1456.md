# Campaign queue — tb470, IE520 stack (`swi_a`) as the bound DUT, 1 AWPTCM script case (Ask-CK validation), from 2026-10-12 14:56 NZDT

The ask, 2026-10-12 14:56 NZDT (`/test-mode --from-ask-ck`, Ask-CK's launcher):
*"/test-mode --from-ask-ck /home/terrenceb/.local/share/ck-agent/runs/2026-10-12T1455-val-0210/2026-10-12T1455-val-0210.json AWPTCM-T33234"*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-12 14:56 NZDT, word for word from the Ask-CK hand-off `2026-10-12T1455-val-0210.json`
(schema 1, run_id `2026-10-12T1455-val-0210`, kind `validation`, seat `10.33.22.17`, created 2026-10-12T14:55:37+13:00):
Test Engineer: terrenceb@terrenceb-dl
Driver: ask-ck (2026-10-12T1455-val-0210)
Testbox: "tb470"
Consoles: "all"
PDU: {"ip": "10.36.150.14", "outlets": {}}
Constraints: "none"

Hand-off case entries:
- AWPTCM-T33234 — kind `script`, script_rel `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33234.py`
  (resolved: `claude/Test-cases/ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33234.py`, read-only;
  sha1 66c23163…, last changed Test-cases d9a08dd 2026-09-29), case_payload_rel
  `ask-ck/functions/generator/refined-cases/Port/AWPTCM-T33234/zephyr_payload.json`.

Sentinel's reading of the facts (not a session fact): "all" on tb470 = u0-u5. The hand-off gives no
outlets, so a power cycle takes each unit's outlet from `bench-setup/tb470.static` (STANDING-ORDERS §1:
"from the Test Engineer's session facts, or the box's `<TB>.static`"): swi_a 6, swi_b 8, swi_c 5, swi_d 4,
swi_e 7, swi_f 1. `<FAMILY>` = IE520 because the script binds `swi_a` = 264A23061, IE520 stack `stk_a`.

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  This is a `Driver: ask-ck` campaign: at completion the sentinel runs `/create-logs --auto` (manual
  cases only; T33234 is a script case, whose framework log is already final).
- `STANDING-ORDERS.md` applies in full (no tightening constraint). §6: the framework's post-failure
  power cycle is accepted; a systematically failing script is stopped and repaired, not re-run blind.
- `/test-mode` §10 applies: nothing stops to wait. Every question becomes a `NOTIFY` line plus an
  entry in `## Issues`. §11 applies (`kind: validation`): repair loop on a COPY in
  `<group dir>/33234/work/`, `repairs.md`, ≤5 runs, then `review.md`.
- Office hours (memory `reboot-heavy-runs-after-hours`): the run starts ~15:00 on a weekday. The
  tester estimates the power cycles at triage; a reboot-heavy run is not launched into office hours.
- Recorded history (not a verdict for this campaign): IE520 port-2026-09-29 run 3 (Test-cases d9a08dd,
  the same script): 14/14 TestCases UNSUPPORTED on `swi_a` (no fixed copper switchport, Terrence's
  ruling I-5), none run, no power cycle. Re-verify; do not inherit.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | port (script, validation): T33234 | tb470/IE520/port-2026-10-12T1456/ | TRIAGE | |

## Setup and restore recipe — group 1

(written by the tester before the group's first case)

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

