# Campaign queue — tb470, AWPTCM Modbus (Proj 2166) on the IE520 stack and the x230v2-28GS, from 2026-10-08 11:31 NZDT

The ask, Test Engineer 2026-10-08 11:2x (`/test-mode`, with a Zephyr screenshot of six Not Executed cases):
*"Can you run these tests on the bench right now??"* — AWPTCM-T22653 (modbus - read port information),
T22654 (modbus - write), T22655 (modbus - dynamic changes), T22651 (S2166.1.10, S2166.1.11, S2166.1.12 -
modbus - read Sensor information), T22650 (… read System information), T22652 (… read alarm information).

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-08 11:31 NZDT (Test Engineer's answers to the setup questions):
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470 (not asked: the last test bench run and this host's default-boxes line; the Test Engineer could name another)
Consoles: "u0 + u2,u4,u5" (option text: "Both, e.g. run the cases on each product." — u0 = x230v2-28GS, u2/u4/u5 = IE520 stack)
PDU: "10.36.150.14 per tb470.static" (outlets by serial in bench-setup/tb470.static: x230v2 swi_f = 1; IE520 swi_a = 6, swi_c = 5, swi_d = 4)
Constraints: "Run now, no power cycles" (option text: "Same scope, and a failing case must not PDU-cycle in office hours: stop and ask instead." — "same scope" = 10-07's "do not interact with any other devices": only the listed consoles and their outlets)

**Updated 2026-10-08 12:0x–12:36 (Test Engineer):**
- *"the x230 is not on 9600 baud, its now the 115200 or whatever one, since we are not doing automated tests"*
- *"All devices have been mostly depopulated for ports, i need you to tell me what ports to connect"*;
  *"The DUT will be the IE520 stack … everything is available, i just need a topology choice from you."*
  → **DUT = the IE520 stack (u2 member 1, u4 member 4, u5 member 3, by serial in the 10-06 records). Only group 1 runs; group 2 (x230 as DUT) is dropped.**
- Topology chosen (sentinel, 2026-09-29 run's shape): **cable 1** tb470 eth1 ↔ stack port3.0.13 (RJ45, member 3 / u5);
  **cable 2** stack port1.0.2 (member 1 / u2, copper SFP) ↔ x230 port1.0.2 (passive link partner, nothing else cabled on the x230).
  Test Engineer 12:3x: *"the x230 link is to the u2 port1.0.1, as requested."* — the sentinel asked to move it to port1.0.2
  (stack port1.0.1 = known dead cage, platforms/IE520.md); **not yet confirmed moved — the probe/LLDP decides.**
- x230 (u0, 115200) prepared by the sentinel at the Test Engineer's request, running-config only (no write):
  `no lacp global-passive-mode enable`, `lldp run`. Otherwise it keeps the autoburnin running-config (per-port VLANs 10–37, RSTP off).
  x230 port1.0.2 read `running` 12:33, `notconnect` 12:34 (during the stack baud work).
- 12:36: *"bauds are fixed, stack is rebooting. am off of minicoms. all yours"*
- 12:5x, ruling on the probe USER-CONFLICT (u2 login_failed, u4 silent): *"I can see all login prompts on u2 and u4, u5 says stack is ok with \"sh stack\" so im taking it as a win"* → conflict resolved, consoles fine. *"i gotta go setup for this demo, i will communicate with you in a peer session"*: the go/no-go for row 1 arrives as a peer-session message just after 13:00.

**Resumed 2026-10-08 13:08 NZDT by device-testing-8a (`/test-mode --resume`, this session = sentinel):**
- Told the expected T22650 FAIL (member 2 `Provisioned`), the Test Engineer said: *"member two is contactable, but lets start the campaign anyway"* → **the go for row 1.**
  Recorded verbatim; the tester measures member 2's state rather than assuming it absent.
- Recorded facts taken as standing: consoles u2,u4,u5 (stack), PDU 10.36.150.14 (u2=6, u4=4, u5=5), **no power cycles**. Sentinel stands down 17:30 unless told otherwise.
- The deployed tb470.setup is still stale (handover OPEN 1: cable 1 = eth1-port3.0.13, stack consoles 115200); no apply this session.

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  The final log is made ONLY by `/create-logs`, on the Test Engineer's request.
- `STANDING-ORDERS.md` applies, **tightened by the constraint above: no power cycles.** Nothing
  that can PDU-cycle a unit runs (no framework TestCase with `powerCycleOnFail`, no `reload` that
  needs a PDU rescue); if a case would need one, `NEEDS TEST ENGINEER:` and move on.
- The cases are **Draft** in Zephyr (folder `/Modbus/Proj 2166 Modbus Support`, label Platform-Test)
  with no framework script; the steps are register reads/writes over Modbus TCP checked against
  the CLI. A Modbus TCP client runs on tb470 (the bench cannot open TCP to office PCs).
- Run each case on each product: group 1 = the IE520 stack, group 2 = the x230v2-28GS.
- Known before triage: the AW+ CLI wiki documents `scada modbus tcp server` for x230 (and AR4050,
  x908Gen2, x930, x950); there are no IE520 pages, and IE520 logs show `modbusd` running.
  bench-state.md was generated 2026-10-06 06:13 and is stale (the IE520 stack is on `main-calanm`,
  bootloader 9.2.0, consoles 9600; u0 at 115200 since the 10-08 autoburnin).

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | AWPTCM-T22650, T22651, T22652, T22653, T22654, T22655 on the IE520 stack (u2,u4,u5) | tb470/IE520/modbus-2026-10-08T1131/ | **RUNNING from 13:16** (bench-runner; gates 13:10-13:15: precheck CLEAR; probe exit 4 again = u2/u4 login_failed (backup-console session drops right after a correct password), sent as NEEDS TE; cases need only u5 + eth1). T22650 FAIL (0x0049 124 vs 93); T22651 PASS; T22652 PASS. Next: T22653 | probe 12:42 exit 4 USER-CONFLICT = u2 login_failed + u4 silent (not a fact disagreement); u5 = member 3 master 115200; member 2 still Provisioned (T22650 0x0049 expected FAIL again); build main-calanm (Oct 6 19:44 UTC), bootloader 9.2.0 x3; master flash 176 KB free. Cable 1 eth1-port3.0.13 linked, ping v4 + link-local OK. Cable 2 port1.0.2-x230 port1.0.2 linked (LLDP), but port1.0.2 is in static-channel-group 2 (sa2) -> exception 4 on T22655 API write, as 09-29. N=6 runnable (need only u5 + eth1), M=0, K=6 gated on the Test Engineer ruling on u2/u4. NEEDS TE: u4 silent at 115200 since 12:42; may it be re-probed, or probe u2,u5 only? |
| 2 | AWPTCM-T22650, T22651, T22652, T22653, T22654, T22655 on the x230v2-28GS (u0) | tb470/x230v2-28GS/modbus-2026-10-08T1131/ | DROPPED 12:2x | Test Engineer: "The DUT will be the IE520 stack" |

## Group 1 (modbus) bench setup and restore recipe (written by the RUN tester 13:16, before the first case)

- **Bench setup for the group: none.** No cabling, aggregator, VLAN or boot change. The cases run on the stack master's
  console (u5 now; re-read `show stack` before driving: master = whichever member reads Active Master) and the Modbus/TCP
  client `tools/mb.py` on tb470 (eth1 10.38.215.1/27, fd32:b1f0:dff8:d701::1/64) -> stack vlan1 10.38.215.10 (port3.0.13).
  Tools are copied to tb470 `/tmp/modbus-1008/tools`; the console transcript is `/tmp/modbus-1008/console-u5.log`.
- **Baseline** = the stack running-config captured 13:12 by the gate probe:
  `bench-setup/captures/2026-10-08T001201Z/u5.show_running-config.txt` (184 lines; no `scada`, no `alarm` lines;
  vlan1 = 10.38.215.10/27 + .40, .66 secondaries, `ipv6 enable`, `ipv6 address dhcp`). Boot config `flash:/tb470-bench.cfg`.
  **Nothing is written to startup** (master flash 176 KB free).
- **Restore recipe (a fresh tester can run it from any point in the group)**, on the master console in `configure terminal`:
  `no scada modbus tcp server port` · `no scada modbus tcp server access` · `no scada modbus tcp server` ·
  `interface vlan1` / `no ipv6 address fd32:b1f0:dff8:d701::10/64` (only if present) ·
  `no alarm facility …` for any `alarm` line in `show running-config | include alarm` (or clear it over Modbus: write 0x0000 to its config word) ·
  `interface port1.0.1` / `no shutdown` and `interface port1.0.2` / `no shutdown` (only if a `shutdown` line was added) · `end`.
  Then `show running-config` and diff it against the baseline above: it must be IDENTICAL. Do not `write`.

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| AWPTCM-T22650 | modbus - read System information | 1 (IE520 stack) | FAIL | 9/10 items equal the CLI at their Mapping-Version-5 addresses; Number of Alarms 0x0049 = 124 vs CLI 93 (member 2 is Provisioned only: no MAC, its unit-2 block answers an exception, bitmap 0x000d, yet the count includes it) | [22650/work/run1.log](modbus-2026-10-08T1131/22650/work/run1.log) (13238ad) | tester |
| AWPTCM-T22651 | S2166.1.10, S2166.1.11, S2166.1.12 - modbus - read Sensor information | 1 (IE520 stack) | PASS | the sensor #1/#2 type, reading (big-endian float 48.0/42.0/44.0), units and status registers equal show system environment on members 1, 3 and 4, and sensors 3-5 agree too | [22651/work/run1.log](modbus-2026-10-08T1131/22651/work/run1.log) (473b0d9) | tester |

## Issues

- 2026-10-08 11:31: tmux session `test-mode` (device-testing-49, pid 1424189) from the 10-07 run is
  still alive, stuck since 01:28 on a pending tool call; its sentinel Monitor/cron may still tick.
  It dispatches nothing (its queue is DONE). Not touched.
- 2026-10-08 13:0x (relayed by device-testing-8a): that session (pid 1424189, tmux "test-mode") has exited — no process, no tmux
  server, no stray sentinel.sh. Nothing was killed.
- 2026-10-08 wrap: `bench_probe.py apply` NOT run — the only fence (capture 2026-10-07T234226Z, u5 only) would cut tb470.setup
  from 6 devices to 1. Decision with the Test Engineer (SESSION-HANDOVER-2026-10-08.md OPEN 1).
