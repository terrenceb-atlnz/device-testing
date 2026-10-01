---
name: bench-probe-one-tool
description: "bench-setup/bench_probe.py is THE bench-state tool since 2026-09-25: run it ON tb470 = capture 7 show commands per console -> bench-state.md (generated, no prose; its ```setup fence IS tb470.setup) -> semantic diff vs the deployed .setup; `apply` writes it. swi_ names and PDU outlets follow the SERIAL in tb470.static. Replaces bench_setup.py and bench_topology.py."
metadata:
  node_type: memory
  type: project
  originSessionId: 41cd590a-840f-44c2-ac1d-f420ac15666e
  modified: 2026-09-28T00:00:00.000Z
---

**Terrence, 2026-09-25:** "consolidate scripts down to one, that reads the output and makes the
bench-state.md file (formatted identically to the .setup) and then you can diff them."
Built the same day as `claude/device-testing/bench-setup/bench_probe.py` (the name is fixed:
Test-cases' `ask-ck/functions/test-composer/bench_probe.md` points at that path).

**The pipeline** (`./bench_probe.py run`, ON tb470, ~15 s for six consoles since 2026-09-30, up to ~40 s when it must switch LLDP on; was ~2 min):
1. **capture** — every `/dev/uN` at once over pyserial: baud detect (115200, then 9600), login
   banner (which member this console is), login, then 7 fixed commands: `show system`, `show
   stack`, `show boot`, `show interface status`, `show lldp neighbors`, `show mac address-table`,
   `show running-config`. Raw text saved under `bench-setup/captures/<UTC stamp>/` (gitignored).
2. **generate** — offline parse into `bench-state.md`: device table, links, advisories, ONE
   ```setup fence. `generate <capture-dir>` re-parses without the bench.
3. **diff** — semantic compare of that fence against the deployed
   `/home/st-art/st-art/configs/tb470.setup` (comments/order ignored; pair links canonicalised).
   Exit 0 MATCH / 1 MISMATCH / 2 NEEDS-CHECK (carrier down, MAC not learned, console busy/down).
4. **apply** — writes the fence to the box: snapshot pair → `backups/<stamp>.*`, readback verify,
   refresh `tb470.setup.current` (read by Test-cases' `pt_preflight.py`). Refuses over a hand-edit.

**Decisions (Terrence, 2026-09-25):**
- Facts no `show` command reveals — swi_ name per serial, PDU IP and outlet — are a one-time
  user entry in `bench-setup/tb470.static`. "We re-hash this every time, and that's an acceptable
  loss." The probe asks on a terminal when it meets an unlisted unit; without one it names the
  unit for the run and says so.
- LLDP proves switch-to-switch cabling: a device with `lldp run` OFF gets it switched on
  (verified by re-reading the running-config). **Changed 2026-09-30 (Terrence): it is LEFT ON**
  — "the first run of a probe on the bench should apply lldp run, and we shouldnt remove it";
  later runs find it on and skip the LLDP wait. Running-config only (never `write`n), so a reboot
  or the framework's post-failure PDU cycle drops it and the next probe re-applies it.
- Keep `apply` for now ("we currently can make use of both"); in future only the diff-check.
  **Applied 2026-09-28** (Terrence: "execute those things"): the deployed `.setup` is now the
  generated 1166-byte fence — no `###` prose; the 22 KB commented file is in
  `backups/2026-09-27T190048Z.tb470.setup`. Framework `LoadSetup` parses it.
- **No prose in bench-state.md.** Run-to-run variance made the "last test" notes mislead more
  than help. Mechanics → orient-dt; cross-session lessons → memories; what a session did → its
  handover.

**Why:** `bench_setup.py check` compared two TEXT FILES (render vs deployed `.setup`) and said IN
SYNC while Terrence's ART run had wiped every device config; `bench_probe.py` (28 commands, JSON
thrown away) and `bench_topology.py` (stale hardcoded scaffold, mis-modelled the standalone SA)
never joined up. One measured pipeline replaces all three.

**How to apply:**
- Run it at every orient and wrap. Never edit bench-state.md by hand — it is overwritten.
- A capture taken while the probe had enabled LLDP includes the temporary `lldp run` line in
  that console's saved running-config (the md says so in Advisories).
- A new unit → add its serial to `tb470.static` (name, outlet) or answer the prompt.
- MATCH ≠ healthy: it means the bench IS the template. Read the Advisories block too.
- A `login_failed` on a console whose banner reads fine is a DRIVER suspect first: until
  2026-09-28 the x230 (9600) failed every run with correct creds because login waited on quiet,
  not on the prompt (fixed: `Probe._expect()`; mechanics in orient-dt §3). Byte-log the
  dialog before doubting the password.

**Speed-up, 2026-09-30** (Terrence: "2 minutes is really silly"). Measured ~110 s: a fixed 35 s
LLDP sleep, 0.8 s quiet-gap endings (1.6 s at 9600) on every read, and the LLDP check run one
console at a time. Now 19–36 s with byte-identical bench-state.md. Reads end on the device's own
prompt after the echo (`Probe._cmd`); the stack's first console alone runs the list; the last
capture's baud is tried first. **Don't bring back a fixed LLDP sleep, and don't read neighbour
tables before every device has finished its LLDP check.** The first rewrite did that: the stack
read its table before the x230 (9600, LLDP off) had switched LLDP on, and two links degraded to
`lldp one end`. The fix is a barrier plus `_read_neighbours()`: EVERY device polls until it sees
its last-run ports and every port a neighbour sees it on. The 7–26 s that remains is the
neighbours' 30 s LLDP send interval, paid only on a run that has to switch LLDP on. Runs that find
it on take ~15 s.

**On a SHARED testbox (not tb470):** run the no-console occupancy check first and probe only the
free consoles with `--read-only` (no `lldp run`, no host pings); without sudo its busy test misses `sudo minicom` holders — [[shared-testbox-console-occupancy]].

Related: [[tb470-topology-and-setup]], [[setup-file-declares-topology]],
[[testbox-console-access]], [[tb470-reboot-nfshome-unmounted]], [[shared-testbox-console-occupancy]].
