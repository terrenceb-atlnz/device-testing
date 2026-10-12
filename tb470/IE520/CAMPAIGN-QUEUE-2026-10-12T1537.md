# Campaign queue — tb470, IE520 stack (`stk_a`) as the DUT, 1 AWPTCM script case (Ask-CK validation), from 2026-10-12 15:37 NZDT

The ask, 2026-10-12 15:37 NZDT (`/test-mode --from-ask-ck`, Ask-CK's launcher):
*"/test-mode --from-ask-ck /home/terrenceb/.local/share/ck-agent/runs/2026-10-12T1537-val-9f45/2026-10-12T1537-val-9f45.json AWPTCM-T33235"*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-12 15:37 NZDT, word for word from the Ask-CK hand-off `2026-10-12T1537-val-9f45.json`
(schema 1, run_id `2026-10-12T1537-val-9f45`, kind `validation`, seat `10.33.22.17`, created 2026-10-12T15:37:17+13:00):
Test Engineer: terrenceb@terrenceb-dl
Driver: ask-ck (2026-10-12T1537-val-9f45)
Testbox: "tb470"
Consoles: "all"
PDU: {"ip": "10.36.150.14", "outlets": {}}
Constraints: "none"

Hand-off case entries:
- AWPTCM-T33235 — kind `script`, script_rel `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py`
  (resolved: `claude/Test-cases/ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py`, read-only;
  sha1 b044d695…, last changed Test-cases 056114d 2026-10-01 13:03, 33 TestCases), case_payload_rel
  `ask-ck/functions/generator/refined-cases/Port/AWPTCM-T33235/zephyr_payload.json`.

Sentinel's reading of the facts (not a session fact): "all" on tb470 = u0-u5. The hand-off gives no
outlets, so a power cycle takes each unit's outlet from `bench-setup/tb470.static` (STANDING-ORDERS §1),
as in today's 14:56 campaign: u0 swi_f 1, u1 swi_e 7, u2 swi_a 6, u3 swi_b 8, u4 swi_d 4, u5 swi_c 5.
`<FAMILY>` = IE520 (the script's DUT is the IE520 stack `stk_a`, as in run 4 of 2026-10-01).

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  This is a `Driver: ask-ck` campaign: at completion the sentinel runs `/create-logs --auto` (manual
  cases only; T33235 is a script case, whose framework log is already final).
- `STANDING-ORDERS.md` applies in full (no tightening constraint). §6: the framework's post-failure
  power cycle is accepted; a systematically failing script is stopped and repaired, not re-run blind.
- `/test-mode` §10 applies: nothing stops to wait. Every question becomes a `NOTIFY` line plus an
  entry in `## Issues`. §11 applies (`kind: validation`): repair loop on a COPY in
  `<group dir>/33235/work/`, `repairs.md`, ≤5 runs, then `review.md`.
- Office hours (memory `reboot-heavy-runs-after-hours`): the campaign starts 15:37 on a weekday (Monday).
  T33235 is reload-bearing (a whole-stack `reload` step; a FAILED/UNSUPPORTED TestCase costs a six-unit
  PDU cycle). The tester estimates the reboot events at triage; the sentinel decides start time from that.
- Recorded history (not a verdict for this campaign): IE520 port-2026-09-29 run 4 (2026-10-01, Test-cases
  3454bc0): PASS, 32 PASS / 1 UNSUPPORTED (TestCase_20) / 0 FAIL, 72 min, one PDU cycle (after TestCase_20)
  plus the script's own whole-stack reload. The script has changed since (056114d: not-applicable cases
  skipped before they run; no startup-config backup). Re-verify; do not inherit.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | port (script, validation): T33235 | tb470/IE520/port-2026-10-12T1537/ | RUNNING | Triage 15:39-15:48 (probe 023956Z MATCH, c1ae32b): 1 runnable / 0 topology / 0 otherwise, after the tester's one-leg isolation (stack port1.0.2 out of sa2; restored after). Expected 31 PASS / 2 UNSUPPORTED (TC20/21 pre-marked) / 0 FAIL, 0 PDU cycles, 1 whole-stack reload (TC33), ~80 min incl. setup/restore. RUN dispatched ~15:52 with validation: repair (§11); office-hours guard in Issues I-1 |

## Setup and restore recipe — group 1

Written by bench-runner (RUN, validation: repair) before touching the bench, 2026-10-12 ~15:50 NZDT.
Setup ONCE before the TestSet, restore ONCE after it (STANDING-ORDERS §6); nothing is changed between TestCases.

**Setup (tester, stack master console u5, `tools/tb ckcon tb470 <scratch> u5 115200 --stop-on-error ...`):**
`configure terminal` / `interface port1.0.2` / `shutdown` / `no static-channel-group` / `no shutdown` / `end`.
Verify: `show running-config interface port1.0.2` has no `static-channel-group` line; `show interface port1.0.2 status`
reads `connected 1 a-full a-1000 1000BASE-T` (allow ~30 s, `@poll`); `show static-channel-group` sa2 = {port1.0.9} only.
Nothing on the x230 (u0), the IE520-sa (u3) or the 4050 (u1). Not written to flash by the tester. The framework then,
on every device the `.setup` declares (stk_a, swi_b, swi_e, swi_f): `no shutdown` on each declared port, and
`no boot config-file` / `copy run <dev>_9001_33235.cfg` / `boot config-file <dev>_9001_33235.cfg` (the isolated
port1.0.2 is therefore in `stk_a_9001_33235.cfg`; TestCase_32/33 `copy running-config startup-config` write that file again,
and TestCase_33 reloads the whole stack into it).

Run: copy in `tb470/IE520/port-2026-10-12T1537/33235/work/` (script, `library_9001.py`, `ck_media.py`), launched
`tools/tb fwprep tb470 33235/<run> <files>` + `tools/tb fw tb470 33235/<run> test-9001.33235.py
/home/st-art/st-art/configs/tb470.setup` (`--noupdate --nodefaultcfg`), workdir `/home/st-art/pytest-create/33235/<run>/`.

**Restore (anyone can run it, even if the tester died mid-run):**
1. `tools/tb ps tb470 'test-9001.33235'` -> nothing running (else `tools/tb waitfor tb470 <workdir>/run.exit <s>`;
   never kill mid power cycle or mid TestCase_33 reload).
2. `tools/tb precheck tb470 u0-u5` -> CLEAR, then `tools/tb scratch tb470 <scratch>`; bare CR (`peek`) on u5 must give
   `IE520-stk#` (a reload or PDU cycle may leave it at `login:`; ckcon logs in).
3. Stack, through `tools/tb ckyn tb470 <scratch> u5 115200 ...`: `show boot`, `configure terminal`, `interface port1.0.2`,
   `shutdown`, `static-channel-group 2`, `no shutdown`, `exit`, `boot config-file flash:/tb470-bench.cfg`, `end`,
   `delete force stk_a_9001_33235.cfg`, `delete force TestCase_tear_down.cfg` (only if `dir` lists it), `show boot`,
   `show static-channel-group`.
4. u3 (swi_b), u1 (swi_e), u0 (swi_f), each: `show boot`, `configure terminal`, `boot config-file flash:/tb470-bench.cfg`,
   `end`, `delete force <swi_b|swi_e|swi_f>_9001_33235.cfg`, `delete force TestCase_tear_down.cfg` (only if listed), `show boot`.
5. Every `show boot` -> `Current boot config: flash:/tb470-bench.cfg (file exists)`; stack sa2 = {port1.0.2, port1.0.9}.
6. `tools/tb probe tb470 --consoles u0-u5 --no-prompt --pdu 10.36.150.14 --outlet u0=1,u1=7,u2=6,u3=8,u4=4,u5=5
   --baud 115200` -> exit 0 MATCH.
7. Running-config diff of the new capture's `u0..u3.show_running-config.txt` against
   `bench-setup/captures/2026-10-12T023956Z/` (CR stripped, ignoring the timestamp header lines) -> IDENTICAL; and on u5
   `remote-diff all show running-config` -> no member differs (memory `stack-refused-command-lands-on-backups`).
8. Every console left at exec (`end`, `terminal no monitor`); tb470 is the Test Engineer's own, so no `exit`.

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

- **I-1 (campaign) office hours, 2026-10-12 15:52.** NOTIFY campaign -- T33235 reboots during office hours (Mon ~15:52 start): triage expects 0 PDU cycles and 1 whole-stack reload (TC33, ~17:10) in an ~80 min run -- Assumed: not reboot-heavy (memory reboot-heavy-runs-after-hours is about repeated cycles); run started now. Guard: if run 1 shows the pre-marking does not take (a framework PDU cycle after a skipped-by-design case) or a repair re-run is needed, the tester stops after that run and no further run starts before 18:00 NZDT.
- **I-2 (T33235) run 1 systematic exception-log FAIL, 2026-10-12 15:58.** NOTIFY T33235 -- the framework's post-case exception-log check failed TestCase 1 (`!!FAIL: stk_a (member-3) contains 5 exceptions`; the case's own checks all PASS), so a six-unit PDU cycle followed at 15:58:14. Member 3 already logged entries on 2026-10-04 and 2026-10-07, before the run -- what it did instead: run 1 is stopped after the cycle (STANDING-ORDERS §6, I-1); the tester saves the log and checks whether any entry is new; if all predate the run, clearing the history is a bench-state repair; a new entry is a DUT finding; run 2 waits for 18:00.


