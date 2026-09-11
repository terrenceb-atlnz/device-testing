# SESSION HANDOVER — 2026-09-11

> **This file now holds TWO sessions from 2026-09-11.** SESSION 2 (T11427) is immediately below;
> the original SESSION 1 (T10623, repo creation, memory split) follows it unchanged, starting at
> its own `# SESSION HANDOVER — 2026-09-11 (wrapped via /wrap-dt)` heading.

---

# SESSION 2 — 2026-09-11 · AWPTCM T11427 (wrapped via /wrap-dt)

## TL;DR (session 2)

- **Bench is WHOLE and re-runnable, restored to the SESSION-1 baseline.** T11427 reconfigured the
  fabric (PIM-SM + 300 routes), measured two master failovers, then **rebooted the stack + u4 from
  their unsaved startup configs** to return to exactly the 2026-09-11 star baseline. u5 untouched.
  Verified: no PIM, no test VLANs, port1.0.2 back to access vlan1, u4 FIB back to 1, OSPF Full
  stack↔u4, all `show boot` `(file exists)`, host NICs clean.
- **AWPTCM T11427 (PIM-SM, full routing table, multicast failovers) COMPLETE, PASS (functional)** —
  `IE520/ipv4-routing/11427.log`. Multicast (50 pps) transited the stack (RP+FHR) to u4 (LHR) to a
  host receiver while the stack held 300 OSPF routes; the **master** was failed over twice
  (`reload stack-member <master>`). Both times: **no measurable multicast interruption** (max
  inter-arrival gap 0.0216 s / 0.0204 s = normal cadence), 300 routes intact, OSPF adjacency never
  dropped (brief ExStart dip ~17–19 s later, Full again +5–7 s).
- **Roles moved:** after the restore reboot, **member 2 (u3) is Active Master, member 1 (u2)
  Backup** (member 2 priority 2 wins the boot election — expected, not a health signal).
- Nothing parked or shut beyond the SESSION-1 baseline. bench-state.md updated (note at the top of
  its "Current state — 2026-09-11" section; prior version archived `backups/2026-09-11T032735Z`).

## 1. Bench state at wrap, and how to verify it (session 2)

Measured 2026-09-11 ~03:25 device clock (host NZST ~15:25).

```bash
sock=/run/user/1971/keyring/ssh
SSH_AUTH_SOCK=$sock ssh tb470 'fuser -v /dev/u*'          # consoles free
# stack (master is now member 2 -> /dev/u3 relays; either console works once logged in)
SSH_AUTH_SOCK=$sock ssh tb470 'cd /tmp/ckorient && printf "%s\n" \
  "show stack" "show boot" "show ip ospf neighbor" \
  "show running-config | include virtual-mac|priority|multicast|pim|network " \
  | python3 drv.py /dev/u3 /tmp/ckorient/v_stk.txt'
# u4 / u5 baseline
SSH_AUTH_SOCK=$sock ssh tb470 'cd /tmp/ckorient && printf "%s\n" "show ip route summary" \
  "show boot | include image" "show ip ospf neighbor" \
  "show running-config | include multicast|pim|ip route 10.10" | python3 drv.py /dev/u4 /tmp/ckorient/v_u4.txt'
SSH_AUTH_SOCK=$sock ssh tb470 'for n in eth1 eth2 eth3; do echo $n=$(cat /sys/class/net/$n/carrier); done; ip -br addr | grep -E "^eth[123] "'
```

Expected: stack `Normal operation`, **2 = Active Master (prio 2), 1 = Backup (prio 128)**, MAC
`0000.cd37.0d6f (Virtual MAC)`, `flash:/IE520-tb470.rel (file exists)`, no `pim`/`multicast` lines,
`network 10.10.10.0/27` + `10.38.215.0/27`; u4 FIB 1, OSPF `10.10.10.1 Full/DR vlan10`, no test
config; host eth1/2/3 carrier 1 with `.1/.33/.65`, **no `eth1.81`/`eth2.82` sub-ifs**.

## 2. What was accomplished (session 2)

1. **T11427 measured and logged** — PIM-SM RP+FHR on the stack, u4 LHR, host source/receiver;
   300 statics redistributed from u4 into OSPF (stack FIB 300); two `reload stack-member <master>`
   failovers under multicast load. Method mirrors T10623 Part 2b (survivor must be member 1 because
   only its inter-switch links are active; mastership moved to member 2 first each time).
2. **Bench fully restored** to the SESSION-1 baseline by reboot-from-unsaved-startup (stack + u4);
   host sub-ifs deleted, `allmulticast` off, `rp_filter` back to 2.
3. **bench-state.md** annotated (T11427 ran + restored; role snapshot updated); applier archived
   the prior version.

## 3. Results (session 2) — each run labelled

