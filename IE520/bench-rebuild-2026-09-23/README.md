# Bench rebuild — 2026-09-23

Console captures from the recable Terrence asked for after the 72-case campaign,
and the reconfiguration that followed. **Not test results** — the campaign's own
group directories hold those.

## What was cabled

| cable | purpose |
| --- | --- |
| stack `port3.0.2` ↔ 4050 `port1.0.3` | second member for a LAG that **straddles stack units 3 and 4** |
| stack `port1.0.9` ↔ x230 `port1.0.4` | second stack↔x230 link |
| `eth1` moved: x230 → stack `port3.0.13` | take the x230 out of the observation path |
| `eth3` moved: 4050 → stack `port3.0.9` | third host directly on the DUT |

## What was configured

- **`sa1`** = stack `port3.0.2` + `port4.0.2` ↔ 4050 `port1.0.3` + `port1.0.4`, vlan 10.
  Replaces the old LACP `po1`. **Straddles stack members** — the thing the ACL/QoS
  LAG cases needed and could not have before.
- **`sa2`** = stack `port1.0.2` + `port1.0.9` ↔ x230 `port1.0.3` + `port1.0.4`, vlan 1.
  The two parallel links were a loop with RSTP off everywhere; **aggregating them is
  what removes it.**
- `vlan1` gained `10.38.215.66/27` secondary so `eth3` has a peer.
- `lacp global-passive-mode` disabled on the x230 (already off on stack and 4050).

## Three things that cost time, now in bench-state.md

1. **A static LAG refuses mismatched members** — `% The properties of port4.0.2 don't
   match other ports in aggregator`. Align VLAN/mode on both members *before*
   `static-channel-group`.
2. **`lacp global-passive-mode` silently enrols freed ports.** Third device it has bitten.
3. **The port budget was recorded wrongly.** Each IE520 member has **three** copper ports
   (`portN.0.2/.9/.13`), not one. That error is why several campaign cases were called
   blocked-on-cabling when the ports existed all along.

## Verified after the rebuild

`eth1→10.38.215.10`, `eth2→10.38.215.40`, `eth3→10.38.215.66` all 0% loss · vlan10
transit 3/3 · transit **through** the DUT (inject eth2, capture eth1) 10/10 · stack
`Normal operation`, 4/4 Ready · `sa1` and `sa2` both up with two members each.
