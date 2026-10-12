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
| 1 | port (script, validation): T33235 | tb470/IE520/port-2026-10-13T0954/ | BLOCKED (topology) | queued 09:54; TRIAGE dispatched 09:56; script `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py`. Triage 09:57-10:08 (probe 205816Z on u2-u5: template minus swi_e/swi_f only, expected; stack and IE520-sa running-config IDENTICAL to 204840Z). **Without u0/u1 the stack has ONE switch-partner link, port4.0.26 <-> IE520-sa port1.0.26, and it is 1000BASE-SX: the REQUIRED copper role finds no link, so init() raises "BENCH PROBLEM ... no unused copper link" and the TestSet aborts before TestCase_1.** Unblock: two twisted-pair links stack <-> IE520-sa (the optional cusfp role takes the first, the copper role needs a second), the second in its own VLAN since STP is off on both; exact change in `## Triage 2026-10-13T0954`. Run .setup drafted: `port-2026-10-13T0954/tb470-u2u5.setup` (re-triage adds the new [portlink]s) |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| T33235 | (3) Port - Fixed port Speed | port-2026-10-13T0954 | NOT TESTED | BLOCKED by topology under the session constraint (no x230/4050): on u2-u5 the stack's only partner link is port4.0.26 <-> IE520-sa port1.0.26, 1000BASE-SX; the script's REQUIRED copper role (after the optional cusfp role takes the first copper link) has no copper link, so init() would abort "no unused copper link". Unblock: recable per `## Triage 2026-10-13T0954` (stack 1.0.10 <-> IE520-sa 1.0.2 + a second copper link on a stack port below 1.0.10, in its own VLAN), or lift the constraint and run after the x230 campaign | (none: not run) | sentinel |

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

## Triage 2026-10-13T0954

Tester: bench-runner, TRIAGE dispatch, 09:57-10:08 NZDT (Tue, office hours). Read-only apart from the probe: one bare-CR
peek on u2-u5 and the probe's own `show` reads. The probe ran `--read-only` (no `lldp run`, no host-NIC pings), because
eth2/eth3 face the 4050/x230 that the other campaign is driving. No case run, no configuration sent, no reload, no PDU
cycle. u0/u1 never opened. **`bench-setup/bench-state.md` NOT touched:** the probe wrote to
`--out /tmp/tri0954/bench-state.md` on the box, so the full u0-u5 file from 204840Z stands and nothing needed restoring.

### Gate

