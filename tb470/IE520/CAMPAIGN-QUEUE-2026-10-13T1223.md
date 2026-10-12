# Campaign queue — tb470, IE520 stack (`stk_a`) as the DUT, 1 AWPTCM script case (Ask-CK validation), from 2026-10-13 12:23 NZDT

The ask, 2026-10-13 12:23 NZDT (`/test-mode --from-ask-ck`, Ask-CK's launcher):
*"/test-mode --from-ask-ck /home/terrenceb/.local/share/ck-agent/runs/2026-10-13T1223-val-3ede/2026-10-13T1223-val-3ede.json AWPTCM-T33235"*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-13 12:23 NZDT, word for word from the Ask-CK hand-off `2026-10-13T1223-val-3ede.json`
(schema 1, run_id `2026-10-13T1223-val-3ede`, kind `validation`, seat `10.33.22.17`, created 2026-10-13T12:23:26+13:00):
Test Engineer: terrenceb@terrenceb-dl
Driver: ask-ck (2026-10-13T1223-val-3ede)
Testbox: "tb470"
Consoles: "u2-u5"
PDU: {"ip": "10.36.150.14", "outlets": {}}
Constraints: "do not attempt to use the 4050 or x230 for this run; recabled: stack port1.0.10–IE520-sa port1.0.2 (link C, VLAN 1); stack port1.0.6–IE520-sa port1.0.14 (link M, both ends in VLAN 106 \"link-m\", saved in tb470-bench.cfg)"

Hand-off case entries:
- AWPTCM-T33235 — kind `script`, script_rel `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py`
  (resolved: `claude/Test-cases/ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py`, read-only;
  sha1 f04ea35931e4…, last changed Test-cases ef53cea 2026-10-13 11:40 "14 TestCases instead of 33 (steps with the same
  gates run as one); step 29 without confCheck" — **NOT the script of the 0626/0954 campaigns** (b044d695…)),
  case_payload_rel `ask-ck/functions/generator/refined-cases/Port/AWPTCM-T33235/zephyr_payload.json`.

Sentinel's reading of the facts (not a session fact):
- "u2-u5" on tb470 = u2 swi_a, u3 swi_b (IE520-sa), u4 swi_d, u5 swi_c — the IE520 stack and the IE520-sa.
  u0 (x230, swi_f) and u1 (AR4050S, swi_e) are outside the session and, per the constraint, not used.
- The hand-off gives no outlets, so a power cycle takes outlets from `bench-setup/tb470.static` (STANDING-ORDERS §1)
  **for the session's units only**: u2 swi_a 6, u3 swi_b 8, u4 swi_d 4, u5 swi_c 5. Outlets 1 (x230) and 7 (AR4050S)
  are never cycled by this run.
- The recable is the one `CAMPAIGN-QUEUE-2026-10-13T0954.md` § Triage asked for, option (a) for link M, with link M in
  VLAN 106 rather than the suggested 105. It is a Test Engineer's change to the standing bench (saved in
  tb470-bench.cfg); the deployed `tb470.setup` is not known to carry it yet — triage's probe will say.
