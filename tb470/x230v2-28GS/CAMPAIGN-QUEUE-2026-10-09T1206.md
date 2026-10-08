# Campaign queue — tb470, x230v2-28GS as the DUT, 2 AWPTCM script cases, from 2026-10-09 12:06 NZDT

The ask, 2026-10-09 12:06 NZDT (`/test-mode --from-ask-ck`, Ask-CK's launcher):
*"/test-mode --from-ask-ck /tmp/claude-1971/-media-terrenceb-mnt-testbox-home-claude-Test-cases/79db4d44-3e69-4db9-99ee-14def1a54245/scratchpad/p0/p0-triage-2026-10-09.json AWPTCM-T33234 AWPTCM-T33235"*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-09 12:06 NZDT, word for word from the Ask-CK hand-off `p0-triage-2026-10-09.json`
(schema 0, run_id `p0-triage-2026-10-09`, kind `validation`, seat `terrenceb@terrenceb-dl`):
Test Engineer: terrenceb@terrenceb-dl
Driver: ask-ck (p0-triage-2026-10-09)
Testbox: "tb470"
Consoles: "u0-u5 all (u0 = DUT x230; stack, IE520-sa u3, AR4050S u1 available as partners)"
PDU: "10.36.150.14" (outlets: u0=1, u1=7, u2=6, u3=8, u4=4, u5=5)
Constraints: "Triage only: run no case and change no device state beyond what the probe itself does. Approved by Terrence 2026-10-09 for P0."

Hand-off case entries (both `kind: script`):
- AWPTCM-T33234 — `claude/Test-cases/ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33234.py`
- AWPTCM-T33235 — `claude/Test-cases/ask-ck/functions/pytest-creator/generated/9001_Port/test-9001.33235.py`

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  This is a `Driver: ask-ck` campaign: at completion the sentinel runs `/create-logs --auto` (manual
  cases only; both cases here are script cases, whose framework logs are already final).
- `STANDING-ORDERS.md` applies, **tightened by the constraint above: triage only.** No case runs and
  no device state changes beyond the probe's own reads.
- `/test-mode` §10 applies: nothing stops to wait. Every question becomes a `NOTIFY` line plus an
  entry in `## Issues`.
- Case texts: Ask-CK `ck.db` table `zephyr_cases` (read-only: `sqlite3 'file:<path>/ck.db?mode=ro'`).
  T33234 "Port - Auto MDI/MDI-X" (Draft); T33235 "(3) Port - Fixed port Speed" (Draft).
- Recorded history (not a verdict for this campaign): the 2026-10-09T0845 queue triaged T33234
  UNSUPPORTED on the x230 ("no fixed copper on the x230"); STANDING-ORDERS §6 records T33234's
  `no polarity` defaulting step failing every case on 2026-09-29.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | port (scripts): T33234, T33235 | tb470/x230v2-28GS/port-2026-10-09T1206/ | BLOCKED (sentinel 2026-10-09 ~12:35: session constraint triage-only, and 0 runnable) | triage only (session constraint). T33235 is BLOCKED on the DUT binding: the scripts take `swi_a` = IE520 stk_a (u2), not the x230 (u0 = swi_f). Remedy, the TE's call: rename swi_a<->swi_f in tb470.static + probe + apply, OR a Test-Composer pair with that swap. Once bound, it is runnable on the present cabling (copper x230 1.0.3, fibre 1.0.4, monitored 1.0.2), with 1 x230 reload, so ask office vs after hours. T33234 is UNSUPPORTED (platform): the x230v2-28GS has no fixed copper switchport, so all 14 TestCases are pre-marked UNSUPPORTED, nothing is sent and nothing cycles. No bench change unblocks it. See `## Triage 2026-10-09` |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| T33234 | Port - Auto MDI/MDI-X | port | NOT TESTED | Session constraint: triage only. Triage: UNSUPPORTED (platform) expected -- x230v2-28GS has no fixed copper switchport, all 14 TestCases pre-marked; also bound to swi_a = IE520 stk_a, not the x230 | -- | tester |
| T33235 | (3) Port - Fixed port Speed | port | NOT TESTED | Session constraint: triage only. Triage: BLOCKED on DUT binding (swi_a = IE520 stk_a u2; x230 = swi_f) -- TE: swap swi_a<->swi_f in tb470.static + probe + apply, or a Test-Composer pair; then runnable on present cabling, 1 x230 reload (office vs after hours) | -- | tester |

## Issues

- NOTIFY campaign -- DUT binding: both scripts bind `.setup` slot `swi_a`, which is the IE520 stack member on u2. The x230 is `swi_f` -- triage reported it as a remedy and ran nothing (sent to sentinel 2026-10-09 ~12:25).
- NOTIFY T33235 -- office or after hours (1 x230 reload; any FAIL means a 6-unit PDU cycle) -- left for the TE's go/no-go.
- NOTIFY campaign -- the P0 permission driver denied the read-only console checks on u0 (ckcon show system pluggable, show interface; qmark parser probe) and a `ps` on tb470 -- the x230v2 CLI check used the AW+ wiki and recorded runs instead. Consoles u0-u5 stay logged in from the probe; not logged out.

## Triage 2026-10-09

Tester: bench-runner, TRIAGE dispatch, ~12:10-12:30 NZDT. Read-only apart from the probe.

### Gate

| gate | result |
| --- | --- |
| 1 occupancy | `precheck --consoles u0-u5`: **CLEAR** (exit 0), run again `&&`-gated right before the probe |
| 2 consoles | the probe logged in on all six at exec (banners awplus, 4050-5g, IE520-stk-1, IE520-sa, IE520-stk-4, IE520-stk); none parked |
| 3 template | `/nfsHome` mounted; `/home/st-art/st-art/configs/tb470.setup` present (Oct 9 11:34) |
| 4 probe | `bench_probe.py --box tb470 run --consoles u0..u5 --no-prompt --pdu 10.36.150.14 --outlet u0=1,u1=7,u2=6,u3=8,u4=4,u5=5` -> **exit 0 MATCH**, capture `captures/2026-10-08T230820Z`. No USER-CONFLICT: the outlets agree with tb470.static. Advisory: eth1 is learned on swi_c port3.0.13 AND swi_f port1.0.2. That is vlan-1 flooding through stack sa2 to the x230, information only |
| 5 setup | `bench-setup/tb470.setup.current` equals the bench-state fence |
| 6 preflight | `pt_preflight.py`: both scripts RUNNABLE vs tb470.setup.current, **but it binds `swi_a /dev/u2 (member of stk_a)`**, so the DUT would be the IE520 stack, not the x230 (see below) |
| 7 boot configs | x230 (u0): **`flash:/default.cfg`** (hostname `awplus`), not the standing `tb470-bench.cfg`. That is the x230's baseline for this campaign; reported, not changed. 4050, IE520-sa, stack: `flash:/tb470-bench.cfg` |
| 8 server path | not checked (triage, no launch) |
| 9 sentinel | `sentinel: parent` |
| 10 CLI | see "Defaulting commands" |

### The blocker common to both scripts: the DUT binding

Both scripts take the DUT from `setup.init_all_devices()['swi_a']` and discover its partners from `[portlink]`.
On tb470 today `swi_a` = /dev/u2 (AT-IE520-28GSX, S/N 264A23061, stk_a member 1). The x230v2-28GS (u0,
S/N A10783G262900002) is `swi_f`, which makes it a partner. So with tb470.setup as it is, either script tests the
IE520 stack (T33235 already PASSED there on 2026-10-01, run 4), not the session's DUT.
**The exact change (the Test Engineer's call, either one):**
1. In `bench-setup/tb470.static`, swap the two names: A10783G262900002 -> `swi_a`, 264A23061 -> `swi_f`. Then
   `bench_probe.py --box tb470 run ...` and `bench_probe.py apply`. The stack becomes `stk_a = swi_f, swi_c, swi_d`,
   and outlets follow the serial. **or**
2. Test Composer pre-loads a topology pair (`templates/<setup>/`) equal to tb470.setup with swi_a<->swi_f swapped.
   Today `setup-a/` and `setup-b/` are empty files.
No recable is needed.

### Per script

**T33235 "(3) Port - Fixed port Speed" (33 TestCases): BLOCKED (binding), otherwise runnable.** With the
x230 as `swi_a`, discovery on the present cabling would bind as follows (media from the probe's `show interface status`):
- cusfp/monitored = x230 port1.0.2 (1000BASE-T SFP) <-> stack port1.0.2 (1000BASE-T). The stack side is in **static-channel-group 2**
  (with port1.0.9). That port is only defaulted (refusal logged) and watched; nothing forces its speed.
- fibre = x230 port1.0.4 (1000BASE-SX) <-> stack port1.0.3 (1000BASE-SX), no LAG.
- copper test port = x230 port1.0.3 (1000BASE-T copper SFP) <-> stack port1.0.17 (1000BASE-T), no LAG on either end.
- tb = eth3 <-> x230 port1.0.5 (optional).

Per TestCase: 1-7, 13-18, 22-27 and 31-33 are runnable. 8-12 (fibre sweep) are runnable, since `has_fibre_test_link` is true. 28-30
(monitored) are runnable, since `has_monitored_link` is true. Three are conditional, and each is pre-marked UNSUPPORTED before it runs,
with no power cycle (`mark_cases_unsupported`, Test-cases 056114d; this fixes the 10-01 D-1 power cycle):
- TestCase_20-21 need `speed 10` AND `speed 100` both accepted on the copper port. TestCase_3 marks them otherwise.
- TestCase_19 needs at least one swept speed rejected. TestCase_7 marks it otherwise.

On run 4 the copper SFP rejected `speed 10`, so expect 20-21 UNSUPPORTED. 14-19/22-24/26/27/29/31-33 depend on TestCase_13 finding a working fixed speed S (`SPEED_S_CASES`).
TestCase_33 does `copy running-config startup-config` and **reloads the x230** (`dut.reboot`, 900 s).
Disruption: 1 x230 reload, plus a six-unit PDU cycle after any FAILED case, so **ask office vs after hours**.
Restore after the run: the x230 boot config goes back to `flash:/default.cfg` (the framework boots its own `<hostname>.cfg`),
and that file is deleted.

**T33234 "Port - Auto MDI/MDI-X" (14 TestCases): UNSUPPORTED, platform; no bench change unblocks it.**
The script (Test-cases d9a08dd, the TE's ruling of 2026-09-29) needs a FIXED copper switchport on the DUT. The x230v2-28GS has
none: all 28 front ports are cages, ports 1.0.1-24 SFP and 1.0.25-28 SFP+. The probe shows 1.0.1/.2/.3/.5 as 1000BASE-T modules,
1.0.4 SX and the rest "not present". `show system pluggable` was not read live (denied). Every TestCase carries
`testCasePlatformWithPropertyIncl has_fixed_copper_port` + `skipIfExcl`, and TestSet.configure() returns before sending
anything, so a run would mark 14/14 UNSUPPORTED with no power cycle. It is safe and cheap to run once the binding is fixed, and
gives the same UNSUPPORTED result as the IE520 stack on 2026-09-29 (run 3). Re-verified, not inherited: the old `no polarity`
defaulting defect (STANDING-ORDERS §6) is gone. The library now sends `polarity auto` (b734b40), and on this DUT no
polarity command is sent at all.

### Defaulting commands (STANDING-ORDERS §6), against the x230 platform

All of them go through `library_9001.configureDefaultPort`: `no speed`, `duplex auto`, `polarity auto`, `no shutdown`. It logs a
refusal and never fails the case. TestSet.configure/tear_down add unchecked `no speed`/`duplex auto`/`no shutdown`. AW+ wiki
(x230): `speed {10..100000}` / `speed auto [...]`, `duplex {auto|full|half}`, `polarity {auto|mdi|mdix}`, all in Interface
Configuration mode. `no speed` is not on the wiki page, but it ran 47 times on IE520 and x230-10GP in T33235 run 4
(2026-10-01, PASS). **A parser refusal cannot fail every case at STEP 1.** It was not live-verified on the x230v2 (qmark was denied).
At launch, the first case's log should show `no speed` accepted on x230 port1.0.3.

### Count (STANDING-ORDERS §3)

- **N = 0 runnable now** (against the session's DUT).
- **M = 1 blocked by topology/binding:** T33235. The remedy is the swi_a<->swi_f rename, or a Test-Composer pair (above). After that,
  all 33 TestCases are runnable on the present cabling (20-21 conditional on speed 10/100 support).
- **K = 1 blocked otherwise:** T33234, UNSUPPORTED (no fixed copper switchport on the x230v2-28GS). It can be run to record the
  framework's 14/14 UNSUPPORTED once bound.
- After the probe the consoles are still logged in (not exited; the permission driver denied further console access). No device state was changed by me.
