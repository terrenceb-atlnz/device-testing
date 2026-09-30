# DHCPv6 group — IE520 stack, tb470, 2026-09-29 campaign

Queue: [../CAMPAIGN-QUEUE-2026-09-29.md](../CAMPAIGN-QUEUE-2026-09-29.md) rows 10 and 14. These are
hand-driven cases with no framework script. `ckcon.py` / `qmark.py` (console.py wrappers, copies in
[../vlan-2026-09-29/evidence/](../vlan-2026-09-29/evidence/)) drive the stack master `/dev/u5` and the
AR4050S `/dev/u1`, with scapy + tcpdump on tb470 eth1 (stack port3.0.13). Raw console transcripts are
in tb470 `/tmp/ck14/` (tmpfs).

| case | title | log | verdict |
| --- | --- | --- | --- |
| T5082 | DHCPv6 - EUI-64 and /64-/128 Advertised Prefix | [5082-fail.log](5082-fail.log) | **FAIL** (2026-09-30). Both illegal configurations were expected to be refused. Both were ACCEPTED, with no `% ` line: (1) `ipv6 address <pd-name> ::/65\|/96\|/128 eui64`, whereas the literal-prefix form of the same thing IS refused (`% Prefix length must not be more than 64`, `% Bad mask /128`); (2) `ipv6 nd prefix …/65, /96, /127, /128` (literal and PD-name forms), and the DUT then advertised all four in its RAs with L=1 A=1 (6 RAs captured on eth1). O-1 (not graded): no PD delegation reached the DUT (4050 ADVERTISE out 6, DUT ADVERTISE in 0) |
| T5093 | DHCPv6 Relay - Basic functionality | [5093.log](5093.log) | **PASS** (2026-09-30). The IE520 stack relays DHCPv6 from the client VLAN (vlan3993, tb470 eth1 scapy client) to the AR4050S server on vlan10. With no relay: no response. With `ip dhcp-relay server-address 2001:db8:5093:10::2 vlan10`: leased 2001:db8:5093:1::1cb, and `show counter dhcp-relay` counted DHCPv6 5/5/5/5. Relay removed after saving: no response again. After a whole-stack reload: relay back from the saved config, and an existing and a new client both leased. O-1 of T5082 narrowed: the vlan10 relay path delivers every server reply |

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

## 2026-09-30 run 2 (queue row 10: T5093)
Pre-group capture `pre-test-configs/2026-09-30b/pre-u{0,1,3,5}.out` (17:06). It is IDENTICAL to the
row-7 baseline in ../vlan-2026-09-29/pre-test-configs/2026-09-30b. Probe 2026-09-30T040553Z MATCH.
T5093 built a scratch client VLAN 3993 (port3.0.13 in it), IPv6 on vlan10 at both ends, and a DHCPv6
pool on the 4050. It saved the config to `flash:/ck5093.cfg` with boot pointed at it for the reboot
step, so `tb470-bench.cfg` was never written. Helpers are in `evidence/5093/tools/` (dhc6.py =
the scapy DHCPv6 client).

## Group close (17:20–17:25, after T5093)
Boot pointer back on `flash:/tb470-bench.cfg`, and `ck5093.cfg` deleted from stack members 3, 1 and
4. `tb470-bench.cfg` is unchanged (2927 bytes, 03:07:49 UTC). `post-test-configs/2026-09-30b/final-u{0,1,3,5}.out`:
`show running-config` is IDENTICAL to the pre-group capture on u5, u3, u1 and u0. Current boot config
is `flash:/tb470-bench.cfg (file exists)` on all four. Stack members 1/3/4 Ready, member 3 Active Master
(re-elected after the step-5 whole-stack reload). `bench_probe.py run` 2026-09-30T042449Z MATCH.
There are no console holders and no client or tcpdump left running, and every console (u0–u5) is
at an exec prompt.
