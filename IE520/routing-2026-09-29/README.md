# Routing group — IE520 stack, tb470, 2026-09-29 campaign

Queue: [../CAMPAIGN-QUEUE-2026-09-29.md](../CAMPAIGN-QUEUE-2026-09-29.md) rows 12 and 14. These are
hand-driven cases on the stack master `/dev/u5`. The console wrappers are ckcon.py / qmark.py (copies in
[../vlan-2026-09-29/evidence/](../vlan-2026-09-29/evidence/)) and ckyn.py, which answers `(y/n)` prompts
(in [evidence/12589/](evidence/12589/)).

| case | title | log | verdict |
| --- | --- | --- | --- |
| T12589 | Interoperability with RIPv1/v2 (PBR) | [12589-fail.log](12589-fail.log) | **FAIL** (2026-10-01, full build, queue row 16): RIPv2 and RIPv1 between the stack, the IE520-sa (VLAN40 route) and the x230 (VLAN30 = PBR next hop); PBR = `mls qos enable` + hardware ACL 3001 class + `set ip next-hop`. Steps 1/3 correct (5,080/5,080 each way) while the next hop is ARP-resolved. Steps 2 (VLAN30 down) and 4 (next-hop 172.16.30.99 / 10.99.99.1): matched Pkts2 are NOT re-routed to VLAN40; the DUT routes them out the ingress port, untagged in vlan1, to an unrelated host MAC (tb470 eth1) (D-1). After VLAN30 up PBR stays broken until the next hop is ARPed by other means (D-2). Same under v1. Misrouted packets leaked through tb470 until Terrence added a FORWARD drop (still in place). Restored: IDENTICAL, stack+SA+x230 reloaded to clear ripd, probe MATCH. (Was PARTIAL 2026-09-30, probe only.) |
| T11346 | PIM-DM end-to-end | [11346.log](11346.log) | **PASS** (run 2026-09-30, written up 2026-10-01 from the evidence, no re-run): PIM-DM stack <-> IE520-sa, client stream 30,001/30,001 at 1000 pps and 2,438,001/2,438,001 at 984 Mbps line rate; no-PIM baseline 0; prune on leave / graft on join ×2; (S,G) in hardware on all 3 members. Restored 2026-10-01 (config removal + `reload` of stack and SA to clear pdmd), IDENTICAL, probe MATCH |
| T18948 | VRRP routes near wirespeed, multiple instances | [18948.log](18948.log) | **PASS** (2026-10-01): 4 VRRP instances (VRID 81–84, vlan3181–3184), stack Master / SA Backup, VMAC; hosts in all 4 VLANs → virtual MACs → routed: 1518 B line rate 984 Mbps 2,431,001/2,431,001 (607,750 per VLAN), 68 B 261 K pps (generator ceiling) 100 %; no-VRRP baseline 0; no VRRP transition, 1 advert/s/instance received through the load. Torn down, IDENTICAL; vrrpd lingers until the group-end reload |
| T10624 | OSPF silicon tables synced | [10624.log](10624.log) | **PASS** (2026-10-01): OSPF Full stack <-> SA; 500 routes (SA statics, `redistribute static`) = 500 in `show ip route` AND `show platform table ip` on members 1/3/4; fluctuations 500→0→500→400→500 tracked by RIB, FIB and silicon, traffic 0/100/80.0026/100 %; 95 % wirespeed (77,210 pps, 1514 B) 30 s 2,316,301/2,316,301 over all 500 prefixes; no-OSPF baseline 0. O-1: 0.01 % loss only at a 100 % offer. Torn down, IDENTICAL |

## 2026-09-30 run (queue row 14)
Run in one group session with T5082. The baseline, pre- and post-group captures are in
[../dhcpv6-2026-09-29/](../dhcpv6-2026-09-29/) (`pre-test-configs/2026-09-30/`, `post-test-configs/2026-09-30/`).
T12589 enabled QoS for the probe and removed it afterwards. Group close: u5/u3/u1/u0 running-config
IDENTICAL to the pre-group capture, and probe 2026-09-30T003900Z MATCH.

## 2026-10-01 run (queue row 16, T12589, sentinel device-testing-67)
Hand-driven; baseline = pre-test-configs/2026-10-01/, pre-case capture evidence/12589/12589-pre-*.out
(IDENTICAL). Scratch VLANs 3210/3230/3240/3289, native VLANs untouched. Close: running-config IDENTICAL
on u5/u3/u0/u1, `no service rip` = "% Save the config and restart", so the stack, SA and x230 were
`reload`ed (nothing written); ripd gone, boot tb470-bench.cfg, stack master member 3 (1/3/4 Ready),
probe 2026-09-30T204444Z MATCH. tb470 FORWARD `-s 192.168.10.0/24 -j DROP` (Terrence's) left in place.

## 2026-10-01 run (queue row 12, sentinel device-testing-67)
T11346 written up from the 09-30 evidence and restored (stack + SA `reload` to clear pdmd).
Pre-group capture for T18948/T10624: [pre-test-configs/2026-10-01/](pre-test-configs/2026-10-01/)
(IDENTICAL to 2026-09-30/ on u5/u3/u1/u0). The `no service vrrp|pdm|ospf` removals answer
"% Save the config and restart", so the group closes with one more reload of the stack and SA.

### Group close (2026-10-01 08:50-08:55)
After T10624's teardown, vrrpd (T18948) and ospfd (T10624) were still running ("% Save the config
and restart" on `no service vrrp|ospf`). The stack and SA were reloaded with `reload` (nothing
written; tools/ckreload.py), and were back at `login:` after 199 s / 188 s. Post-group capture
[post-test-configs/2026-10-01/](post-test-configs/2026-10-01/):
- running-config IDENTICAL to pre-test-configs/2026-10-01/ on u5/u3/u1/u0;
- no ospfd/vrrpd/pdmd;
- stack members 1/3/4 Ready, member 3 Active Master;
- boot `<platform>-tb470.rel` + `flash:/tb470-bench.cfg` (file exists) on all four;
- probe 2026-09-30T195444Z MATCH, Advisories none.
T12589 (its full PBR build) is queue row 16, run after this group (above).
