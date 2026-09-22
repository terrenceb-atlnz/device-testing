---
name: stp-mode-change-reenables-spanning-tree
description: "Changing `spanning-tree mode` on AW+ SILENTLY RE-ENABLES spanning tree, discarding a prior `no spanning-tree <mode> enable`. On this bench STP is off by design, so that quietly changes which ports forward."
metadata:
  node_type: memory
  type: project
---

Measured on tb470, 2026-09-22, during the MSTP instance-limit case.

Before:
```
spanning-tree mode rstp
no spanning-tree rstp enable        <- STP deliberately DISABLED
```
After `spanning-tree mode mstp` … then `spanning-tree mode rstp`, the running config read
only `spanning-tree mode rstp`, and `show spanning-tree brief` reported
**`Spanning Tree Enabled`**. The disable was gone.

**Why it matters here specifically:** tb470 runs RSTP off on all three devices by design —
the x230/4050/stack triangle is held open by an administratively-down link, not by a
spanning tree. STP silently coming back changes which ports forward, and would have
invalidated every subsequent STP, switching and storm-control result **without looking like
an error**. It was caught only by diffing the config during teardown.

**How to apply**
- After ANY `spanning-tree mode` change, re-read BOTH
  `show running-config | include spanning-tree` AND `show spanning-tree brief`, re-assert
  `no spanning-tree <mode> enable`, and re-check forwarding (the three TB paths).
- Order matters on restore: set the **mode first**, then the **disable**. Doing it the other
  way round loses the disable again.

Related: [[lacp-passive-hides-links-from-stp]] — the other way a spanning-tree assumption
turned out to be wrong on this bench the same day.
