# SESSION HANDOVER — 2026-09-11 (PAUSED, not wrapped)

Terrence paused this session mid-flow: "pause this, leave a note. we will wrap it in the next
session." So this is a **pause note**, not a `/wrap-dt` close-out — nothing on the bench has been
restored or torn down, and the FINAL bench-state ground-truth pass has NOT been done. Run
`/orient-dt` next session, then finish with `/wrap-dt`.

## 1. What got done (deliverables)

- **AWPTCM T10623 (Stack Fail-over Master) — COMPLETE, PASS (functional).**
  `IE520/ipv4-routing/10623.log`. Three parts, all measured:
  - Part 1, default config: master reload → stack MAC follows the master → **23.20 s** L2 outage
    (host ARP staleness).
  - Part 2, `stack virtual-mac` (vMAC `0000.cd37.0d6f`): MAC held across the failover → **2.08 s**.
  - Part 2b, OSPF across the failover: traffic **2.05 s** again; u4's adjacency never dropped —
    `Full → ExStart (+21 s) → Full (+26 s)`, no dead-timer expiry. Route table during the 5 s
    ExStart window was NOT captured (noted in the log as inferred).
- The other 7 ipv4-routing cases from this batch were already logged earlier (7741, 11405, 11402,
  11762, 11773, 30403, 18945 — all PASS) in the same directory.
- **Bench topology recorded** in `bench-setup/bench-state.md` → "Current state — 2026-09-11"
  (prose only; the generated ```setup fences are still the stale 2026-09-03 tree).
- Memory written: `tb470-ie520-flash-boot-reboots-ok` (flash boot + the stale boot-pointer gotcha).
- Started (NOT executed) the memory / repo split — see §4.

## 2. Bench state AS LEFT (not restored — /wrap-dt must decide keep vs revert)

Measured at pause time (~22:35 device clock); re-verify with `show stack` before trusting.

- **DUT stack u2(m1)/u3(m2):** member 1 = Active Master, member 2 was rebooting/rejoining after
  the Part 2b `reload stack-member 2` (a rejoin poller was stopped at pause; confirm
  `Operational Status Normal operation` and both `Ready`).
  - RUNNING + SAVED to startup (`flash:/default.cfg`): `stack virtual-mac`, `stack 2 priority 2`,
    `boot system flash:/IE520-tb470.rel` (the boot pointer was stale → fixed), `lldp run`.
  - RUNNING ONLY (startup still has the OLD vlan210 version): `router ospf 1` with
    `network 10.10.10.0/27 area 0` + `network 10.38.215.0/27 area 0`; the dead `interface vlan210`
    SVI 10.10.210.1/30 still exists. **A full stack reload reverts OSPF to vlan210 — decide:
    save or remove.**
  - `service epsr` present but no ring — inert.
- **u4 (standalone):** EPSR **removed** (`no epsr ring1`, `no service epsr` pending reboot),
  `interface sa3` + `port1.0.23` **shutdown**, `service ospf` + `router ospf 1` (router-id
  10.10.10.2, network 10.10.10.0/27 area 0), `lldp run`. **ALL SAVED to startup.**
- **u5 (standalone):** EPSR removed, `interface sa3` + `port2.0.23` shutdown, `lldp run`.
  **SAVED to startup.** No OSPF on u5.
- **Resulting topology:** loop-free vlan10 (10.10.10.0/27) star off stack **member 1**:
  `stack 1.0.26 ↔ u4 1.0.25` and `stack 1.0.25 ↔ u5 2.0.25`; the u4↔u5 edge (sa3/sa3) and the
  member-2 legs (u4 1.0.23, u5 2.0.23) are admin-shut. Cabling is LLDP-confirmed both ends and
  written in bench-state.md.
- **vlan1 SVIs untouched** (Terrence's rule): stack 10.38.215.10/27, u5 .12/27, u4 .36/27.
- **Host tb470:** nothing persistent changed. `/tmp/ckorient/` (tmpfs, wipes on reboot) holds
  `drv.py` + a local copy of `console.py` (see §5) and all console transcripts from today.

## 3. Open / pending for next session

1. **/wrap-dt** proper: ground-truth the bench, decide what of §2 stays (candidates to KEEP:
   virtual-mac, flash boot pointer, EPSR removal + star; candidates to REMOVE: OSPF scaffolding on
   stack + u4, the dead vlan210 SVI, `lldp run` if unwanted), then update bench-state.md's
   current-state section and consider finally rewriting the stale ```setup fences.
2. **T11427** (PIM-SM full table + multicast failover) — now unblocked by the working vlan10
   transit; not started.
3. `MEMORY-SPLIT-PROPOSAL.md` + repo init — waiting on Terrence (§4).

## 4. The memory / repo split (Terrence's ask, NOT executed)

Terrence wants device-testing's memories moved *physically* out of
`claude/Test-cases/.claude/memory/` into this project, and `claude/device-testing/` turned into
its own git repo. He is checking with a session in the Test-cases repo and will return a list of
which memories that side does NOT need (move outright) and which it wants to keep a symlink to.
**Do not move anything until that list arrives.**

- Proposal (20 DT / 13 BOTH / 55 CK) for them to annotate: `MEMORY-SPLIT-PROPOSAL.md` (repo root).
- Facts found: all 89 memory files are **tracked in Test-cases git**, so the move is a `git mv`/
  `git rm` commit on the Test-cases side. Two project slugs symlink `memory` → Test-cases:
  `~/.claude/projects/-media-terrenceb-mnt-testbox-home/memory` (the lab home — should re-point to
  device-testing after the split) and `…-claude-Test-cases/memory` (stays).
- Repo readiness: 364 MB, no `.git`/`.gitignore`, `.github/` empty. Five files >20 MB under
  `old test runs/` (83 MB `.rel`, two 31 MB tech-support `.tgz`, two ~30 MB `.stdout`) → LFS or
  gitignore. `framework -> /home/st-art/framework` (read-only, not ours) must be gitignored.
  `git init` not run — wait for Terrence's go.

## 5. Gotchas learned today (candidates for /orient-dt or memory at wrap)

- **The lab tree moved mid-session**: `old test runs/` and `claude/IE520-testing/` were relocated
  under `claude/device-testing/`. Nothing lost. `drv.py`'s hardcoded NFS path broke; fixed by copying
  `console.py` into `/tmp/ckorient/` and importing from there. If tmpfs is wiped, recreate both
  (`console.py` source: `IE520/stack-tests/2026-09-02-driver-test/console.py`).
- **Backup-member console needs a login** (`awplus-2 login:`); console.py's `login()` handles it
  only from a clean prompt — if it fails with `Password:` in the tail, the port was mid-dialog;
  send a CR and retry.
- **`boot system` on a stack syncs the 40 MB image to the other member** — console dark ~10 min
  (SPIFlash). Wait it out.
- **EPSR removal order that works on this build:** `epsr configuration` → `epsr <ring> state
  disabled` → `no epsr <ring> datavlan <vid>` → `no epsr <ring>`; then `no service epsr`
  (reboot to take effect). Plain `no epsr <ring>` alone leaves the mode/datavlan lines.
- **Break the loop BEFORE removing a ring**: shut the third edge while EPSR still blocks, so there
  is no storm window. Asymmetric LAG (aggregated one end, not the other) produces DUP pings —
  reduce to a single link.
- **AW+ stack priority**: LOWEST value wins master; only decides at boot / next election, a
  running master is not preempted.
