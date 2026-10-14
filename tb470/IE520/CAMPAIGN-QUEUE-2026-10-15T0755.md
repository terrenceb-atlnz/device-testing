# Campaign queue — tb470, IE520 2-member stack, corosync flow-control reproduction (office hours), from 2026-10-15 07:55 NZDT

The ask, Test Engineer 2026-10-15: reproduce the reported defect on the rebuilt stack. The report
(screenshot shared in session):
*"with term mon enabled and DLF traffic going across the stack link the following logs can be seen:"*
```
20:53:19 IE520 corosync[1927]:   [IPC   ] coroipcs.c:383 Enabling flow control for 705
20:53:19 IE520 corosync[1927]:   [IPC   ] coroipcs.c:373 Disabling flow control for 705
... (pairs every ~3-30 s, 20:53:19 - 20:55:26)
```
Consequences: none observed. Reproduction method: 1. connect an Ixia port to each stack member;
2. use Ixia to send DLF traffic into both stack members. The reporter's config was supplied and is
loaded (adapted, below) as the stack's boot config `flash:/coro-repro.cfg`.

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-15 07:55 NZDT (Test Engineer's answers, this session):
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u4,u5 (the IE520 stack: u5 = S/N 264A23066 member 1, u4 = S/N 264A23052 member 2)
PDU: 10.36.150.14, u4=4, u5=5 (tb470.static)
Constraints: "Now" (office hours; ~1 Gb/s of DLF per NIC accepted; no reloads beyond the one config reload already done)
Topology: "Adapted load" of the reporter's config; "I'll recable now": tb470 eth3 (was x230 port1.0.5) -> stack port2.0.13 (member 2)

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, final output: `logged-output.md`. Final logs only by `/create-logs`.
- STANDING-ORDERS.md. This session is the sentinel (`/test-mode` shape A); the tester is a `bench-runner` subagent.
- Consoles u4/u5 only. u0-u3 are not this campaign's. Nothing is written (`write`) by the tester.
- Drive consoles with `tools/` drivers on `/dev/u4`, `/dev/u5`, transcripts at the box's `/tmp/coro1015/console-uN.log`.
  `terminal monitor` ON for the observation window (the report's condition); `console.py`-based drivers only
  (the framework driver times out under terminal monitor, orient-dt §3).

## Bench at queue creation (2026-10-15 07:59 NZDT, set up by this session at the Test Engineer's direction)

- Stack (built this session, commits `576a5f2`): member 1 = u5, member 2 = u4, both `tomahawk_ie520-20260825-42`,
  bootloaders 9.2.0 forced to `flash:IE520-tb470.rel`; stack links port1.0.27<->2.0.28, port1.0.28<->2.0.27.
- Boot config `flash:/coro-repro.cfg` = the reporter's config with these adaptations (Test Engineer: "Adapted load"):
  our `username manager` line kept (theirs has an unknown password); `line con 0` `exec-timeout 0 0` kept;
  port1.0.13 and port2.0.13 (the tb470 injection ports) in VLAN 100; `no service ospf` (this build prints the
  OSPF line either way; theirs shows none). Everything else is theirs: hostname IE520, chassis-id 2662,
  `stack 2 priority 1`, alarm facility lines, no ssh, no LLDP, VLANs 100/200/1000, sa1 = port1.0.1+2.0.1 (empty SFP
  cages here), sa2 = port1.0.2+2.0.2 (VLAN 100, cabled to the AR4050S, u1), port1.0.9/1.0.24/2.0.9 VLAN 1000,
  vlan1000 10.38.29.15/27.
- Restore afterwards: `boot config-file flash:/tb470-bench.cfg` + stack reload (that file is untouched, IDs 1/2).
- Injection: tb470 eth1 -> port1.0.13 (member 1); tb470 eth3 -> port2.0.13 (member 2, Test Engineer's recable, unverified
  at queue creation). DLF floods in VLAN 100 cross the stack link to the other member's sa2 leg and injection port.

## Group 1 bench setup and restore recipe (tester, 2026-10-15 08:10 NZDT; written before the first run)

- **Setup:** none by the tester. The stack already boots `flash:/coro-repro.cfg` (sentinel, at the Test
  Engineer's direction; see "Bench at queue creation"). The tester changes only session-scoped,
  running-only state: `terminal monitor` on the u4 and u5 console sessions. Traffic: `tools/linerate.py`
  from tb470 eth1 / eth3 (DLF dst 02:00:00:00:99:99), plus a few MAC-learning frames per NIC.
  No `write`, no reload, no boot/config-file change, no lldp change, no `bench_probe.py apply`.
- **Restore (a fresh tester can do this if the run dies):**
  1. `tools/tb ps tb470 'linerate|tcpreplay|tcpdump'` and `tools/tb killmine tb470 <pid>` for any of
     this run's senders/counters still alive.
  2. On u4 and u5: `tools/tb ckcon tb470 coro1015 u4 115200 "show clock"` (its login/exit path does
     `end` then `terminal no monitor` via console.py `monitor_off()`), then `exit` at the exec prompt.
  3. Check `show boot` still says `Current boot config: flash:/coro-repro.cfg` and `show running-config`
     equals `corosync-dlf-2026-10-15T0755/coro-dlf/stk_a.cfg` (less its 3 header lines).
  4. Going back to `flash:/tb470-bench.cfg` (+ stack reload) is the Test Engineer's decision, NOT the tester's.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | coro-dlf (corosync flow-control repro) | tb470/IE520/corosync-dlf-2026-10-15T0755/ | DONE 08:36 -- PASS (not reproduced); cleanup closed 09:13: u5 witness stopped 09:11:04, u5 terminal no monitor at exec, after-run read-only probe = same expected MISMATCH set, no USER-CONFLICT (eth1 FDB entry aged out -> NEEDS-CHECK). Still open, a tools defect: `tb killmine` refuses tb-launched console tools | runs: A = eth1 only (member 1 ingress); B = eth1 + eth3 at once (the report's method). Each: line rate, several minutes, terminal monitor on u5 and u4, sdma CPU counters before/after |

## Row 2 — coro-cpu: the CPU-bound variant (Test Engineer, 2026-10-15 09:2x: "run a version that reaches the CPU")

Why: in row 1 the ~48.6 M flooded frames never reached either CPU (sdma ~24 pps throughout). corosync is the
VCS cluster messaging and `coroipcs` flow control is its IPC back-pressure, so the reporter's trigger is most
likely CPU-bound traffic crossing the stack (ingress on the backup, handled on the master), not a hardware flood.
Hypothesis to test: frames the switch must punt to the CPU, entering on the BACKUP member.

Setup (running-only, restored after; no `write`, no reload): the reporter's `vlan1000` (10.38.29.15/27, ports
1.0.9/1.0.24/2.0.9, all down) is the only L3 interface. Move the injection ports into it so it comes up and
to-me traffic exists: `interface port1.0.13,port2.0.13` / `switchport access vlan 1000`. Restore = back to VLAN 100,
diff against the pre-run running-config.

Probe first (15 s each, --rate 50, sdma `rxDmaPcktCnt[*]` on BOTH members before/after, baseline ~24 pps; memory
`ie520-is-marvell-cpu-queues`: copy-to-cpu q0, send-to-cpu q6, background q7). Distinct --dport per variant:
- P1 unicast to-me: `--dst-mac 0000.cd37.0a66` (the stack MAC) `--dst-ip 10.38.29.15` — must reach the CPU;
- P2 subnet broadcast: `--dst-mac ff:ff:ff:ff:ff:ff --dst-ip 10.38.29.31`;
- P3 (control) broadcast in VLAN 100 as row 1 was, if cheap.
Keep the variants whose sdma delta is thousands per 15 s. CPU rate-limiting will cap the punted rate; that is the
point (sustained max CPU/IPC load), so offer line rate in the runs and record what `show cpu` and sdma show.

Runs (5 min each, terminal monitor ON on u4 AND u5 — ckcon window on one, witness_log on the other, as row 1;
`show cpu` + sdma from the u4 window every ~60 s; corosync/coroipcs/flow-control grep after each):
- R1 ingress on the BACKUP (member 1): eth1 -> port1.0.13 only, P1;
- R2 ingress on the MASTER (member 2): eth3 -> port2.0.13 only, P1;
- R3 both at once, P1; then R4 = R3 with P2 if P2 reached the CPU.
Verdict as row 1: FAIL = the lines appear (record first time, cadence, member); PASS = none, WITH sdma/`show cpu`
proof the CPU was loaded. Restore, then the read-only after-run probe to /tmp/coro1015/bench-state-after2.md.

## Queue (continued)

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 2 | coro-cpu (corosync flow-control repro, CPU-bound traffic) | tb470/IE520/corosync-dlf-2026-10-15T0755/ (case folder `coro-cpu/`) | QUEUED | plan in "Row 2" above; same consoles, same facts; the only config change is running-only (VLAN 1000 on the injection ports) and is restored |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| coro-dlf | corosync coroipcs "flow control" log lines under DLF across the stack link (defect repro) | corosync-dlf-2026-10-15T0755 | PASS (not reproduced) | No corosync/coroipcs flow-control line on terminal monitor (u4+u5, debugging) or buffered/permanent log through baseline, run A (eth1 DLF into member 1, 24.67M frames, 100% across the stack) and run B (eth1+eth3 into both members at once, 5 min, 100% / 99.99998% on the far NICs); CPU sdma unchanged (~24 pps/member): the flood never reached either CPU | corosync-dlf-2026-10-15T0755/coro-dlf/work/run1.log | tester |

## Issues

- **I-1 (2026-10-15 08:28) `tools/tb killmine` refuses tb-launched console tools.** `tb` starts them as
  `cd /tmp/<scratch>/tools && python3 <tool>.py`, so the command line carries no `/tmp/.../tools/` path and
  killmine's pattern never matches; the tester could not stop its own u5 `witness_log.py` (PID 1024901). A widened
  match was denied by the auto-mode classifier and reverted. NEEDS TEST ENGINEER: stop PID 1024901 by hand, and
  decide the killmine fix.
