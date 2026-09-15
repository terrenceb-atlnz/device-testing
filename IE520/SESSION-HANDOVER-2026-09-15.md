# SESSION HANDOVER — 2026-09-15 (wrapped via /wrap-dt)

> Rewritten at the second wrap of 2026-09-15 to cover the whole day: the earlier version (flashing
> + probe rework) is superseded and lives in git history. This session ran **no test campaign** —
> it was firmware records + **tooling**: `bench_probe.py` v2, the 4-member `.setup` rewrite, and a
> new **verify-setup** tool (`bench_topology.py`). No DUT or host config was changed by me; all
> hardware access was **read-only** probe sweeps.

## TL;DR

- **⚠️ The LIVE bench is intentionally SPLIT** into **two independent 2-member VCStacks** — Terrence's
  test of the new verify-setup tooling, NOT a fault:
  - **stack A** = member 1 (`264A23061`, `/dev/u2`, backup) + member 2 (`264A23068`, `/dev/u3`,
    **master**); members 3 & 4 read `Provisioned`.
  - **stack B** = member 3 (`264A23066`, `/dev/u5`, **master**) + member 4 (`264A23052`, `/dev/u4`,
    backup); members 1 & 2 read `Provisioned`.
  - Both halves share VMAC `0000.cd37.0d6f` (split-brain — cosmetic while L2-isolated; don't bridge
    them). All four run `awplus_main-20260913-1734`, flash boot. Host cables MOVED: `eth1`→m3
    `port3.0.2`, `eth2`→m2 `port2.0.2`; `eth3` carrier-down. `/dev/u6` = standalone x230-52GT V2;
    `/dev/u0`,`/dev/u1` powered off.
- **The RECORD and the deployed `tb470.setup` are still the 4-member stack** (the *intended* bench).
  bench-state.md carries the split as a dated ⚠️ note at the top of "Current state — 2026-09-15" but
  the ```setup fences were NOT rewritten from a split (wrap rule). **Terrence to reconverge the ring
  or settle a final topology**; then a fresh probe→`bench_topology.py` should read MATCH again.
- **Main deliverable: the verify-setup loop** — `bench-setup/bench_topology.py` (commit `d0dc610`):
  `generate` a live physical-topology `.md` from a probe, `diff` it against an immutable `.setup`
  template. Validated live across single-stack (MATCH), split (2× MOVED + stack diffs), and
  down/mis-cabled NICs (LINK_DOWN / CHECK_CABLE). See `[[verify-setup-topology-flow]]` memory.

## 1. Bench state at wrap, and how to verify it

Measured 2026-09-15 ~01:3x UTC. **The console↔unit map shifts every restack — always re-derive; the
probe does it for you.**

```bash
sock=/run/user/1971/keyring/ssh
# consoles free? (fuser on the node is the only reliable answer)
SSH_AUTH_SOCK=$sock ssh tb470 'fuser -v /dev/u*'
# THE authoritative read: sweep all consoles, identity re-derived from each unit's own output.
# stdout-only now: JSON to stdout (no --json flag), summary to stderr.
SSH_AUTH_SOCK=$sock ssh tb470 'cd /home/terrenceb/claude/device-testing/bench-setup && \
  python3 bench_probe.py --consoles 0-6' > /tmp/probe.json
# host NICs
SSH_AUTH_SOCK=$sock ssh tb470 'for n in eth1 eth2 eth3; do echo $n=$(cat /sys/class/net/$n/carrier); done'
```

Expected at wrap: u2=`awplus-1`(m1), u3=`awplus`(m2=**stackA master**), u4=`awplus-4`(m4), u5=`awplus`
(m3=**stackB master**), u6=x230; u0/u1 no response. Two stacks, each `Normal operation` for its own
pair. Host eth1(.1)/eth2(.33) up, **eth3(.65) down**. `show boot` still reads `(file not found)` — a
non-issue: the bootloader overrides the AW+ pointer (see bench-state.md / the boot-field note).

## 2. What was accomplished

1. **`bench_probe.py` v2** (`bench-setup/bench_probe.py`, commit `d22075a`) — the standalone bench
   source-of-truth gained: per-member flash (`dir awplus-N/flash:`), a host-NIC→switch-port map
   (ping + filtered `show mac address-table`), **stdout-only** output (no `--json`), and a fix so the
   per-console stack role reads the connected unit's role, not the first `show stack` row.
2. **bench-state.md + `.setup` rewritten for the 4-member stack** (commit `d22075a`) — the boot field
   reframed as bootloader-overridden (not an action item), host edges + per-member flash recorded,
   and the ```setup fences rewritten from the 2026-09-03 2-member tree to the 4-member stack, then
   `apply`-ed (verified IN SYNC; superseded pair archived).
3. **`bench_topology.py`** (`bench-setup/bench_topology.py`, commit `d0dc610`) — the verify-setup
   loop (details in TL;DR and `[[verify-setup-topology-flow]]`).
