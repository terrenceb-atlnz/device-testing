# Routing group — IE520 stack, tb470, 2026-09-29 campaign

Queue: [../CAMPAIGN-QUEUE-2026-09-29.md](../CAMPAIGN-QUEUE-2026-09-29.md) rows 12 and 14. These are
hand-driven cases on the stack master `/dev/u5`. The console wrappers are ckcon.py / qmark.py (copies in
[../vlan-2026-09-29/evidence/](../vlan-2026-09-29/evidence/)) and ckyn.py, which answers `(y/n)` prompts
(in [evidence/12589/](evidence/12589/)).

| case | title | log | verdict |
| --- | --- | --- | --- |
| T12589 | Interoperability with RIPv1/v2 (PBR) | [12589-partial.log](12589-partial.log) | **PARTIAL** (2026-09-30), probe only. PBR EXISTS: with `mls qos enable`, the policy-map class offers `set ip ?` → `next-hop  Set the Policy Based Routing nexthop`, and `set ip next-hop 10.10.10.2` was accepted. (`policy-based-routing` and `ip policy` are `% Unrecognized command`.) The full RIP + two-next-hop build waits for Terrence's scope decision (NEEDS TERRENCE sent 13:37) |
| T11346 | PIM-DM end-to-end | — | **NOT TESTED** yet (queue row 12) |
| T18948 | VRRP routes near wirespeed, multiple instances | — | **NOT TESTED** yet (queue row 12) |
| T10624 | OSPF silicon tables synced | — | **NOT TESTED** yet (queue row 12) |

## 2026-09-30 run (queue row 14)
Run in one group session with T5082. The baseline, pre- and post-group captures are in
[../dhcpv6-2026-09-29/](../dhcpv6-2026-09-29/) (`pre-test-configs/2026-09-30/`, `post-test-configs/2026-09-30/`).
T12589 enabled QoS for the probe and removed it afterwards. Group close: u5/u3/u1/u0 running-config
IDENTICAL to the pre-group capture, and probe 2026-09-30T003900Z MATCH.
