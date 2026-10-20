# tb101 — bench state

> **Generated 2026-10-20T192814Z by `bench_probe.py`** from `captures/2026-10-20T192814Z/` on tb101. Measured state only;
> nothing here is hand-written. Regenerate with `./bench_probe.py --box tb101 run` on tb101. The
> `setup` fence at the end IS `tb101.setup`; `./bench_probe.py apply` writes it to the box.
> Names and PDU outlets come from `tb101.static`; platform mechanics live in the orient-dt
> skill; what a session did lives in its handover.

## Devices

| console | baud | name | model | serial | hostname | stack | role | software | bootloader | boot image |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| /dev/u0 | 115200 | swi_a | AT-IE520-28GSX | 264A23061 | IE520 | stk_a member 1 | Backup Member | awplus_main-20261019-75 | 9.2.0 | flash:/IE520-awplus_main-20261019-75.rel |
| /dev/u1 | 115200 | swi_b | AT-IE520-28GSX | 264A23068 | IE520 | stk_a member 2 | Backup Member | awplus_main-20261019-75 | 9.2.0 | flash:/IE520-awplus_main-20261019-75.rel |
| /dev/u2 | 115200 | swi_d | AT-IE520-28GSX | 264A23052 | IE520 | stk_a member 3 | Backup Member | awplus_main-20261019-75 | 9.2.0 | flash:/IE520-awplus_main-20261019-75.rel |
| /dev/u3 | 115200 | swi_c | AT-IE520-28GSX | 264A23066 | IE520 | stk_a member 4 | Active Master | awplus_main-20261019-75 | 9.2.0 | flash:/IE520-awplus_main-20261019-75.rel |

**stk_a**: Not all stack ports are up; Stack MAC 0000.cd37.0d6f; members 1=swi_a (84e3.2787.0ac0, prio 1, Backup Member), 2=swi_b (84e3.2787.0780, prio 128, Backup Member), 3=swi_d (84e3.2787.09c0, prio 128, Backup Member), 4=swi_c (84e3.2787.0740, prio 128, Active Master).

## Links

| A | port | B | port | proof |
| --- | --- | --- | --- | --- |
| tb | eth2 (10.37.101.1/27) | swi_d | port3.0.1 | MAC learned on a physical port |
| tb | eth3 (10.37.101.33/27) | swi_b | port2.0.1 | MAC learned on a physical port |
| tb | eth4 (10.37.101.65/27) | swi_a | port1.0.1 | MAC learned on a physical port |

## Advisories

- none

## tb101.setup

```setup
### GENERATED 2026-10-20T192814Z by bench_probe.py from a console capture -- DO NOT HAND-EDIT.
### Source: claude/device-testing/bench-setup/bench-state.md (regenerate with
### `bench_probe.py run` on tb101; `bench_probe.py apply` writes this file).
### Names and PDU outlets come from bench-setup/tb101/tb101.static.

[power]

[switch]
swi_a = /dev/u0
swi_b = /dev/u1
swi_c = /dev/u3
swi_d = /dev/u2

[baudrates]
swi_a = 115200
swi_b = 115200
swi_c = 115200
swi_d = 115200

[stack]
stk_a = swi_a, swi_b, swi_d, swi_c

[configured_stackport]

[powerlink]

[boot_from_flash]
stk_a = True
swi_a = True
swi_b = True
swi_c = True
swi_d = True

[portlink]
tb-swi_a = eth4-port1.0.1
tb-swi_b = eth3-port2.0.1
tb-swi_d = eth2-port3.0.1
```

```nic-state
# NIC  carrier  learned_on
eth2 up swi_d:port3.0.1
eth3 up swi_b:port2.0.1
eth4 up swi_a:port1.0.1
```

```probe-meta
capture 2026-10-20T192814Z
```
