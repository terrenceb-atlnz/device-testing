# The drivers that produced warmup-run1.log and runs2-3.log

Kept for reproducibility (the "code in a run dir" exception of `no-stray-scripts`). They
are exactly what ran on 2026-09-25; the standalone traffic tool distilled from them is
`IE520/tools/linerate.py`.

| file | role |
| --- | --- |
| `tdlf1.py` | run 1: known-unicast ramp 100 / 500 / line rate, then 10 s of line-rate DLF from eth3 into the master; `terminal monitor` captured; sdma CPU counters before/after |
| `tdlf2.py` | run 2 (DLF from eth2 via IE520-sa → sa3 → members 1/4) and run 3 (eth3 + eth2 at once); console lines logged as they arrive |
| `console.py` | the maintained pyserial console driver (copy of `IE520/stack-tests/2026-09-02-driver-test/console.py`) |
| `am2.py` | `session(tag)` / `do(c, tag, cmd)` / `log()` on top of console.py; `DEV` maps stk=/dev/u5, sa=/dev/u3, ar=/dev/u1, x230=/dev/u0 (9600); `do()` stops on any `% ` line unless `allow_err=True`; everything is appended to `$RUN/work-raw.log` |
| `gate.py` | `poll()` and `conf()` helpers on top of am2 |

## How they were run

The helpers lived in tb470's tmpfs `/tmp/ckorient/` (recreate it from this directory after a
reboot); scapy pcaps go in `/tmp/ckorient/q/`. Each driver is fed on stdin over ssh, as root
(tcpreplay, tcpdump, raw sockets), with `RUN` naming the log directory:

```bash
export SSH_AUTH_SOCK=/run/user/1971/keyring/ssh
ssh tb470 'mkdir -p /tmp/ckorient/q /tmp/ckorient/tmc'
scp console.py am2.py gate.py tb470:/tmp/ckorient/
ssh tb470 'cd /tmp/ckorient && sudo -n env RUN=/tmp/ckorient/tmc timeout 480 python3 - 2>&1 | tr -d "\r"' < tdlf2.py
```

Gates inside the drivers stop the run (exit 1) if the DLF MAC `0200.0000.9999` is already in
the MAC table or `terminal monitor` is not confirmed by "Console logging enabled". Give the
wrapper `timeout` more than the run needs: run 1's 260 s cut off the final log dump.
