# tb277 — bench state

> **Generated 2026-10-16T015257Z by `bench_probe.py`** from `captures/2026-10-16T015257Z/` on tb277. Measured state only;
> nothing here is hand-written. Regenerate with `./bench_probe.py --box tb277 run` on tb277. The
> `setup` fence at the end IS `tb277.setup`; `./bench_probe.py apply` writes it to the box.
> Names and PDU outlets come from `tb277.static`; platform mechanics live in the orient-dt
> skill; what a session did lives in its handover.

## Devices

| console | baud | name | model | serial | hostname | stack | role | software | bootloader | boot image |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| /dev/u2 | 115200 | swi_d | AT-x960-56YSQ | A2WQS700B | awplus | standalone | Active Master | sin_x96056-20261012-24 | Unknown | flash:/x960-tb277.rel |
| /dev/u3 | 9600 | swi_b | AT-x960-28YSQ | A10737A261700021 | x960-28YSQ | standalone | Active Master | sin_x96056-20260921-9 | 8.24.0 | flash:/backup.rel |
| /dev/u5 | 9600 | swi_a | AT-x950 GEN2-52XSTQm | A10713A262600012 | awplus | standalone | Active Master | awplus_main-20261008-56 | 8.24.0 | Not |

## Links

| A | port | B | port | proof |
| --- | --- | --- | --- | --- |
| tb | eth3 (10.38.22.33/27) | swi_d | port1.0.10 | MAC learned on a physical port |
| tb | eth4 (10.38.22.65/27) | swi_d | port1.0.48 | MAC learned on a physical port |
| swi_a | port1.0.1 | swi_b | port1.0.1 | lldp both ends |
| swi_a | port1.0.11 | swi_b | port1.0.11 | lldp both ends |
| swi_a | port1.0.14 | swi_d | port1.0.14 | lldp both ends |
| swi_a | port1.0.4 | swi_d | port1.0.4 | lldp both ends |
| swi_b | port1.0.16 | swi_d | port1.0.16 | lldp both ends |
| swi_b | port1.0.2 | swi_d | port1.0.2 | lldp both ends |
| tb | eth2 (10.38.22.1/27) | — | — | carrier up, MAC not learned |

## Advisories

- none

## tb277.setup

```setup
### GENERATED 2026-10-16T015257Z by bench_probe.py from a console capture -- DO NOT HAND-EDIT.
### Source: claude/device-testing/bench-setup/bench-state.md (regenerate with
### `bench_probe.py run` on tb277; `bench_probe.py apply` writes this file).
### Names and PDU outlets come from bench-setup/tb277/tb277.static.

[power]
pwr_a = (pdu, 10.36.230.35, 3)
pwr_b = (pdu, 10.36.230.212, 7)
pwr_d = (pdu, 10.36.230.212, 1)

[switch]
swi_a = /dev/u5
swi_b = /dev/u3
swi_d = /dev/u2

[baudrates]
swi_a = 9600
swi_b = 9600
swi_d = 115200

[stack]

[configured_stackport]

[powerlink]
swi_a = pwr_a
swi_b = pwr_b
swi_d = pwr_d

[boot_from_flash]
swi_a = False
swi_b = True
swi_d = True

[portlink]
tb-swi_d = eth3-port1.0.10, eth4-port1.0.48
swi_a-swi_b = port1.0.1-port1.0.1, port1.0.11-port1.0.11
swi_a-swi_d = port1.0.14-port1.0.14, port1.0.4-port1.0.4
swi_b-swi_d = port1.0.16-port1.0.16, port1.0.2-port1.0.2
```

```nic-state
# NIC  carrier  learned_on
eth2 up -
eth3 up swi_d:port1.0.10
eth4 up swi_d:port1.0.48
```

```probe-meta
capture 2026-10-16T015257Z
```