| run | trigger | multicast | OSPF (u4's view of stack) | verdict |
| --- | --- | --- | --- | --- |
| T11427 failover 1 | `reload stack-member 2` (master); member 1 survivor holds source + uplink | 2999/3000 pkts, **max gap 0.0216 s** (= 50 pps jitter, no loss) | Full → ExStart at +16.6 s → Full at +21.3 s; never dropped | **clean** |
| T11427 failover 2 | same, after re-position | 3096/3096 pkts, **max gap 0.0204 s** | Full → ExStart at +18.9 s → Full at +26.0 s | **clean** |

300 OSPF routes present in the stack FIB before and after (member 1 held the RIB as backup, so no
relearn). The reposition step (`reload stack-member 1` to make member 2 master) is a member-1
failover with the path down while it reboots — **not** a continuity measurement, and not counted.

## 4. Findings (session 2)

**Measured**
- Multicast continuity across a stack **master** failover is **loss-free** when the surviving
  member holds the whole forwarding path (FHR ingress, the (S,G) mroute, the uplink to the LHR) and
  `stack virtual-mac` is on. Stronger than T10623's unicast ~2 s: multicast has no host-ARP-to-
  gateway dependency to re-resolve.
- A full 300-route unicast table survives the master failover intact (synced to the backup); OSPF
  re-synchronises its neighbour ~17–19 s later without the adjacency falling below ExStart.
- `service pim` + `ip multicast-routing` gate PIM-SM (u4 runs it without the FL01 licence). The
  stack learns the RP (loopback) and source subnet via OSPF for RPF.

**Inferred (not measured)**
- Route continuity to the 300 destinations *during* the 5–7 s ExStart window (no traffic was sent
  to them; FIB=300 before/after + adjacency never below ExStart is the evidence).

**Host-side gotchas (durable — folded into memory `ie520-mcast-l3-test-method`)**
- `IGMP` is `scapy.contrib.igmp`, not `scapy.all` — a wrong import silently sends no join.
- The receiver interface needs `ip link set dev ethN allmulticast on` **and** `rp_filter=0`, else
  the host socket drops cross-interface multicast though the frames reach the wire (tcpdump sees
  them). Simplest receiver: a **kernel IGMP join** (socket `IP_ADD_MEMBERSHIP`) to hold membership +
  **tcpdump `-tt`** to record arrivals; parse the epoch gaps.

## 5. OPEN (session 2)

- None new. SESSION-1 OPEN items (u5 vlan1 subnet; the stale `​```setup` fences) still stand — see
  the SESSION-1 block below. The fences were **not** rewritten (out of scope for this run).

## 6. Next steps (session 2)

1. `/orient-dt` — re-read the hardware (member 2 is master now).
2. SESSION-1's next steps still apply (u5 vlan1 decision; the Ask-CK memory-split commit).
3. If more T11427 coverage is wanted: push route count toward the platform FIB limit, or add a
   backup-member (slave) failover data point for contrast.

## 7. Recipes (session 2)

**Multicast failover measurement (T11427).** Scratch scripts were in tb470 tmpfs `/tmp/ckorient/`
(gone with the box); recreate from these shapes:
- `mcast_src.py <src_ip> <grp> <port> <pps> <dur>` — UDP `SOCK_DGRAM`, `IP_MULTICAST_TTL=8`, bind to
  the source sub-if IP, seq+timestamp payload (`struct !Qd`).
- `mcast_recv.py <local_ip> <grp> <port> <dur> <out>` — UDP socket, `IP_ADD_MEMBERSHIP`
  (grp+local_ip) to hold the kernel IGMP join so the switch forwards; used only for membership.
- Recorder: `sudo tcpdump -i ethN.<vid> -tt -n --immediate-mode "udp and dst <grp>"` → epoch per
  frame; max inter-arrival gap = the outage.
- Trigger: `reload_trigger.py <port> <member>` = `console.py` `send("reload stack-member N",
  need_prompt=False)` then `send("y", need_prompt=False)`, printing the y-epoch.
- Sequence: make member 2 master (`reload stack-member 1`, poll `show stack` for both `Ready` +
  `Normal operation`), verify flow, then start recorder+source, `sleep 12`, trigger
  `reload stack-member 2`, analyse the gap; correlate to the trigger epoch.
- **Restore = reboot from unsaved startup** (`reload`, y): nothing was `write`-saved, so a plain
  reboot returns the exact baseline. Then delete host sub-ifs, `allmulticast off`, `rp_filter` → 2.

## 8. Pointers (session 2)

- Results: `IE520/ipv4-routing/11427.log`.
- Bench facts: `bench-setup/bench-state.md` "Current state — 2026-09-11" (T11427 note at top).
- Method/gotchas memory: `.claude/memory/ie520-mcast-l3-test-method.md`.
- SESSION 1 (T10623 etc.) is the block below.

---

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