4. **Records**: memory `verify-setup-topology-flow` + index; `orient-dt` §0 pointers for the probe
   (stdout-only) and `bench_topology.py`.

## 3. Results

No pass/fail test cases. Tooling validated (not a DUT verdict): `bench_topology.py diff` returns
`0` MATCH / `1` MISMATCH / `2` NEEDS-CHECK; confirmed on the live single-stack (MATCH), the live
split (2× MOVED + `stk_a` CHANGED + `stk_b` EXTRA), and synthetic LINK_DOWN / CHECK_CABLE / mutation
cases.

## 4. Findings

**Measured (this build, `awplus_main-20260913-1734`):**
- A **VCStack split leaves both halves sharing the original VMAC** (`0000.cd37.0d6f`) and each half
  provisions the absent members — the classic phantom-member state, now seen on a 4→2+2 split. Both
  halves report `Normal operation` for their own pair, so the split is *stable*, not transient at
  the AW+ level (it persists until the ring is recabled).
- The **stack master is not pinned** here: member 2 is priority 2 (lowest) and won mastership of
  stack A; a failover earlier in the day had already moved the 4-member master from m4 to m2. Read
  `show stack` every time.
- All four members hold exactly `IE520-awplus_main-20260913-1734.rel` (40052759 B) — fleet-uniform,
  no intra-stack build mismatch.

**Inferred:** none load-bearing.

## 5. OPEN

1. **The bench is left SPLIT (2×2), intentionally.** Reconverge to the 4-member ring (recable the
   27/28 stackports) or decide the split is the new intended bench. Until then the deployed
   `tb470.setup` (4-member) does not match live — by design.
2. **`bench_topology.py` is a prototype**, not yet wired to the "verify setup" button or to
   auto-`bench_setup.py apply`-on-clean (step 7 of the intended flow). The static scaffold (PDU
   outlets / `ck_cap_*` / profile / baud) is **hardcoded per-bench** in the tool — externalize to a
   per-testbox config when generalizing to other benches.
3. **Stacking-ring gap** knowingly accepted: `.setup` can't express the 27/28 ring, so a single
   missing *stack* cable that leaves membership intact won't be caught by the diff.
4. **AW+ `show boot` dangling pointer** (`flash:/IE520-tb470.rel (file not found)`) — ruled a
   non-issue 2026-09-15 (bootloader overrides it); read the build from `show system`, not `show boot`.

## 6. Next steps, in order

1. `/orient-dt` — it will sweep the hardware; expect the **split** until Terrence reconverges.
2. If reconverging: recable the ring, re-probe, `bench_topology.py generate | diff` against the
   4-member `.setup` to confirm MATCH, then (only from a whole, measured bench) trust the fences.
3. If the split (or another shape) becomes the intended bench: author its `.setup` template and,
   from a whole measured bench, rewrite the fences + `apply`.
4. Wire `bench_topology.py` to the button + auto-apply-on-clean; externalize the static scaffold.

## 7. Recipes

**Run the bench probe (the source of truth):**
```bash
SSH_AUTH_SOCK=/run/user/1971/keyring/ssh ssh tb470 \
  'cd /home/terrenceb/claude/device-testing/bench-setup && python3 bench_probe.py --consoles 0-6' > /tmp/probe.json
# summary -> stderr; full JSON -> stdout (no --json flag). --consoles accepts 0-6 or 2,3,4,5.
```

**Verify-setup loop (physical topology vs a template):**
```bash
cd .../claude/device-testing/bench-setup      # tools are here; run on the dev host
python3 bench_topology.py generate /tmp/probe.json > /tmp/live.md
python3 bench_topology.py diff /tmp/live.md <template.setup>   # exit 0 MATCH / 1 MISMATCH / 2 NEEDS-CHECK
# either side may be a .md (fences extracted) or a raw .setup; comment/order-insensitive.
```

**tb470 driver scratch** (`/tmp/ckorient/`, tmpfs — recreate if wiped): `console.py` + `drv.py` from
the maintained copy in `/orient-dt` §0. `bench_probe.py` and `bench_topology.py` are repo tools.

## 8. Pointers

- Bench facts: `bench-setup/bench-state.md` "Current state — 2026-09-15" (split note at top;
  superseded records dated in `bench-setup/backups/`).
- Probe: `bench-setup/bench_probe.py`. Verify-setup: `bench-setup/bench_topology.py`.
- Verify-setup design/state: `.claude/memory/verify-setup-topology-flow.md`.
- Commits this session: `e510cf5`, `d22075a` (probe v2 + 4-member rewrite), `d0dc610`
  (bench_topology.py) — all committed, **not pushed** (push is Terrence's).
- Previous handover shape: `IE520/SESSION-HANDOVER-2026-09-11.md`.