| gate | result |
| --- | --- |
| 1 occupancy | `tools/tb precheck tb470 u2-u5` 09:57:44: **CLEAR** (exit 0, all four free, no FOUND at all this time). `&&`-gated into scratch `tri0954` and template; re-run CLEAR, `&&`-gated into the probe |
| 2 consoles | peek: u2 `IE520-stk#`, u3 `IE520-sa#`, u4 `IE520-stk#`, u5 `IE520-stk#`. No shell, no config mode. Left at exec (tb470 is the Test Engineer's own box, so no `exit`) |
| 3 template | `/nfsHome` mounted (nfs4 10.36.250.11:/home); `/home/st-art/st-art/configs/tb470.setup` present (Oct 9 11:34) |
| 4 probe | `tools/tb probe tb470 --consoles u2-u5 --no-prompt --read-only --baud 115200 --pdu 10.36.150.14 --outlet u2=6 --outlet u3=8 --outlet u4=4 --outlet u5=5 --out /tmp/tri0954/bench-state.md` -> **exit 1 MISMATCH**, capture `bench-setup/captures/2026-10-12T205816Z` (10.0 s). All 13 MISMATCH lines are swi_e/swi_f (switch, baud, boot, power, powerlink, their portlinks): the excluded u0/u1, expected. 3 NEEDS-CHECK `tb-swi_c/e/f` "NIC MAC not learned" come from `--read-only` (no host pings); stack port3.0.13 (eth1) still reads `connected 1000BASE-T`. **No USER-CONFLICT.** Banners u2 `IE520-stk-1`, u3 `IE520-sa`, u4 `IE520-stk-4`, u5 `IE520-stk` agree with tb470.static. Nothing on u2-u5 moved |
| 5 setup | `bench-setup/tb470.setup.current` = the bench-state fence, except `swi_e-swi_f = port1.0.5-port1.0.8` (4050 <-> x230), which is absent from the deployed file. Outside this session; reported only |
| 6 preflight | on the u2-u5 run .setup, `pt_preflight.py` says **RUNNABLE (3/3)**. It is media-blind and says so ("whether that link IS copper is read from the DUT at run time"), and the measured media make the case NOT runnable (below). Worth a Test-cases note: when the only link it can offer a role is fibre, preflight still reports RUNNABLE |
| 7 boot configs | capture 205816Z: stack and IE520-sa `Current boot config: flash:/tb470-bench.cfg (file exists)`; software `awplus_main-20261008-57`. Stack 1 Backup / 3 Active Master / 4 Backup, Normal operation. Uptime: stack 02:30 (the 0626 run's TC33 reload, ~07:28), IE520-sa 17:59. `show running-config`, `show interface status` and `show stack` of u2 (stack) and u3 are IDENTICAL to 204840Z |
| 8 server path | retired (no `FRAMEWORK_RUN_FLAGS` in `pt_exec.py`); a run launches with `tools/tb fwprep` / `tools/tb fw` |
| 9 sentinel | `sentinel: parent` |
| 10 CLI | not reached for this binding (it aborts in init). Same script sha1 b044d695 and same DUT build as the 0626 clean run |

### Why the script cannot bind on u2-u5 as cabled

The script binds three roles from the `.setup`'s [portlink]s and the media the DUT reports (`_ck_discover` l.84,
`_ck_bind_link` l.155):
- **cusfp**: optional, taken first;
- **fibre**: optional;
- **copper**: REQUIRED. It takes bucket `copper`, then `cusfp`. A TestBox link never counts.

On the IE520 every front port is an SFP cage, so every twisted-pair link lands in `cusfp` (0626 run:
`cusfp=port1.0.2,port1.0.17,...`). The run .setup without swi_e/swi_f (`port-2026-10-13T0954/tb470-u2u5.setup`) leaves
the stack two links:

| link | measured media (stack end / IE520-sa end) | role |
| --- | --- | --- |
| tb eth1 <-> stack port3.0.13 | 1000BASE-T | `tb` only, never a partner |
| stack port4.0.26 <-> IE520-sa port1.0.26 (VLAN 4000, lldp both ends) | 1000BASE-SX / 1000BASE-SX | `fibre` |

So the binding goes:
- cusfp = none (its cases UNSUPPORTED);
- fibre = port4.0.26;
- **copper = none, so init() raises `RuntimeError: BENCH PROBLEM, not a product defect: no unused copper link on
  swi_a` and the TestSet aborts.**

No config change fixes this, because the stack has no twisted-pair link to any unit on u2-u5. Its other copper links
all go to the x230 (port1.0.2, 1.0.17) or to the 4050 (sa1: port3.0.2, port4.0.2). Loosening the copper role, or
pointing it at the testbox, would weaken the case (STANDING-ORDERS §3), so neither is offered.

### Exact change that unblocks T33235 without the x230 or the 4050 (the Test Engineer's: a recable)

Fitted modules with no cable (`show interface status` notconnect, capture 205816Z), none of them in a channel-group:

| unit | 1000BASE-T | 10GBASE-TM | 10GBASE-T | empty cage |
| --- | --- | --- | --- | --- |
| stack | port1.0.10 | port1.0.6, port1.0.14, port1.0.26, port3.0.10 | port1.0.24 | port1.0.4 |
| IE520-sa | port1.0.2 | port1.0.14 | none | port1.0.4 |

1. **Link C (the copper test port, required):** a Cat5e/6 cable from **stack member 1 port1.0.10** (1000BASE-T, fitted)
   to **IE520-sa port1.0.2** (1000BASE-T, fitted). Both are access VLAN 1. The IE520-sa's only other link is in VLAN
   4000, so this link makes no loop.
2. **Link M (the cusfp/monitored role):** this second twisted-pair link is needed only so that the cusfp role does not
   take link C. It goes on a stack port numbered **below** port1.0.10, so the sorted binding gives C the copper role,
   as in the 0626 run. Either of these:
   - (a) **stack port1.0.6 (10GBASE-TM, fitted) <-> IE520-sa port1.0.14 (10GBASE-TM, fitted).** Needs no module
     handling. A 10G module in a 1G cage has not been measured here, so it must read `connected` on both ends, and
     re-triage must `qmark` `speed` and `duplex` on both ports: configure() and tear_down() send `no speed`,
     `duplex auto` and `no shutdown` there.
   - (b) fit a 1000BASE-T copper SFP (AT-SPTX/SPTXa) in **stack port1.0.4** and **IE520-sa port1.0.4** (both empty), and
     cable them. This copies the 0626 run, where both copper roles were AT-SPTXa-class.

   **Loop hazard:** STP is off on both units (`no spanning-tree rstp enable`), and the stack's VLAN 1 reaches the x230
   (sa2) and tb eth1. So link M must NOT be in VLAN 1 when it is plugged in:
   - put its two ports in their own VLAN first: `vlan 105` in `vlan database`, then `switchport access vlan 105` on
     both ends (as the x230 legs use 103/104);
   - plug M in only after that.

   This port setup is in-test: the tester can do it, and restores it, once the Test Engineer says the cable is going
   in. Or the Test Engineer makes it part of the standing config.
3. **Then re-dispatch TRIAGE.** It will:
   - run the probe, so LLDP proves C and M;
   - add `swi_a-swi_b = port1.0.10-port1.0.2, <M stack port>-<M sa port>` to `tb470-u2u5.setup`, from the probe's fence;
   - preflight the result;
   - `qmark` the partner-side commands on the IE520-sa ports.

   Recording the new cables in the deployed `tb470.setup` (`bench_probe.py apply`) stays the Test Engineer's call.

**Alternative with no recable:** run when the x230 campaign (0949) is finished, with the 0626 recipe. That uses the
x230, so it needs the constraint lifted; the Test Engineer decides.

### Expected result once unblocked (estimate, not measured)

- **Binding:**
  - cusfp/monitored = link M;
  - fibre = stack port4.0.26 <-> IE520-sa port1.0.26, 1000BASE-SX both ends (the 0626 run's fibre was port1.0.3 <-> x230);
  - copper = port1.0.10 <-> IE520-sa port1.0.2.

  The partner is now the IE520-sa (same build) instead of the x230. The partner-side commands are ones this DUT already
  accepted on its own AT-SPTXa and SX ports this morning.
- **Tally: about 31 PASS / 2 UNSUPPORTED / 0 FAIL, if the IE520-sa behaves as a partner as the x230 did.** The 2
  UNSUPPORTED are TC20/21 (speed 10 on a copper SFP, pre-marked). This is less certain than 0626: the autoneg and
  forced-mismatch cases TC25-27 and the fibre TC8 (`speed 100` on SX) now face an IE520 partner, and none of them has
  been seen on hardware that way.
- **Reloads: 1:** TC33 reloads the whole stack near the end (~3 min).
- **PDU cycles: 0 expected, worst plausible 2.** Each cycle hits ONLY outlets 4, 5, 6 and 8 (stack and IE520-sa,
  ~4-5 min), because the run .setup declares no swi_e/swi_f.
- **Time: ~85 min:** ~5 min setup (VLAN for M, R1 exception re-read), ~67 min run, ~12 min restore and probe.
- **Office hours:** 1 reload plus 0-2 four-unit cycles is not reboot-heavy, but it falls inside office hours. The Test
  Engineer chooses.
- **Restore outline** (written in full before a RUN):
  - on the stack and the IE520-sa, `boot config-file flash:/tb470-bench.cfg`;
  - delete every `*_9001_33235*.cfg` and `TestCase_tear_down.cfg` on the stack master, on both backups' flash, and on
    the IE520-sa;
  - put link M's ports back in their pre-run VLAN;
  - probe u2-u5: MATCH against the run .setup;
  - running-config IDENTICAL to 205816Z;
  - `remote-diff all show running-config`.

### MANUAL-ONLY

T33235 is not listed in MANUAL-ONLY.md, and triage found no step in it that needs a person. The recable is a bench
change, not a case step, so no row was added.

### Count (STANDING-ORDERS §3)

- **N = 0 runnable.**
- **M = 1 blocked by topology:** T33235. The change has two parts:
  - cable stack port1.0.10 <-> IE520-sa port1.0.2 (copper);
  - add a second twisted-pair stack <-> IE520-sa link on a lower-numbered stack port, in its own VLAN: either (a)
    stack port1.0.6 <-> IE520-sa port1.0.14 (both 10GBASE-TM, already fitted), or (b) new 1000BASE-T SFPs in
    port1.0.4 on both.
- **K = 0 blocked otherwise.**
- **I-3 (T33235 / campaign) BLOCKED by topology, campaign ended, 2026-10-13 10:12.** NOTIFY campaign -- T33235 needs a copper partner link the stack/IE520-sa (u2-u5) do not have without the x230/4050 (recable, STANDING-ORDERS §4: the Test Engineer's) -- marked BLOCKED / NOT TESTED; it is the only case, so the campaign ends (test-mode §10 step 4). No case run, no device state changed, no reload, no PDU cycle. Draft run setup kept: `port-2026-10-13T0954/tb470-u2u5.setup`. Side finding for Test-cases: `pt_preflight.py` said RUNNABLE (3/3) on the u2-u5 setup because it does not check media.