## Triage 2026-10-12T1537

Tester: bench-runner, TRIAGE dispatch, 15:39-15:47 NZDT. Read-only apart from the probe and one bare-CR peek on
u0-u5 (transcripts `/tmp/tri1537/console-uN.log`). No case run, no reload, no PDU cycle, no configuration sent.

### Gate

| gate | result |
| --- | --- |
| 1 occupancy | `tools/tb precheck tb470 u0-u5` 15:39:55: **CLEAR** (exit 0), `&&`-gated into the probe; re-run CLEAR before the 15:46 peek |
| 2 consoles | probe logged in on all six (banners awplus, 4050-5g, IE520-stk-1, IE520-sa, IE520-stk-4, IE520-stk); peek 15:46 and the transcripts' last lines: u0 `awplus#`, u1 `4050-5g#`, u2/u4/u5 `IE520-stk#`, u3 `IE520-sa#`. No shell, no config mode |
| 3 template | `/nfsHome` mounted (nfs4 10.36.250.11:/home); `/home/st-art/st-art/configs/tb470.setup` present (Oct 9 11:34) |
| 4 probe | `tools/tb probe tb470 --consoles u0-u5 --no-prompt --pdu 10.36.150.14 --outlet u0=1,u1=7,u2=6,u3=8,u4=4,u5=5 --baud 115200` (outlets from `tb470.static` by serial) -> **exit 0 MATCH**, capture `captures/2026-10-12T023956Z` (10.1 s). No USER-CONFLICT. Advisory unchanged (information only): eth1 learned on swi_c port3.0.13 AND swi_f port1.0.2 (the stack's VLAN 1 reaches the x230 over port1.0.2). `bench-state.md`: only its stamps changed |
| 5 setup | `bench-setup/tb470.setup.current` equals the new bench-state fence (ignoring `###` lines) |
| 6 preflight | `pt_preflight.py --setup bench-setup/tb470.setup.current --script .../test-9001.33235.py`: **RUNNABLE (3/3)**, `swi_a /dev/u2 (member of stk_a)`, tb = the box. Its role notes (copper 1.0.17, cusfp 1.0.2, fibre 1.0.3) are offline guesses; the real binding is below |
| 7 boot configs | capture 023956Z: u0 x230, u1 4050, u2 stack, u3 IE520-sa all `Current boot config: flash:/tb470-bench.cfg (file exists)`. That is the run's baseline. Stack 1 Backup / 3 Active Master / 4 Backup, all Ready |
| 8 server path | retired (no `FRAMEWORK_RUN_FLAGS` in `pt_exec.py`); launch with `tools/tb fwprep` / `tools/tb fw` (hard-codes `--noupdate --nodefaultcfg`, refuses `--update`/`--defaultcfg`) |
| 9 sentinel | `sentinel: parent` |
| 10 CLI | below ("Defaulting commands"): no command fails every TestCase, PROVIDED stack port1.0.2 is out of sa2 |

### What changed since run 4 (2026-10-01, Test-cases 3454bc0, PASS 32/1/0)

- **Script:** one commit, Test-cases **056114d** (2026-10-01 13:03): `mark_cases_unsupported()` pre-marks later cases
  before they run (TestCase_3 -> TestCase_20/21 unless speed 10 AND 100 were both accepted; TestCase_7 -> TestCase_19 if
  no speed was rejected; TestCase_13 -> the 15 `SPEED_S_CASES` if no S; TestCase_20 -> TestCase_21), each with
  `skipIfExcl = True`; TestCase_28-30 gated on `has_monitored_link`; TestCase_21 now goes with TestCase_20 (it would
  read UNSUPPORTED, not PASS); **the startup-config backup/restore is gone** (`ck_t33235_startup_backup` 0 hits).
  `library_9001.py` (b734b40) and `ask-ck/tools/pt_media.py` unchanged since before run 4. Sha1 b044d695... matches the hand-off.
- **Software:** `awplus_main-20261008-57` on the stack, IE520-sa, x230 and AR4050S (run 4: `awplus_main-20260923-20`).
- **Bench (probe 023956Z vs tb470.setup of 2026-10-01, 2ab61f7):**
  - swi_f is a different unit: **AT-x230-28GS V2** (A10783G262900002, all 28 ports cages), not the x230-10GP with fixed RJ45.
  - Stack <-> x230 now three links, each in its own VLAN pair, no LAG on the x230:
    port1.0.2 (AT-SPTXa, **stack sa2 member**, VLAN 1) <-> x230 port1.0.2 (AT-SPTX, VLAN 1);
    port1.0.17 (AT-SPTXa, VLAN 103) <-> x230 port1.0.3 (AT-SPTX, VLAN 103);
    port1.0.3 (1000BASE-SX, VLAN 104) <-> x230 port1.0.4 (AT-SPSX, VLAN 104).
    Run 4's pair (stack 1.0.2/1.0.9 in sa2 <-> x230 1.0.3/1.0.4 in sa2) is gone; stack port1.0.9 is "not present"
    but still configured in sa2.
  - Stack <-> IE520-sa: only the fibre 4.0.26 <-> 1.0.26 (VLAN 4000); the sa3 links (1.0.13/4.0.9) are gone (config kept).
  - tb eth1 moved to stack port3.0.13 (was 3.0.10); eth2 now on the 4050 port1.0.1, eth3 on x230 port1.0.5.
  - Spanning tree off on all four (`no spanning-tree rstp enable`), as before.

### Binding the run will make (the frame's own rules, worked through on today's capture)

`_ck_discover` sorts non-LAG links first (natural port order), LAG members last; `cusfp` binds before `fibre`
before `copper`, and `copper` falls back to `cusfp` (no fixed copper port on the IE520-28GSX).
- **As cabled now (no isolation):** cusfp = port1.0.17 <-> swi_f port1.0.3 (only non-LAG copper SFP);
  fibre = port1.0.3 <-> swi_f port1.0.4 (sorts before 4.0.26); **copper test port = port1.0.2 [LAG member, sa2]**
  <-> swi_f port1.0.2, with the frame's "aggregator member" WARNING. Measured on this build 2026-10-09 (T47208,
  `tb470/x230v2-28GS/ports-2026-10-09T0845/47208/47208.log` l.282/287): `% port1.0.2: Cannot configure aggregator member.`
  for speed on that port. Every DUT speed command would be refused, TestCase_13 would find no S, and 15+ cases would
  read UNSUPPORTED for a missed setup step: **not a clean run.**
