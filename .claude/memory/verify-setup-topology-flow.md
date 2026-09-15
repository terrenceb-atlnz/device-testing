---
name: verify-setup-topology-flow
description: "bench_topology.py = the verify-setup flow: probe→live physical-topology .md, semantic diff vs an IMMUTABLE .setup template; tri-state gate; multi-stack aware"
metadata:
  node_type: memory
  type: project
  originSessionId: aa8b636c-a8ac-4c70-bfc5-0e9663aa981b
  modified: 2026-09-15T01:00:00.000Z
---

Terrence, 2026-09-15: building a **"verify setup"** flow so a bench can be checked against
pre-filled `.setup` templates before a test suite runs, and reused across benches.
`bench-setup/bench_topology.py` (commit `d0dc610`) is the prototype; validated against real
sweeps this session but not yet wired to a button or to auto-deploy.

**The pipeline** (steps of the intended button flow):
1. `bench_probe.py` sweeps the bench — the SOLE hardware parser (parse once; downstream reads
   fields, never re-parses console text).
2. `bench_topology.py generate <probe.json>` → a live **physical-topology** `.md`: the
   `​```setup` fences (deployable) **+ a `​```nic-state` block** (host NIC carrier / learned-port;
   read by the diff, NOT deployed — `bench_setup.py` only extracts `​```setup` fences).
3. `bench_topology.py diff <live> <template>` → semantic `.setup`-vs-`.setup` compare
   (ignores `###` comments, ordering, comma-list order; either side may be a `.md`).
4. If clean, the accepted `.md` renders to `tbXXX.setup` via `bench_setup.py apply` (existing).

**Design decisions (Terrence):**
- **Physical state + `.rel` age ONLY.** The test suite supplies device configs; the diff never
  touches VLAN/SVI/routing. `.rel` staleness is an *advisory* (build date is in the name; ≥48h
  warns), never a diff field — the template must NOT pin a `.rel` date.
- **The template is an IMMUTABLE, server-side `.setup`**, used only for the diff — never written
  to `tbXXX.setup` (its comments and served location differ). It MAY carry `###` annotations.
- **Stacking-ring gap ACCEPTED** 2026-09-15: `.setup` can't express the 27/28 ring, so a single
  missing *stack* cable that leaves membership intact won't be caught. Risk knowingly ignored.
- **Tri-state gate via exit code**: `0` MATCH / `1` MISMATCH (block) / `2` NEEDS-CHECK (human).
  Labels — MISMATCH: `MOVED` (NIC on a different switch port; collapses missing+extra into one),
  `CHANGED`, `MISSING_IN_LIVE`, `EXTRA_IN_LIVE`. NEEDS-CHECK: `LINK_DOWN` (host NIC no carrier →
  check cable/SFP/far-end), `CHECK_CABLE` (NIC has link but MAC unlearned → likely mis-cabled).
- **Multi-stack aware**: `swi_*` is keyed by GLOBAL member ID, so a split bench reads cleanly as
  "stk_a shrank, stk_b appeared" instead of noise. Consoles unchanged stay silent.

**Why:** end goal = a fixed set of physical bench permutations, each with an authored `.setup`
template; tests build/tear down device configs digitally on top of a known physical topology. So
the tool only needs the physical topology to diff against.

**How to apply:** keep `bench_probe.py` the ONLY thing that parses console text. **Pending work:**
the static scaffold (PDU outlets / `ck_cap_*` / profile / baud) is HARDCODED per-bench inside
`bench_topology.py` — externalize to a per-testbox config when generalizing; and wire the flow to
the "verify setup" button + auto-`apply`-on-clean (step 7, not built). The `.rel` staleness check
could also compare against latest-on-TFTP ("N builds behind"), not just age. Related:
[[setup-file-declares-topology]], [[tb470-topology-and-setup]].
