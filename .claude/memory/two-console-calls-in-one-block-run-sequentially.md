---
name: two-console-calls-in-one-block-run-sequentially
description: "Two Bash/console tool calls issued in ONE tool block run one AFTER the other, never in parallel; a \"partner watcher beside a DUT change\" sees nothing. Use tools/tb speedrow (both ends, one process) or run_in_background FIRST."
metadata:
  node_type: memory
  type: feedback
  originSessionId: 4ba10cb2-03ea-492a-81c8-f254fbd32ffd
  modified: 2026-10-21T02:38:29.958Z
---

**Fact (measured 2026-10-21, tb470 T47208):** the tester issued the x230's whole speed matrix and a 4050 poll
(`@poll 120 a-full\s+a-100 …` then `… a-10 …`) as two console calls in one tool block, expecting them to run
side by side. They ran in sequence: the 4050 poll started only after the x230 call had finished, polled 4
minutes for states that had already passed, timed out twice, and the partner readings had to be taken in a
second pass (4 more calls). T47210 avoided it by starting the 4050 watcher with `run_in_background` BEFORE
the x230 call.

**Why:** the harness runs a block's tool calls in order and waits for each; only `run_in_background` detaches one.

**How to apply:**
- One link, two ends: `tools/tb speedrow <TB> <run> <dutU> <partnerU> <baud> --dut-port P --partner-port P
  [--lldp] [--tlv] [--flap N --flap-end dut|partner|both] ROW...` drives both consoles from ONE process with
  parallel polls (speed/duplex rows, link-up timing, LLDP, the MAC/PHY TLV decoded at the partner, flaps).
- Anything else: start the watcher call with `run_in_background` FIRST, then the DUT call; read the watcher's
  output file afterwards.
- The same holds for the health samples: `tools/tb health` is one call per sample (STANDING-ORDERS §8).

Related: [[campaigns-measured-for-token-waste]], [[bench-scripts-stop-on-cli-errors]].