- **With stack port1.0.2 taken out of sa2 (the recipe below):** both copper SFP links are non-LAG, so
  **cusfp/monitored = port1.0.2 <-> swi_f port1.0.2**, **copper test port = port1.0.17 (AT-SPTXa) <-> swi_f port1.0.3
  (AT-SPTX)**, **fibre = port1.0.3 (SX) <-> swi_f port1.0.4 (AT-SPSX)**, tb = port3.0.13 <-> eth1. The IE520-sa
  fibre (4.0.26) is not bound; the SA only takes the framework's boot-config save.

### Isolation: ONE leg, no VLAN change, no loop risk

Run 4's two-leg recipe (both sa2 legs out, VLANs 3998/3999 on both ends) existed because both legs ended on the
x230's own sa2 in one VLAN with STP off. Today the x230 has no LAG and each stack<->x230 link already sits in its
own VLAN pair (1 / 103 / 104), and port1.0.9 is empty. Taking stack port1.0.2 out of sa2 leaves it in VLAN 1,
the only VLAN-1 path between the stack and the x230 (as it already is: sa2's one live member). **No loop.**

Setup (tester, stack console u5 or u2, `ckcon --stop-on-error`, before launch):
`interface port1.0.2` / `shutdown` / `no static-channel-group` / `no shutdown`; verify
`show running-config interface port1.0.2` has no channel-group line and `show interface port1.0.2 status` reads
`connected 1 a-full a-1000 1000BASE-T`; sa2 keeps port1.0.9. Nothing on the x230.

Restore (after the run, in this order):
1. `tools/tb ps tb470 'test-9001.33235'` -> nothing running (else wait for `run.exit`).
2. Stack: `interface port1.0.2` / `shutdown` / `static-channel-group 2` / `no shutdown`;
   `boot config-file flash:/tb470-bench.cfg`; `delete force flash:/stk_a_9001_33235*.cfg`,
   `delete force flash:/TestCase_tear_down.cfg`.
3. x230 (u0), IE520-sa (u3), AR4050S (u1): `boot config-file flash:/tb470-bench.cfg`;
   `delete force flash:/<swi_f|swi_b|swi_e>_9001_33235*.cfg`, `delete force flash:/TestCase_tear_down.cfg`.
4. `show boot` on all four -> `flash:/tb470-bench.cfg (file exists)`; stack `show static-channel-group` sa2 = {1.0.2, 1.0.9}.
5. Probe (same facts) -> MATCH; running-config diff vs `captures/2026-10-12T023956Z` (ignore headers) -> IDENTICAL,
   plus `remote-diff all show running-config` on the stack (memory `stack-refused-command-lands-on-backups`).
6. Consoles left at exec (`end`, `terminal no monitor`); tb470 is the Test Engineer's own, so no `exit`.

### Defaulting commands (STANDING-ORDERS §6)

Every command the script sends: TestSet.configure() on the six bound ports (DUT 1.0.17/1.0.2/1.0.3, x230
1.0.3/1.0.2/1.0.4): `configureDefaultPort` (`no speed`, `duplex auto`, `polarity auto`, `no shutdown`; a refusal is
logged, never failed) then unchecked `no speed`, `duplex auto`, `no shutdown`. tear_down(): `no speed`, `duplex auto`.
Cases: `speed 10|100|1000|2500|5000|10000|40000|100000|auto|fast|5|200000`, `duplex full|auto`, `shutdown`,
`no shutdown`, `copy running-config startup-config` (+`y`), `show interface [<p>] [status]`,
`show running-config interface <p>`, `show system pluggable`, `show log [tail 250]`, `show startup-config`,
and `dut.reboot('', timeOut=900)`.
- IE520: all ran in run 4 (32 PASS) except on this build; nothing in them is new syntax. Only refusal known on this
  build is the aggregator-member one, removed by the isolation.
- x230v2-28GS (same build): `speed`/`duplex`/`no speed` ran in T47208/T47210 on 2026-10-09 (x230 port1.0.3 forced
  100/full against stack port1.0.17 linked). `polarity auto` on an x230 SFP port is not live-verified; a refusal is
  only logged by `configureDefaultPort`.
- No `yesNo()`/operator prompt is called by any case (the library defines it; unused).
- **Verdict: no command that fails every TestCase.** No live `qmark` was needed.

### T33235 "(3) Port - Fixed port Speed" (33 TestCases), DUT = IE520 stack `stk_a` via `swi_a` (u2)

Expected, with the isolation (prediction, not a result):
- TestCase_1-7 copper sweep on 1.0.17 <-> x230 1.0.3: `speed 10` rejected by the AT-SPTXa (T47208), 100 and 1000
  accepted and linked (100/full measured on this pair 2026-10-09), 2500/5000/10000 rejected. TestCase_3 then
  **pre-marks TestCase_20 and TestCase_21 UNSUPPORTED** (speed 10 not accepted); TestCase_7 does not mark 19.
- TestCase_8-12 fibre sweep on stack 1.0.3 <-> x230 1.0.4, both AT-SPSX-class 1000BASE-SX. **Changed since run 4:**
  on this build both SX ends ACCEPT `speed 100` and read `connected a-full 100` while passing no frames (T47209 FAIL on
  the x230, "the IE520 does the same", same stack port 1.0.3, 2026-10-09). With both ends forced 100/full,
  TestCase_8 most likely PASSes on the status row and `current speed 100` (the script checks no traffic, so it
  cannot see that defect: a false-PASS risk for the §11 review). If the row does not read connected within 30 s it
  FAILs, a real DUT fault (still clean), and costs one six-unit PDU cycle. 10000/40000/100000: rejected at both ends expected.
- TestCase_13 S = 1000; 14-19, 22-33 as run 4 (S2 = 100 in TestCase_30; monitored = 1.0.2 and 1.0.3).
- **Expected tally: 31 PASS / 2 UNSUPPORTED (20, 21, skipped with no cycle) / 0 FAIL**, framework rc 0.

### Reboot events and time (office-hours decision; Monday, now ~15:47)

- **Framework PDU cycles: 0 expected.** TestCase_20/21 are now marked `supported = False` by TestCase_3 before they
  run; with `skipIfExcl` the framework's `run()` takes the skip branch, which never sets `powerCycleOnFail`
  (framework copy of 2026-08-11, ATTestCase.py l.958-972; the same branch skipped 14/14 with 0 cycles in today's
  T33234 run). Caveat: the run-time marking itself (056114d) has never run on hardware; this run is its first test.
  If it does not take, TestCase_20 cycles once as in run 4 and TestCase_21 PASSes or cycles: worst case 2 cycles.
- **Risk of a cycle:** TestCase_8 (above), or any unexpected FAIL: one six-unit cycle each (outlets 1, 4, 5, 6, 7, 8:
  stack, IE520-sa, AR4050S, x230), ~4-5 min.
- **The script's own reload: 1**, TestCase_33, `reload` of the whole stack (three IE520 members together, via
  `dut.reboot`); run 4: 3 min 5 s (11:08:36-11:11:41). No `dut.reboot` elsewhere; the x230, 4050 and SA never reboot.
