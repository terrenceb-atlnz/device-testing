# SESSION HANDOVER — 2026-09-15 (wrapped via /wrap-dt)

## TL;DR

- **Bench is WHOLE and re-runnable.** Single **4-member IE520 VCStack**, `Normal operation`, all
  `Ready`, virtual MAC `0000.cd37.0d6f`, running `awplus_main-20260913-1734` (flash boot). **Active
  Master = member 4** (on `/dev/u4`). Full layout: `bench-setup/bench-state.md` "Current state —
  2026-09-15" (written this session from a `bench_probe.py` sweep). A standalone **x230-52GT V2** sits
  on `/dev/u6` (separate device, not L3-joined); `/dev/u0`,`/dev/u1` powered off.
- **This was NOT a test campaign.** Three things happened: (1) Terrence flashed all four members with
  the new build, re-formed the 4-stack, and set flash boot (I only flashed the *master* earlier; the
  members were Terrence's); (2) I **reworked `bench_probe.py`** into a standalone, deterministic
  bench source-of-truth and placed it in the repo; (3) I updated the records from it.
- **⚠️ Dangling boot pointer** on the stack: `show boot` → `Current boot image : flash:/IE520-tb470.rel
  (file not found)` while running/flashed image is `IE520-awplus_main-20260913-1734.rel` (old filename
  removed at flash time). Boots fine via the bootloader; repoint AW+ with `boot system
  flash:/IE520-awplus_main-20260913-1734.rel` + `write` when convenient so `show boot` reads `(file
  exists)`. Not fixed this session (Terrence is managing the flashing).
- Nothing of mine left running; no DUT/host config changed by me (all reads + file copies).
  eth3 is currently carrier-down (Terrence's cabling in flux).

## 1. Bench state at wrap, and how to verify it

Measured 2026-09-15 ~08:2x UTC. **The console↔unit map shifts** (ttyUSB enumeration changed again this
session) — always re-derive; the probe does this for you.

```bash
sock=/run/user/1971/keyring/ssh
# consoles free? (fuser on the node is the only reliable answer)
SSH_AUTH_SOCK=$sock ssh tb470 'fuser -v /dev/u*'
# THE authoritative read: sweep all consoles, identity re-derived from each unit's own output
SSH_AUTH_SOCK=$sock ssh tb470 'cd /home/terrenceb/claude/device-testing/bench-setup && \
  python3 bench_probe.py --consoles 0-6 --json /tmp/ckorient/probe.json'
# host
SSH_AUTH_SOCK=$sock ssh tb470 'for n in eth1 eth2 eth3; do echo $n=$(cat /sys/class/net/$n/carrier); done; ip -br addr | grep -E "^eth[123] "'
```

Expected (2026-09-15): u2=`awplus-1`(member1), u3=`awplus-2`(member2, prio 2), u4=`awplus`(member4=
**master**), u5=`awplus-3`(member3); u6=`lp-AT-x230-52GT-V2`; u0/u1 no response. Stack `Normal
operation`, VMAC `0000.cd37.0d6f`, all on `awplus_main-20260913-1734`, ring 1—2—4—3—1. `show boot`
still `(file not found)` until the pointer is repointed. Host eth1/eth2 up (`.1`/`.33`), **eth3 down**.

## 2. What was accomplished

1. **`bench_probe.py` reworked into the bench source of truth** — `bench-setup/bench_probe.py` (new).
   Standalone: no framework, no `tb470.setup`, no bench-state.md dependency (only pyserial). Sweeps
   `/dev/u0`–`u6` identically every run; fuser-guards each console; auto-detects baud (115200→9600);
   forces the login banner to identify the physical unit; logs in (manager/friend, enable to `#`,
   refuses a forced-password dialog); runs one FIXED 28-command read-only set; emits JSON + a summary.
   Records absent/busy/powered-off consoles instead of guessing. Tested end-to-end; runs from its repo
   path on tb470.
2. **Stray-script hook fixed** (Terrence approved): added `claude/device-testing` to `ALLOWED_REPOS`
   in `~/.claude/hooks/no-stray-py.py` — it was stale (device-testing became a repo 2026-09-11), which
   had blocked placing any `.py` here.
3. **bench-state.md updated twice from ground truth**: a 2026-09-14 section (the first 4-stack, from
   console reads) and the current **2026-09-15** section (from the `bench_probe.py` sweep). Applier
   archived the superseded record (`backups/2026-09-14T203049Z.bench-state.md`).
4. **Master flashed earlier this session** with `IE520-awplus_main-20260913-1734.rel` (local TFTP);
   members 1/3/4 were flashed by Terrence afterwards.
5. **Memory corrected**: `ie520-4stack-flashprep` (the old "2-member cap" is now flagged as an
   OLD-build limit the new build lifted; plus how to flash members) + its `MEMORY.md` index line.

## 3. Results

No pass/fail test cases this session. The one operational task — get the new `.rel` onto every unit —
outcome: **master flashed by me; members 1/3/4 flashed by Terrence**; all four now run
`awplus_main-20260913-1734`.

## 4. Findings

**Measured (this build, `awplus_main-20260913-1734`; durable — also in `ie520-4stack-flashprep`):**
- A large (~40 MB) file can be written to a member's flash **only while that member is the master**
  (local TFTP). For a non-master member: `copy flash:/F awplus-N/flash:F` (flash-to-flash push) and
  `copy tftp:… awplus-N/flash:…` both fail — `nfs: server 192.168.255.N not responding, timed out` →
  `% Input/Output error due to external media removal`. **SMALL** cross-member writes succeed, and ICMP
  to `192.168.255.N` is clean; only the large transfer stalls. The only proven large cross-member copy
  is a **pull** (member→master), never a large push.
- `remote-login N` then `copy tftp:` is refused: `% Copying to/from remote file systems is only
  supported from the stack master`.
- AW+ refuses to overwrite or delete the file set as the current boot image; `boot system tftp://…` is
  rejected (`% Invalid format for file URL`). Stage a new release under a dated name.
- Cross-member path syntax for small files is `awplus-N/flash:<file>` (**no slash** after `flash:`).
- The console→unit and `/dev/uN`→ttyUSB maps both shift across restacks — trust neither; sweep.

**Inferred:** none load-bearing.

## 5. OPEN

1. **Dangling AW+ boot pointer** on the stack (`flash:/IE520-tb470.rel (file not found)`). Repoint to
   `flash:/IE520-awplus_main-20260913-1734.rel` + `write` so a reload never depends on a missing file.
2. **The `​```setup` fences in bench-state.md are still the 2026-09-03 2-stack tree.** The bench is now
   whole and cleanly measured, so a rewrite is *possible* — but the framework `.setup` schema for a
   4-member stack (+ the x230, + host edges) needs deciding first. Not attempted; fences flagged stale.
3. **`bench_probe.py` enhancements** (both natural additions): per-member flash *contents* — relayed
   stack consoles only show the master's flash, so add `dir awplus-N/flash:` per member; and the
   **host-NIC↔switch-port** map — needs host-side MAC learning (a ping out each ethN + `show mac
   address-table | include <ethN MAC>`), which the probe does not yet do.
4. **`/orient-dt` §0** bench_probe.py pointer updated this session to the new repo path; the old
   Test-cases framework-driver `bench_probe.py` still exists there (different tool) — confirm which is
   canonical for which purpose.
5. **Version-control the raw probe JSON?** (~1.1 MB/run.) Terrence to decide whether a canonical
   capture lives alongside bench-state.md.
6. Two shared memory files (`legacy-scripts-vs-framework.md`, `no-stray-scripts.md`) carry another
   session's uncommitted 2026-09-14 edits — left untouched, NOT in this session's commit.

## 6. Next steps, in order

1. `/orient-dt` — it will sweep the hardware (master is member 4 now; map shifts).
2. Repoint the boot pointer (OPEN 1) if a clean `show boot` is wanted before any reload.
3. Add the two `bench_probe.py` enhancements (OPEN 3) if the probe is to be the *complete* source.
4. When ready, rewrite the `.setup` fences for the 4-stack (OPEN 2) — from a whole, measured bench.

## 7. Recipes

**Run the bench probe (the source of truth):**
```bash
SSH_AUTH_SOCK=/run/user/1971/keyring/ssh ssh tb470 \
  'cd /home/terrenceb/claude/device-testing/bench-setup && python3 bench_probe.py --consoles 0-6 --json /tmp/ckorient/probe.json'
# summary prints to stderr; full JSON to the --json path. --consoles accepts 0-6 or 2,3,4,5.
```
Runs on tb470 (consoles local), needs no sudo, depends only on pyserial (3.5 present).

**Flash a member on this build** (large cross-member write is broken): make that member the master
(set its `stack priority` lowest + `reload` the current master), then TFTP locally from `10.38.215.1`
(reachable from any master), then restore master = member with lowest priority. Small files can be
pushed cross-member with `copy flash:/F awplus-N/flash:F` (no slash).

**tb470 driver scratch** (`/tmp/ckorient/`, tmpfs — recreate if wiped): `console.py` + `drv.py` from
the maintained copy in `/orient-dt` §0; `bench_probe.py` is now a repo tool, run from its repo path.

## 8. Pointers

- Bench facts: `bench-setup/bench-state.md` "Current state — 2026-09-15" (prior archived
  `bench-setup/backups/2026-09-14T203049Z.bench-state.md`).
- The probe: `bench-setup/bench_probe.py`.
- Firmware/flashing lessons: `.claude/memory/ie520-4stack-flashprep.md`.
- Previous handover: `IE520/SESSION-HANDOVER-2026-09-11.md`.
