# tb277 — bench state

> **Generated 2026-10-07T034454Z by `bench_probe.py`** from `captures/2026-10-07T034454Z/` on tb277. Measured state only;
> nothing here is hand-written. Regenerate with `./bench_probe.py --box tb277 run` on tb277. The
> `setup` fence at the end IS `tb277.setup`; `./bench_probe.py apply` writes it to the box.
> Names and PDU outlets come from `tb277.static`; platform mechanics live in the orient-dt
> skill; what a session did lives in its handover.

## Devices

| console | baud | name | model | serial | hostname | stack | role | software | bootloader | boot image |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| /dev/u2 | 115200 | swi_c | AT-x960-56YSQ | A2WQS7004 | x960-56YSQ | standalone | Active Master | sin_x96056-20260921-9 | benb | Not |
| /dev/u3 | 9600 | swi_b | AT-x960-28YSQ | A10737A261700021 | x960-28YSQ | standalone | Active Master | sin_x96056-20260921-9 | 8.24.0 | flash:/backup.rel |
| /dev/u5 | 9600 | swi_a | AT-x950 GEN2-52XSTQm | A10713A262600012 | x950gen2 | standalone | Active Master | awplus_main-20260920-12 | 8.24.0 | Not |

## Links

| A | port | B | port | proof |
| --- | --- | --- | --- | --- |
| tb | eth4 (10.38.22.65/27) | swi_c | port1.0.48 | MAC learned on a physical port |
| swi_a | port1.0.1 | swi_b | port1.0.1 | lldp both ends |
| swi_b | port1.0.2 | swi_c | port1.0.2 | lldp both ends |
| tb | eth2 (10.38.22.1/27) | — | — | carrier up, MAC not learned |
| tb | eth3 (10.38.22.33/27) | — | — | carrier up, MAC not learned |

## Advisories

- none

## tb277.setup

```setup
### GENERATED 2026-10-07T034454Z by bench_probe.py from a console capture -- DO NOT HAND-EDIT.
### Source: claude/device-testing/bench-setup/bench-state.md (regenerate with
### `bench_probe.py run` on tb277; `bench_probe.py apply` writes this file).
### Names and PDU outlets come from bench-setup/tb277/tb277.static.

[power]
pwr_a = (pdu, 10.36.230.35, 3)
pwr_b = (pdu, 10.36.230.212, 7)
pwr_c = (pdu, 10.36.230.212, 1)

[switch]
swi_a = /dev/u5
swi_b = /dev/u3
swi_c = /dev/u2

[baudrates]
swi_a = 9600
swi_b = 9600
swi_c = 115200

[stack]

[configured_stackport]

[powerlink]
swi_a = pwr_a
swi_b = pwr_b
swi_c = pwr_c

[boot_from_flash]
swi_a = False
swi_b = True
swi_c = False

[portlink]
tb-swi_c = eth4-port1.0.48
swi_a-swi_b = port1.0.1-port1.0.1
swi_b-swi_c = port1.0.2-port1.0.2
```

```nic-state
# NIC  carrier  learned_on
eth2 up -
eth3 up -
eth4 up swi_c:port1.0.48
```

```probe-meta
capture 2026-10-07T034454Z
```