- **Time:** run 4 took 72 min with one PDU cycle, so ~67 min without; plus ~3 min isolation and ~10 min restore and
  probe: **~80 min**, i.e. a 16:00 start ends ~17:20.
- **D-2** (refused startup-config restore under `--nodefaultcfg`) is **resolved by removal** in 056114d: the script
  takes no backup and restores none. The boot pointer still ends on `stk_a_9001_33235.cfg` (the framework's file,
  written again by TestCase_32/33's `copy running-config startup-config`): the restore recipe's step 2-3.

### Clean under /test-mode §11?

**Yes, expected on run 1, provided the one-leg isolation is made before launch.** Without it the copper role lands on
an aggregator member and the run is not clean (above). Known defects still present, none expected to fire:
- **D-1 / I-8 pattern, latent:** every gated case keeps a `self.supported = False` + `self.failed(...)` fallback in
  main(), so a pre-mark that misses still costs a cycle. Two guards have no pre-mark at all: TestCase_30
  `speed2 is None` (needs a second fixed speed that links; 100 does here) and TestCase_25 `peer is None`
  (unreachable: the copper role is required).
- **Accuracy risk (review, not repair):** TestCase_8-12 grade link state from the status row only; on this build the
  SX-at-100 dead link reads `connected`, so a PASS there is not proof of a working 100 Mb/s fibre link.
- Case text vs script: the refined payload (3c680c9) has 11 steps; the script has 33 TestCases (STEP 2-34), a finer split.

### Count (STANDING-ORDERS §3)

- **N = 1 runnable**, T33235, after the tester's one-leg setup (stack port1.0.2 out of sa2, restored after). That
  change is within the test (STANDING-ORDERS §1, the run-4 precedent), not a recable.
- **M = 0 blocked by topology.**
- **K = 0 blocked otherwise.**
- Reboot load: 1 whole-stack reload + 0 expected PDU cycles (worst plausible 1-2), ~80 min: the sentinel's office-hours call.
