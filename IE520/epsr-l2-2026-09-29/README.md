# EPSR/L2 group — IE520 stack, tb470, 2026-10-02 (queue row 6)

Queue: [../CAMPAIGN-QUEUE-2026-09-29.md](../CAMPAIGN-QUEUE-2026-09-29.md) row 6. T45788/T45789 are the
Test Engineer's to run by hand (not here). Tester: bench-runner subagent; sentinel: parent session
device-testing-67 (one-session `/test-mode`). Session facts: tb470, consoles u0–u5, PDU 10.36.150.14
(outlets per bench-setup/tb470.static), constraints None.

Bench for this group: the standing tb470 template (probe MATCH), with host NICs eth1 → stack port3.0.10
(AT-SPTXc 1000BASE-T) and eth3 → stack port3.0.9 (AT-SP10TM at 1000), both on member 3.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T24032 | 5706 L2 platform test | [24032-partial.log](24032-partial.log) | **PARTIAL** (2026-10-02). Framework run of the legacy suite `raw-data/test_scripts/5706_Platform_L2` (staged copy, TC120 sa4/sa5). TC10/20/30/40/50/80 PASS; TC60 FAIL is the console's 80-column wrap (the DUT did log add and age-out); TC70 FAIL is the suite deleting the bench VLAN 10 in tear_down (its own check passed). Stopped after TC80; TC90–190 not run. Unblock: remap VLAN 10 → unused VID in the staged copy (asked) |
| T12067 | Flow control operation with MDI | — | running |

Directories: `pre-test-configs/` and `post-test-configs/` (running-config + show boot per console),
`evidence/` (patch diff + md5, framework log copy, raw wrapped log lines).
