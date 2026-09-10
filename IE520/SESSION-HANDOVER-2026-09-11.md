# SESSION HANDOVER — 2026-09-11 (wrapped via /wrap-dt)

## TL;DR

- **Bench is WHOLE and re-runnable.** DUT stack (u2 m1 + u3 m2) `Normal operation`, both `Ready`,
  member 1 Active Master, virtual MAC `0000.cd37.0d6f`; u4, u5 standalone with the EPSR ring
  **removed**. Inter-switch topology is a **loop-free vlan10 star off stack member 1**. All three
  units flash-boot with a valid `show boot` pointer. Everything Terrence chose to keep is saved
  to startup; nothing is running-only. Topology and addressing: `bench-setup/bench-state.md`
  "Current state — 2026-09-11".
- **AWPTCM T10623 (Stack Fail-over Master) COMPLETE, PASS (functional)** — three measured parts,
  `IE520/ipv4-routing/10623.log`. Headline: `stack virtual-mac` cuts the master-failover outage
  from **23.20 s to 2.08 s**; an OSPF neighbour on a survivor-homed uplink **never lost its
  adjacency** across the failover.
- **This directory became its own git repo today** (`terrenceb-atlnz/device-testing`, `main`, pushed),
  and 27 device-testing memories moved here out of Test-cases (`MEMORY-SPLIT-2026-09-11.md`).
