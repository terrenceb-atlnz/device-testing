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
| 1 | port (script): T33234 | tb470/x230v2-28GS/port-2026-10-09T1349/ | BLOCKED | triage only (session constraint). Triage 13:51: UNSUPPORTED on the x230v2-28GS (no fixed copper switchport; all 5 linked ports are cages, `show system pluggable` 13:52) AND bound to the wrong DUT (`swi_a` = IE520 stk_a u2; x230 = `swi_f`). Remedy for the binding: swap swi_a<->swi_f in tb470.static + probe + apply, or a Test-Composer pair. No bench change gives it a fixed copper port. See "## Triage 2026-10-09T1349" |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

## Triage 2026-10-09T1349

Tester: bench-runner, TRIAGE dispatch, 13:51-13:55 NZDT. Read-only apart from the probe, plus one read-only
`show system pluggable` / `show system` on u0 and a bare-CR peek on u1-u5. No case run, no reload, no PDU
cycle, no configuration sent. x230 VLANs 103/104/105 on port1.0.3/.4/.5 untouched (read from the capture:
`vlan 103-105 state enable`, access vlans 103/104/105 present).

### Gate

| gate | result |
| --- | --- |
| 1 occupancy | `tools/tb precheck tb470 u0-u5` 13:51:37: **CLEAR** (exit 0), `&&`-gated directly into the probe; re-run CLEAR before each later console open |
| 2 consoles | probe logged in on all six (banners awplus, 4050-5g, IE520-stk-1, IE520-sa, IE520-stk-4, IE520-stk); none parked in a shell or config mode |
| 3 template | `/nfsHome` mounted (nfs4 10.36.250.11:/home); `/home/st-art/st-art/configs/tb470.setup` present (Oct 9 11:34) |
| 4 probe | `tools/tb probe tb470 --consoles u0-u5 --no-prompt --pdu 10.36.150.14 --outlet u0=1,u1=7,u2=6,u3=8,u4=4,u5=5 --baud 115200` -> **exit 0 MATCH**, capture `captures/2026-10-09T005138Z` (10.4 s). No USER-CONFLICT. Advisory (unchanged from 12:06, information only): eth1 learned on swi_c port3.0.13 AND swi_f port1.0.2. `bench-state.md` regenerated; only its stamps changed |
| 5 setup | `bench-setup/tb470.setup.current` equals the new bench-state fence (ignoring `###` header lines) |
| 6 preflight | `pt_preflight.py --setup bench-setup/tb470.setup.current --script .../test-9001.33234.py`: RUNNABLE (2/2), **binding `swi_a /dev/u2 (member of stk_a)`**; copper role would take swi_a-swi_f = port1.0.17-port1.0.3 |
| 7 boot configs | x230 (u0): `flash:/default.cfg` (unchanged since 12:06; this campaign's baseline). 4050 (u1), IE520-sa (u3), stack (u2): `flash:/tb470-bench.cfg` |
| 8 server path | `pt_exec.FRAMEWORK_RUN_FLAGS = ("--noupdate", "--nodefaultcfg")` (line 552) |
| 9 sentinel | `sentinel: parent` |
| 10 CLI | configure()/tear_down() return before sending anything when no fixed copper link is bound; with one: `duplex auto`, `polarity auto`, `no shutdown` (no `no polarity`; b734b40). No defaulting defect |

### What changed since the 12:06 triage: nothing

- `bench-setup/tb470.static`, `tb470.setup.current`: no commit since e841432 (11:35); the probe fence is identical. `264A23061 = swi_a` (IE520 stk_a member 1, u2), `A10783G262900002 = swi_f` (x230, u0).
- The script: `test-9001.33234.py` last changed d9a08dd (2026-09-29), sha1 66c23163...; `library_9001.py` unchanged.
- Test-Composer templates `setup-a/`, `setup-b/`: still 0-byte files, so no pre-loaded topology pair exists.

### T33234 "Port - Auto MDI/MDI-X" (14 TestCases)

**Still true: UNSUPPORTED on the x230v2-28GS, and bound to the wrong DUT.**
- **Binding:** the script takes `setup.init_all_devices()['swi_a']`; on tb470 that is the IE520 stack (u2). Launched as-is it tests the
  IE520 stack (which gave 14/14 UNSUPPORTED on 2026-09-29, run 3), not the session's DUT.
- **Platform:** the role needs a FIXED copper switchport (`has_fixed_copper_port`, Terrence's ruling 2026-09-29). Read live today
  (u0, 13:52, `show system pluggable`): 1.0.1 AT-SPTXa, 1.0.2 AT-SPTX, 1.0.3 AT-SPTX, 1.0.5 AT-SPTXc (all 1000BASE-T in cages),
  1.0.4 AT-SPSX; 1.0.6-1.0.28 "not present". `_ck_discover` buckets a twisted-pair port listed by `show system pluggable` as
  `cusfp`, never `copper`, so with the x230 bound as `swi_a` every TestCase is pre-marked UNSUPPORTED (skipIfExcl), configure()
  and tear_down() send nothing, and no power cycle follows. The x230v2-28GS has no fixed RJ45 front port, so no recable or
  module swap changes this. Standalone `swi_a` is handled (`_ck_discover` falls back to the DUT when `get_stack()` is None).
- **Exact change for the binding (the Test Engineer's call):** in `bench-setup/tb470.static` swap the names
  (A10783G262900002 -> `swi_a`, 264A23061 -> `swi_f`), then `bench_probe.py --box tb470 run ...` and `bench_probe.py apply`;
  or Test Composer pre-loads a topology pair equal to tb470.setup with swi_a<->swi_f swapped. No recable. Either way the
  expected outcome is a recorded 14/14 UNSUPPORTED (platform), not a measurement.

### Count (STANDING-ORDERS §3)

- **N = 0 runnable now** against the session's DUT (and the session constraint is triage only).
- **M = 0 blocked by topology** that a bench change would make measurable. The binding block (swi_a<->swi_f rename, above)
  only redirects the script to the x230, where it is UNSUPPORTED.
- **K = 1 blocked otherwise:** T33234, UNSUPPORTED (platform: no fixed copper switchport on the x230v2-28GS) and bound to
  `swi_a` = IE520 stack. Runnable cheaply to record the framework's 14/14 UNSUPPORTED once the binding is fixed.
- Consoles left: u0 `awplus#` (transcript `/tmp/tri1349/console-u0.log`: `terminal no monitor`, `awplus#`, closed 13:52:49);
  u1 `4050-5g#`, u2/u4/u5 `IE520-stk#`, u3 `IE520-sa#` (bare-CR peek 13:53). All logged in at exec, not exited.
- DUT clock vs box: x230 `show system` read 13:51:54 when the box read 13:52:48 (DUT ~54 s behind).
