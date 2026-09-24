# QoS group — IE520, tb470, 2026-09-22

12 cases. **11 PASS / 1 UNMEASURED.** (2026-09-24: 13549 and 13553 re-run with tcpreplay line-rate congestion — PASS.)

| case | title | verdict |
| --- | --- | --- |
| [13587](13587.log) | switchport interface - class set dscp | **PASS** |
| [13586](13586.log) | switchport interface - class set cos | **PASS** |
| [13565](13565.log) | DSCP - Specify IP DSCP | **PASS** |
| [13563](13563.log) | CoS - Specify CoS | **PASS** |
| [13819](13819.log) | Classify traffic via Source/Destination IPv6 address | **PASS** |
| [31599](31599.log) | QoS: Matching (access-group) | **PASS** |
| [13594](13594.log) | Single Rate Policing standard test | **PASS** |
| [13595](13595.log) | Twin Rate Policing Standard test | **PASS** |
| [13604](13604.log) | static LAG based policing - single-rate | **PASS** (LAG not straddling) |
| [13549](13549.log) | defaults to strict priority queueing | **PASS** (re-run 2026-09-24; untagged queue-assignment finding) |
| [13553](13553.log) | wrr weightings applied | **PASS** (re-run 2026-09-24; 2.99:1 at 3:1) |
| [38148](38148.log) | IPv6 QoS - Exploratory testing | **UNMEASURED** — case has no steps |

## Method

Classification is measured **on the wire**, not inferred from counters. Every
classifier uses `set dscp 46` as its action, frames are injected with a known
marking, and the egress frame is **decoded with scapy** — so "matched" means
the DUT rewrote the field. Policing is likewise measured behaviourally: frames
are offered far above the CIR and counted at egress.

## Platform notes worth keeping

- **QoS must be enabled globally first.** `policy-map` / `class-map` are
  rejected with `% QoS is not enabled globally!` until then, and the enable
  command **prompts**: `mls qos enable` → *"Traffic will stop while
  configuration is applied. Continue? (y/n)"*. A config driver that does not
  answer it gets `% Command aborted.`
- **Policer counters need separate enabling.** `show mls qos interface <port>
  policer-counters` reports *"Policy map ... does not have any class maps with
  policer counters configured"* even with a working policer, which is why
  13594/13595/13604 are graded on observed drops instead.
- **CoS is only observable on a tagged frame.** For 13586 the whole egress path
  (stack `port1.0.2` → x230 `port1.0.3` → x230 `port1.0.1` → eth1) was put into
  trunk mode with native vlan 999 so vlan 1 egressed tagged. Restored afterwards.

## The UNMEASURED

- (13549 / 13553 were here on 2026-09-22 for want of congestion; re-run
  2026-09-24 with two NICs × tcpreplay at ~983 Mbps into one 1G egress — PASS.
  The untagged queue-assignment finding is in 13549.log NOTES.)
- **38148** — `num_steps = 0`. No procedure to execute. IPv6 QoS was still
  exercised and passed via 13819.

## Bench state at exit

`port1.0.2` and `port2.0.2` back to plain access vlan 1, vlan 999 removed from
both the stack and the x230, x230 ports back to access vlan 100, no policy-maps,
class-maps or QoS ACLs left, static LAG removed. All three TB paths verified
0% loss.