- One OPEN bench-rule question for Terrence (u5's vlan1 subnet, §6). Nothing is parked or shut
  that isn't intended.

## 1. Bench state at wrap, and how to verify it

Measured 2026-09-10 ~23:20 device clock (device clocks run ~UTC-ish; host is NZST 2026-09-11).

```bash
# consoles free?  (fuser on the node is the only reliable answer)
ssh tb470 'fuser -v /dev/u*; pgrep -a -f "ckorient|drv\.py|ping -i|tcpdump" | grep -v pgrep'
# driver scratch (tmpfs; recreate from IE520/stack-tests/2026-09-02-driver-test/console.py if gone)
ssh tb470 'ls /tmp/ckorient/drv.py /tmp/ckorient/console.py'
# stack (either console relays to the master once logged in; backup console has its own login)
ssh tb470 'cd /tmp/ckorient && printf "%s\n" "show stack" "show boot" "show ip ospf neighbor" \
  "show running-config | include virtual-mac|priority|router ospf|network |lldp run" \
  | python3 drv.py /dev/u2 /tmp/ckorient/verify_stack.txt'
# u4 / u5
ssh tb470 'cd /tmp/ckorient && printf "%s\n" "show boot | include image" "show epsr" \
  "show running-config | include epsr|shutdown|router ospf|network " | python3 drv.py /dev/u4 /tmp/ckorient/v_u4.txt'
ssh tb470 'cd /tmp/ckorient && printf "%s\n" "show boot | include image" "show epsr" \
  "show running-config | include epsr|shutdown" | python3 drv.py /dev/u5 /tmp/ckorient/v_u5.txt'
# host
ssh tb470 'for n in eth1 eth2 eth3; do echo $n carrier=$(cat /sys/class/net/$n/carrier); done; ip -br addr | grep eth'
```

Expected: stack `Normal operation`, 1 = Active Master (prio 128), 2 = Backup (prio 2), MAC
`0000.cd37.0d6f (Virtual MAC)`, `flash:/IE520-tb470.rel (file exists)`, OSPF neighbour
`10.10.10.2 Full/Backup vlan10`; u4/u5 `% There were no EPSR instances found`, two `shutdown`
lines each, `(file exists)`; host eth1/2/3 carrier 1 with `.1/27`, `.33/27`, `.65/27`.

**Which member is master moves after every failover and never pre-empts** — with member 2 at
priority 2 it wins the *next election* (a full reboot), not before.

## 2. What was accomplished

1. **T10623 Parts 1, 2, 2b** measured and logged (§3).
2. **Bench boot made safe:** stale `show boot` pointers fixed on the stack (before its reboot) and
   on u4/u5 (at wrap); all three now `(file exists)`.
3. **EPSR ring removed from u4/u5** (Terrence's call) after diagnosing it as a two-transit ring with
   no master; topology reduced to a loop-free star with no storm window; `pre-*.cfg` backups deleted
   from all three units (Terrence: no backups wanted).
4. **bench-state.md "Current state — 2026-09-11"** written from measurement (LLDP both ends for
   inter-switch links; MAC learning for the three testbox edges).
5. **Skills made move-proof:** `orient-dt` got a §0 path table and lost every bench fact (all now
   pointers to bench-state.md); `wrap-dt` renamed/re-pointed and gained the large-file prompt.
   Snapshots `SKILL.md.pre-20260911` in both dirs.
6. **Memory split executed** (27 moved, 12 symlinked back, 13 deleted, 48 untouched; both indexes
   rebuilt; project-slug links repointed) — `MEMORY-SPLIT-2026-09-11.md`.
7. **Repo created**: `git init`, `.gitignore` (framework symlink, `__pycache__`, large/binary
   artefacts by default), five large artefacts deleted first (83 MB GEN3 `.rel`, two tech-support
   `.tgz`, three unreferenced x950 `.stdout`), pushed to `git@github.com:terrenceb-atlnz/device-testing.git`.

## 3. Results — each run labelled

| run | trigger | traffic | OSPF (u4's view) | verdict |
| --- | --- | --- | --- | --- |
| T10623 Part 1 — default config | `reload stack-member 2` (master); host on m1 | **23.20 s** gap (ARP staleness; stack MAC 0780→0ac0) | n/a | **clean** |
| T10623 Part 2 — `stack virtual-mac` | same, after save + full reboot | **2.084 s** gap, 0 DUPs; MAC `0000.cd37.0d6f` held; host ARP never re-resolved | n/a | **clean** |
| T10623 Part 2b (first attempt) | — | — | no adjacency: vlan10 partitioned by a masterless EPSR ring | **confounded** — bench, not product; led to the ring removal |
| T10623 Part 2b — OSPF across failover | `reload stack-member 2` (master) with m1 holding host + vlan10 uplink | **2.051 s** gap | `Full` → `ExStart` at +21.3 s → `Full` at +26.3 s; never Down | **clean** |

The 7 other ipv4-routing cases (7741, 11405, 11402, 11762, 11773, 30403, 18945) were logged PASS
earlier in the same directory; nothing changed for them today.

## 4. Findings

**Measured**
- Without `stack virtual-mac` the SVI MAC is the master's base MAC and changes at failover; the
  host's ARP entry for the gateway goes stale → 23 s outage. With it the MAC is derived from the
  chassis ID (`0000.cd37.0d6f`) and held → ~2 s (VCS promotion time). Needs save + reboot.
- AW+ stack priority: **lowest value wins, and only at an election**; a running master is not
  pre-empted (`reload stack-member <master>` is the way to move mastership without a full reboot).
- OSPF process moves to the new master and re-synchronises inside the dead interval: the
  neighbour saw a ~5 s `ExStart/Exchange` dip ~21 s after the failover, no dead-timer expiry.
- A two-transit EPSR ring with no master never converges; each transit blocks a port and the data
  VLAN partitions. Removal order that works: `epsr configuration` → `epsr <ring> state disabled` →
  `no epsr <ring> datavlan <vid>` → `no epsr <ring>` → `no service epsr` (reboot to complete).
  Break the third edge FIRST (while EPSR still blocks) so there is no loop window.
- Asymmetric LAG (aggregated on u4/u5, not on the stack) forwards but duplicates
  broadcast/multicast (DUP pings); reducing each leg to one active link removed the DUPs.
- `show boot … (file not found)` while running the same-named image occurred on all three units
  (dangling pointers to deleted `tomahawk` / `IE520-20260825` files).
- `no interface vlanN` is refused ("Removal of interface not allowed"); `no vlan N` in `vlan
  database` removes the SVI with the VLAN. `show mac address-table interface <port>` is invalid;
  filter with `| include`.
- Cabling (LLDP both ends + MAC learning) — in bench-state.md.

**Inferred (not measured)**
- Route continuity through the 5 s ExStart window: the adjacency never fell below ExStart so no
  LSDB flush was triggered — but u4's route table was not captured during the window.
- Whether the AW+ `show boot` pointer matters under a bootloader-configured flash default was
  never tested (all pointers were fixed before any reload).

## 5. OPEN

1. **u5 vlan1 subnet vs Terrence's rule** — u5 is cabled to tb eth3 (`.64/27`) but its vlan1 is
   `10.38.215.12/27` (eth1's /27). Reachable today only because vlan1 is bridged across all three
   switches. Terrence to decide; not changed. (bench-state.md, Addressing.)
2. **Generated `​```setup` fences in bench-state.md are still the 2026-09-03 tree.** The bench is now
   whole and cleanly measured, so a rewrite is *possible* — it still needs the framework `.setup`
   schema decisions noted in the 09-09 section (multi-node roles, `[portlink]` for the star). Not
   attempted at wrap.
3. **Test-cases side of the memory split is staged, not committed** (28 D · 12 T · MEMORY.md) — for
   the Ask-CK `/wrap-ck`, which also owns `tool/check_memory_links.py` (assumed one store) and the
   dangling `[[links]]` to the 13 deleted memories.
4. **Files the skills still reach into Test-cases for** (`/orient-dt` §0 ¹): TESTBOX-ACCESS.md,
   TB470-HOST-NETWORKING.md, bench_probe.py, fw_async_test.py / fw_async_chatter.py, CLAUDE.md
   "How we work". Move or symlink into this repo — Terrence's call; `TESTBOX-ACCESS.md:49` and
   `TB470-HOST-NETWORKING.md:14` also still cite `orient-ie520`.
5. **T11427** (PIM-SM full table + multicast failover) — now unblocked by the working vlan10
   transit; not started.

## 6. Next steps, in order

1. `/orient-dt` — verify §1 above matches the hardware (roles may have moved if anyone rebooted).
2. Settle OPEN 1 (u5 vlan1) — one `interface vlan1 / ip address` change + write if Terrence agrees.
3. T11427 on the star: RP on the stack, u4/u5 as PIM neighbours over vlan10; for the failover part
   keep source/receiver/uplinks on member 1 and reload member 2 (set master = member 2 first via
   `reload stack-member 1`, exactly as Part 2b did).
4. When the Ask-CK side has committed the split, decide OPEN 4 and update `/orient-dt` §0 once.

## 7. Recipes

**Console driver on tb470** (tmpfs `/tmp/ckorient/`, recreate if wiped):
`cat IE520/stack-tests/2026-09-02-driver-test/console.py | ssh tb470 'mkdir -p /tmp/ckorient; cat > /tmp/ckorient/console.py'`,
then `drv.py` = the 12-line stdin wrapper (`sys.path.insert(0,"/tmp/ckorient")`, `Console(port,
transcript).login()`, one `c.cmd(line)` per stdin line; `#TO <secs> <cmd>` for a long command).
Never let two processes touch one `/dev/uN`.

**Failover measurement** (both parts of T10623): host `timeout 130 ping -i 0.02 -D <SVI> >
file`; on the neighbour a console loop of `show ip ospf neighbor` printing state changes with
epochs; trigger from the *survivor's* console: `reload stack-member <master>` → `reboot stack
master? (y/n):` → `y\r`; outage = the single gap in the `-D` timestamps > 0.1 s; correlate to the
trigger epoch. The failing master must not carry the host port or the uplink you watch.

**Whole-stack reboot:** `reload` → `Are you sure you want to reboot the whole stack? (y/n):` →
`y\r`; back in ~3.5 min; poll `show stack` for `Operational Status`.

## 8. Pointers

- Bench facts: `bench-setup/bench-state.md` (2026-09-11 section; archived prior version in
  `bench-setup/backups/`).
- Results: `IE520/ipv4-routing/10623.log` (+ the 7 sibling logs).
- Split record: `MEMORY-SPLIT-2026-09-11.md`; Ask-CK's inventory: `claude/Test-cases/MEMORY-SPLIT-INVENTORY.md`.
- Skills: `.claude/skills/orient-dt/SKILL.md` (§0 = where everything lives), `.claude/skills/wrap-dt/SKILL.md`.
- Previous handover (EPSR-ring era, now superseded): `IE520/SESSION-HANDOVER-2026-09-09.md`.
