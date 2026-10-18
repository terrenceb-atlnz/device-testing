# Campaign queue — tb470, IE520 as the DUT, 1 AWPTCM script case (Ask-CK validation), from 2026-10-19 11:34 NZDT — ENDED at precheck: no console the hand-off names exists on tb470

The ask, 2026-10-19 11:34 NZDT (`/test-mode --from-ask-ck`, Ask-CK's launcher):
*"/test-mode --from-ask-ck /home/terrenceb/.local/share/ck-agent/runs/2026-10-19T1133-val-ef4c/2026-10-19T1133-val-ef4c.json AWPTCM-T33235"*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-19 11:34 NZDT, word for word from the Ask-CK hand-off `2026-10-19T1133-val-ef4c.json`
(schema 1, run_id `2026-10-19T1133-val-ef4c`, kind `validation`, seat `10.33.22.17`, created 2026-10-19T11:33:55+13:00):
Test Engineer: terrenceb@terrenceb-dl
Driver: ask-ck (2026-10-19T1133-val-ef4c)
Testbox: "tb470"
Consoles: "u2-u5"
PDU: {"ip": "10.36.150.14", "outlets": {}}
Constraints: "do not attempt to use the 4050 or x230 for this run; recabled: stack port1.0.10–IE520-sa port1.0.2 (link C, VLAN 1); stack port1.0.6–IE520-sa port1.0.14 (link M, both ends in VLAN 106 \"link-m\", saved in tb470-bench.cfg)"

Hand-off case entries:
- AWPTCM-T33235: kind `script`, script_rel `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py`
  (resolved: `claude/Test-cases/ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py`, read-only;
  sha1 f04ea359, last changed Test-cases ef53cea 2026-10-13, **the same script as the 2026-10-13T1223 validation**),
  case_payload_rel `ask-ck/functions/generator/refined-cases/Port/AWPTCM-T33235/zephyr_payload.json`.

Sentinel's reading of the facts (not a session fact):
- The constraint text is word for word the one the 2026-10-13T1223 and 2026-10-13T1455 campaigns ran under, when
  u2-u5 = the IE520 stack (swi_a, swi_c, swi_d) and the IE520-sa (swi_b).
- **The recorded bench no longer matches it.** `bench-setup/tb470.static` (Test Engineer, commit 8d45d67, 2026-10-16):
  *"The four IE520-28GSX units were REMOVED from the bench 2026-10-16"*; the AR4050S moved to outlet 3 and the x230 to
  outlet 4. `bench-state.md` (generated 2026-10-15T213406Z) shows only u7 = swi_f (x230) and u8 = swi_e (AR4050S).
- `<FAMILY>` = IE520 (the script's DUT is the IE520 stack `stk_a`).

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  This is a `Driver: ask-ck` campaign: `/test-mode` §10 applies (nothing stops to wait; every question is a `NOTIFY`
  line plus an entry in `## Issues`), and §11 (`kind: validation`).
- `STANDING-ORDERS.md` applies, tightened by the constraint: the x230 and the AR4050S are not used.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | port (script, validation): T33235 | (none: never attempted) | BLOCKED 11:36 | No DUT reachable: `tools/tb precheck tb470 u2-u5` (11:35) reports `/dev/u2`, `/dev/u3`, `/dev/u4`, `/dev/u5` **absent (no such device node)**; tb470 has only `/dev/u7 -> ttyUSB0` and `/dev/u8 -> ttyUSB1` (the x230 and the AR4050S, which the constraint excludes). Unblock: put an IE520 DUT (stack + IE520-sa partner, links C/M/SX as in `port-2026-10-13T1223/tb470-u2u5.setup`) back on tb470 consoles, or send Ask-CK the consoles and constraints of the bench the IE520s are now on; then re-launch the validation. kind `script`, script_rel `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py` (sha1 f04ea359) |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| T33235 | (3) Port - Fixed port Speed | port-2026-10-19T1134 | NOT TESTED | never attempted: none of the hand-off's consoles u2-u5 exists on tb470 (only u7 x230 and u8 AR4050S, both excluded by the constraint); IE520s recorded as removed from tb470 on 2026-10-16 (tb470.static, 8d45d67) | (none) | sentinel |

## Issues

- **I-0 (campaign) precheck, 2026-10-19 11:35.** `tools/tb precheck tb470 u2-u5`, exit 0 (CLEAR: no holder, lock file,
  screen/tmux/minicom-type session or python script), but every session console is
  `absent (no such device node)`. A read-only `ls /dev/u[0-9]* /dev/ttyUSB*` on tb470: only `/dev/u7 -> ttyUSB0` and
  `/dev/u8 -> ttyUSB1` (both created Oct 15 14:56). Logged in: only the Test Engineer's own ssh sessions.
- **I-1 (campaign) ended, 2026-10-19 11:36.**
  NOTIFY campaign -- an IE520 DUT on tb470 consoles u2-u5 (the hand-off's consoles) -- none exists: /dev/u2-u5 are absent on tb470 (only u7 x230 and u8 AR4050S, excluded by the constraint; tb470.static records the four IE520s removed 2026-10-16); T33235 not attempted (NOT TESTED), campaign ended
  The block covers every case in the campaign (§10 step 4), so no TRIAGE or RUN was dispatched, no probe ran, no
  console was opened, and the sentinel was not armed (nothing to watch). Nothing on tb470 was changed.
