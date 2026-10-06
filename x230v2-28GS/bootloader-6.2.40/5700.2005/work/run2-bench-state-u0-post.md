# tb470 — bench state

> **Generated 2026-10-06T080737Z by `bench_probe.py`** from `captures/2026-10-06T080737Z/` on tb470. Measured state only;
> nothing here is hand-written. Regenerate with `./bench_probe.py run` on tb470. The
> `setup` fence at the end IS `tb470.setup`; `./bench_probe.py apply` writes it to the box.
> Names and PDU outlets come from `tb470.static`; platform mechanics live in the orient-dt
> skill; what a session did lives in its handover.

## Devices

| console | baud | name | model | serial | hostname | stack | role | software | bootloader | boot image |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| /dev/u0 | 9600 | swi_f | AT-x230-28GS V2 | A10783G262900002 | awplus | standalone | standalone | awplus_main-20261006-52 | 6.2.40 | flash:/x230v2_28GS-tb470.rel |

## Links

| A | port | B | port | proof |
| --- | --- | --- | --- | --- |
| tb | eth1 (10.38.215.1/27) | — | — | carrier DOWN |
| tb | eth2 (10.38.215.33/27) | — | — | carrier DOWN |
| tb | eth3 (10.38.215.65/27) | — | — | carrier up, MAC not learned |

## Advisories

- none

## tb470.setup

```setup
### GENERATED 2026-10-06T080737Z by bench_probe.py from a console capture -- DO NOT HAND-EDIT.
### Source: claude/device-testing/bench-setup/bench-state.md (regenerate with
### `bench_probe.py run` on tb470; `bench_probe.py apply` writes this file).
### Names and PDU outlets come from bench-setup/tb470.static.

[power]
pwr_f = (pdu, 10.36.150.14, 1)

[switch]
swi_f = /dev/u0

[baudrates]
swi_f = 9600

[stack]

[configured_stackport]

[powerlink]
swi_f = pwr_f

[boot_from_flash]
swi_f = True

[portlink]
```

```nic-state
# NIC  carrier  learned_on
eth1 down -
eth2 down -
eth3 up -
```

```probe-meta
capture 2026-10-06T080737Z
```
