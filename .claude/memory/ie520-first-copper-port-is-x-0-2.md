---
name: ie520-first-copper-port-is-x-0-2
description: "On the IE520-28GSX, portN.0.1 is an EMPTY SFP CAGE — the first copper port is portN.0.2, so 'uN port1' in bench talk means portN.0.2. CORRECTED 2026-09-23: each member has THREE copper ports (.2/.9/.13), not one."
metadata:
  node_type: memory
  type: project
---

Measured on tb470, 2026-09-21; **CORRECTED 2026-09-23**; 2026-10-06 note below.

> ## 2026-10-06 — check the module before blaming a cable
> `show system pluggable` on the stack (2026-10-06) listed modules in `x.0.2` (AT-SPTXa
> 1000BASE-T on members 1 and 3, AT-SP10TM on 4), `3.0.10` (an old **AT-SPTX**, datecode 2008),
> `4.0.26` (AT-SPSX) and the stackports, and **nothing at `x.0.9` / `x.0.13`**. The Test Engineer
> plugged RJ45 straight into `3.0.13`, so `.9`/`.13` are probably FIXED copper ports (a fixed
> port is not a pluggable) — inferred, not checked against a datasheet. `x.0.2` and `3.0.10` take
> RJ45 only because copper SFPs are fitted, so they are a **bench fact** (`show system pluggable`).
> Observed: tb470 eth1 into the AT-SPTX at `3.0.10` never worked — `show platform port` read
> `hwMode QSGMII to 1000BASE-X`, `Fiber Auto Negotiation Enabled Incomplete`, partner none. The
> module first fitted linked at the switch but passed no frames; a swapped one did not link at
> all. Cause (old module vs port) inferred, not proven.

> ## CORRECTION — I got the port COUNT wrong
> The original version of this memory said each member has "effectively ONE usable copper
> port". **That is false.** Each IE520-28GSX member has **THREE**: `portN.0.2`,
> `portN.0.9`, `portN.0.13` (the `.13`s are 10GBASE-TM; `port4.0.9` is 10GBASE-T). The
> stack therefore has **12** copper ports, not 4. I only ever listed ports 1–4, saw
> `portN.0.1/3/4` read `not present`, and generalised.
>
> This error was load-bearing: it was cited across the 2026-09-22 campaign as the reason
> several cases were unrunnable. The real constraint was that the extra ports were
> **uncabled**, plus the host-NIC count — a much cheaper problem, and one Terrence fixed
> with three patch leads on 2026-09-23.

What IS true, and is the useful part:

The IE520-28GSX is an **SFP** switch. On each member:

```
portN.0.1   notconnect   not present     <-- EMPTY SFP CAGE, not a copper port
portN.0.2   connected    1000BASE-T      <-- the first usable COPPER port
portN.0.3   notconnect   not present
portN.0.4   notconnect   not present
```

**Two consequences that have each cost bench time:**

1. **`portN.0.1` cannot be cabled with RJ45.** A cable "plugged into port 1" gets no link and
   the port reads `notconnect` / `not present` forever. That is an empty cage, NOT a fault,
   NOT a dead port, and NOT a loop-protection block — check the Type column before
   diagnosing anything.

2. **Terrence's "uN port1" means AW+ `portN.0.2`.** He counts the first usable copper port.
   This is how an x230 got cabled into the middle of a LAG member on 2026-09-21: "u2 port1"
   landed on `port1.0.2`, which was already a `channel-group 1` member of the LAG to the
   AR4050S. **Always resolve a described port to its AW+ name with LLDP before acting on it**
   (`show lldp neighbors` on both ends), rather than trusting the number.

**Each member has effectively ONE usable copper port**, so the whole 4-member stack has four:
`port1.0.2`, `port2.0.2`, `port3.0.2`, `port4.0.2`. That is the real cabling budget — plan
topologies around it. As of 2026-09-21: `1.0.2` = AMF link to the x230, `2.0.2` = TB eth2,
`3.0.2` = free (TB eth1 moved off it), `4.0.2` = the single remaining LAG link to the 4050.

Related: [[setup-file-declares-topology]], [[tb470-topology-and-setup]].
