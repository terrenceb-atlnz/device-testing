# tb5 — bench state

> **Generated 2026-10-29T023125Z by `bench_probe.py`** from `captures/2026-10-29T023125Z/` on tb5. Measured state only;
> nothing here is hand-written. Regenerate with `./bench_probe.py --box tb5 run` on tb5. The
> `setup` fence at the end IS `tb5.setup`; `./bench_probe.py apply` writes it to the box.
> Names and PDU outlets come from `tb5.static`; platform mechanics live in the orient-dt
> skill; what a session did lives in its handover.

## Devices

| console | baud | name | model | serial | hostname | stack | role | software | bootloader | boot image |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| /dev/u0 | 115200 | swi_x950 | AT-x950-52XTQm | A10307A213600014 | x950-ptp | standalone | Active Master | awplus_main-20261020-78 | 6.2.30 | flash:/x950-5.5.5-2.1.rel |
| /dev/u1 | 115200 | swi_x530 | AT-x530-18GHXm | A10402G214500008 | awplus | standalone | Active Master | awplus_main-20261028-87 | 7.0.16 | Not set |
| /dev/u2 | 115200 | swi_ar | AR4050S | A05049G221700121 | wlg-ar4050s | standalone | standalone | awplus_main-20261027-86 | 5.2.8 | flash:/AR4050S-awplus_main-20251103-998.rel |

## Links

| A | port | B | port | proof |
| --- | --- | --- | --- | --- |
| tb | eth6 (10.37.5.129/27) | swi_x950 | port1.0.39 | MAC learned on a physical port |
| tb | eth2 (10.37.5.1/27) | — | — | carrier up, MAC not learned |
| tb | eth3 (no IPv4) | — | — | carrier DOWN |
| tb | eth4 (10.37.5.65/27) | — | — | carrier up, MAC not learned |
| tb | eth5 (no IPv4) | — | — | carrier DOWN |

## Advisories

- eth6 learned on swi_x950 port1.0.39 AND swi_x530 port1.0.16

## tb5.setup

```setup
### GENERATED 2026-10-29T023125Z by bench_probe.py from a console capture -- DO NOT HAND-EDIT.
### Source: claude/device-testing/bench-setup/bench-state.md (regenerate with
### `bench_probe.py run` on tb5; `bench_probe.py apply` writes this file).
### Names and PDU outlets come from bench-setup/tb5/tb5.static.

[power]

[switch]
swi_ar = /dev/u2
swi_x530 = /dev/u1
swi_x950 = /dev/u0

[baudrates]
swi_ar = 115200
swi_x530 = 115200
swi_x950 = 115200

[stack]

[configured_stackport]

[powerlink]

[boot_from_flash]
swi_ar = True
swi_x530 = False
swi_x950 = True

[portlink]
tb-swi_x950 = eth6-port1.0.39
```

```nic-state
# NIC  carrier  learned_on
eth2 up -
eth3 down -
eth4 up -
eth5 down -
eth6 up swi_x950:port1.0.39
```

```probe-meta
capture 2026-10-29T023125Z
```
