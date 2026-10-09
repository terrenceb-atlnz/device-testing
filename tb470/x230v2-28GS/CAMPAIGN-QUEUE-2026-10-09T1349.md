# Campaign queue — tb470, x230v2-28GS as the DUT, 1 AWPTCM script case (triage only), from 2026-10-09 13:49 NZDT

The ask, 2026-10-09 13:49 NZDT (`/test-mode --from-ask-ck`, Ask-CK's launcher):
*"/test-mode --from-ask-ck /tmp/claude-1971/-media-terrenceb-mnt-testbox-home-claude-Test-cases/79db4d44-3e69-4db9-99ee-14def1a54245/scratchpad/agent-runs/2026-10-09T1349-val-1709/2026-10-09T1349-val-1709.json AWPTCM-T33234"*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-09 13:49 NZDT, word for word from the Ask-CK hand-off `2026-10-09T1349-val-1709.json`
(schema 1, run_id `2026-10-09T1349-val-1709`, kind `validation`, seat `127.0.0.1`, created 2026-10-09T13:49:20+13:00):
Test Engineer: terrenceb@terrenceb-dl
Driver: ask-ck (2026-10-09T1349-val-1709)
Testbox: "tb470"
Consoles: "u0-u5 all (u0 = x230 DUT; u2,u4,u5 IE520 stack; u3 IE520-sa; u1 AR4050S)"
PDU: "10.36.150.14" (outlets: u0=1, u1=7, u2=6, u3=8, u4=4, u5=5)
Constraints: "TRIAGE ONLY — Ask-CK end-to-end test approved by Terrence 2026-10-09: run NO case; change no device state beyond what the probe itself does; no reloads, no PDU cycles. Leave the x230 (u0) running-config VLANs 103/104/105 on port1.0.3/1.0.4/1.0.5 untouched. Leave every console at exec when done. Bench window ends 17:45 (x230 campaign from 18:00)."

Hand-off case entries:
- AWPTCM-T33234 — kind `script`, script_rel `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33234.py`
  (resolved: `claude/Test-cases/ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33234.py`, read-only)

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  This is a `Driver: ask-ck` campaign: at completion the sentinel runs `/create-logs --auto` (manual
  cases only; T33234 is a script case, whose framework log is already final).
- `STANDING-ORDERS.md` applies, **tightened by the constraint above: triage only.** No case runs, no
  reload, no PDU cycle, and no device state changes beyond the probe's own. x230 VLANs 103/104/105 on
  port1.0.3/1.0.4/1.0.5 stay as they are. Every console is left at exec.
- `/test-mode` §10 applies: nothing stops to wait. Every question becomes a `NOTIFY` line plus an
  entry in `## Issues`.
- Case text: Ask-CK `ck.db` table `zephyr_cases` (read-only). T33234 "Port - Auto MDI/MDI-X" (Draft).
- Recorded history (not a verdict for this campaign): the 2026-10-09T1206 queue triaged T33234
  UNSUPPORTED on the x230 (no fixed copper switchport) and BLOCKED on the DUT binding (`swi_a` =
  IE520 stk_a u2, the x230 is `swi_f`). Re-verify both; do not inherit them.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | port (script): T33234 | tb470/x230v2-28GS/port-2026-10-09T1349/ | TRIAGE | triage only (session constraint) |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

