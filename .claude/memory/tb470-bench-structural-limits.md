---
name: tb470-bench-structural-limits
description: "What the tb470 bench physically cannot test and why. CORRECTED 2026-09-23: the port limit was UNCABLED ports + host-NIC count, not one copper port per member; three patch leads on 09-23 removed much of it. Real remaining limits: ~26 Mbps offered load, no MRP partners, no TACACS+, no ixia."
metadata:
  node_type: memory
  type: project
---

Established across the full 72-case IE520 campaign on 2026-09-22. **Know these before
planning a suite — they decide in advance which cases can produce a verdict.**

## 1. ~~ONE usable copper port per IE520 member~~ — WRONG, corrected 2026-09-23

**Superseded.** Each member has THREE copper ports (`portN.0.2/.9/.13`) — 12 on the stack.
The real constraint was that they were **uncabled**, plus tb470 having only 3 test NICs.
On 2026-09-23 Terrence added three patch leads (a second 4050 link giving a LAG that
**straddles stack units 3 and 4**, a second stack↔x230 link, and both spare NICs moved
onto the stack), which unblocked much of what this section claimed was impossible.
See [[ie520-first-copper-port-is-x-0-2]] and bench-state.md "Current state — 2026-09-23".

### original text (kept so the campaign logs that cite it still make sense)

`portN.0.1/3/4…` are **empty SFP cages** (`show interface status` → `not present`); only
`portN.0.2` is copper. See [[ie520-first-copper-port-is-x-0-2]]. On the 4-member stack that
is four ports total, and as of 2026-09-22 they are all committed:

| port | use |
| --- | --- |
| `port1.0.2` | → x230 (the egress/observation path) |
| `port2.0.2` | → tb470 eth2 (the only injection point) |
| `port3.0.2` | **free but UNCABLED** |
| `port4.0.2` | → the LAG to the AR4050S |

**One injection point + one observation point.** That is what blocks: any "flood to ALL
ports" fan-out, any "traffic BETWEEN two supplicants", any multi-receiver multicast/PIM
topology, any mirror-destination capture (nothing is cabled to `port3.0.2`, so a mirror port
cannot transmit and its counters stay 0), and any **LAG straddling stack members** — the one
straddling pair that existed was broken when `port1.0.2` was recabled to the x230.

**ONE RECABLE is the highest-value bench change available** — a second cabled port, ideally
on a different stack member, unblocks roughly 14 cases across four groups.

## 2. No line rate — scapy peaks at ~26 Mbps

2.6% of a gigabit port. Anything whose assertion is a RATE claim cannot be discriminated:
strict-priority/WRR queueing (needs congestion), 802.3x flow control (needs a congested
port), "line rate is achieved", storm-control at the 10–95% levels (level 10 ≈ 100 Mbps),
guest-VLAN loss-vs-line-rate. Policing IS measurable behaviourally at a low CIR (2000 kbps
gets exceeded and drops are countable). ~9 cases need a real generator.

## 3. No MRP-capable ring partners

The three devices are cabled as a ring, but `show mrp` / config `mrp ?` are **unrecognised
on both the AR4050S and the x230**. Only the IE520 supports MRP. The whole MRP group (5
cases) is blocked on peers, not on the DUT. Note the AR4050S LISTS MRP as a licensed feature
while exposing no MRP CLI — a licence entry is not a capability.

## 4. No TACACS+ anywhere

No binary at any absolute path, nothing in dpkg, no TCP/49 listener. The DUT has the client
side. Verify absence three ways, not with `command -v` ([[ssh-path-has-no-sbin]]).

## What IS available and is easy to forget

- **FreeRADIUS runs on tb470 and the IE520 is ALREADY an authorised client** via an
  Ansible-managed `client 10.38.0.0/16 { secret = secret }` block, users `test_user/test_pass`
  and `user15`. No testbox writes needed.
- The DUT's **own local RADIUS server** (`radius-server local`) also works and touches
  nothing outside the device — the better choice under the write-boundary rule.
- **wpa_supplicant v2.10 with the wired driver** is present at `/usr/sbin/` for real 802.1X.
- The AR4050S and x230 can peer **BGP4+ and OSPFv3** with the stack over the vlan10 transit.
