# IE520 campaign test harness

Extracted from the 2026-09-22 campaign session's scratchpad so it survives the
session. Copy to the testbox and import:

```
scp bench.py qosbench.py tb470:/tmp/<scratch>/
ssh tb470 'cd /tmp/<scratch> && python3 -c "import sys; sys.path.insert(0,\".\"); from bench import *"'
```

## bench.py

- `DUT(tag)` — console session on the stack master (`/dev/u5`) via the shared
  `console.py`. `cmd(c, t)`, `conf([lines], t)`, `errs(out)`.
  **`conf()` aborts on the first `%` error on purpose**: a bad line leaves the
  console in the wrong mode and the following blind `exit` chain logs it out
  entirely, after which every later command is typed at a `login:` prompt.
- `send_capture(pkt_expr, bpf, n)` — inject `n` scapy frames on tb470 `eth2`
  into DUT `port2.0.2` and count what reaches `eth1` via the x230. **A frame
  counted has TRANSITED the DUT**, which is what makes a drop meaningful.
- Ports/MACs are module constants: `ING_IF/EGR_IF`, `ING_MAC/EGR_MAC`,
  `ING_PORT/EGR_PORT`.

## qosbench.py

- `send_decode(pkt_expr, bpf, n)` — same path, but **decodes** each egress
  frame and returns dicts with `tos`/`dscp` (IPv4), `tc`/`dscp` (IPv6),
  `cos`/`vlan` (802.1Q). This is what lets QoS marking be measured on the wire
  instead of inferred from counters.
- `summarise(rows, key)` -> `(count, sorted_unique_values)`.

## Two rules the harness encodes

1. **Always take a baseline with the feature OFF first.** Every case in this
   campaign does. A drop only means something if the same traffic demonstrably
   forwarded a minute earlier.
2. **Run unprivileged; elevate only the packet I/O.** Running the whole script
   under `sudo` writes root-owned logs onto the NFS share and blocks later
   appends. `send_capture`/`send_decode` call `sudo -n` on just the tcpdump and
   scapy subprocesses.

## Safe CLI syntax probing

To discover syntax without executing anything, write `"<partial> ?"` to the
serial port **with no trailing CR**, read, then send `\x03`. Never use the
normal `send()` helper for this — it appends CR, and if `<cr>` is a valid
completion the command RUNS. That is how ATMF secure mode got enabled by
accident on 2026-09-21. Note `\x03` also exits a config sub-mode, so re-enter
it afterwards.
