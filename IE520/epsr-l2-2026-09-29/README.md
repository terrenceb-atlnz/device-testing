# EPSR/L2 group — IE520 stack, tb470, 2026-10-02 (queue row 6)

Queue: [../CAMPAIGN-QUEUE-2026-09-29.md](../CAMPAIGN-QUEUE-2026-09-29.md) row 6. T45788/T45789 are the
Test Engineer's to run by hand (not here). Tester: bench-runner subagent; sentinel: parent session
device-testing-67 (one-session `/test-mode`). Session facts: tb470, consoles u0–u5, PDU 10.36.150.14
(outlets per bench-setup/tb470.static), constraints None.

Bench for this group: the standing tb470 template (probe MATCH), with host NICs eth1 → stack port3.0.10
(AT-SPTXc 1000BASE-T) and eth3 → stack port3.0.9 (AT-SP10TM at 1000), both on member 3.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T24032 | 5706 L2 platform test | [24032-fail.log](24032-fail.log) | **FAIL** (2026-10-02, 3 framework runs of the legacy suite, staged copy: TC120 sa4/sa5 + VLAN 10 → 3910). 12/19 PASS in the framework; 5 framework FAILs are the 80-column console wrap (TC60, 130–160 — the DUT's own log proves add/age-out and every thrash action + timeout); TC170 a check-timing race (vlan-disable acted by +15 s); **TC180 (loop-protection port-disable) unexplained: not blocked at +10 s, traffic still flowing at +15 s**. Bench confounds found and removed: suite VLAN 10 = bench VLAN, bench loop-protection baseline blocks ingress-filter disable |
| T12067 | Flow control operation with MDI | [12067-unsupported.log](12067-unsupported.log) | **UNSUPPORTED** (2026-10-02). `flowcontrol receive/send on` is refused on every port of both IE520s: "% Error setting flow control ...", log "exfx_port_flowControlSet: Configuring flow-control receive is not supported on this product". Feature-off baseline: wire rate (976 Mbps) delivered in full, and 195 PAUSE frames from IXIA2 were counted by the DUT (RX FlowCtrlFrms) and ignored. Steps 2–3 (polarity mdi/mdix) UNSUPPORTED on SFP cages. Observation O-1: the refused command was still applied to the BACKUP members (stack desync until a reboot) |

Directories: `pre-test-configs/` and `post-test-configs/` (running-config + show boot per console),
`evidence/` (patch diff + md5, framework log copy, raw wrapped log lines).
