# tb470 — bench state

> **Generated 2026-10-15T213406Z by `bench_probe.py`** from `captures/2026-10-15T213406Z/` on tb470. Measured state only;
> nothing here is hand-written. Regenerate with `./bench_probe.py run` on tb470. The
> `setup` fence at the end IS `tb470.setup`; `./bench_probe.py apply` writes it to the box.
> Names and PDU outlets come from `tb470.static`; platform mechanics live in the orient-dt
> skill; what a session did lives in its handover.

## Devices

| console | baud | name | model | serial | hostname | stack | role | software | bootloader | boot image |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| /dev/u7 | 115200 | swi_f | AT-x230-28GS V2 | A10783G262900002 | awplus | standalone | standalone | awplus_main-20261008-57 | 6.2.40 | flash:/x230v2_28GS-awplus_main-20261008-57.rel |
| /dev/u8 | 115200 | swi_e | AR4050S-5G | A10401G214000005 | 4050-5g | standalone | standalone | awplus_main-20261008-57 | 5.2.8 | flash:/AR4050S-awplus_main-20261008-57.rel |

## Links

| A | port | B | port | proof |
| --- | --- | --- | --- | --- |
| swi_e | port1.0.2 | swi_f | port1.0.1 | lldp both ends |
| tb | eth1 (10.38.215.1/27) | — | — | carrier DOWN |
| tb | eth2 (10.38.215.33/27) | — | — | carrier DOWN |
| tb | eth3 (10.38.215.65/27) | — | — | carrier DOWN |

## Advisories

- none

## tb470.setup

```setup
### GENERATED 2026-10-15T213406Z by bench_probe.py from a console capture -- DO NOT HAND-EDIT.
### Source: claude/device-testing/bench-setup/bench-state.md (regenerate with
### `bench_probe.py run` on tb470; `bench_probe.py apply` writes this file).
### Names and PDU outlets come from bench-setup/tb470.static.

[power]
pwr_e = (pdu, 10.36.150.14, 3)
pwr_f = (pdu, 10.36.150.14, 4)

[switch]
swi_e = /dev/u8
swi_f = /dev/u7

[baudrates]
swi_e = 115200
swi_f = 115200

[stack]

[configured_stackport]

[powerlink]
swi_e = pwr_e
swi_f = pwr_f

[boot_from_flash]
swi_e = True
swi_f = True

[portlink]
swi_e-swi_f = port1.0.2-port1.0.1
```

```nic-state
# NIC  carrier  learned_on
eth1 down -
eth2 down -
eth3 down -
```

```probe-meta
capture 2026-10-15T213406Z
```
