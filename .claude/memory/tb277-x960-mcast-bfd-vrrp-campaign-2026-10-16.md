---
name: tb277-x960-mcast-bfd-vrrp-campaign-2026-10-16
description: "10 AWPTCM cases on the x960-56YSQ unattended, 9 PASS + 1 UNSUPPORTED; the keepers are F-15 (BFD detects in ~1.4 s, RIP cannot be bound to it and black-holes for ~171.6 s) and F-17 (one firmware image disagrees with itself about its own VRRPv3 checksum; a mismatched pair splits into two masters)"
metadata:
  node_type: memory
  type: project
---

2026-10-16 on tb277, DUT **AT-x960-56YSQ S/N `A2WQS700B`**, build `sin_x96056-20261012-24`,
partners swi_b (AT-x960-28YSQ, Base licence) and swi_a (AT-x950 GEN2-52XSTQm). Ten cases run
**unattended** in four groups by `bench-runner` subagents under a sentinel: **9 PASS, 1
UNSUPPORTED, none BLOCKED**. Final logs `tb277/x960/{snmp,ipv4svc,mcast,bfd-vrrp}-2026-10-16T1406/`,
handover `tb277/x960/SESSION-HANDOVER-2026-10-19.md`.

T43870 SNMPv3 · T44181 Ping Polling · T44378 UDP Broadcast Helper · T44182 Directed Broadcast ·
T43863 PIM-SM · T43864 PIM-DM · T43865 PIM-SSM · T43866 multicast VRF-Lite · T47201 BFD with RIP ·
T47873 VRRP(v3).

**This bench CAN test real multicast routing with two routers.** The standing assumption that it
could not was wrong. swi_b licence-refuses both `service pim` and `service pdm`, but **swi_a** is
a full PIM partner, and the topology that works is: put the receiver's port in a VLAN the DUT has
no SVI for, trunk it to swi_a which owns the SVI, and read the transit VLAN with the DUT's own
`tcpdump`. Four multicast cases passed on it.

**The two findings worth a developer:**

- **F-15 — AW+ has no RIP↔BFD binding, and the measurement is the point.** BFD detected a silent
  neighbour failure in **~1.4 s** (RIPv2) / ~1.1 s (RIPv1) with `Diagnostics: control detection
  time expired`, while RIP kept the dead prefix in the FIB marked **`best` for ~171.6 s** and a
  counted leg read 0/5 against an in-leg instrument at 5/5. The absence was established by
  **enumeration with both daemons running** — five CLI probes, the RIP guide's 0 hits for "bfd"
  in 1045 lines, and `ip ospf bfd` accepted on the **same interface in the same minute**. That
  contrast is what makes it UNSUPPORTED rather than "BFD is broken".
- **F-17 — one firmware image disagrees with itself about the checksum of its own default
  VRRPv3 advertisement**, and the vendor ships `alternate-checksum-mode` to make the two agree.
  **Which mode is RFC 5798 §5.2.8-conformant was deliberately NOT claimed** — that rests on the
  validator being right, and it was not independently verified. Bounded by two controls:
  default↔default fine, alternate↔alternate fine, **only the MISMATCH splits the pair** into two
  masters sharing virtual MAC `00:00:5e:00:01:0a` (priority 100 displacing priority 150, ten ARP
  replies to five requests). The vendor's own two modes simulate a conformant and a
  non-conformant peer — so a bench with no third-party router **can** demonstrate the interop
  hazard, which the sentinel had wrongly called unmeasurable.

Also: **F-13** (`ip pim sparse-mode` does not enable router-side IGMP, and snooping shows the
membership anyway while nothing forwards; a snoop-only membership does **not** migrate when
`ip igmp` is later enabled — it must be re-sent) and **F-14** (the IGMPv2 any-source-join
rejection is bound to hardcoded 232/8 only, not to a configured `ip pim ssm range`; the wrongly
accepted membership is inert, so a spec gap not a forwarding hole). **F-9 from 10-15 was
answered negatively** — its stale-forwarding shape does not occur in the multicast path, so it
is specific to the unicast inter-VRF path.

**Method notes that generalise.** Half the cases had **no authored step text at all** (one had a
steps array holding a single completely empty step) — each log says so rather than implying the
steps were authored. Grading "v3" needed the **advertisement's own version field**, because AW+
has no VRRP `version` command; grading VRRP mastership needed the **dataplane** (a static route
back through the DUT makes a partner-mastered frame hairpin, so the virtual-MAC flow reads
ttl 63 → 62 → 63 across a failover) because both routers answer from the same virtual MAC and
nothing at L2/L3 tells them apart.

**Process, measured:** 126.0 M cache-read over 599 calls, **group overhead 9%** against the
10-15 campaign's 46% — the gain came from per-group dispatch and reading the prior campaign's
`REVIEW.md` first. Three lessons in the review files: an **idle gap longer than the prompt
cache's lifetime costs a full context re-write** (one call cost 327 k tokens after a 339 s gap);
**cache-read per call rises ~4.9×** from a group's start to its last case, so front-load all
reading and order the reading-heavy case first; and a group brief must be **readable alone**,
because ~115 kB of overhead went on slicing the campaign-wide queue to reconstruct what the
dispatch already said.

Related: [[awplus-service-gated-routing-daemons]] (O-24 proven both directions here),
[[tb277-x960-routing-arp-campaign-2026-10-15]], [[scapy-for-traffic-tests]],
[[campaigns-measured-for-token-waste]], [[ckdb-case-lookup-by-title]] (corrected by this run),
[[sentinel-session-keeps-long-runs-moving]].
