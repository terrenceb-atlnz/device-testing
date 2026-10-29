# tb5 — bench state

> **Generated 2026-10-29T000612Z by `bench_probe.py`** from `captures/2026-10-29T000612Z/` on tb5. Measured state only;
> nothing here is hand-written. Regenerate with `./bench_probe.py --box tb5 run` on tb5. The
> `setup` fence at the end IS `tb5.setup`; `./bench_probe.py apply` writes it to the box.
> Names and PDU outlets come from `tb5.static`; platform mechanics live in the orient-dt
> skill; what a session did lives in its handover.

## Devices

| console | baud | name | model | serial | hostname | stack | role | software | bootloader | boot image |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| /dev/u0 | 115200 | swi_b | AT-x950-52XTQm | A10307A213600014 | x950-ptp | standalone | Active Master | awplus_main-20261020-78 | 6.2.30 | flash:/x950-5.5.5-2.1.rel |
| /dev/u1 | 115200 | swi_c | AT-x530-18GHXm | A10402G214500008 | awplus | standalone | Active Master | awplus_main-20261028-87 | 7.0.16 | Not set |
| /dev/u2 | 115200 | swi_a | AR4050S | A05049G221700121 | wlg-ar4050s | standalone | standalone | awplus_main-20261027-86 | 5.2.8 | flash:/AR4050S-awplus_main-20251103-998.rel |

## Links

| A | port | B | port | proof |
| --- | --- | --- | --- | --- |
| tb | eth4 (10.37.5.65/27) | swi_a | port1.0.8 | MAC learned on a physical port |
| tb | eth6 (10.37.5.129/27) | swi_c | port1.0.16 | MAC learned on a physical port |
| swi_b | port1.0.39 | swi_c | port1.0.1 | lldp both ends |
| tb | eth2 (10.37.5.1/27) | — | — | carrier up, MAC not learned |
| tb | eth3 (no IPv4) | — | — | carrier DOWN |
| tb | eth5 (no IPv4) | — | — | carrier DOWN |

## Advisories

- unit AR4050S S/N A05049G221700121 on /dev/u2 is not in bench-setup/tb5/tb5.static -- named swi_a for this run; add it there (name, PDU outlet)
- unit AT-x950-52XTQm S/N A10307A213600014 on /dev/u0 is not in bench-setup/tb5/tb5.static -- named swi_b for this run; add it there (name, PDU outlet)
- unit AT-x530-18GHXm S/N A10402G214500008 on /dev/u1 is not in bench-setup/tb5/tb5.static -- named swi_c for this run; add it there (name, PDU outlet)
- `lldp run` was OFF on x950-ptp (/dev/u0); the probe switched it on and left it on (running-config only -- a reboot drops it and the next run re-applies it)
- `lldp run` was OFF on awplus (/dev/u1); the probe switched it on and left it on (running-config only -- a reboot drops it and the next run re-applies it)

## tb5.setup

```setup
### GENERATED 2026-10-29T000612Z by bench_probe.py from a console capture -- DO NOT HAND-EDIT.
### Source: claude/device-testing/bench-setup/bench-state.md (regenerate with
### `bench_probe.py run` on tb5; `bench_probe.py apply` writes this file).
### Names and PDU outlets come from bench-setup/tb5/tb5.static.

[power]

[switch]
swi_a = /dev/u2
swi_b = /dev/u0
swi_c = /dev/u1

[baudrates]
swi_a = 115200
swi_b = 115200
swi_c = 115200

[stack]

[configured_stackport]

[powerlink]

[boot_from_flash]
swi_a = True
swi_b = True
swi_c = False

[portlink]
tb-swi_a = eth4-port1.0.8
tb-swi_c = eth6-port1.0.16
swi_b-swi_c = port1.0.39-port1.0.1
```

```nic-state
# NIC  carrier  learned_on
eth2 up -
eth3 down -
eth4 up swi_a:port1.0.8
eth5 down -
eth6 up swi_c:port1.0.16
```

```probe-meta
capture 2026-10-29T000612Z
```
