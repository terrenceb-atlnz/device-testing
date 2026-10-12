# Campaign queue — tb470, IE520 stack (`stk_a`) as the DUT, 1 AWPTCM script case (Ask-CK validation), from 2026-10-12 15:37 NZDT

The ask, 2026-10-12 15:37 NZDT (`/test-mode --from-ask-ck`, Ask-CK's launcher):
*"/test-mode --from-ask-ck /home/terrenceb/.local/share/ck-agent/runs/2026-10-12T1537-val-9f45/2026-10-12T1537-val-9f45.json AWPTCM-T33235"*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-12 15:37 NZDT, word for word from the Ask-CK hand-off `2026-10-12T1537-val-9f45.json`
(schema 1, run_id `2026-10-12T1537-val-9f45`, kind `validation`, seat `10.33.22.17`, created 2026-10-12T15:37:17+13:00):
Test Engineer: terrenceb@terrenceb-dl
Driver: ask-ck (2026-10-12T1537-val-9f45)
Testbox: "tb470"
Consoles: "all"
PDU: {"ip": "10.36.150.14", "outlets": {}}
Constraints: "none"

Hand-off case entries:
- AWPTCM-T33235 — kind `script`, script_rel `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py`
  (resolved: `claude/Test-cases/ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py`, read-only;
  sha1 b044d695…, last changed Test-cases 056114d 2026-10-01 13:03, 33 TestCases), case_payload_rel
  `ask-ck/functions/generator/refined-cases/Port/AWPTCM-T33235/zephyr_payload.json`.

Sentinel's reading of the facts (not a session fact): "all" on tb470 = u0-u5. The hand-off gives no
outlets, so a power cycle takes each unit's outlet from `bench-setup/tb470.static` (STANDING-ORDERS §1),
as in today's 14:56 campaign: u0 swi_f 1, u1 swi_e 7, u2 swi_a 6, u3 swi_b 8, u4 swi_d 4, u5 swi_c 5.
`<FAMILY>` = IE520 (the script's DUT is the IE520 stack `stk_a`, as in run 4 of 2026-10-01).

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  This is a `Driver: ask-ck` campaign: at completion the sentinel runs `/create-logs --auto` (manual
  cases only; T33235 is a script case, whose framework log is already final).
- `STANDING-ORDERS.md` applies in full (no tightening constraint). §6: the framework's post-failure
  power cycle is accepted; a systematically failing script is stopped and repaired, not re-run blind.
- `/test-mode` §10 applies: nothing stops to wait. Every question becomes a `NOTIFY` line plus an
  entry in `## Issues`. §11 applies (`kind: validation`): repair loop on a COPY in
  `<group dir>/33235/work/`, `repairs.md`, ≤5 runs, then `review.md`.
- Office hours (memory `reboot-heavy-runs-after-hours`): the campaign starts 15:37 on a weekday (Monday).
  T33235 is reload-bearing (a whole-stack `reload` step; a FAILED/UNSUPPORTED TestCase costs a six-unit
  PDU cycle). The tester estimates the reboot events at triage; the sentinel decides start time from that.
- Recorded history (not a verdict for this campaign): IE520 port-2026-09-29 run 4 (2026-10-01, Test-cases
  3454bc0): PASS, 32 PASS / 1 UNSUPPORTED (TestCase_20) / 0 FAIL, 72 min, one PDU cycle (after TestCase_20)
  plus the script's own whole-stack reload. The script has changed since (056114d: not-applicable cases
  skipped before they run; no startup-config backup). Re-verify; do not inherit.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | port (script, validation): T33235 | tb470/IE520/port-2026-10-12T1537/ | TRIAGE | |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