- The x230 campaign (`tb470/x230v2-28GS/CAMPAIGN-QUEUE-2026-10-13T0949.md`) shows both groups DONE by 12:06.
- `<FAMILY>` = IE520 (the script's DUT is the IE520 stack `stk_a`).

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  This is a `Driver: ask-ck` campaign: at completion the sentinel runs `/create-logs --auto` (manual
  cases only; T33235 is a script case, whose framework log is already final).
- `STANDING-ORDERS.md` applies, tightened by the constraint: **the x230 (u0) and the AR4050S (u1) are not used** —
  not opened, configured, declared in the run's `.setup`, or power-cycled. §6: the framework's post-failure power
  cycle is accepted only over outlets 4, 5, 6, 8.
- `/test-mode` §10 applies: nothing stops to wait. Every question becomes a `NOTIFY` line plus an
  entry in `## Issues`. §11 applies (`kind: validation`): repair loop on a COPY in
  `<group dir>/33235/work/`, `repairs.md`, ≤5 runs, then `review.md`.
- Office hours (memory `reboot-heavy-runs-after-hours`): the campaign starts 12:23 on a weekday (Tuesday). The 0954
  triage estimated 1 reload (TC33) and 0-2 four-unit PDU cycles: not reboot-heavy. See `## Issues`.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | port (script, validation): T33235 | tb470/IE520/port-2026-10-13T1223/ | RUN (triage 12:27-12:38: N=1, commit 490988e; RUN dispatched 12:40, validation: repair) | kind `script`, script_rel `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py` (sha1 f04ea359). Expected binding after the recable: cusfp = link M (stack 1.0.6 <-> sa 1.0.14), copper = link C (stack 1.0.10 <-> sa 1.0.2), fibre = stack 4.0.26 <-> sa 1.0.26 |

## Setup and restore recipe — group 1

Written by bench-runner at TRIAGE, 2026-10-13 12:34 NZDT, so the RUN tester (or anyone after it dies) starts from it; the
RUN tester re-reads it and commits any correction before the first case. Setup ONCE before the TestSet, restore ONCE after
it (STANDING-ORDERS §6); nothing is changed between TestCases. Scratch on tb470: `/tmp/<run scratch>/` (triage used
`tri1223`). **Consoles u2-u5 only; u0 (x230) and u1 (AR4050S) are never opened; outlets 1 and 7 are never cycled.**
Pre-run reference capture: `bench-setup/captures/2026-10-12T232732Z/` (u2 = stack, u3 = IE520-sa; gitignored, on the NFS
share) and its twin `2026-10-12T233314Z` (same probe, diffed against the run .setup).

**Run .setup:** `tb470/IE520/port-2026-10-13T1223/tb470-u2u5.setup` (on the box:
`/home/terrenceb/claude/device-testing/tb470/IE520/port-2026-10-13T1223/tb470-u2u5.setup`). It declares stk_a (swi_a u2,
swi_c u5, swi_d u4) and swi_b (u3, IE520-sa), outlets 6/5/4/8, and the links tb-swi_c eth1-port3.0.13,
swi_a-swi_b port1.0.10-port1.0.2 (link C) + port1.0.6-port1.0.14 (link M), swi_b-swi_d port1.0.26-port4.0.26 (SX).
The deployed `/home/st-art/st-art/configs/tb470.setup` is NOT used and NOT edited.

**Setup (nothing to configure):** links C, M and SX are standalone ports (no channel-group on either end), C in VLAN 1,
M in VLAN 106 `link-m`, SX in VLAN 4000, STP off on both units, all saved in `flash:/tb470-bench.cfg` by the Test
Engineer. So, unlike the 0626 recipe, **no port leaves an aggregator and no VLAN is changed**. Before launch only:
1. `tools/tb precheck tb470 u2-u5` CLEAR `&&` scratch; `peek` u2-u5 at 115200 -> `IE520-stk#` x3, `IE520-sa#`.
2. R1 (exception history): on u5 and u3 `show exception log` -> saved to `port-2026-10-13T1223/33235/work/pre-run<N>-<uN>-exc.out`.
   Triage 12:31: `None` on all three stack members and on the IE520-sa. An entry predating the run: `clear exception log`
   there and re-read; an entry from during a run is a DUT finding, reported, never cleared.
3. Save `33235/stk_a.cfg` (u5 `show running-config`) and `33235/swi_b.cfg` (u3) with the three `!` header lines.
4. Launch from a COPY in `port-2026-10-13T1223/33235/work/` (script f04ea359, `library_9001.py`, `ck_media.py` =
   Test-cases `ask-ck/tools/pt_media.py`): `tools/tb fwprep tb470 33235/run<N> <files>` then
   `tools/tb fw tb470 33235/run<N> test-9001.33235.py <run .setup above>` (`--noupdate --nodefaultcfg` by the wrapper).
   The framework then, on stk_a and swi_b: `no shutdown` on each declared port, `no boot config-file` /
   `copy run <dev>_9001_33235.cfg` / `boot config-file <dev>_9001_33235.cfg`, a per-TestCase save, and
   TestCase_31_to_33 writes startup and reloads the whole stack into that file.

**Restore (anyone can run it, even if the tester died mid-run):**
1. `tools/tb ps tb470 'test-9001.33235'` -> nothing running (else `tools/tb waitfor tb470 <workdir>/run.exit <s>`;
   never kill mid PDU cycle or mid TestCase_31_to_33 reload).
2. `tools/tb precheck tb470 u2-u5` -> CLEAR `&&` `tools/tb scratch tb470 <run>`; `peek` u5 and u3 must give `IE520-stk#` /
   `IE520-sa#` (a reload or PDU cycle may leave `login:`; ckcon/ckyn log in).
3. Stack, `tools/tb ckyn tb470 <run> u5 115200 ...`: `show boot`, `configure terminal`,
   `boot config-file flash:/tb470-bench.cfg`, `end`, `dir`; then `delete force <f>` for EVERY `stk_a_9001_33235*.cfg`
   and `TestCase_tear_down.cfg` that `dir` lists; then `dir IE520-stk-1/flash:/` and `dir IE520-stk-4/flash:/` and
   `delete force IE520-stk-<1|4>/flash:/<f>` for each such file there (a delete on the master does not remove the
   backups' copies); `show boot`.
4. IE520-sa, `tools/tb ckyn tb470 <run> u3 115200 ...`: `show boot`, `configure terminal`,
   `boot config-file flash:/tb470-bench.cfg`, `end`, `dir`, `delete force` every `swi_b_9001_33235*.cfg` and
   `TestCase_tear_down.cfg` listed, `show boot`.
5. Every `show boot` -> `Current boot config: flash:/tb470-bench.cfg (file exists)`.
6. Ports: `show running-config interface <p>` on stack port1.0.10, port1.0.6, port4.0.26 and IE520-sa port1.0.2,
   port1.0.14, port1.0.26 must match the reference capture (no `speed`, `duplex`, `polarity` or `shutdown` line; access
   VLAN 1 / 106 / 4000 as before). If tear_down did not run, send `no speed`, `duplex auto`, `no shutdown` there.
7. `tools/tb probe tb470 --consoles u2-u5 --no-prompt --read-only --baud 115200 --pdu 10.36.150.14 --outlet u2=6
   --outlet u3=8 --outlet u4=4 --outlet u5=5 --out /tmp/<run>/bench-state.md --template
   /home/terrenceb/claude/device-testing/tb470/IE520/port-2026-10-13T1223/tb470-u2u5.setup` -> exit 2 with exactly ONE
   NEEDS-CHECK (`tb-swi_c eth1`, a `--read-only` artefact) and no MISMATCH, as at triage 12:33. Never write
   `bench-setup/bench-state.md` from a u2-u5 probe (it would drop u0/u1): always `--out /tmp/...`.
8. Running-config diff of the new capture's `u2.show_running-config.txt` / `u3.show_running-config.txt` against
   `bench-setup/captures/2026-10-12T232732Z/` (CR stripped, header lines ignored) -> IDENTICAL; on u5
   `remote-diff all show running-config` -> no member differs (memory `stack-refused-command-lands-on-backups`).
9. Every console left at exec (`end`, `terminal no monitor`); tb470 is the Test Engineer's own box, so no `exit`.

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

- **I-0 (campaign) precheck CLEAR, 2026-10-13 12:24.** `tools/tb precheck tb470 u2-u5`: u2-u5 free, no holder, lock
  file, screen/tmux/minicom-type session or python script anywhere on the box (the x230 campaign 0949 is DONE).
- **I-1 (campaign) sentinel armed 12:25** on this session (Monitor, normal mode, UPDATES → the hand-off's
  sentinel_updates file; cron backstop every 15 min). Assumed: stand-down `2026-10-13 20:00` rather than the 17:30
  end of day, because a §11 repair loop of up to 5 runs may outlast 17:30; the campaign ends sooner on `ASKCK-DONE`.
- **I-2 (T33235) the script changed since the 0626 clean run.** Test-cases ef53cea (11:40 today): 14 grouped
  TestCases instead of 33, step 29 without confCheck. The 0626 PASS (31 PASS / 2 UNSUPPORTED) is not evidence for
  this script; triage reads the new grouping before any run.
- **I-3 (T33235) office-hours run, 2026-10-13 12:40.** NOTIFY T33235 -- run timing during office hours (Tue 12:35); triage estimates 1 stack reload and 0-2 four-unit PDU cycles (outlets 4,5,6,8) -- Assumed: run now, not reboot-heavy (memory reboot-heavy-runs-after-hours); repair loop capped at 5 runs.

## Triage 2026-10-13T1223

Tester: bench-runner, TRIAGE dispatch, 12:27-12:35 NZDT (Tue, office hours). Read-only apart from the probe: bare-CR
peeks, the probe's own `show` reads, six `qmark` help probes (no CR after `?`), and one `ckcon` of `show` commands on u5
and u3. No case run, no configuration sent, no reload, no PDU cycle. u0/u1 never opened. **`bench-setup/bench-state.md`
NOT touched** (both probes wrote `--out /tmp/tri1223/...`).

**Probe flag: `--read-only`, decided by what the other path touches.** Without it the probe (1) pings `.+2` out of EVERY
up host NIC with an IPv4 address, i.e. eth2 (faces the AR4050S) and eth3 (faces the x230), which the constraint says
not to use, and (2) switches `lldp run` on where it is off. `lldp run` is already on in both units' running and saved
config, so (2) buys nothing; (1) would only re-learn eth1's MAC. Cost: one NEEDS-CHECK (`tb-swi_c eth1`), see below.

### Gate

| gate | result |
| --- | --- |
| 1 occupancy | `tools/tb precheck tb470 u2-u5` 12:27:02: **CLEAR** (exit 0; u2-u5 free; only the Test Engineer's own ssh logins, information only). `&&`-gated into scratch `tri1223` and the template check, and re-run CLEAR `&&`-gated before each probe |
| 2 consoles | peek: u2 `IE520-stk#`, u3 `IE520-sa#`, u4 `IE520-stk#`, u5 `IE520-stk#`. No shell, no config mode. After the qmark/ckcon passes the transcripts (`/tmp/tri1223/console-u3.log`, `console-u5.log`) end `end` -> `#`, `terminal no monitor` -> `#`, closed at exec |
| 3 template | `/nfsHome` mounted (nfs4 10.36.250.11:/home); `/home/st-art/st-art/configs/tb470.setup` present, **Oct 13 12:21** (the Test Engineer's apply, fe119f1: adds `swi_e-swi_f = port1.0.5-port1.0.8`). It does not carry links C/M |
| 4 probe (vs deployed tb470.setup) | `tools/tb probe tb470 --consoles u2-u5 --no-prompt --read-only --baud 115200 --pdu 10.36.150.14 --outlet u2=6 --outlet u3=8 --outlet u4=4 --outlet u5=5 --out /tmp/tri1223/bench-state.md` -> **exit 1 MISMATCH**, capture `bench-setup/captures/2026-10-12T232732Z` (10.4 s). 14 of the 15 MISMATCH lines are swi_e/swi_f (the excluded u0/u1: switch, baud, boot, power, powerlink, their portlinks), expected. The 15th is **EXTRA_IN_LIVE `[portlink] swi_a-swi_b = {port1.0.10-port1.0.2, port1.0.6-port1.0.14}`: exactly the constraint's links C and M**, not yet in the deployed template (recording them there is the Test Engineer's `apply`, not needed for this run). 3 NEEDS-CHECK `tb-swi_c/e/f` "NIC MAC not learned" = `--read-only`. **No USER-CONFLICT.** Banners u2 `IE520-stk-1`, u3 `IE520-sa`, u4 `IE520-stk-4`, u5 `IE520-stk` agree with tb470.static |
| 4b probe (vs the run .setup) | same flags `--template .../port-2026-10-13T1223/tb470-u2u5.setup --out /tmp/tri1223/bench-state-vs-run.md` -> **exit 2**, capture `2026-10-12T233314Z`: **no MISMATCH**; ONE NEEDS-CHECK `tb-swi_c eth1` (read-only artefact; stack port3.0.13 reads `connected 1 a-full a-1000 1000BASE-T`; the script binds no tb role) |
| 5 setup | run .setup written: `tb470/IE520/port-2026-10-13T1223/tb470-u2u5.setup` = the 0954 draft + the probe fence's `swi_a-swi_b = port1.0.10-port1.0.2, port1.0.6-port1.0.14`; no swi_e/swi_f, no pwr_e/pwr_f |
| 6 preflight | `pt_preflight.py --setup <run .setup> --script test-9001.33235.py` -> **RUNNABLE (3/3)**: copper can take port1.0.10-port1.0.2, cusfp port1.0.6-port1.0.14, fibre port1.0.26-port4.0.26. Preflight is media-blind; the measured media (below) agree with every role this time |
| 7 boot configs | capture 232732Z: stack and IE520-sa `Current boot config: flash:/tb470-bench.cfg (file exists)`; software `IE520-awplus_main-20261008-57.rel` on both; bootloader 9.2.0. Stack 1 Backup / 3 Active Master / 4 Backup, Normal operation. Uptime: stack 04:59:57 (the 0626 run's TC33 reload), IE520-sa 20:28:46. `show startup-config` on both carries `vlan 106 name link-m` and `switchport access vlan 106` (the constraint's "saved in tb470-bench.cfg", confirmed) |
| 8 server path | retired (no `FRAMEWORK_RUN_FLAGS` in `pt_exec.py`); launch with `tools/tb fwprep` / `tools/tb fw` |
| 9 sentinel | `sentinel: parent` |
| 10 CLI | qmark on all six bound ports (below): every defaulting and partner-side command the script sends is offered. No refused command found |

### Links C and M exist as stated, and there is no loop

Diff of capture 232732Z against the 0954 triage's 205816Z on u2 (stack) and u3 (IE520-sa): **the only changes are the
constraint's**: `vlan 106 name link-m` + state enable on both; stack port1.0.6 and IE520-sa port1.0.14 to access VLAN 106;
stack port1.0.6/1.0.10 and IE520-sa port1.0.2/1.0.14 notconnect -> connected. `show boot`, `show stack` unchanged.

| link | stack end | IE520-sa end | LLDP (both ends) | MAC table | VLAN | channel-group |
| --- | --- | --- | --- | --- | --- | --- |
| C | port1.0.10, AT-SPTXc, `connected 1 a-full a-1000 1000BASE-T` | port1.0.2, AT-SPTXc, `connected 1 a-full a-1000 1000BASE-T` | stack 1.0.10 -> 84e3.2787.0780 port1.0.2; sa 1.0.2 -> 0000.cd37.0d6f port1.0.10 | each end learns the other's MAC in VLAN 1 | 1 / 1 | none / none |
| M | port1.0.6, AT-SP10TM, `connected 106 a-full a-1000 10GBASE-TM` | port1.0.14, AT-SP10TM, `connected 106 a-full a-1000 10GBASE-TM` | stack 1.0.6 -> port1.0.14; sa 1.0.14 -> port1.0.6 | each end in VLAN 106 | 106 / 106 | none / none |
| SX (standing) | port4.0.26, AT-SPSX, `connected 4000 a-full a-1000 1000BASE-SX` | port1.0.26, AT-SPSX, `1000BASE-SX` | both ends | each end in VLAN 4000 | 4000 / 4000 | none / none |

**No loop:** `no spanning-tree rstp enable` (mode rstp) on both units; `loop-protection loop-detect ldf-interval 1
fast-block` on both. The IE520-sa's only connected ports are C (VLAN 1), M (VLAN 106) and SX (VLAN 4000), each a single
link to the stack in its own VLAN, so no VLAN has two paths. The stack's VLAN 1 also reaches the x230 (sa2 =
port1.0.2; port1.0.9 reads `not present`, unchanged since 0954) and tb eth1, one path each. Side effect, expected:
tb470 eth1 now has the IE520-sa as an IPv6 neighbour (`fe80::86e3:27ff:fe87:780`, STALE) through link C.

Host NIC MACs (for the RUN's first working log): eth1 00:f0:4d:00:77:16, eth2 :17, eth3 :18. DUT clock vs box at 12:31:
stack `show clock` 23:33:15 UTC against box 23:31:44 UTC (**stack ~+91 s ahead**); IE520-sa 23:33:54 against 23:31:54
(**~+120 s ahead**). Exception logs: `None` on all three stack members and the IE520-sa.

### Predicted binding for the new script (f04ea359, 14 TestCases)

`_ck_discover` (l.99) walks the stack's declared links; `ck_media.classify` maps `BASE-T[A-Z0-9]*$` (1000BASE-T AND
10GBASE-TM) to twisted pair, and a twisted-pair port that `show system pluggable` lists is `cusfp`. No bound port is an
aggregator member, so no WARNING and no LAG-last reordering. Buckets, natural-sorted:
- tb = [port3.0.13 <-> eth1]
- cusfp = [**port1.0.6** <-> swi_b port1.0.14 (M), **port1.0.10** <-> swi_b port1.0.2 (C)]
- fibre = [**port4.0.26** <-> swi_b port1.0.26]
- copper = [] (no fixed RJ45 on the IE520)

`_ck_bind_link` order (init l.253-291): cusfp (optional) takes the FIRST cusfp = **port1.0.6 (link M, the monitored
copper-SFP port)**; fibre (optional) = **port4.0.26 <-> IE520-sa port1.0.26**; copper (required) finds `copper` empty and
takes the next `cusfp` = **port1.0.10 <-> IE520-sa port1.0.2 (link C, the copper test port; `peer` = swi_b)**. So
`cusfp_supported` and `fibre_supported` are True, `has_fibre_test_link` and `has_monitored_link` True: no TestCase is
excluded at init. Partner for all three roles is the IE520-sa (same build), not the x230 of the 0626 run.

### STANDING-ORDERS §6: the commands on the bound ports, checked with qmark

The script sends, on the DUT port AND its partner port of each bound link: configure() / tear_down() and
`configureDefaultPort` (library_9001 l.167): `interface <p>`, `no speed`, `duplex auto`, `polarity auto`, `no shutdown`;
in steps: `speed 10|100|1000|10000|<S>|auto|fast(invalid, expected refused)`, `duplex full|<forced>`, `shutdown`,
`copy running-config startup-config` (+ `y`). `qmark` (`tools/tb qmark ... --mode "configure terminal" "interface <p>" --
speed duplex polarity "no speed" "no shutdown" shutdown`) on stack port1.0.10, port1.0.6, port4.0.26 (u5) and IE520-sa
port1.0.2, port1.0.14, port1.0.26 (u3) gave **the identical help on all six ports** (self-test passed each time):
- `speed ?`: 10, 100, 1000, 10000, 100000, 200000, 2500, 25000, 40000, 400000, 5000, auto
- `duplex ?`: auto, full, half
- `polarity ?`: auto, mdi, mdix
- `no speed ?`, `no shutdown ?`, `shutdown ?`: `<cr>`

So no defaulting command is refused at the parser on any bound port. Caveat (platform row "The CLI is media-blind"):
offered is not accepted; a speed the module cannot run is refused only when it runs (SPTXc `speed 10` ->
`% Unsupported speed/duplex combination`; SX `speed 10000` refused). The script treats those as recorded answers, and
`configureDefaultPort` logs a refused line rather than failing, so they cannot fail every case at STEP 1. `no speed` /
`duplex auto` / `no shutdown` were accepted on this build on AT-SPTXa and AT-SPSX ports in the 0626 run; on an AT-SP10TM
(link M, monitored only) they have not been executed here (triage sends no config), but they are the ports' current
defaults.

### Expected result, reloads, PDU cycles, time (estimate, not measured)

- **Tally: 12 PASS / 2 UNSUPPORTED / 0 FAIL of 14 TestCases**, if the IE520-sa answers as a partner as the x230 did.
  The 2 UNSUPPORTED are TestCase_20 and TestCase_21 (speed 10), pre-marked by step 4 inside TestCase_1_to_7 when the
  AT-SPTXc refuses `speed 10`, and skipped with no PDU cycle (as in 0626 on AT-SPTXa). Less certain than 0626: the
  forced-mismatch / re-force cases (TestCase_25, TestCase_26_to_27) and the fibre sweep (TestCase_8_to_12, SX `speed 100`,
  review A1 "likely false PASS") now face an IE520 partner, never seen on hardware that way. TestCase_28 runs with
  `confCheck=False` (new).
- **Reloads: 1**: TestCase_31_to_33 reloads the whole stack near the end (~3 min). The IE520-sa is not reloaded by the
  script.
- **PDU cycles: 0 expected, worst plausible 2.** Each one cycles **only outlets 6, 5, 4 (stack) and 8 (IE520-sa)**, ~4-5
  min, because the run .setup declares no swi_e/swi_f. With 14 grouped TestCases a failing group costs one cycle, not one
  per step.
- **Time: ~60-70 min**: ~5 min pre-run checks (no setup config this time), ~45-55 min framework (0626: 56 min for 33
  TestCases; 19 fewer per-TestCase config saves on SPIFlash), ~10 min restore + probe.
- **Office hours (Tue ~12:35):** 1 stack reload + 0-2 four-unit cycles is not reboot-heavy, but it lands inside office
  hours (memory `reboot-heavy-runs-after-hours`). The Test Engineer chooses; the 0626 and 0954 campaigns asked the same.

### MANUAL-ONLY

T33235 is not listed in MANUAL-ONLY.md, and triage found no step in the new script that needs a person (its "pluggables
fitted and cabled" precondition is met by the bench). No row added.

### Count (STANDING-ORDERS §3)

- **N = 1 runnable:** T33235 on `tb470/IE520/port-2026-10-13T1223/tb470-u2u5.setup`, setup/restore recipe above.
- **M = 0 blocked by topology** (the 0954 block is cleared by the recable, proven by LLDP, link state, media and MAC
  learning on both ends).
- **K = 0 blocked otherwise.**
- For the Test Engineer, not blocking: recording links C and M in the deployed `tb470.setup` is `bench_probe.py apply`
  (theirs); the current deployed template lacks them, so a full u0-u5 probe will report them as EXTRA_IN_LIVE until then.
