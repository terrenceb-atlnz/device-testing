# Campaign queue — tb470, x230v2-28GS as the DUT, 2 AWPTCM script cases, from 2026-10-09 12:06 NZDT

The ask, 2026-10-09 12:06 NZDT (`/test-mode --from-ask-ck`, Ask-CK's launcher):
*"/test-mode --from-ask-ck /tmp/claude-1971/-media-terrenceb-mnt-testbox-home-claude-Test-cases/79db4d44-3e69-4db9-99ee-14def1a54245/scratchpad/p0/p0-triage-2026-10-09.json AWPTCM-T33234 AWPTCM-T33235"*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-09 12:06 NZDT, word for word from the Ask-CK hand-off `p0-triage-2026-10-09.json`
(schema 0, run_id `p0-triage-2026-10-09`, kind `validation`, seat `terrenceb@terrenceb-dl`):
Test Engineer: terrenceb@terrenceb-dl
Driver: ask-ck (p0-triage-2026-10-09)
Testbox: "tb470"
Consoles: "u0-u5 all (u0 = DUT x230; stack, IE520-sa u3, AR4050S u1 available as partners)"
PDU: "10.36.150.14" (outlets: u0=1, u1=7, u2=6, u3=8, u4=4, u5=5)
Constraints: "Triage only: run no case and change no device state beyond what the probe itself does. Approved by Terrence 2026-10-09 for P0."

Hand-off case entries (both `kind: script`):
- AWPTCM-T33234 — `claude/Test-cases/ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33234.py`
- AWPTCM-T33235 — `claude/Test-cases/ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py`

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  This is a `Driver: ask-ck` campaign: at completion the sentinel runs `/create-logs --auto` (manual
  cases only; both cases here are script cases, whose framework logs are already final).
- `STANDING-ORDERS.md` applies, **tightened by the constraint above: triage only.** No case runs and
  no device state changes beyond the probe's own reads.
- `/test-mode` §10 applies: nothing stops to wait. Every question becomes a `NOTIFY` line plus an
  entry in `## Issues`.
- Case texts: Ask-CK `ck.db` table `zephyr_cases` (read-only: `sqlite3 'file:<path>/ck.db?mode=ro'`).
  T33234 "Port - Auto MDI/MDI-X" (Draft); T33235 "(3) Port - Fixed port Speed" (Draft).
- Recorded history (not a verdict for this campaign): the 2026-10-09T0845 queue triaged T33234
  UNSUPPORTED on the x230 ("no fixed copper on the x230"); STANDING-ORDERS §6 records T33234's
  `no polarity` defaulting step failing every case on 2026-09-29.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | port (scripts): T33234, T33235 | tb470/x230v2-28GS/port-2026-10-09T1206/ | TRIAGE | triage only (session constraint) |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

