---
name: ie520-first-copper-port-is-x-0-2
description: "On the IE520-28GSX, portN.0.1 is an EMPTY SFP CAGE — the first copper port is portN.0.2, and each stack member has effectively only ONE usable copper port. 'uN port1' in bench talk means portN.0.2."
metadata:
  node_type: memory
  type: project
---

Measured on tb470, 2026-09-21, from `show interface status` across all four members.

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
