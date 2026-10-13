# Campaign queue — tb470, IE520 stack (`stk_a`) as the DUT, 1 AWPTCM script case (Ask-CK validation), from 2026-10-13 14:55 NZDT

The ask, 2026-10-13 14:55 NZDT (`/test-mode --from-ask-ck`, Ask-CK's launcher):
*"/test-mode --from-ask-ck /home/terrenceb/.local/share/ck-agent/runs/2026-10-13T1454-val-43dd/2026-10-13T1454-val-43dd.json AWPTCM-T33234"*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-13 14:55 NZDT, word for word from the Ask-CK hand-off `2026-10-13T1454-val-43dd.json`
(schema 1, run_id `2026-10-13T1454-val-43dd`, kind `validation`, seat `10.33.22.17`, created 2026-10-13T14:54:46+13:00):
Test Engineer: terrenceb@terrenceb-dl
Driver: ask-ck (2026-10-13T1454-val-43dd)
Testbox: "tb470"
Consoles: "u2-u5"
PDU: {"ip": "10.36.150.14", "outlets": {}}
Constraints: "do not attempt to use the 4050 or x230 for this run; recabled: stack port1.0.10–IE520-sa port1.0.2 (link C, VLAN 1); stack port1.0.6–IE520-sa port1.0.14 (link M, both ends in VLAN 106 \"link-m\", saved in tb470-bench.cfg)"

Hand-off case entries:
- AWPTCM-T33234 — kind `script`, script_rel `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33234.py`
  (resolved: `claude/Test-cases/ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33234.py`, read-only;
  sha1 66c2316363f8…, last changed Test-cases d9a08dd 2026-09-29 — **the same script as the 2026-10-12T1456 validation**),
  case_payload_rel `ask-ck/functions/generator/refined-cases/Port/AWPTCM-T33234/zephyr_payload.json`.

Sentinel's reading of the facts (not a session fact):
- "u2-u5" on tb470 = u2 swi_a, u3 swi_b (IE520-sa), u4 swi_d, u5 swi_c — the IE520 stack and the IE520-sa.
  u0 (x230, swi_f) and u1 (AR4050S, swi_e) are outside the session and, per the constraint, not used.
- The hand-off gives no outlets, so a power cycle takes outlets from `bench-setup/tb470.static` (STANDING-ORDERS §1)
  **for the session's units only**: u2 swi_a 6, u3 swi_b 8, u4 swi_d 4, u5 swi_c 5. Outlets 1 (x230) and 7 (AR4050S)
  are never cycled by this run.
- The constraint is the one the 2026-10-13T1223 campaign ran under (same words); its run .setup
  `tb470/IE520/port-2026-10-13T1223/tb470-u2u5.setup` (stk_a + swi_b only) is the starting point for this run's .setup.
- `<FAMILY>` = IE520 (the script's DUT is the IE520 stack `stk_a`).

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  This is a `Driver: ask-ck` campaign: at completion the sentinel runs `/create-logs --auto` (manual
  cases only; T33234 is a script case, whose framework log is already final).
- `STANDING-ORDERS.md` applies, tightened by the constraint: **the x230 (u0) and the AR4050S (u1) are not used** —
  not opened, configured, declared in the run's `.setup`, or power-cycled. §6: the framework's post-failure power
  cycle is accepted only over outlets 4, 5, 6, 8.
- `/test-mode` §10 applies: nothing stops to wait. Every question becomes a `NOTIFY` line plus an
  entry in `## Issues`. §11 applies (`kind: validation`): repair loop on a COPY in
  `<group dir>/33234/work/`, `repairs.md`, ≤5 runs, then `review.md`.
- Ruling carried (memory `sfp-is-not-a-fixed-copper-port`, platforms/IE520.md row "MDI/MDI-X polarity is UNSUPPORTED"):
  the IE520 has no fixed RJ45 switchport, so T33234 is UNSUPPORTED on it; the copper-SFP links C and M do not change
  that, and no legacy copper-SFP polarity script is a substitute. The validation checks that the Ask-CK script itself
  reaches that verdict cleanly (its `has_fixed_copper_port` gate).
- Recorded history (not a verdict for this campaign): 2026-10-12T1456 validation of the same script (sha1 66c23163) on
  the full u0-u5 bench: clean run 1, 14/14 TestCases UNSUPPORTED, 0 power cycles, rc 0. Re-verify on the u2-u5 setup;
  do not inherit.
- Office hours (memory `reboot-heavy-runs-after-hours`): starts 14:55 on a weekday (Tuesday); expected 0 power cycles.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | port (script, validation): T33234 | tb470/IE520/port-2026-10-13T1455/ | RUN (dispatched 15:05) | Triage 15:00 (f29260f): 1 runnable / 0 topology / 0 otherwise; probe 015738Z vs run .setup exit 2 (1 read-only NEEDS-CHECK); expected 14/14 UNSUPPORTED, 0 reloads, 0 PDU cycles, ~15-20 min. kind `script`, script_rel `ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33234.py` (sha1 66c23163) |

## Setup and restore recipe — group 1

Written by bench-runner at TRIAGE, 2026-10-13 ~15:00 NZDT, so the RUN tester (or anyone after it dies) starts from it; the
RUN tester re-reads it and commits any correction before the case. Setup ONCE before the TestSet, restore ONCE after it
(STANDING-ORDERS §6). Scratch on tb470: `/tmp/<run scratch>/` (triage used `tri1455`). **Consoles u2-u5 only; u0 (x230)
and u1 (AR4050S) are never opened; outlets 1 and 7 are never cycled.** Pre-run reference capture:
`bench-setup/captures/2026-10-13T015738Z/` (u2 = stack, u3 = IE520-sa; gitignored, on the NFS share). Its u2/u3
running-configs are IDENTICAL to the 1223 campaign's pre-run reference `2026-10-12T232732Z` (header lines ignored), so the
1223 restore left the bench exactly at baseline.

**Run .setup:** `tb470/IE520/port-2026-10-13T1455/tb470-u2u5.setup` (on the box:
`/home/terrenceb/claude/device-testing/tb470/IE520/port-2026-10-13T1455/tb470-u2u5.setup`): a copy of the 1223 run .setup,
body unchanged, a 4-line header added. Declares stk_a (swi_a u2, swi_c u5, swi_d u4) and swi_b (u3, IE520-sa), outlets
6/8/5/4, links tb-swi_c eth1-port3.0.13, swi_a-swi_b port1.0.10-port1.0.2 (C) + port1.0.6-port1.0.14 (M), swi_b-swi_d
port1.0.26-port4.0.26 (SX). The deployed `/home/st-art/st-art/configs/tb470.setup` is NOT used and NOT edited.

**Setup (nothing to configure):** T33234's `init()` reads `has_fixed_copper_port` from discovery; the IE520 has no fixed
RJ45 port, so with this .setup discovery gives `tb=port3.0.13; cusfp=port1.0.6,port1.0.10; fibre=port4.0.26; copper=[]`
(exactly what the 1223 T33235 run printed on the same .setup at 12:41:01), nothing is bound, `configure()`/`tear_down()`
return at once, and the framework marks all 14 TestCases UNSUPPORTED. Before launch only:
1. `tools/tb precheck tb470 u2-u5` CLEAR `&&` `tools/tb scratch tb470 <run>`; `peek` u2-u5 at 115200 -> `IE520-stk#` x3,
   `IE520-sa#` (triage 14:57: exactly that).
2. Save `33234/stk_a.cfg` (u5 `show running-config`) and `33234/swi_b.cfg` (u3) with the three `!` header lines, and
   `show boot` on u5/u3 (baseline `flash:/tb470-bench.cfg`).
3. Launch from a COPY in `port-2026-10-13T1455/33234/work/` (script 66c23163 byte copy, `library_9001.py`, `ck_media.py` =
   Test-cases `ask-ck/tools/pt_media.py`): `tools/tb fwprep tb470 33234/run<N> <files>` then
   `tools/tb fw tb470 33234/run<N> test-9001.33234.py <run .setup above>` (`--noupdate --nodefaultcfg` by the wrapper;
   no `--include-test-cases`). The framework then, on stk_a and swi_b only: `no shutdown` on each declared port (all are
   already up), `no boot config-file`, `delete force` / `copy run <dev>_9001_33234.cfg`, `boot config-file
   <dev>_9001_33234.cfg`, then the marking pass. No reload, no PDU cycle expected (10-12: 0).

**Restore (anyone can run it, even if the tester died mid-run):**
1. `tools/tb ps tb470 'test-9001.33234'` -> nothing running (else `tools/tb waitfor tb470 <workdir>/run.exit <s>`; never
   kill mid PDU cycle).
2. `tools/tb precheck tb470 u2-u5` CLEAR `&&` `tools/tb scratch tb470 <run>`; `peek` u5 and u3 -> `IE520-stk#` / `IE520-sa#`
   (a PDU cycle may leave `login:`; ckcon/ckyn log in).
3. Stack, `tools/tb ckyn tb470 <run> u5 115200 ...`: `show boot`, `configure terminal`, `boot config-file
   flash:/tb470-bench.cfg`, `end`, `dir`; `delete force <f>` for EVERY `stk_a_9001_33234*.cfg` and `TestCase_tear_down.cfg`
   that `dir` lists; then `dir IE520-stk-1/flash:/` and `dir IE520-stk-4/flash:/` and `delete force
   IE520-stk-<1|4>/flash:/<f>` for each such file there (a delete on the master, currently member 3, does not remove the
   backups' copies); `show boot`.
4. IE520-sa, `tools/tb ckyn tb470 <run> u3 115200 ...`: `show boot`, `configure terminal`, `boot config-file
   flash:/tb470-bench.cfg`, `end`, `dir`, `delete force` every `swi_b_9001_33234*.cfg` and `TestCase_tear_down.cfg`
   listed, `show boot`.
5. Every `show boot` -> `Current boot config: flash:/tb470-bench.cfg (file exists)`.
6. `tools/tb probe tb470 --consoles u2-u5 --no-prompt --read-only --baud 115200 --pdu 10.36.150.14 --outlet u2=6
   --outlet u3=8 --outlet u4=4 --outlet u5=5 --out /tmp/<run>/bench-state.md --template
   /home/terrenceb/claude/device-testing/tb470/IE520/port-2026-10-13T1455/tb470-u2u5.setup` -> exit 2 with exactly ONE
   NEEDS-CHECK (`tb-swi_c eth1`, a `--read-only` artefact) and no MISMATCH, as at triage 14:57. **Never write
   `bench-setup/bench-state.md` from a u2-u5 probe** (it would drop u0/u1): always `--out /tmp/...`.
7. Running-config diff of the new capture's `u2.show_running-config.txt` / `u3.show_running-config.txt` against
   `bench-setup/captures/2026-10-13T015738Z/` (CR stripped, `!`/header lines ignored) -> IDENTICAL; on u5
   `remote-diff all show running-config` -> no member differs (memory `stack-refused-command-lands-on-backups`).
8. Every console left at exec (`end`, `terminal no monitor`); tb470 is the Test Engineer's own box, so no `exit`.

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

- **I-0 (campaign) precheck CLEAR, 2026-10-13 14:55.** `tools/tb precheck tb470 u2-u5`: u2-u5 free, no holder, lock
  file, screen/tmux/minicom-type session or python script on the box; only the Test Engineer's own ssh logins.
- **I-1 (campaign) sentinel armed 14:58** on this session (Monitor, normal mode, UPDATES → the hand-off's
  sentinel_updates file; cron backstop every 15 min). Assumed: stand-down `2026-10-13 18:00` (a short case, expected
  ~45 min; the campaign ends sooner on `ASKCK-DONE`).

## Triage 2026-10-13T1455

Tester: bench-runner, TRIAGE dispatch, ~14:56-15:00 NZDT (Tue, office hours). Read-only apart from the probe: bare-CR
peeks and the probe's own `show` reads. No case run, no configuration sent, no reload, no PDU cycle, no qmark. u0/u1 never
opened. `bench-setup/bench-state.md` NOT touched (probe wrote `--out /tmp/tri1455/...`).

| gate | result |
| --- | --- |
| 1 occupancy | `tools/tb precheck tb470 u2-u5` -> **CLEAR** (exit 0; u2-u5 free; only the Test Engineer's own ssh logins), `&&` into scratch `tri1455`; CLEAR again `&&`-gated before the probe |
| 2 consoles | peek: u2 `IE520-stk#`, u3 `IE520-sa#`, u4 `IE520-stk#`, u5 `IE520-stk#`. No shell, no config mode |
| 3 template | `/nfsHome` mounted (nfs4 10.36.250.11:/home); `/home/st-art/st-art/configs/tb470.setup` present (Oct 13 12:21), not used by this run |
| 4 probe | `tools/tb probe tb470 --consoles u2-u5 --no-prompt --read-only --baud 115200 --pdu 10.36.150.14 --outlet u2=6 --outlet u3=8 --outlet u4=4 --outlet u5=5 --out /tmp/tri1455/bench-state-vs-run.md --template .../port-2026-10-13T1455/tb470-u2u5.setup` -> **exit 2**, capture `bench-setup/captures/2026-10-13T015738Z` (10.4 s): **no MISMATCH, no USER-CONFLICT**; ONE NEEDS-CHECK `tb-swi_c eth1` (NIC MAC not learned = `--read-only`, as at 1223; stack port3.0.13 reads `connected 1 a-full a-1000 1000BASE-T`). Banners u2 `IE520-stk-1`, u3 `IE520-sa`, u4 `IE520-stk-4`, u5 `IE520-stk` |
| 5 setup | run .setup = byte copy of the 1223 run .setup (body), `tb470/IE520/port-2026-10-13T1455/tb470-u2u5.setup` |
| 6 preflight | `pt_preflight.py --setup <run .setup> --script test-9001.33234.py` -> **RUNNABLE (2/2)**: swi_a OK (member of stk_a), tb OK; role `copper` "can take" port1.0.10-port1.0.2 per the file, but preflight is media-blind: at run time the DUT reports that port as a cage (AT-SPTXc), so copper stays empty and the UNSUPPORTED gate fires |
| 7 boot configs | stack and IE520-sa `Current boot config: flash:/tb470-bench.cfg (file exists)`; software `IE520-awplus_main-20261008-57.rel`, bootloader 9.2.0. Stack 1 Backup / 3 Active Master / 4 Backup, Normal operation; uptime stack 01:41 (the 1223 run's TC31-33 reload), IE520-sa 22:58. Running-configs IDENTICAL to the 1223 pre-run reference `2026-10-12T232732Z` |
| 8 server path | retired; launch with `tools/tb fwprep` / `tools/tb fw` |
| 9 sentinel | `sentinel: parent` |
| 10 CLI | with no fixed copper port the script's `configure()`/`tear_down()` return before any command (l.387, l.414) and no TestCase body runs, so the script sends nothing to the DUT. The framework's own bring-up/save commands (`no shutdown` on declared ports, `no boot config-file`, `copy run`, `boot config-file`) ran clean on these same ports and devices in the 1223 run. No refused command possible at STEP 1 |

Links on the capture: stack port1.0.6 `connected 106 10GBASE-TM`, port1.0.10 `connected 1 1000BASE-T`, port4.0.26 `connected
4000 1000BASE-SX`, port3.0.13 `connected 1 1000BASE-T`; IE520-sa port1.0.2 `connected 1 1000BASE-T`, port1.0.14 `connected
106 10GBASE-TM`, port1.0.26 `connected 4000 1000BASE-SX`.

**Predicted binding (66c23163, 14 TestCases):** discovery `tb=port3.0.13<->tb.eth1; cusfp=port1.0.6<->swi_b.port1.0.14,
port1.0.10<->swi_b.port1.0.2; fibre=port4.0.26<->swi_b.port1.0.26` (same .setup, same discovery frame as the 1223 run,
which printed exactly this); `copper=[]` -> `has_fixed_copper_port=False` -> "UNSUPPORTED: no copper switchport on DUT"
-> only the optional `tb` role binds (port3.0.13 <-> eth1).

**Expected result (estimate, not measured):**
- **Tally: 0 PASS / 14 UNSUPPORTED / 0 FAIL of 14 TestCases**, rc 0: the framework's marking pass, "marked as unsupported
  ... without property has_fixed_copper_port, for device swi_a", as on 10-12. Case verdict UNSUPPORTED (ruling: memory
  `sfp-is-not-a-fixed-copper-port`, platforms/IE520.md). Links C and M are copper SFPs and do not change it.
- **Reloads: 0. PDU cycles: 0** (10-12: 0; skipIfExcl marks before the body runs, so no post-failure cycle). Worst
  plausible: an ERROR in init/discovery would cost one cycle of outlets 6, 5, 4, 8 only (~4-5 min); nothing else is declared.
- **Time: ~15-20 min**: ~5 min pre-run (peek, .cfg saves), ~2-3 min framework (10-12: 2 min 50 s with four devices'
  SPIFlash config saves; two devices here), ~8-10 min restore + probe + drift diff. Office hours: no reboot, no cycle, so
  not reboot-heavy (memory `reboot-heavy-runs-after-hours`).

**MANUAL-ONLY:** T33234 was not listed. The script asks an operator to swap the straight-through cable for a crossover
and back (`yesNo` at l.753/788 TestCase_3, l.1228/1267 TestCase_7, l.1340 TestCase_8; 10-12 review (a)). On a
fixed-copper DUT that step needs a person, so a row was added to MANUAL-ONLY.md, dated. On this IE520 bench nothing
manual arises: every TestCase is UNSUPPORTED before any prompt.

**Count (STANDING-ORDERS §3):** N = 1 runnable (T33234, expected UNSUPPORTED 14/14) / M = 0 blocked by topology (no
cabling change can help: the IE520-28GSX has no fixed RJ45 switchport) / K = 0 blocked otherwise.
