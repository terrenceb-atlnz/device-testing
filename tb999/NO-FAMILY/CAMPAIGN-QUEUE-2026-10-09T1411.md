# Campaign queue — tb999, Ask-CK composer-validate of template `setup-a` (triage only, no cases), from 2026-10-09 14:11 NZDT

The ask, 2026-10-09 14:11 NZDT (`/test-mode --from-ask-ck`, Ask-CK's launcher):
*"/test-mode --from-ask-ck /tmp/claude-1971/-media-terrenceb-mnt-testbox-home-claude-Test-cases/79db4d44-3e69-4db9-99ee-14def1a54245/scratchpad/agent-runs/2026-10-09T1410-com-bdcf/2026-10-09T1410-com-bdcf.json"*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

`NO-FAMILY`: the hand-off names no cases and no DUT, and the box could not be reached, so there
is no product family to file this under.

## Session facts

Recorded 2026-10-09 14:11 NZDT, word for word from the Ask-CK hand-off `2026-10-09T1410-com-bdcf.json`
(schema 1, run_id `2026-10-09T1410-com-bdcf`, kind `composer-validate`, seat `127.0.0.1`, created 2026-10-09T14:10:15+13:00):
Test Engineer: terrenceb@terrenceb-dl
Driver: ask-ck (2026-10-09T1410-com-bdcf)
Testbox: "tb999"
Consoles: "u0"
PDU: null (no PDU / do not power-cycle)
Constraints: "Ask-CK P4 scheduling test (Claude, 2026-10-09): tb999 does not exist on purpose — do NOT use tb470 or any other box; report that the box is unreachable and end."

Hand-off template: `setup-a`, template_setup_rel `ask-ck/functions/test-composer/templates/setup-a/a.setup`
(resolved: `claude/Test-cases/ask-ck/functions/test-composer/templates/setup-a/a.setup`, read-only). Cases: none.

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  `Driver: ask-ck` campaign; `composer-validate` is a TRIAGE only with no cases, so `/create-logs --auto` has nothing to build.
- `STANDING-ORDERS.md` applies, tightened by the constraint above.
- `/test-mode` §10 applies: nothing stops to wait. Every question becomes a `NOTIFY` line plus an entry in `## Issues`.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | composer-validate: template `setup-a` (probe `--template`) | -- | BLOCKED | tb999 is unreachable. `tools/tb precheck tb999 u0` exited 255 with `ssh: Could not resolve hostname tb999: Name or service not known`, and `getent hosts tb999` returns nothing. Under §3, an ssh failure counts as FOUND. It blocks the whole campaign, so the campaign ends under §10 step 4. No probe was run, no console was opened, the sentinel was never armed, and no other box was used (constraint). |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| (template setup-a) | composer-validate | -- | NOT TESTED | Testbox tb999 is unreachable (hostname does not resolve; precheck ssh exit 255), so no probe was run. Separately, the template `a.setup` is still 0 bytes (Sep 25 11:28), as in run 2026-10-09T1356-com-767a, so this probe could not have produced a result even with a reachable box. | -- | sentinel |

## Issues

- NOTIFY campaign -- composer-validate needs testbox tb999 reachable for the occupancy precheck and probe -- `tools/tb precheck tb999 u0` failed (ssh: Could not resolve hostname tb999; exit 255), so the campaign ended with no probe, no console and no other box (sentinel 2026-10-09 14:11).
- NOTIFY campaign -- composer-validate needs a non-empty template .setup (`ask-ck/functions/test-composer/templates/setup-a/a.setup`) -- the file is still 0 bytes (a.swi_a.cfg and a.swi_b.cfg are too), as recorded by run 2026-10-09T1356-com-767a; nothing was done about it (sentinel 2026-10-09 14:11).
