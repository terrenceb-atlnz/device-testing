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

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | coro-dlf (corosync flow-control repro) | tb470/IE520/corosync-dlf-2026-10-15T0755/ | QUEUED | runs: A = eth1 only (member 1 ingress); B = eth1 + eth3 at once (the report's method). Each: line rate, several minutes, terminal monitor on u5 and u4, sdma CPU counters before/after |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues
