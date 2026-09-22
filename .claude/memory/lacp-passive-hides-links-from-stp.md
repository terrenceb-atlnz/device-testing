---
name: lacp-passive-hides-links-from-stp
description: "`lacp global-passive-mode enable` auto-enrols a freed port into a channel-group, and spanning tree then runs on the AGGREGATOR — so a live physical link can forward on a path STP cannot block. Seen on the stack AND the AR4050S."
metadata:
  node_type: memory
  type: project
---

Bit twice on tb470 within two days, on two different devices.

**2026-09-21, the stack.** A port freed from `po1` immediately reappeared as
`channel-group 2 mode passive`, and `switchport atmf-link` was then refused with
"Cannot configure atmf-link on aggregator member".

**2026-09-22, the AR4050S.** Closing the ring for the RSTP case produced **NO blocking port
anywhere** — a loop with nothing holding it. Cause:
```
4050# show running-config interface port1.0.2
 channel-group 2 mode passive        <- auto-added, never configured by hand
```
Spanning tree runs on the **aggregator**, and that aggregator was down, so STP had no port
it could block while the physical link forwarded.

## The rule this gives you

> **Before closing a redundant leg, confirm the port appears in
> `show spanning-tree brief` AS A PORT WITH A REAL STATE.**
> "Spanning Tree Enabled" is NOT the check. A leg inside a down aggregator is invisible to
> spanning tree, and that is the worst case — a loop with no blocking port, on a bench with
> RSTP disabled on all three devices.

Also check convergence rather than configuration: a root bridge elected and **agreed by all
nodes**, and after closure exactly one port actually Discarding.

## Fixes applied

`no lacp global-passive-mode enable` is now set on **both** the stack and the AR4050S, and
is deliberately left off — it fights explicit port configuration. If you find it back on,
that is a regression, not a default worth keeping.

Out-of-band recovery: the serial consoles stay usable during a storm, so a leg can always be
shut from `/dev/uN` without needing the network.

Related: [[stp-mode-change-reenables-spanning-tree]], [[tb470-bench-structural-limits]].
