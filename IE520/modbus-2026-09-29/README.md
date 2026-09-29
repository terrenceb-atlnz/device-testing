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
| T22653 | modbus — read port information | [22653.log](22653.log) | **PASS** (re-graded 09-30; was PARTIAL) — steps 1,2,6,7 PASS (port1.0.1 0x5000=0x0000 down/auto, 0x5001=0xf000 admin-up/auto, bytes 0/0 = CLI; linked port1.0.2 0xf103 = up/full/1000 and byte counters = CLI too); steps 3,4,5 (PoE 0x5002–0x5004) unsupported by platform: illegal-data-address, no PoE on the IE520-28GSX |
| T22654 | modbus — write | [22654.log](22654.log) | **PASS** (re-graded 09-30; was PARTIAL) — steps 1,2,4,5 PASS: alarm config 0x3001 written (LED = **0x8000**, MSB-first; read-back, `show alarm facility settings` "L", running-config line, modbusd log), port1.0.1 0x5001 written down/up (shutdown line, NSM + modbusd log), the same over global IPv6 fd32:…::10 and link-local; step 3 PoE write unsupported by platform (exception, "Request failed"). Findings: a write of an unmapped bit (0x0001) is acknowledged with no effect; mapping-5 alarm entries are 6 words (status at +5) |
| T22655 | modbus — dynamic changes | [22655.log](22655.log) | **PASS** — port 5020 answers while 502 refuses (and back); disable refuses / enable answers; API down/up of linked port1.0.2 reflected in CLI + 0x500d/0x500e; CLI shutdown reflected in the registers. Observation: on an aggregator-member port the state write is applied but answered exception 4 (duplex/polarity/speed nibbles refused on a LAG member) |
| T22651 | S2166.1.10–12 — modbus — read Sensor information | [22651.log](22651.log) | **PASS** — sensor #1 (type 2, float 43.0/42.0/45.0 °C, units 2, status 0) and #2 (type 11, 0.0 = "LED Output No") and sensors 3–5 (relay Open/Closed, Power Input Yes/No as 1.0/0.0) equal `show system environment` on members 1, 3, 4 |
| T22650 | S2166.1.10–12 — modbus — read System information | [22650-fail.log](22650-fail.log) | **FAIL** (step 5) — 9/10 steps equal the CLI at their Mapping-Version-5 addresses (name, software, MAC, ports 84, faults 0, sensors 15, board name/serial per member); Number of Alarms 0x0049 = **124 vs 93** in `show alarm facility settings` (one extra member's worth; the stack has a provisioned member 2). The case text uses the version-1 addresses |
| T22652 | S2166.1.10–12 — modbus — read alarm information | [22652.log](22652.log) | **PASS** — alarm #1 (External PSU 1) type 1, config 0x0000 ("-"), status False/True/False = `show system environment` Power Input 1 Yes/No/Yes on members 1/3/4; PSU 2 and Link-down entries consistent too. The case-text addresses 0x3600–0x3602 are illegal-data-address on this map-5 DUT; the block is at 0x3000, 6 words per alarm |

Group result: 6 cases — 5 PASS (22655, 22651, 22652, and 22653/22654, whose PoE steps are UNSUPPORTED by the platform — re-graded from PARTIAL 2026-09-30), 1 FAIL (22650: 0x0049 alarm count 124 vs CLI 93). Findings for Terrence / the case owner: (a) the AWPTCM step texts of 22650/22652 carry version-1 register addresses; the DUT is Mapping Version 5 (system name 0x0001, software 0x0021, MAC 0x0041, counts 0x0045–0x0049, per-member blocks by unit id); (b) alarm-config bit numbering is MSB-first (LED = 0x8000) and an unmapped bit is accepted silently; (c) alarm entries are 6 words (status at +5); (d) a state write to an aggregator-member port is applied but answered exception 4; (e) 0x0049 counts a provisioned-but-absent stack member's alarms.

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
