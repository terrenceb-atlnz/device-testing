# Campaign queue — tb470, IE520 stack (`stk_a`) as the DUT, 1 AWPTCM script case (Ask-CK validation), from 2026-10-13 06:26 NZDT

The ask, 2026-10-13 06:26 NZDT (`/test-mode --from-ask-ck`, Ask-CK's launcher):
*"/test-mode --from-ask-ck /home/terrenceb/.local/share/ck-agent/runs/2026-10-13T0626-val-fbe9/2026-10-13T0626-val-fbe9.json AWPTCM-T33235"*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-13 06:26 NZDT, word for word from the Ask-CK hand-off `2026-10-13T0626-val-fbe9.json`
(schema 1, run_id `2026-10-13T0626-val-fbe9`, kind `validation`, seat `10.33.22.17`, created 2026-10-13T06:26:06+13:00):
Test Engineer: terrenceb@terrenceb-dl
Driver: ask-ck (2026-10-13T0626-val-fbe9)
Testbox: "tb470"
Consoles: "all"
PDU: {"ip": "10.36.150.14", "outlets": {}}
Constraints: "none"

Hand-off case entries:
- AWPTCM-T33235 — kind `script`, script_rel `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py`
  (resolved: `claude/Test-cases/ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py`, read-only;
  sha1 b044d695…, last changed Test-cases 056114d 2026-10-01), case_payload_rel
  `ask-ck/functions/generator/refined-cases/Port/AWPTCM-T33235/zephyr_payload.json`.

Sentinel's reading of the facts (not a session fact): "all" on tb470 = u0-u5. The hand-off gives no
outlets, so a power cycle takes each unit's outlet from `bench-setup/tb470.static` (STANDING-ORDERS §1),
as in the 2026-10-12 campaigns: u0 swi_f 1, u1 swi_e 7, u2 swi_a 6, u3 swi_b 8, u4 swi_d 4, u5 swi_c 5.
`<FAMILY>` = IE520 (the script's DUT is the IE520 stack `stk_a`).

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  This is a `Driver: ask-ck` campaign: at completion the sentinel runs `/create-logs --auto` (manual
  cases only; T33235 is a script case, whose framework log is already final).
- `STANDING-ORDERS.md` applies in full (no tightening constraint). §6: the framework's post-failure
  power cycle is accepted; a systematically failing script is stopped and repaired, not re-run blind.
- `/test-mode` §10 applies: nothing stops to wait. Every question becomes a `NOTIFY` line plus an
  entry in `## Issues`. §11 applies (`kind: validation`): repair loop on a COPY in
  `<group dir>/33235/work/`, `repairs.md`, ≤5 runs, then `review.md`.
- Office hours (memory `reboot-heavy-runs-after-hours`): the campaign starts 06:26 on a weekday (Tuesday),
  before office hours. Yesterday's triage expected 1 whole-stack reload (TC33) and 0 PDU cycles in ~80 min,
  so a ~06:45 start ends ~08:05. Any repair re-run that would start after ~08:00 waits for the tester's
  reboot estimate and the sentinel's call.
- **Prior attempt (not a verdict for this campaign):** `CAMPAIGN-QUEUE-2026-10-12T1537.md`, same case, same
  script sha1. Its triage (one-leg isolation: stack port1.0.2 out of sa2; restored after) and its repair
  R1 (`clear exception log` of pre-run history as a setup step, under `--nodefaultcfg`) are carried
  forward as a starting point, to be RE-VERIFIED against today's probe, not inherited. Run 1 there
  was PARTIAL (TC1 failed on stale exception log); run 2 was BLOCKED by stephenh's minicom on u2.
  That group's copy (`port-2026-10-12T1537/33235/work/test-9001.33235.py`) is unedited.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | port (script, validation): T33235 | tb470/IE520/port-2026-10-13T0626/ | TRIAGE | queued 06:26 |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

