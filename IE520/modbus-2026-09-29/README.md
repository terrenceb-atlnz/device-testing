# Modbus group — IE520 stack, tb470, 2026-09-29

Queue: [../CAMPAIGN-QUEUE-2026-09-29.md](../CAMPAIGN-QUEUE-2026-09-29.md) row 8. Hand-driven
cases (no framework script): `ckcon.py` (console.py wrapper) on the stack master console
`/dev/u5` + `mb.py` (pymodbus 3.8.6) on tb470 `eth1` 10.38.215.1 → stack vlan1 10.38.215.10,
TCP 502. Run through `/test-mode` with the bench-runner agent as tester, Terrence away.

DUT facts that shape every verdict here: the AT-IE520-28GSX has **no PoE** (`show power-inline`
= `% Invalid input`), so every PoE register step is unsupported by platform; the DUT reports
**Mapping Version 5**; per-member register blocks (0x0120, 0x0200, 0x1000, 0x3000, 0x5000) are
addressed by Modbus **unit id = stack member** (1, 3, 4 here; unit 0 serves the system block only).

| case | title | log | verdict |
| --- | --- | --- | --- |
| T22653 | modbus — read port information | [22653-partial.log](22653-partial.log) | **PARTIAL** — steps 1,2,6,7 PASS (port1.0.1 0x5000=0x0000 down/auto, 0x5001=0xf000 admin-up/auto, bytes 0/0 = CLI; linked port1.0.2 0xf103 = up/full/1000 and byte counters = CLI too); steps 3,4,5 (PoE 0x5002–0x5004) unsupported by platform: illegal-data-address, no PoE on the IE520-28GSX |

## What is in this directory
- `<id>[-verdict].log` — one log per case, latest run, name = verdict (STANDING-ORDERS §2).
- `pre-test-configs/u0..u5.show_running-config.txt` — from the 13:42 probe capture
  (`bench-setup/captures/2026-09-29T004156Z`), the baseline every teardown is diffed against.
- `post-test-configs/<id>.u5.show_running-config.txt` — the stack's running-config after each
  case's teardown (diffed IDENTICAL against the baseline in the case log).
- `<id>.sh` / `<id>.out` / `<id>-teardown.out` — the per-case driver script and its full stdout
  (console commands with output, every Modbus request as TX bytes with the decoded reply).
- `mb-<id>.log` — the pymodbus client's own per-request log; `mb-baseline.log` — the
  connection-refused baseline with the server disabled; `mb.py` — the client.
- `console-u5.log` — the ckcon.py transcript of the stack master console for the whole group.
