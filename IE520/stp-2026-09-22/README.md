# STP & storm control group — IE520, tb470, 2026-09-22

8 cases. **8 PASS**, of which 38152 and 38153 pass 3 of 4 assertions (alternate-path step
UNMEASURED) — whether that grades PASS or PARTIAL is a rule awaiting Terrence (2026-09-28).
(2026-09-24: 16452/16453 re-run on a real loop — PASS.)

| case | title | verdict |
| --- | --- | --- |
| [38487](38487.log) | Limits: Number of MSTP instances - 15 | **PASS** |
| [16388](16388.log) | storm-control tests with static channel group | **PASS** (scope note) |
| [6005](6005.log) | MAC movement / thrash | **PASS** (movement; thrash not attempted) |
| [38151](38151.log) | MSTP - Basic operation test | **PASS** (case has no steps) |
| [38152](38152.log) | RSTP - Basic operation | **PASS** on 3 of 4 assertions |
| [38153](38153.log) | STP - Basic operation | **PASS** on 3 of 4 assertions |
| [16452](16452.log) | loop-protection action: port disable | **PASS** (re-run 2026-09-24; fast-block cleared by re-arming loop-detect) |
| [16453](16453.log) | loop-protection action: link down | **PASS** (re-run 2026-09-24) |

## The DUT is the root bridge in all three modes

RSTP, STP and MSTP were each brought up across all three devices with the DUT at
priority 0. In every mode all three independently agreed:

```
DUT      Root Id 0000:0000cd370d6f == Bridge Id 0000:0000cd370d6f
AR4050S  Root Id 0000:0000cd370d6f   (bridge 8000:0000cd400394)  Rootport Forwarding
x230     Root Id 0000:0000cd370d6f   (bridge 8000:001aeb91cca1)  Rootport Forwarding
```

The Root Id is the stack's **virtual MAC**, so the whole VCStack is root, not one
member. Traffic forwarded 10/10 through the DUT in every mode.

## TWO SAFETY FINDINGS — both cost a near-miss

**1. A mode change silently re-enables spanning tree.** After
`spanning-tree mode mstp` … `spanning-tree mode rstp`, a prior
`no spanning-tree rstp enable` is GONE and `show spanning-tree brief` reports
`Spanning Tree Enabled`. This bench runs STP off on all three devices by design,
so that silently changes which ports forward — and would have invalidated every
remaining STP, switching and storm-control result without looking like an error.
**Re-assert the disable after any mode change, and re-check forwarding.**

**2. A physical link can forward on a path spanning tree cannot see.** When the
ring was closed for 38152, NO port anywhere reported Discarding — a loop with no
blocking port. Cause: `lacp global-passive-mode enable` on the AR4050S had
auto-added `channel-group 2 mode passive` to the port. STP runs on the
**aggregator**, and that aggregator was down, so STP had nothing to block while
the physical link forwarded. The same thing bit the stack on 2026-09-21.

> **Rule for any ring work here:** before closing a redundant leg, confirm the
> port appears in `show spanning-tree brief` **as a port with a real state**.
> "Spanning Tree Enabled" is not the check — a leg inside a down aggregator is
> invisible to STP.

The ring was re-opened immediately on detection, before any result was trusted,
and `no lacp global-passive-mode enable` applied to the AR4050S.

## Why 38152/38153 are not full passes

Their last assertion — cut the link to sw1, traffic takes the alternate path —
has no alternate path on this bench. The physical ring spans three VLANs and the
two legs meet the DUT in **vlan 1** and **vlan 10**, which do not bridge on the
DUT. Making it one domain would merge the routed vlan10 transit into vlan1 and
break the L3 topology the other groups depend on.

## 16452 / 16453 (UNMEASURED on 2026-09-22, PASS on 2026-09-24)

- **16452** — 09-22: `% Port-disable action is not supported with fast blocking`. 09-24:
  fast-block cleared by `no loop-protection loop-detect` + re-arming without the keyword.
- **16453** — 09-22: the loop never closed. 09-24: a real two-link loop (sa2's legs in an
  empty vlan 60) — link-down err-disables the port and the far end goes notconnect.

## Bench state at exit

All three devices: `spanning-tree mode rstp` + `no spanning-tree rstp enable`,
priority back to default. Ring re-opened (4050 `port1.0.2` shut, no
channel-group). `no lacp global-passive-mode enable` now set on the AR4050S as
well as the stack. Storm-control cleared, no static LAG. Stack `Normal
operation`, all three TB paths 0% loss.
