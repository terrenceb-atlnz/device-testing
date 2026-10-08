# Modbus plans -- tb470 IE520 stack (AWPTCM T22650-T22655)

One `tools/mbplan.py` plan per case, holding the steps AND their expected results as measured on
tb470, `main-calanm`, 2026-10-08 (`../../modbus-2026-10-08T1131/`, whose `<id>-review.md` files
explain each value). The runner grades every line itself and prints one row per line, so the
tester compares, never rediscovers. **Bench facts are in these files** (ports, serials, which
power inputs are present): re-check them against bench-state.md before a run, and change the
plan, never the expectation in your head.

Run ON tb470, from a copy of `tools/` (it imports `mb.py` and calls `ckcon.py` beside it):

    cp -r ~/claude/device-testing/tools /tmp/<campaign>/tools
    P=~/claude/device-testing/tb470/IE520/plans/modbus
    python3 -B /tmp/<campaign>/tools/mbplan.py --host 10.38.215.10 \
        --console /dev/u5 --baud 115200 --transcript /tmp/<campaign>/console-u5.log \
        --log <case>/work/mb-<id>.log --out <case>/work/<id>.out  $P/<id>.plan

- `--console` is the stack MASTER's console (`show stack` first; u5 on 2026-10-08).
- T22654 steps 4-5 are `22654-ipv6.plan`, run twice: `--host fd32:b1f0:dff8:d701::10` and
  `--host fe80::200:cdff:fe37:d6f%eth1`, after `22654.plan` (which ends by adding the global
  address, step `setup-v6`) and before `22654-teardown.plan` (which removes it and disables the
  server).
- The per-case `stk_a.cfg` (`rc2cfg.py`) and the teardown diff (`rcdiff.py`) stay with the tester,
  as logged-output.md §2 says. Each plan ends with the server disabled.
- `--var` fills `${NAME}`: 22650 needs `SWVER=<show system Software version>`.

Expected FAILs on this bench, not plan errors: T22650 `0x0049` (124, while member 2 is
provisioned; the plan expects the CLI's 93).
