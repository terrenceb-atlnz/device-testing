# Why the first snooping runs were wrong, and what fixed them

Recorded because it would mislead anyone reading the raw first-pass numbers.

**The observation path contains a second switch.** Traffic is injected on tb470
`eth2` into DUT `port2.0.2` and observed on tb470 `eth1`, which is reachable
only via DUT `port1.0.2` → **x230** → `eth1`. The x230 runs its own IGMP/MLD
snooping, enabled by default.

So the first pass measured:

| case | DUT snooping | measured | expected |
| --- | --- | --- | --- |
| 10300 / 38417 | **disabled** | 1/10 | 10/10 flood |

The DUT was flooding correctly; the **x230 was pruning it downstream**. The
result said nothing about the DUT.

**Fix:** disable IGMP/MLD snooping on the x230 for these four cases, so the
observation path cannot prune. Re-run gave 10/10 with DUT snooping disabled and
1/10→0/10 with it enabled — the discriminating result. x230 defaults restored
afterwards.

**Second correction:** `1/10` with snooping enabled is NOT a failure. Three
back-to-back bursts gave 1/10, 0/10, 0/10 — the first frame of a new group
floods while the snooping entry installs, then pruning is complete. Grading it
as "must be exactly 0" was my error, not the DUT's.

**General rule for this bench:** when a measurement runs through the x230, ask
whether the x230's own features affect the result. It is a switch in the path,
not a wire.
