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


## Triage 2026-10-13T0626

Tester: bench-runner, TRIAGE dispatch, 06:27-06:32 NZDT (Tue). Read-only apart from the probe: one bare-CR peek on
u0-u5 and `show` reads on u5, u0, u1, u3 (transcripts `/tmp/tri0626/console-uN.log` on tb470). No case run, no
reload, no PDU cycle, no configuration sent, nothing cleared. This re-verifies `## Triage 2026-10-12T1537` in
`CAMPAIGN-QUEUE-2026-10-12T1537.md` against today's bench; what is not restated here holds as written there.

### Gate

| gate | result |
| --- | --- |
| 1 occupancy | `tools/tb precheck tb470 u0-u5` 06:27:59: **CLEAR** (exit 0; all six free, stephenh's minicom on u2 is gone), `&&`-gated into scratch and template; re-run CLEAR, `&&`-gated into the probe |
| 2 consoles | peek 06:28: u0 `awplus login:`, u1 `4050-5g#`, u2 `IE520-stk-1 login:`, u3 `IE520-sa#`, u4/u5 `IE520-stk#`. No shell, no config mode. Transcripts close at exec: u0 `awplus#`, u1 `4050-5g#`, u3 `IE520-sa#`, u5 `IE520-stk#` |
| 3 template | `/nfsHome` mounted (nfs4 10.36.250.11:/home); `/home/st-art/st-art/configs/tb470.setup` present (Oct 9 11:34) |
| 4 probe | `tools/tb probe tb470 --consoles u0-u5 --no-prompt --pdu 10.36.150.14 --outlet u0=1,u1=7,u2=6,u3=8,u4=4,u5=5 --baud 115200` -> **exit 0 MATCH**, capture `captures/2026-10-12T172836Z` (10.1 s). No USER-CONFLICT. Advisory unchanged (eth1 learned on swi_c port3.0.13 AND swi_f port1.0.2). `bench-state.md`: only its three stamps changed |
| 5 setup | `bench-setup/tb470.setup.current` equals the new bench-state fence (ignoring `###` lines) |
| 6 preflight | `pt_preflight.py`: **RUNNABLE (3/3)**, swi_a /dev/u2 (member of stk_a), tb = the box |
| 7 boot configs | capture 172836Z: u0 x230, u1 4050, u2 stack, u3 IE520-sa all `Current boot config: flash:/tb470-bench.cfg (file exists)`; software `awplus_main-20261008-57` on all four. Stack 1 Backup / 3 Active Master / 4 Backup, all Ready |
| 8 server path | retired (no `FRAMEWORK_RUN_FLAGS` in `pt_exec.py`); launch with `tools/tb fwprep` / `tools/tb fw` |
| 9 sentinel | `sentinel: parent` |
| 10 CLI | unchanged since yesterday (script sha1 b044d695caa3..., Test-cases 056114d is still the last change to `9001_Port/` and `pt_media.py`): no command fails every TestCase, PROVIDED stack port1.0.2 is out of sa2 |

### Diff vs yesterday (post-restore capture 2026-10-12T030621Z, 16:06 NZDT)

- **Nothing changed.** `show running-config` of u0, u1, u2 (stack), u3 is IDENTICAL (CR stripped, `!`/timestamp lines
  ignored); `show stack` identical; `show system` differs only in free RAM.
- **No reboot since yesterday's run-1 PDU cycle:** uptimes 14:29-14:30 at 06:28 on every unit (booted ~15:58 Mon).
  So stephenh's 17:13+ session on u2 changed no config and rebooted nothing measurable here.
- No `*_9001_33235.cfg` or `TestCase_tear_down.cfg` left on any flash (`dir` on u5, u0, u1, u3): the restore held.
- No framework or probe process running on the box (`tools/tb ps`).

### Isolation re-checked: ONE leg is still right and sufficient

- Stack `show static-channel-group`: sa2 = {port1.0.2, port1.0.9}; port1.0.9 holds no pluggable (empty cage).
- Stack `show interface ... status`: port1.0.2 connected VLAN 1 a-full a-1000 1000BASE-T (AT-SPTXa);
  port1.0.17 connected VLAN 103 a-1000 1000BASE-T (AT-SPTXa); port1.0.3 connected VLAN 104 a-1000 1000BASE-SX (AT-SPSX).
- x230 (u0): port1.0.2 VLAN 1 (AT-SPTX), port1.0.3 VLAN 103 (AT-SPTX), port1.0.4 VLAN 104 (AT-SPSX), all connected
  a-1000; running-config identical to yesterday, so still no LAG on the x230.
- Hence the binding of yesterday's triage holds: without isolation the copper role lands on LAG member port1.0.2
  (`% Cannot configure aggregator member`, not clean); with port1.0.2 out of sa2: cusfp/monitored = 1.0.2 <-> x230
  1.0.2, copper = 1.0.17 <-> x230 1.0.3, fibre = 1.0.3 <-> x230 1.0.4. Taking 1.0.2 out of sa2 leaves it the only
  VLAN-1 path to the x230: no loop. Setup and restore recipe as written in yesterday's queue file.

### Exception logs (read-only, nothing cleared)

`show exception log`: stack members 1, 3, 4 **None**; x230 (u0) **None**; AR4050S (u1) **None**; IE520-sa (u3) **None**.
Yesterday's Oct 04/07 entries on member 3 were cleared by the framework's `check_exceptions()` after run 1's hit.
R1 (repairs.md) still applies as a pre-launch step: re-read all four just before launch and clear only entries that
predate the run; today it is expected to be a no-op.

### Expected result, reboots, time (office-hours call; Tue, now ~06:32)

- **Expected tally: 31 PASS / 2 UNSUPPORTED (TestCase_20, 21, pre-marked by TestCase_3, skipped) / 0 FAIL**, rc 0.
- **Framework PDU cycles: 0 expected.** Risk: TestCase_8 (SX forced to 100: reads connected on this build, so most
  likely PASS; if not, 1 cycle); the 056114d pre-marking never yet run on hardware (if it misses, TestCase_20 and
  maybe 21 cycle: worst plausible 2). Each cycle = outlets 1, 4, 5, 6, 7, 8 (stack, IE520-sa, AR4050S, x230), ~4-5 min.
- **Script reloads: 1**, TestCase_33, whole stack (`dut.reboot`), ~3 min, at the end of the run (~60-65 min after
  launch). Nothing else reboots.
- **Time: ~80 min** (~3 min isolation + exception re-read, ~67 min run, ~10 min restore + probe). A 06:45 launch
  reloads the stack ~07:45-07:50 and ends ~08:05; each unexpected cycle adds ~5 min.

### Count (STANDING-ORDERS §3)

- **N = 1 runnable**: T33235, after the tester's one-leg setup (stack port1.0.2 out of sa2, restored after; within the test).
- **M = 0 blocked by topology.**
- **K = 0 blocked otherwise.**
