# tb277 — bench state

> **Generated 2026-10-20T041840Z by `bench_probe.py`** from `captures/2026-10-20T041840Z/` on tb277. Measured state only;
> nothing here is hand-written. Regenerate with `./bench_probe.py --box tb277 run` on tb277. The
> `setup` fence at the end IS `tb277.setup`; `./bench_probe.py apply` writes it to the box.
> Names and PDU outlets come from `tb277.static`; platform mechanics live in the orient-dt
> skill; what a session did lives in its handover.

## Devices

| console | baud | name | model | serial | hostname | stack | role | software | bootloader | boot image |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| /dev/u2 | 115200 | swi_d | AT-x960-56YSQ | A2WQS700B | awplus | standalone | Active Master | sin_x96056-20261012-24 | Unknown | flash:/x960-tb277.rel |
| /dev/u3 | — | ? | ? | ? | ? | — | login_failed | | |  |
| /dev/u5 | — | ? | ? | ? | ? | — | login_failed | | |  |

## Links

| A | port | B | port | proof |
| --- | --- | --- | --- | --- |
| tb | eth3 (10.38.22.33/27) | swi_d | port1.0.10 | MAC learned on a physical port |
| tb | eth4 (10.38.22.65/27) | swi_d | port1.0.48 | MAC learned on a physical port |
| tb | eth2 (10.38.22.1/27) | — | — | carrier up, MAC not learned |

## Advisories

- !! USER-CONFLICT: the session gives facts for /dev/u3 (outlet 7, name -), but no device was read on /dev/u3 this run
- swi_d port1.0.2: neighbour 0000.cd42.3029 '' is not a device on any console read
- swi_d port1.0.16: neighbour 0000.cd42.3029 '' is not a device on any console read

## tb277.setup

```setup
### GENERATED 2026-10-20T041840Z by bench_probe.py from a console capture -- DO NOT HAND-EDIT.
### Source: claude/device-testing/bench-setup/bench-state.md (regenerate with
### `bench_probe.py run` on tb277; `bench_probe.py apply` writes this file).
### Names and PDU outlets come from bench-setup/tb277/tb277.static.

[power]
pwr_d = (pdu, 10.36.230.212, 1)

[switch]
swi_d = /dev/u2

[baudrates]
swi_d = 115200

[stack]

[configured_stackport]

[powerlink]
swi_d = pwr_d

[boot_from_flash]
swi_d = True

[portlink]
tb-swi_d = eth3-port1.0.10, eth4-port1.0.48
```

```nic-state
# NIC  carrier  learned_on
eth2 up -
eth3 up swi_d:port1.0.10
eth4 up swi_d:port1.0.48
```

```probe-meta
capture 2026-10-20T041840Z
unread /dev/u3 login_failed
unread /dev/u5 login_failed
```
