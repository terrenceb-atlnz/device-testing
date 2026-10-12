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


## Triage 2026-10-12T1456

Tester: bench-runner, TRIAGE dispatch, 14:58-15:02 NZDT. Read-only apart from the probe, plus one read-only
`show system pluggable` / `show clock` on u2 (the console the script's `swi_a` handle uses) and a bare-CR peek on
u0-u5. No case run, no reload, no PDU cycle, no configuration sent.

### Gate

| gate | result |
| --- | --- |
| 1 occupancy | `tools/tb precheck tb470 u0-u5` 14:58:13: **CLEAR** (exit 0), `&&`-gated directly into the probe; re-run CLEAR before each later console open (u2 14:59, u0-u5 15:01) |
| 2 consoles | probe logged in on all six (banners awplus, 4050-5g, IE520-stk-1, IE520-sa, IE520-stk-4, IE520-stk); none parked in a shell or config mode |
| 3 template | `/nfsHome` mounted (nfs4 10.36.250.11:/home); `/home/st-art/st-art/configs/tb470.setup` present (Oct 9 11:34) |
| 4 probe | `tools/tb probe tb470 --consoles u0-u5 --no-prompt --pdu 10.36.150.14 --outlet u0=1,u1=7,u2=6,u3=8,u4=4,u5=5 --baud 115200` (outlets from `tb470.static` by serial: u0 swi_f 1, u1 swi_e 7, u2 swi_a 6, u3 swi_b 8, u4 swi_d 4, u5 swi_c 5) -> **exit 0 MATCH**, capture `captures/2026-10-12T015814Z` (10.3 s). No USER-CONFLICT. Advisory (unchanged, information only): eth1 learned on swi_c port3.0.13 AND swi_f port1.0.2. `bench-state.md` regenerated; only its stamps changed |
| 5 setup | `bench-setup/tb470.setup.current` equals the new bench-state fence (ignoring `###` header lines) |
| 6 preflight | `pt_preflight.py --setup bench-setup/tb470.setup.current --script .../test-9001.33234.py`: RUNNABLE (2/2), **binding `swi_a /dev/u2 (member of stk_a)`**; copper role *could* take swi_a-swi_f = port1.0.17-port1.0.3 (offline note; media is read from the DUT at run time, below) |
| 7 boot configs | all four devices (u0 x230, u1 4050, u2 stack, u3 IE520-sa): `Current boot config: flash:/tb470-bench.cfg (file exists)` (capture 015814Z). This is the run's baseline |
| 8 server path | `pt_exec.py` no longer carries `FRAMEWORK_RUN_FLAGS` (server run path retired 2026-10-12, TESTBOX-ACCESS §3): launch by hand with `tools/tb fwprep` / `tools/tb fw` (which hard-codes `--noupdate --nodefaultcfg`) |
| 9 sentinel | `sentinel: parent` |
| 10 CLI | `TestSet.configure()` / `tear_down()` return at `if peer is None` before sending anything when no FIXED copper link is bound; with one they send `interface <p>`, `duplex auto`, `polarity auto`, `no shutdown` (per-case tear_downs also `no speed`). No `no polarity` (fixed b734b40). Not reached on this bench (below), so no defaulting defect can fire |

### What changed since the last triage of this script (x230 campaign 2026-10-09T1349): nothing that matters

- `bench-setup/tb470.static`, `tb470.setup.current`: unchanged; `264A23061 = swi_a` (IE520 stk_a member 1, u2), outlet 6.
- The script: `test-9001.33234.py` sha1 66c23163..., last changed Test-cases d9a08dd (2026-09-29); same as run 3.
- Stack software `awplus_main-20261008-57` on all units (run 3 was `awplus_main-20260923-20`).
- Test-Composer templates: `setup-a/`, `setup-b/` hold no files; only `mock-tb470/`, `mock-swapped/` have content. No pre-loaded pair.

### T33234 "Port - Auto MDI/MDI-X" (14 TestCases), DUT = IE520 stack `stk_a` via `swi_a`

**Re-verified live: UNSUPPORTED on the IE520-28GSX (no fixed copper switchport; ruling I-5, platforms/IE520.md §3).**
- **Discovery, reproduced by hand:** the stack's non-member data links in `tb470.setup` and their media
  (capture 015814Z `show interface status` Type, plus live `show system pluggable` 14:59 on u2):
  port1.0.2 1000BASE-T (AT-SPTXa, in cage), port1.0.17 1000BASE-T (AT-SPTXa, in cage), port1.0.3 1000BASE-SX,
  port3.0.2 1000BASE-T (AT-SPTXa, in cage), port4.0.2 10GBASE-TM (AT-SP10TM, in cage), port4.0.26 1000BASE-SX;
  port3.0.13 (AT-SPTXc) is the tb link. Every twisted-pair link is listed by `show system pluggable`, so
  `_ck_discover` buckets it `cusfp`, never `copper` -> `has_fixed_copper_port = False`, `self.peer = None`.
- **Expected run:** init (all six units, `powerOn=False`), discovery as above, `UNSUPPORTED: no copper switchport`
  log line, configure() skipped, framework "Bring up all switch ports" (`no shutdown` on every port the .setup
  declares, already up), framework "Save the current running config as the boot config" on stk_a, swi_b, swi_e,
  swi_f (`no boot config-file`, `copy run <dev>_9001_33234.cfg`, `boot conf <dev>_9001_33234.cfg`), then the
  marking pass: 14/14 "marked as unsupported ... without property has_fixed_copper_port, for device swi_a",
  no TestCase body, rc 0. Run 3 took 1 min 50 s.
- **Power cycles: 0 expected.** Skipped (skipIfExcl) cases take `ATTestCase.run()`'s `skipIfExcl and not
  self.supported` branch without entering `__run()`, so `powerCycleOnFail` stays False (run 3 source read +
  evidence: every power-sock log 127 bytes, no switching). The framework code was not re-read today (not
  reachable through `tools/tb`); if a cycle does happen it is the framework's, one six-unit cycle (~4 min).
  Office-hours safe.
- **Restore the RUN must do (gate 7, from run 3's recipe, 33234-unsupported.log lines 125-140):** on u5 (stack
  master), u3, u1, u0: `boot config-file flash:/tb470-bench.cfg`, `delete force <dev>_9001_33234.cfg`
  (stk_a / swi_b / swi_e / swi_f), `show boot` -> tb470-bench.cfg; then probe MATCH and running-config diff vs
  capture 015814Z (run 3: IDENTICAL).
- **Clean under /test-mode §11:** yes, expected on run 1 with zero repairs: no exception, no `% ` line (the
  script sends no CLI; the framework's boot-config save gave none in run 3), and the UNSUPPORTED is the
  platform's (no fixed copper port), not a missed enable step. No bench change makes it measurable.

### Case text vs script (for the §11 review)

- The refined case (`zephyr_payload.json`, 3c680c9, 2026-09-18) has 11 action steps (2-12); the script has
  14 TestCases numbered STEP 2-15 (finer split from the generator session), so step numbers do not line up.
- Payload step 7 (copper SFP) and step 8 (fibre SFP: polarity "not applicable") have no TestCase: stripped by
  the 2026-09-29 ruling (script header SCOPE). The payload itself does not record the ruling.
- The whole suite is gated on `has_fixed_copper_port`, including step 9 (invalid polarity values rejected),
  which needs no copper link at all. platforms/IE520.md §3 says the CLI is media-blind (polarity offered
  on fibre, nothing errors), so a fibre "not applicable" check would likely FAIL on the IE520 if it ran.

### Count (STANDING-ORDERS §3)

- **N = 1 runnable now**, as a validation run that records the framework's 14/14 UNSUPPORTED (platform) on
  `swi_a` = IE520 stack, 0 power cycles, ~2 min plus restore.
- **M = 0 blocked by topology.** Every IE520-28GSX front port is a cage, so no recable gives a fixed copper port.
- **K = 0 blocked otherwise.** (As a measurement: UNSUPPORTED on this platform; nothing on tb470 changes that.)
- Consoles left: u0 `awplus#`, u1 `4050-5g#`, u2/u4/u5 `IE520-stk#`, u3 `IE520-sa#` (bare-CR peek 15:01,
  transcripts `/tmp/tri1456/console-uN.log`); u2's ckcon ended `terminal no monitor` -> `IE520-stk#`. All logged
  in at exec, not exited (tb470, no constraint).
- DUT clock vs box: stack `show clock` 02:00:08 UTC when the box read 14:59:20 NZDT (01:59:20 UTC), DUT ~48 s ahead.
