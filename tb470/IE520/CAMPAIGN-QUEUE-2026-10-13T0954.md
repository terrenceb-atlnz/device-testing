# Campaign queue — tb470, IE520 stack (`stk_a`) as the DUT, 1 AWPTCM script case (Ask-CK validation), from 2026-10-13 09:54 NZDT

The ask, 2026-10-13 09:54 NZDT (`/test-mode --from-ask-ck`, Ask-CK's launcher):
*"/test-mode --from-ask-ck /home/terrenceb/.local/share/ck-agent/runs/2026-10-13T0954-val-01c5/2026-10-13T0954-val-01c5.json AWPTCM-T33235"*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-13 09:54 NZDT, word for word from the Ask-CK hand-off `2026-10-13T0954-val-01c5.json`
(schema 1, run_id `2026-10-13T0954-val-01c5`, kind `validation`, seat `10.33.22.17`, created 2026-10-13T09:54:07+13:00):
Test Engineer: terrenceb@terrenceb-dl
Driver: ask-ck (2026-10-13T0954-val-01c5)
Testbox: "tb470"
Consoles: "u2-u5"
PDU: {"ip": "10.36.150.14", "outlets": {}}
Constraints: "do not attempt to use the 4050 or x230 for this run"

Hand-off case entries:
- AWPTCM-T33235 — kind `script`, script_rel `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py`
  (resolved: `claude/Test-cases/ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py`, read-only;
  sha1 b044d695caa3…, last changed Test-cases 056114d 2026-10-01 — the same script as `CAMPAIGN-QUEUE-2026-10-13T0626.md`),
  case_payload_rel `ask-ck/functions/generator/refined-cases/Port/AWPTCM-T33235/zephyr_payload.json`.

Sentinel's reading of the facts (not a session fact):
- "u2-u5" on tb470 = u2 swi_a, u3 swi_b (IE520-sa), u4 swi_d, u5 swi_c — the IE520 stack and the IE520-sa.
  u0 (x230, swi_f) and u1 (AR4050S, swi_e) are outside the session and, per the constraint, not used.
- The hand-off gives no outlets, so a power cycle takes outlets from `bench-setup/tb470.static` (STANDING-ORDERS §1)
  **for the session's units only**: u2 swi_a 6, u3 swi_b 8, u4 swi_d 4, u5 swi_c 5. **Outlets 1 (x230) and 7 (AR4050S)
  must never be cycled by this run**: a live campaign of another session (`tb470/x230v2-28GS/CAMPAIGN-QUEUE-2026-10-13T0949.md`,
  session 50f164f5, consoles u0,u1) is driving those two units right now.
- `<FAMILY>` = IE520 (the script's DUT is the IE520 stack `stk_a`).

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  This is a `Driver: ask-ck` campaign: at completion the sentinel runs `/create-logs --auto` (manual
  cases only; T33235 is a script case, whose framework log is already final).
- `STANDING-ORDERS.md` applies, tightened by the constraint: **the x230 (u0) and the AR4050S (u1) are not used** —
  not opened, configured, probed past `bench_probe.py`'s own read of u2-u5, declared in the run's `.setup`, or
  power-cycled. §6: the framework's post-failure power cycle is accepted only over outlets 4, 5, 6, 8.
- `/test-mode` §10 applies: nothing stops to wait. Every question becomes a `NOTIFY` line plus an
  entry in `## Issues`. §11 applies (`kind: validation`): repair loop on a COPY in
  `<group dir>/33235/work/`, `repairs.md`, ≤5 runs, then `review.md`.
- Office hours (memory `reboot-heavy-runs-after-hours`): the campaign starts 09:54 on a weekday (Tuesday), inside
  office hours. See `## Issues`.
- **Prior run (not a verdict for this campaign):** `CAMPAIGN-QUEUE-2026-10-13T0626.md`, same case, same script sha1:
  clean run 1, PASS (31 PASS / 2 UNSUPPORTED), with the x230 as the link partner (cusfp/copper/fibre all to x230
  port1.0.2/1.0.3/1.0.4). This campaign may not use the x230, so its triage must find whether the script can bind to
  links that do not touch u0/u1 at all.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | port (script, validation): T33235 | tb470/IE520/port-2026-10-13T0954/ | TRIAGE | queued 09:54; TRIAGE dispatched 09:56; script `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py` |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

- **I-0 (campaign) concurrent campaign on u0/u1, 2026-10-13 09:54.** Session 50f164f5 is running the x230 office-hours
  campaign (`tb470/x230v2-28GS/CAMPAIGN-QUEUE-2026-10-13T0949.md`) on u0/u1 at the same time, with its own sentinel.sh.
  This session's sentinel sweep is scoped to its own scratchpad so it never kills that watch; this run never touches
  u0/u1 or outlets 1/7.
- **I-1 (campaign) precheck FOUND outside the session's consoles, 2026-10-13 09:55.** `tools/tb precheck tb470 u2-u5`: u2-u5 all
  free; FOUND 1 = process 787356 (terrenceb, up 00:07) `qmark.py /dev/u0 … /tmp/x230tri-1013/console-u0.log` — the x230 campaign's
  tester (I-0) on u0, outside this session. Assumed: not a holder of any session console; proceed on u2-u5, never touch u0/u1.
- **I-2 (campaign) sentinel armed 09:55** on this session (Monitor, normal mode, UPDATES → the hand-off's sentinel_updates file;
  cron backstop every 15 min, until 17:30). Sweep scoped to this session's scratchpad only. TRIAGE dispatched 09:56.
