---
name: ie520-is-marvell-cpu-queues
description: "The IE520 is a MARVELL platform despite the \"tomahawk\" build name; copy-to-cpu lands on sdma rx queue 0, send-to-cpu on queue 6; one packet on the wire, never two"
metadata:
  node_type: memory
  type: project
  originSessionId: d78cedf4-6845-4b83-95bd-5439822917eb
  modified: 2026-09-28T23:05:20.733Z
---

The IE520's `show platform counter` dump is the Marvell format (`sdmaRegs.rxDmaPcktCnt[N]`,
`egrTxQConf…`, "Dump Counters for device number"), captured on the tb470 stack 2026-08-26
(`IE520/stack-tests/failover-300/evidence-cycle293/hafailover-platform_counters`). The
`tomahawk_ie520` build name is a codename, NOT the Broadcom Tomahawk ASIC, and I wrongly assumed
Broadcom (`packet[2]`) from it on 2026-09-29.

Per the ART 1336 ACL library (`check_SDMA_counters`, Marvell branch, CR30477): **copy-to-cpu →
`rxDmaPcktCnt[0]`; send-to-cpu → `rxDmaPcktCnt[6]`** (shared with EPSR etc.); the count is the
3rd whitespace column. Queue 7 carries most background CPU traffic. Not yet confirmed by a run on
this build — if queue 0 stays flat, find whichever `rxDmaPcktCnt[N]` moved by N.

**Why:** the queue decides whether a copy/send-to-cpu test reads PASS; the wrong one reads as
"nothing reached the CPU".

**How to apply:** `no system hw-monitoring`, `show platform counter sdma` before and after a
counted burst on the member owning the ingress port. copy-to-cpu must still forward exactly ONE
packet per packet sent (1336 grades `len == numPkts`; a `DUP!` = software re-forwarding = defect).
Only ONE rule may claim the flow — an interface `access-group` and a QoS `service-policy` on the
same port for the same flow cannot be attributed. Related: [[ie520-dos-test-method]],
[[campaign-measurement-discipline]].
