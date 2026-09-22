---
name: campaign-measurement-discipline
description: "Four rules that made the 72-case IE520 campaign trustworthy: baseline the feature OFF first, make traffic TRANSIT the DUT, split PROVEN from NOT MEASURABLE in every verdict, and ask what the x230 in the path does to the measurement."
metadata:
  node_type: memory
  type: feedback
---

From the full IE520 campaign, 2026-09-22. Each of these caught at least one result that
would otherwise have been reported wrongly.

## 1. Baseline with the feature OFF, first, every time

A drop only means something if the identical traffic demonstrably forwarded a minute
earlier. Every case in that campaign ran `baseline → apply → measure → teardown`, and the
baseline is quoted in the log next to the result (`base=10/10 acl=0/10`). Without it you
cannot separate "the feature blocked it" from "the path was dead".

## 2. Traffic must TRANSIT the DUT

Inject on one TB NIC, capture on another. A frame counted at egress has crossed the switch;
a link-up check or a device-local `ping` has not. The strongest probes are the ones designed
so a correct switch must NOT forward — e.g. learn the destination MAC on the INGRESS port,
then send to it and require 0 at the observation point.

## 3. Split PROVEN from NOT MEASURABLE inside the verdict

Never let a bench limit hide inside a PASS, and never grade a bench limit as a FAIL. Write
both halves explicitly:

> PROVEN: an ACL binds to a static-aggregator interface and filters traffic transiting it.
> UNMEASURED: consistent programming across stack members — `sa1` had ONE member, and a
> straddling LAG needs a recable.

And distinguish **bench limit** (more hardware fixes it) from **case-scope mismatch**
(hardware never will — e.g. "Run the 5706 automated test" against an IE520) from
**case-definition gap** (`num_steps = 0` in ck.db). They need different answers from
Terrence. Three cases in that campaign had no steps at all; say so rather than inventing a
procedure, and if you do interpret a title, state that you did.

## 4. Ask what else is in the measurement path

**The x230 is a switch, not a wire.** IGMP/MLD snooping cases first read `1/10` with DUT
snooping DISABLED — the DUT was flooding correctly and the **x230 was pruning it
downstream**. The number said nothing about the DUT. Same class of error: the mirror
destination that cannot transmit because nothing is cabled to it.

## Two grading mistakes worth not repeating

- **Don't invent a threshold the case does not state.** I graded "snooping enabled" as
  requiring exactly 0/10 and called `1/10` a FAIL. Three back-to-back bursts gave
  `1/10, 0/10, 0/10` — the first frame of a new group floods while the entry installs. The
  threshold was wrong, not the product. Likewise an "implicit deny" probe I graded FAIL
  against my own assumption rather than the case text.
- **Tear down the previous case before the next one on a shared session.** T3111 showed the
  DUT advertising nothing; the cause was T3112's outbound prefix-list, still bound to the
  same BGP neighbour, containing `deny ::/0 le 128`. Two cases sharing one live session,
  the earlier silently grading the later.

Deliverables: per-case `<case-id>.log` ([[log-is-the-deliverable]]) plus a per-group
`README.md` whose headline carries the PASS/UNMEASURED split and the reasons, so a reader
gets the true picture without opening every file.
