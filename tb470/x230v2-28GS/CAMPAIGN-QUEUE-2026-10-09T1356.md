# Campaign queue — tb470, Ask-CK composer-validate of template `setup-a` (triage only, no cases), from 2026-10-09 13:56 NZDT

The ask, 2026-10-09 13:56 NZDT (`/test-mode --from-ask-ck`, Ask-CK's launcher):
*"/test-mode --from-ask-ck /tmp/claude-1971/-media-terrenceb-mnt-testbox-home-claude-Test-cases/79db4d44-3e69-4db9-99ee-14def1a54245/scratchpad/agent-runs/2026-10-09T1356-com-767a/2026-10-09T1356-com-767a.json"*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-09 13:56 NZDT, word for word from the Ask-CK hand-off `2026-10-09T1356-com-767a.json`
(schema 1, run_id `2026-10-09T1356-com-767a`, kind `composer-validate`, seat `127.0.0.1`, created 2026-10-09T13:56:44+13:00):
Test Engineer: terrenceb@terrenceb-dl
Driver: ask-ck (2026-10-09T1356-com-767a)
Testbox: "tb470"
Consoles: "u0-u5 all (u0 = x230 DUT; u2,u4,u5 IE520 stack; u3 IE520-sa; u1 AR4050S)"
PDU: "10.36.150.14" (outlets: u0=1, u1=7, u2=6, u3=8, u4=4, u5=5)
Constraints: "Ask-CK end-to-end test approved by Terrence 2026-10-09: composer-validate only; change no device state beyond what the probe itself does; no reloads, no PDU cycles; leave the x230 VLANs 103/104/105 untouched; leave consoles at exec. Bench window ends 17:45."

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
| 1 | composer-validate: template `setup-a` (probe `--template`) | -- | BLOCKED | `a.setup` is a 0-byte file (Sep 25 11:28), so there is no template to probe against (§1: empty `*_rel` file → §10 notice, campaign ends). No precheck, no probe, no console opened, sentinel never armed. |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| (template setup-a) | composer-validate | -- | NOT TESTED | Template `ask-ck/functions/test-composer/templates/setup-a/a.setup` is empty (0 bytes); its siblings `a.swi_a.cfg` and `a.swi_b.cfg` are 0 bytes too. Nothing to compare the bench against; the bench was not touched. | -- | sentinel |

## Issues

- NOTIFY campaign -- composer-validate needs a non-empty template .setup to probe against (`--template ~/claude/Test-cases/ask-ck/functions/test-composer/templates/setup-a/a.setup`) -- the file is 0 bytes (as are a.swi_a.cfg and a.swi_b.cfg in setup-a/), so no probe was run and the campaign ended; bench untouched (sentinel 2026-10-09 13:57). The 2026-10-09T1349 triage also recorded setup-a/ and setup-b/ as 0-byte files.
