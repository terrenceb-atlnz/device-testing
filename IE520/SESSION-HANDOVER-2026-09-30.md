# Session handover — 2026-09-30 (wrapped ~10:20 NZDT)

Session `device-testing-ba`: `/orient-dt`, then a speed-up of `bench_probe.py` (Terrence: "2
minutes is really silly, and a 35 second sleep seems excessive"). **No test cases ran and no
sentinel was armed** — none was needed, since nothing but read-only probing touched the bench.

## TL;DR

- **The bench is WHOLE and unchanged since the 09-29 wrap.** The final probe,
  `2026-09-29T211548Z` (10:15 NZDT), reads **MISMATCH on ONE declared link only**: the SX fibre
  link `swi_b-swi_d port1.0.26-port4.0.26`. **Its `apply` is still Terrence's and still
  pending**, exactly as at the 09-29 wrap. The generated bench-state.md is byte-identical to this
  morning's orient run apart from its stamp.
- **`bench_probe.py run` now takes 19–36 s instead of ~110 s** (four live runs, below), and
  produces the same bench-state.md. Every run prints a `timing:` line and saves it in `meta.json`.
- **Resume point unchanged:** `/test-mode --resume`, queue row 7 (VLAN): T38408, T38407,
  T18302, T18303 — see [SESSION-HANDOVER-2026-09-29.md](SESSION-HANDOVER-2026-09-29.md) §6 and
  [CAMPAIGN-QUEUE-2026-09-29.md](CAMPAIGN-QUEUE-2026-09-29.md).
- **Commits:** this wrap's commit on device-testing main — **committed, NOT pushed** (Claude
  cannot push).

## 1. Bench state and how to verify it

Topology and measured state: [bench-setup/bench-state.md](../bench-setup/bench-state.md),
generated 2026-09-29T211548Z. Read at wrap (10:1x NZDT):

```
stack      members 1/3/4 Ready, Normal operation, member 3 (u5) Active Master, VMAC 0000.cd37.0d6f
builds     IE520s awplus_main-20260923-20 on all three members and the SA (build date equal)
boot       every device <platform>-tb470.rel (file exists) + flash:/tb470-bench.cfg (file exists)
flash      stack and SA: tb470-bench.cfg, default.cfg, IE520-tb470.rel only
reboots    none since the 09-29 framework PDU cycles (last entry 2026-09-28 23:5x UTC on u5, u3, u0);
           every unit ~21 h uptime at 09:57 NZDT
x230 LLDP  `lldp run` absent from BOTH running- and startup-config (the probe's temporary on/off reverted)
host       eth1/eth2/eth3 carrier up; /nfsHome mounted; no ethtool/IP/route changes this session
consoles   all free at wrap (sudo fuser: none); no tmux, sniffer, sender, Monitor or cron
```

Verify, ON tb470, with consoles free:

```bash
cd ~/claude/device-testing/bench-setup && ./bench_probe.py run
# expect MISMATCH (1): [portlink] swi_b-swi_d bench {port1.0.26-port4.0.26, port1.0.9-port4.0.9}
# vs template port1.0.9-port4.0.9 -- MATCH after Terrence's `./bench_probe.py apply`
```

## 2. What was accomplished

