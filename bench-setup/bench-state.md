# tb470 — bench state

> **Generated 2026-10-04T224833Z by `bench_probe.py`** from `captures/2026-10-04T224833Z/` on tb470. Measured state only;
> nothing here is hand-written. Regenerate with `./bench_probe.py run` on tb470. The
> `setup` fence at the end IS `tb470.setup`; `./bench_probe.py apply` writes it to the box.
> Names and PDU outlets come from `tb470.static`; platform mechanics live in the orient-dt
> skill; what a session did lives in its handover.

## Devices

| console | baud | name | model | serial | hostname | stack | role | software | bootloader | boot image |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| /dev/u0 | 9600 | swi_f | x230-10GP | G26ZE80EN | x230-10GP | standalone | standalone | awplus_5.5.5_2-20260918-7 | 3.2.16 | flash:/x230-tb470.rel |
| /dev/u2 | 115200 | swi_a | AT-IE520-28GSX | 264A23061 | IE520-u2 | standalone | Active Master | awplus_main-20260923-20 | 9.1.0 | flash:/IE520-tb470.rel |
| /dev/u4 | 115200 | swi_d | AT-IE520-28GSX | 264A23052 | IE520-stk | stk_a member 2 | Active Master | tomahawk_ie520-20260825-42 | pauld | flash:/coro-IE520-tb470.rel |
| /dev/u5 | 115200 | swi_c | AT-IE520-28GSX | 264A23066 | IE520-stk | stk_a member 1 | Backup Member | tomahawk_ie520-20260825-42 | 9.1.0 | flash:/coro-IE520-tb470.rel |

**stk_a**: Not all stack ports are up; Stack MAC 0000.cd37.0d6f; members 1=swi_c (84e3.2787.0740, prio 128, Backup Member), 2=swi_d (84e3.2787.09c0, prio 128, Active Master).

## Links

| A | port | B | port | proof |
| --- | --- | --- | --- | --- |
| tb | eth1 (10.38.215.1/27) | swi_c | port1.0.10 | MAC learned on a physical port |
| tb | eth3 (10.38.215.65/27) | swi_c | port1.0.9 | MAC learned on a physical port |
| swi_a | port1.0.2 | swi_f | port1.0.3 | lldp both ends |
| swi_a | port1.0.9 | swi_f | port1.0.4 | lldp both ends |
| tb | eth2 (10.38.215.33/27) | — | — | carrier up, MAC not learned |

## Advisories

- swi_c port1.0.2: neighbour 0000.cd40.0394 '' is not a device on any console read
- swi_d port2.0.2: neighbour 0000.cd40.0394 '' is not a device on any console read

## tb470.setup

```setup
### GENERATED 2026-10-04T224833Z by bench_probe.py from a console capture -- DO NOT HAND-EDIT.
### Source: claude/device-testing/bench-setup/bench-state.md (regenerate with
### `bench_probe.py run` on tb470; `bench_probe.py apply` writes this file).
### Names and PDU outlets come from bench-setup/tb470.static.

[power]
pwr_a = (pdu, 10.36.150.14, 6)
pwr_c = (pdu, 10.36.150.14, 5)
pwr_d = (pdu, 10.36.150.14, 4)
pwr_f = (pdu, 10.36.150.14, 1)

[switch]
swi_a = /dev/u2
swi_c = /dev/u5
swi_d = /dev/u4
swi_f = /dev/u0

[baudrates]
swi_a = 115200
swi_c = 115200
swi_d = 115200
swi_f = 9600

[stack]
stk_a = swi_c, swi_d

[configured_stackport]

[powerlink]
swi_a = pwr_a
swi_c = pwr_c
swi_d = pwr_d
swi_f = pwr_f

[boot_from_flash]
stk_a = True
swi_a = True
swi_c = True
swi_d = True
swi_f = True

[portlink]
tb-swi_c = eth1-port1.0.10, eth3-port1.0.9
swi_a-swi_f = port1.0.2-port1.0.3, port1.0.9-port1.0.4
```

```nic-state
# NIC  carrier  learned_on
eth1 up swi_c:port1.0.10
eth2 up -
eth3 up swi_c:port1.0.9
```

```probe-meta
capture 2026-10-04T224833Z
```
