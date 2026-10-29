# tb490 — bench state

> **Generated 2026-10-29T000558Z by `bench_probe.py`** from `captures/2026-10-29T000558Z/` on tb490. Measured state only;
> nothing here is hand-written. Regenerate with `./bench_probe.py --box tb490 run` on tb490. The
> `setup` fence at the end IS `tb490.setup`; `./bench_probe.py apply` writes it to the box.
> Names and PDU outlets come from `tb490.static`; platform mechanics live in the orient-dt
> skill; what a session did lives in its handover.

## Devices

| console | baud | name | model | serial | hostname | stack | role | software | bootloader | boot image |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| /dev/u2 | 115200 | swi_a | AT-x980-16CDQ | A10732A263200035 | x980-CDQ | standalone | Active Master | awplus_main-20261029-90 | 260616 | flash:/x980-tb490.rel |

## Links

| A | port | B | port | proof |
| --- | --- | --- | --- | --- |
| tb | eth1 (10.38.235.1/27) | — | — | carrier up, MAC not learned |
| tb | eth2 (10.38.235.33/27) | — | — | carrier DOWN |
| tb | eth3 (10.38.235.65/27) | — | — | carrier DOWN |
| tb | eth4 (10.38.235.97/27) | — | — | carrier DOWN |
| tb | eth5 (10.38.235.129/27) | — | — | carrier DOWN |
| tb | eth6 (10.38.235.161/27) | — | — | carrier DOWN |
| tb | eth7 (10.38.235.193/27) | — | — | carrier DOWN |

## Advisories

- unit AT-x980-16CDQ S/N A10732A263200035 on /dev/u2 is not in bench-setup/tb490/tb490.static -- named swi_a for this run; add it there (name, PDU outlet)
- `lldp run` was OFF on x980-CDQ (/dev/u2); the probe switched it on and left it on (running-config only -- a reboot drops it and the next run re-applies it)

## tb490.setup

```setup
### GENERATED 2026-10-29T000558Z by bench_probe.py from a console capture -- DO NOT HAND-EDIT.
### Source: claude/device-testing/bench-setup/bench-state.md (regenerate with
### `bench_probe.py run` on tb490; `bench_probe.py apply` writes this file).
### Names and PDU outlets come from bench-setup/tb490/tb490.static.

[power]

[switch]
swi_a = /dev/u2

[baudrates]
swi_a = 115200

[stack]

[configured_stackport]

[powerlink]

[boot_from_flash]
swi_a = True

[portlink]
```

```nic-state
# NIC  carrier  learned_on
eth1 up -
eth2 down -
eth3 down -
eth4 down -
eth5 down -
eth6 down -
eth7 down -
```

```probe-meta
capture 2026-10-29T000558Z
```
