# IE520 campaign test harness — DESIGN NOTE (code deliberately not here)

The campaign harness is **not checked in under this directory.** A repo guard
(`~/.claude/hooks/no-stray-py.py`) refuses `.py` files in the lab tree, and it
is right to: the sanctioned homes are the session scratchpad for throwaway
scripts, or the canonical tools in the Test-cases repo
(`ask-ck/tools/`, `ask-ck/functions/test-composer/`) for anything worth running
twice.

**OPEN QUESTION FOR TERRENCE:** this harness is worth running twice — every
remaining campaign group needs it. The guard points at
`ask-ck/functions/test-composer/` as the home for bench scripts, but `bench_probe.py`
has lived in THIS repo's `bench-setup/` since 2026-09-23 (consolidated into the one
bench-state tool on 2026-09-25), so the natural home is now `bench-setup/` here. It is
still a placement decision rather than something to do silently. Until then the code lives in the
session scratchpad and this note records how to rebuild it.

## What it does

Two small modules, ~120 lines total.

**`bench.py`**
- `DUT(tag)` — console session on the stack master (`/dev/u5`) via the shared
  `console.py` from `IE520/stack-tests/linkflap-38378-2026-09-18/`.
  Methods: `cmd(c, t)`, `conf([lines], t)`, `errs(out)`, `close()`.
- `send_capture(pkt_expr, bpf, n)` — inject `n` scapy frames on tb470 `eth2`
  into DUT `port2.0.2`, count what reaches `eth1` via the x230.
- Constants: `ING_IF="eth2"`, `EGR_IF="eth1"`,
  `ING_MAC="00:f0:4d:00:77:17"`, `EGR_MAC="00:f0:4d:00:77:16"`,
  `ING_PORT="port2.0.2"`, `EGR_PORT="port1.0.2"`,
  `RUN = os.environ.get("CAMPAIGN_RUN", <default group dir>)`.

**`qosbench.py`**
- `send_decode(pkt_expr, bpf, n)` — same path, but **decodes** each egress frame
  and returns dicts carrying `tos`/`dscp` (IPv4), `tc`/`dscp` (IPv6),
  `cos`/`vlan` (802.1Q). This is what lets QoS marking be measured on the wire
  rather than inferred from counters.
- `summarise(rows, key)` -> `(count, sorted_unique_values)`.

## The four rules it encodes — these are the point, not the code

1. **Baseline first, with the feature OFF.** Every case does. A drop only means
   something if the same traffic demonstrably forwarded a minute earlier.
2. **Traffic must TRANSIT the DUT.** Inject on one TB NIC, capture on another.
   A frame counted at egress has crossed the switch; a link-up check has not.
3. **Run unprivileged, elevate only the packet I/O.** Running the whole script
   under `sudo` writes root-owned logs onto the NFS share and blocks later
   appends — that happened once and had to be chowned back.
4. **`conf()` aborts on the first `%` error.** A bad line leaves the console in
   the wrong mode, and the blind `exit`/`end` chain that follows logs it out
   entirely; every later command then goes to a `login:` prompt. This cost one
   20-minute wedged run before it was fixed.

## Safe CLI syntax probing

Write `"<partial> ?"` to the serial port **with no trailing CR**, read, then send
`\x03`. Never use the normal `send()` helper — it appends CR, and if `<cr>` is a
valid completion the command RUNS. That is how ATMF secure mode got enabled by
accident on 2026-09-21. Note `\x03` also drops you out of a config sub-mode, so
re-enter it afterwards.

## Set-up on the testbox

```
mkdir -p /tmp/<scratch>
scp bench.py qosbench.py tb470:/tmp/<scratch>/
ssh tb470 'cd /tmp/<scratch> && CAMPAIGN_RUN=/home/terrenceb/claude/device-testing/IE520/<group-dir> python3 <case>.py'
```
`CAMPAIGN_RUN` is what keeps console captures filed with their own group.
