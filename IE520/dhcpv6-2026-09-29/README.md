# DHCPv6 group — IE520 stack, tb470, 2026-09-29 campaign

Queue: [../CAMPAIGN-QUEUE-2026-09-29.md](../CAMPAIGN-QUEUE-2026-09-29.md) rows 10 and 14. These are
hand-driven cases with no framework script. `ckcon.py` / `qmark.py` (console.py wrappers, copies in
[../vlan-2026-09-29/evidence/](../vlan-2026-09-29/evidence/)) drive the stack master `/dev/u5` and the
AR4050S `/dev/u1`, with scapy + tcpdump on tb470 eth1 (stack port3.0.13). Raw console transcripts are
in tb470 `/tmp/ck14/` (tmpfs).

| case | title | log | verdict |
| --- | --- | --- | --- |
| T5082 | DHCPv6 - EUI-64 and /64-/128 Advertised Prefix | [5082-fail.log](5082-fail.log) | **FAIL** (2026-09-30). Both illegal configurations were expected to be refused. Both were ACCEPTED, with no `% ` line: (1) `ipv6 address <pd-name> ::/65\|/96\|/128 eui64`, whereas the literal-prefix form of the same thing IS refused (`% Prefix length must not be more than 64`, `% Bad mask /128`); (2) `ipv6 nd prefix …/65, /96, /127, /128` (literal and PD-name forms), and the DUT then advertised all four in its RAs with L=1 A=1 (6 RAs captured on eth1). O-1 (not graded): no PD delegation reached the DUT (4050 ADVERTISE out 6, DUT ADVERTISE in 0) |
| T5093 | DHCPv6 Relay basic | — | **NOT TESTED** yet (queue row 10) |

## 2026-09-30 run (queue row 14, with T12589 in ../routing-2026-09-29)
Pre-group capture `pre-test-configs/2026-09-30/pre-u{0,1,3,5}.out` (13:19–13:20; IDENTICAL to the 12:50
baseline in ../vlan-2026-09-29/pre-test-configs/2026-09-30). Probe 2026-09-30T001909Z MATCH. T5082 built
a scratch SVI (vlan3995), moved port3.0.13 into it for one minute, and used the 4050's vlan10 as a
PD server. Everything was removed at the case's end. The stack and 4050 running-configs are IDENTICAL
to the pre-group capture.

## Group close (13:38–13:39, after T12589)
`post-test-configs/2026-09-30/final-u{0,1,3,5}.out`: `show running-config` is IDENTICAL to the pre-group
capture on u5, u3, u1 and u0. Current boot config is `flash:/tb470-bench.cfg (file exists)` on all four.
Stack members 1/3/4 Ready, member 3 Active Master, Normal operation. `bench_probe.py run` 2026-09-30T003900Z
MATCH. No console holders, no tcpdump/sender left running, and every console (u0–u5) is at an exec prompt.