1. `/orient-dt`: probe `2026-09-29T205700Z` MISMATCH = only the pending SX link, as predicted.
2. **`bench_probe.py` speed-up** (capture side only; `generate`/`diff`/`apply` untouched):
   - **Where the ~110 s went** (from the 09:57 capture's file mtimes): login + serial LLDP
     check ~44 s, the fixed `LLDP_SETTLE` 35 s sleep, commands 20 s (x230 at 9600 the tail),
     LLDP revert + closes 11 s.
   - Reads end on the device's own prompt after the echo (`Probe._cmd`), not on a 0.8 s quiet
     gap (1.6 s at 9600). The login dialog uses `_expect` throughout. `capture_banner` hands
     `login()` the console's current state, so no extra CR is sent at `login:`.
   - Consoles are grouped by `show stack` (the key `build_model()` uses). Only a stack's first
     console runs the command list; the others read their banner and `show stack`.
   - LLDP check runs on all devices in parallel and they meet at a barrier. Neighbour tables are
     read LAST. If any device had LLDP switched on, every device polls (`_read_neighbours`)
     until it sees its last-run ports AND every port a neighbour sees it on, capped at 35 s. A
     capped wait becomes an Advisory in bench-state.md.
   - The previous capture's baud per console is tried first. Host pings and closes run in
     parallel.
3. Records: probe docstring; orient-dt §0/§1/§3 runtime (snapshot
   `SKILL.md.pre-20260930b`); wrap-dt §4; bench-runner gate 4; memory `bench-probe-one-tool`.

## 3. Results — the probe runs

| capture | total | LLDP wait (x230) | bench-state vs morning | label |
| --- | --- | --- | --- | --- |
| 2026-09-29T205700Z (old code, orient) | ~110 s | fixed 35 s | — (baseline) | clean |
| 2026-09-29T210917Z (first rewrite) | 31.4 s | 21.7 s | **2 links `lldp one end`** | regression, fixed |
| 2026-09-29T211132Z | 18.5 s | 7.1 s | identical | clean |
| 2026-09-29T211213Z | 36.0 s | 25.9 s | identical | clean |
| 2026-09-29T211548Z (wrap) | 33.9 s | 24.2 s | identical | clean |

The offline `generate` of the baseline capture is also byte-identical before and after the
change. The driver was also exercised against a simulated AW+ console in the session scratchpad
(login from `login:`, from a stray `Password:` and from `#`; a 0.4 s pause mid-output did not end
the read).

## 4. Findings

**Measured:**
- **The remaining 7–26 s is the neighbours' LLDP send interval** (30 s). The x230 has LLDP off,
  the probe turns it on, and the x230 only learns its neighbours from their next periodic
  send. With every device already running LLDP, a run would be ~12 s.
- **Reading neighbour tables before every device's LLDP check is done loses proof.** The first
  rewrite let the stack read its table before the x230 (9600, slower login) had switched LLDP
  on, so swi_a↔swi_f links graded `lldp one end`. The old fixed sleep had been hiding this. The
  barrier plus cross-check fixes it (memory `bench-probe-one-tool`).

## 5. OPEN — Terrence's decisions

1. **NEW: keep `lldp run` on the x230?** Adding it to the x230's `tb470-bench.cfg` (or leaving
   it in running-config) would drop every probe run to ~12 s and remove the only config change
   the probe makes. It changes the x230's baseline, so it is his call.
2. Everything in [SESSION-HANDOVER-2026-09-29.md](SESSION-HANDOVER-2026-09-29.md) §5, unchanged:
   the SX-link `apply`, a second host port on the stack (port3.0.9), the seven decision-blocked
   cases, the 22650 / GVRP O-1 defect question, the Modbus case-text update, removing `switch 2
   provision ie520-28` (I-27), and the ignored evidence files (3.3 MB, keep or delete).

## 6. Next steps, in order

1. `/orient-dt` (the probe now takes well under a minute). Expect the one-link MISMATCH until
   the apply.
2. `/test-mode --resume` from queue row 7, as in the 09-29 handover §6 — the list and recipes
   there are unchanged.

## 7. Recipes

**Timing a probe run:** the probe prints its own line, e.g.
`timing: login 5.9 s, commands 26.2 s, revert_close 1.8 s, total 33.9 s`; the same dict is under
`"timing"` in `captures/<stamp>/meta.json`, and `lldp_wait` per console under `"consoles"`.

**Checking a probe change does not alter the output** (what was done this session):

```bash
# offline: re-generate a saved capture and compare with the bench-state it produced
./bench_probe.py generate captures/<stamp> --out /tmp/regen.md --no-prompt
diff <(sed 's/<stamp>/S/g' <bench-state from that run>) <(sed 's/<stamp>/S/g' /tmp/regen.md)
# live: run, then diff the new bench-state.md against the baseline with both stamps masked
```

## 8. Pointers

- Code: [bench-setup/bench_probe.py](../bench-setup/bench_probe.py) — `Probe` (driver),
  `capture()` / `_read_neighbours()` (phases).
- Memory updated: `bench-probe-one-tool` (speed-up section, don't-reintroduce rules).
- Previous handover (campaign detail, recipes): [SESSION-HANDOVER-2026-09-29.md](SESSION-HANDOVER-2026-09-29.md).
