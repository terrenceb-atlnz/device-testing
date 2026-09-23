# tb470 — bench state

**This file is the source of truth for the tb470 bench.** `/home/st-art/st-art/configs/tb470.setup`
on the testbox is *generated* from it. Edit here, then run the applier; never hand-edit the
`.setup` on the box, because the next apply will silently discard the edit.

```
edit bench-state.md  ->  ./bench_setup.py apply  ->  tb470.setup written IN PLACE
                                                     previous content snapshotted to backups/
```

## How it works

Every fenced ```setup block in this document is concatenated, **in document order**, to form
`tb470.setup`. Prose outside those fences (this section, the diagram, the evidence log) is for
readers here and never reaches the testbox. Prose that testbox users must see goes *inside* a
fence as a `###` comment.

| command | what it does |
| --- | --- |
| `./bench_setup.py render` | render to stdout, touch nothing |
| `./bench_setup.py check` | render, compare against the live file, report drift, exit 1 if it differs |
| `./bench_setup.py apply` | snapshot the live file into `backups/`, then write it in place |

`apply` refuses to run if the live file has drifted from the last snapshot *and* from the
render — that means someone hand-edited the box, and overwriting would lose their work.

**`bench-state.md` always names the current truth.** When it is updated, the superseded
version is dated into `backups/` as `<UTC stamp>.bench-state.md`, paired under the same stamp
with `<UTC stamp>.tb470.setup` — the record and the reflection it produced, archived together.
The name never moves, so every pointer to this file stays correct forever; only history is
dated. `bench-state.current.md` mirrors the last applied version, which is what makes the
pairing possible.

**No more `.bak` files beside the live file.** History lives in `backups/` here, named
`tb470.setup.<UTC ISO timestamp>`. The two `tb470.setup.bak-2026-08-*` files in there keep
their original names on purpose: they are the last of the old scheme, lifted off the box
before it was cleaned up, and the name records where they came from.

## Current state — 2026-09-23 (x230-10GP added as a third device; TWO static LAGs; all three TB NICs on the stack)

**Measured 2026-09-23** by LLDP on both ends, host-MAC learning per port, and end-to-end
ping. Terrence recabled this morning; everything below was verified after the change, not
carried forward.

### What changed from 2026-09-18

1. **A third device joined: the x230-10GP on `/dev/u0`.** Console is **9600 baud** — every
   other console here is 115200. At the wrong rate the port returns NUL bytes and looks
   like a dead device.
2. **Two STATIC LAGs replaced the single LACP `po1`:**
   - **`sa1` = stack `port3.0.2` + `port4.0.2` ↔ 4050 `port1.0.3` + `port1.0.4`**, access
     vlan 10. Its members are on **stack units 3 and 4**, so this LAG **straddles stack
     members** — that was the point of the new cable, and it is what the ACL/QoS
     LAG-on-aggregator cases need.
   - **`sa2` = stack `port1.0.2` + `port1.0.9` ↔ x230 `port1.0.3` + `port1.0.4`**, vlan 1
     (x230 side vlan 100). The second cable created two parallel stack↔x230 links; with
     RSTP disabled on both devices that was a loop, and **aggregating them is what removes
     it.** Do not un-bundle one end.
3. **All three TB NICs now land directly on the stack** — the x230 and the 4050 are no
   longer in any host path:
   - `eth1` moved off the x230 → **stack `port3.0.13`**
   - `eth3` moved off the 4050 → **stack `port3.0.9`**
   - `eth2` unchanged → stack `port2.0.2`
   This matters for measurement, not just tidiness: the x230 runs its own IGMP/MLD
   snooping and was silently pruning multicast in the observation path, which produced a
   result that looked like a DUT failure and was not.
4. **`vlan1` gained a third secondary, `10.38.215.66/27`**, so `eth3` has a peer now that
   it no longer reaches the 4050's `10.38.215.70/27`.

### Addressing, verified 2026-09-23

| | |
| --- | --- |
| stack `vlan1` | `10.38.215.10/27` primary + `10.38.215.40/27` + `10.38.215.66/27` secondary |
| stack `vlan10` | `10.10.10.1/27`, on **`sa1`** |
| 4050 `vlan10` | `10.10.10.2/27`, on **`sa1`** |
| 4050 `vlan1` | `10.38.215.70/27` — **no longer has a TB edge** |
| x230 | all ports access **vlan 100**; SVI `10.38.215.2/27` |

Verified: `eth1→10.38.215.10`, `eth2→10.38.215.40`, `eth3→10.38.215.66` all 0% loss;
vlan10 transit `10.10.10.1→10.10.10.2` 3/3; transit **through** the DUT (inject eth2,
capture eth1) 10/10; stack `Normal operation`, 4/4 Ready.

### Standing gotchas that bit during this rebuild

- **`lacp global-passive-mode enable` silently enrols a port into an aggregation.** It has
  now caused a failure on **all three devices**: the stack (2026-09-21), the AR4050S
  (2026-09-22, where it produced a ring with no blocking port because STP runs on the
  aggregator and that aggregator was down) and the x230 (2026-09-23, `% already under
  lacp control`). It is now **disabled on all three**.
- **A static LAG refuses members whose properties differ** — `% The properties of
  port4.0.2 don't match other ports in aggregator`. Align VLAN/mode on both member ports
  **before** `static-channel-group`, not after.
- **Changing `spanning-tree mode` re-enables spanning tree**, discarding a prior
  `no spanning-tree <mode> enable`. RSTP is deliberately **off** on all three devices here.

### Port budget — corrected

An earlier record claimed each IE520-28GSX member has one usable copper port. **That is
wrong.** Each member has **three**: `portN.0.2`, `portN.0.9`, `portN.0.13` (the `.13`s are
10GBASE-TM, `port4.0.9` is 10GBASE-T). Everything else is an empty SFP cage — 92 of them.
So the stack has 12 copper ports; after this rebuild **6 are in use and 6 are free**:
`port1.0.13`, `port2.0.9`, `port2.0.13`, `port3.0.9`(used), `port4.0.9`, `port4.0.13`.

## Current state — 2026-09-18 (4-member ring + AR4050S over an LACP LAG) — SUPERSEDED 2026-09-23 (x230 added, two STATIC LAGs, all three TB NICs on the stack — above)

> **Terrence recabled the bench on 2026-09-18** (his words: 4-stack again; AR4050S ports 2 and 4 to
> the stack on u2/u4; TB to 4050 port 1 and to u3/u5 — *the member-side cables are on port .2, not
> .1*, see the LLDP table). Claude then, on Terrence's explicit instructions and with every design
> decision his (LACP; reuse vlan10; primary+secondary vlan1 on the stack; RSTP off both devices;
> OSPF + EPSR deconfigured; both configs written), configured the two devices and verified traffic
> end to end. **Everything below is MEASURED 2026-09-18** (`bench_probe.py` sweep, LLDP on BOTH ends,
> `show` output, raw-frame injection captured with `tcpdump`). Evidence, transcripts and the final
> running-configs: `IE520/bench-rebuild-2026-09-18/`. The ```setup fences below were **REWRITTEN
> 2026-09-18** from this whole, measured bench and applied.

### Consoles — swept `/dev/u0`–`u6`, 2026-09-18

| console | unit | identity (from banner + `show`) |
| --- | --- | --- |
| `/dev/u0` | — | **no response** (powered off; the x230-10GP per the 09-09 record — not re-verified) |
| `/dev/u1` | **AR4050S-5G "4050-5g"** | S/N A10401G214000005, base MAC `0000.cd40.0394`, sw `awplus_main-20260918-7` (`AR4050S-tb470.rel`, build Thu Sep 17 22:08 UTC), bootloader 5.2.8, boot config `flash:/default.cfg` |
| `/dev/u2` | IE520 stack **member 1** | banner `awplus-1`, S/N 264A23061, MAC 84e3.2787.0ac0, prio 128, Backup |
| `/dev/u3` | IE520 stack **member 2** | banner `awplus-2`, S/N 264A23068, MAC 84e3.2787.0780, **prio 2**, Backup |
| `/dev/u4` | IE520 stack **member 4** | banner `awplus-4`, S/N 264A23052, MAC 84e3.2787.09c0, prio 128, Backup |
| `/dev/u5` | IE520 stack **member 3 = ACTIVE MASTER** | banner `awplus`, S/N 264A23066, MAC 84e3.2787.0740, prio 128 |
| `/dev/u6` | — | **absent** (the x230-52GT V2 that was here on 09-15 is gone / off) |

### IE520 4-member stack — MEASURED 2026-09-18

`Operational Status: Normal operation`, all four `Ready`. VC ID 3439 (0xd6f); Stack (virtual) MAC
`0000.cd37.0d6f` (`stack virtual-mac`). **Active Master = member 3** (`/dev/u5`, the historical
suspect-hardware S/N …066); member 2 is priority 2 and wins the NEXT election (no pre-emption —
read `show stack`). All four run `awplus_main-20260913-1734` (Build Sun Sep 13 11:21 UTC) —
fleet-uniform, one `.rel` each (`IE520-awplus_main-20260913-1734.rel`), ~64 MB free per member.
Bootloaders per member: m1 `9.1.0`, m2 `master-20260822-535`, m3 `9.1.0`, m4 `pauld`.

Stacking ring (27/28, `show stack detail`, all "Learnt neighbor"): `m1.28↔m2.27`, `m2.28↔m4.27`,
`m4.28↔m3.27`, `m3.28↔m1.27` → ring order **1 — 2 — 4 — 3 — 1** (unchanged from 09-15).

`show boot` still reads `Current boot image : flash:/IE520-tb470.rel (file not found)` — **not a
usable field, bootloader-overridden, not an action item** (ruled 2026-09-15). Read the build from
`show system`.

**Reboot history since 09-15 (both new signatures noted):** the `2026-09-17 21:25 Unexpected
Rebooting due to VCS duplicate master` on m1/m2/m4 is the two split halves (each with a master)
meeting when the ring was recabled — the expected consequence of healing a split, not a fault.
Member 2 additionally took `2026-09-16 09:47 Unexpected System reboot` (this is what moved stack
A's master from m2 to m1 while the bench sat split) and `2026-09-15 18:59 Unexpected Rebooting due
to critical process (marvell) failure!` — a **new signature** on this fleet, worth watching.

### Cabling — LLDP-confirmed on BOTH ends, 2026-09-18 (`lldp run` on the stack and, from today, the 4050)

```
                                   TB (tb470)
        eth1 10.38.215.1/27  ──── member 3 port3.0.2        (vlan1 untagged)   1000BASE-T
        eth2 10.38.215.33/27 ──── member 2 port2.0.2        (vlan1 untagged)   10GBASE-TM SFP+ @1G
        eth3 10.38.215.65/27 ──── 4050 port1.0.1            (vlan1 untagged)   1000BASE-T

  IE520 stack (VMAC 0000.cd37.0d6f)                 AR4050S-5G (0000.cd40.0394)
        member 1 port1.0.2  ═════════════════════  port1.0.2  ┐  ONE LACP aggregate: po1 on
        member 4 port4.0.2  ═════════════════════  port1.0.4  ┘  BOTH ends, both links synchronized
                              (access vlan10 only)

  No other front-panel cables exist (Terrence removed the ports-23..26 member-to-member
  cables; only the five links above plus the eight 27/28 stackport cables).
```

LLDP evidence: stack sees `0000.cd40.0394 port1.0.2` on `1.0.2` and `0000.cd40.0394 port1.0.4` on
`4.0.2`; the 4050 sees `0000.cd37.0d6f port1.0.2` on `1.0.2` and `0000.cd37.0d6f port4.0.2` on
`1.0.4`. TB edges by MAC learning: `00f0.4d00.7716` (eth1) on stack `port3.0.2`, `.7717` (eth2) on
stack `port2.0.2`, `.7718` (eth3) on 4050 `port1.0.1` — each a physical port, not via the LAG.

### Layer 2 / Layer 3 design as configured 2026-09-18 (Terrence's decisions)

- **Aggregate:** `channel-group 1 mode active` on stack `port1.0.2` + `port4.0.2` and on 4050
  `port1.0.2` + `port1.0.4` → **`po1`** each end (a *dynamic* LACP aggregator is `poN` on AW+; `saN`
  is static — `interface sa1` errors `Can't find interface`). `po1` is `switchport mode access` /
  `switchport access vlan 10` on both. Both devices also carry `lacp global-passive-mode enable`
  (pre-existing) — harmless with `mode active` on both ends.
- **Transit vlan10 `10.10.10.0/27`** rides the LAG and nothing else: stack SVI `10.10.10.1/27`
  (the pre-existing "data" vlan10, its old trunk residue on `port1.0.25-26`/`port2.0.23-24` and the
  `port2.0.1` access assignment removed), 4050 SVI `10.10.10.2/27` (`vlan 10 name transit`).
- **vlan1 retained, in the connected TB NIC's /27 (Terrence's rule):**
  - stack vlan1 `10.38.215.10/27` **primary** (eth1's `.0/27`) **+ `10.38.215.40/27 secondary`**
    (eth2's `.32/27`) — the stack's vlan1 is ONE L2 domain carrying two TB /27s (eth1 via m3, eth2
    via m2), so it gateways both.
  - 4050 vlan1 **`10.38.215.70/27` STATIC** (eth3's `.64/27`). It was `ip address dhcp` and had
    leased exactly `.70` from tb470's dhcpd on eth3 (plus a default route via `.65`); pinned static
    to the same address so it cannot move under test — the DHCP default route is gone, which the
    design does not need. `.70` sits inside dhcpd's eth3 pool (`.68–.94`) with no other clients;
    exclude it if a DHCP client ever appears there.
  - **The two vlan1 domains (stack's, 4050's) are NOT bridged** — the LAG carries vlan10 only.
- **Static routes:** stack `ip route 10.38.215.64/27 10.10.10.2`; 4050 `ip route 10.38.215.0/27
  10.10.10.1` + `ip route 10.38.215.32/27 10.10.10.1`. Verified installed (`S … via 10.10.10.x,
  vlan10`) on both.
- **Spanning tree OFF on both:** `no spanning-tree rstp enable` (`show spanning-tree brief` →
  `Spanning Tree Disabled`). Applied only AFTER the LAG was `synchronized` on both ends — before
  that, RSTP was the only thing blocking the two-leg loop (4050 `port1.0.4` was `Alternate`).
  Loop-free now by construction: LAG = one logical link, TB edges are leaves (the TB routes, it
  does not bridge). The stack's `loop-protection loop-detect ldf-interval 1 fast-block` stays on as
  a safety net — every instance `Normal`.
- **OSPF and EPSR deconfigured on the stack:** `no router ospf 1`, `no service ospf`, `no service
  epsr` (the 4050 never had either). AW+ answered `% Save the config and restart for this change to
  take effect` for both `no service` lines — saved, **the daemons stop at the next stack reboot,
  which was NOT done** (open item). `lldp run` added on the 4050.
- **Both running-configs WRITTEN** (`write`; the stack synced startup to members 1, 2, 4). Final
  configs: `IE520/bench-rebuild-2026-09-18/05-through-test-write-final.txt`.

### Verification — 2026-09-18, all PASS

- DUT↔DUT: `ping 10.10.10.2` / `10.10.10.1` across the LAG 0% loss; **via the static routes** 4050 →
  `10.38.215.10` and `→ .40` 0% loss, stack → `10.38.215.70` 0% loss.
- DUT → TB (source-specified, so the request transits the other device): stack `ping 10.38.215.65
  source 10.38.215.10` and `source 10.38.215.40` 3/3; 4050 `ping 10.38.215.1 source 10.38.215.70`
  and `ping 10.38.215.33 source 10.38.215.70` 3/3. (tb470 `rp_filter` is 2/loose, so the asymmetric
  reply — the TB answers on its directly-connected NIC — is accepted.)
- **TB → TB THROUGH the topology, both ways** (method (a): the TB owns all three /27s locally, so an
  ordinary `ping` never leaves the box; raw frames were injected on one NIC addressed to the
  switch's gateway MAC and captured with `tcpdump` on the far NIC): `eth1→eth3` and `eth2→eth3` via
  VMAC → stack → LAG → 4050, arriving on eth3 from `0000.cd40.0394`; `eth3→eth1` and `eth3→eth2` via
  the 4050 → LAG → stack, arriving on eth1/eth2 from `0000.cd37.0d6f`. **3/3 in all four
  directions.** The TB itself was NOT changed (no aggregation, no re-subnetting, no namespaces).

### PDU outlets (per physical unit / console — unchanged for the IE520s; the 4050's is UNKNOWN)

| outlet | console | unit |
| --- | --- | --- |
| 6 (F) | `/dev/u2` | member 1 |
| 8 (H) | `/dev/u3` | member 2 |
| 4 (D) | `/dev/u4` | member 4 |
| 5 (E) | `/dev/u5` | member 3 (master) |
| **?** | `/dev/u1` | **AR4050S — outlet not known; not declared in `[power]`/`[powerlink]`** (Terrence to supply) |

PDU `10.36.150.14`; letters A–H = 1–8.

### Open items from 2026-09-18

1. **4050 PDU outlet** unknown → `swi_e` has no `[powerlink]`; a test calling `swi_e.off()` will
   not fail fast (see §6). Terrence to identify it.
2. ~~`no service ospf` / `no service epsr` complete only on a stack reboot~~ **DONE 2026-09-18 ~02:02 UTC:** Terrence approved a whole-stack `reboot`; login banner back after 193 s, all four `Ready`, `Normal operation`. **Master is now member 2 (`/dev/u3`)** — priority 2 won the fresh election (roles are not a health signal; the fences' "member 3 master today" is the pre-reboot snapshot). LAG `synchronized` both links, vlan10 + static route back, RSTP still disabled; `no service ospf` in running-config, no `service epsr` line. Transcript: `IE520/bench-rebuild-2026-09-18/06-stack-reboot-postcheck.txt`.
3. **`ck_profile`:** an inter-DEVICE swi↔swi link now exists (the stack↔4050 LAG), so `base` is
   satisfiable for the first time — declaring it is Terrence's decision; left empty.
4. **Tooling:** `bench_probe.py`'s host-edge merge does not namespace ports by device, so the
   4050's `port1.0.x` hits were folded into the stack's (it reported eth3 on "member 1
   port1.0.1/port1.0.2"). `bench_topology.py generate` models IE520 stacks only and will not emit
   `swi_e` — its `diff` against this `.setup` would misreport until it learns about non-stack
   devices. Neither was fixed this session.
5. Pre-existing: tb470 dhcpd's eth1 pool (`10.38.215.2–.10`) contains the stack's static `.10`.
6. `service onm` and `spanning-tree mode rstp` (with RSTP disabled) remain on the stack as found.

## Current state — 2026-09-15 (4-member stack re-formed, flash boot; captured by bench_probe.py) — SUPERSEDED 2026-09-18 (ring re-formed + AR4050S over LACP LAG, above)

> **⚠️ LIVE STATE AT WRAP (2026-09-15 ~01:0x UTC, later same day): the bench is intentionally
> SPLIT into TWO independent 2-member VCStacks** — Terrence's test of the verify-setup tooling
> (`bench_topology.py`), NOT a fault. Measured by a `bench_probe.py` sweep:
> - **stack A** = member 1 (`264A23061`, `/dev/u2`, backup) + member 2 (`264A23068`, `/dev/u3`,
>   **master**); members 3 & 4 read `Provisioned`.
> - **stack B** = member 3 (`264A23066`, `/dev/u5`, **master**) + member 4 (`264A23052`,
>   `/dev/u4`, backup); members 1 & 2 read `Provisioned`.
> - Both stacks still carry the SAME virtual MAC `0000.cd37.0d6f` (split-brain — cosmetic while
>   the two halves are L2-isolated, but do not bridge them). All four run
>   `awplus_main-20260913-1734`, flash boot.
> - **Host cables were moved**: `eth1`→member 3 `port3.0.2`, `eth2`→member 2 `port2.0.2`
>   (was eth1→m1 port1.0.2, eth2→m4 port4.0.2); `eth3` still carrier-down.
>
> **The 4-member description and the ```setup fences below are the INTENDED bench and were NOT
> changed.** The deployed `tb470.setup` is still the 4-member topology. Do **not** `apply`/deploy
> from the split — it is transient. Terrence to reconverge the ring or settle the final topology,
> after which a fresh probe → `bench_topology.py` should read MATCH again. (No config was changed
> by me this session; all hardware access was read-only sweeps.)

> **Source: a `bench_probe.py` sweep of `/dev/u0`–`u6`, 2026-09-15 ~08:03 UTC** — the standalone
> console-sweeping probe that depends on nothing (not this file, not `tb470.setup`) and re-derives
> every unit's identity from its own banner + `show` output on each run. Terrence flashed all four
> members with the new build, re-formed the stack, and set flash boot by default. **The console↔unit
> map SHIFTED again** (all seven `/dev/uN` now exist and the ttyUSB enumeration changed) — always read
> it fresh; never trust a prior map. The ```setup fences below were **REWRITTEN 2026-09-15** for this
> 4-member stack (§1–§8), from this whole, cleanly-measured bench (host edges from the probe's own
> host-NIC mapping).

### Consoles — swept `/dev/u0`–`u6`, 2026-09-15

| console | unit | identity (from banner + `show`) |
| --- | --- | --- |
| `/dev/u0` | — | **powered off / no response** |
| `/dev/u1` | — | **powered off / no response** |
| `/dev/u2` | IE520 stack **member 1** | banner `awplus-1`, S/N 264A23061, MAC 84e3.2787.0ac0, prio 128 |
| `/dev/u3` | IE520 stack **member 2** | banner `awplus-2`, S/N 264A23068, MAC 84e3.2787.0780, **prio 2** |
| `/dev/u4` | IE520 stack **member 4 = ACTIVE MASTER** | banner `awplus`, S/N 264A23052, MAC 84e3.2787.09c0, prio 128 |
| `/dev/u5` | IE520 stack **member 3** | banner `awplus-3`, S/N 264A23066, MAC 84e3.2787.0740, prio 128 |
| `/dev/u6` | **standalone x230-52GT V2** | banner `lp-AT-x230-52GT-V2`, S/N A10723G261600010 |

(member↔console: `awplus-N` banners give members 1/2/3 directly on u2/u3/u5; u4 shows the bare master
banner and is member 4 by elimination + S/N. `show system serialnumber` gives member→S/N.)

### IE520 4-member stack — MEASURED 2026-09-15

`Operational Status: Normal operation`, all `Ready`. VC ID 3439 (0xd6f); Stack (virtual) MAC
`0000.cd37.0d6f`. **Active Master = member 4** (`/dev/u4`); member 2 is priority 2 and wins the NEXT
election (a running master is not pre-empted — read `show stack`). All four run
`awplus_main-20260913-1734` (build Sun Sep 13). Bootloaders differ per member (m1 `9.1.0`,
m2 `master-20260822-535`, m3 `9.1.0`, m4 `pauld`). ~65 MB free/member.

Stacking ring (27/28, all "Learnt neighbor"): `m1.28↔m2.27`, `m2.28↔m4.27`, `m4.28↔m3.27`,
`m3.28↔m1.27` → ring order **1 — 2 — 4 — 3 — 1**.

**AW+ `show boot` is NOT a usable field on this bench — the bootloader overrides the AW+ `boot
system` pointer** (ruled a non-issue by Terrence, 2026-09-15: discard the boot field). For the
record, `show boot` reads `Current boot image : flash:/IE520-tb470.rel (file not found)` while every
member actually runs `IE520-awplus_main-20260913-1734.rel` (the only `.rel` in flash, 40052759 B;
the old `IE520-tb470.rel` was removed at flash time). This is **expected and is NOT an action item**:
the bootloader boots the image it is told to at its own prompt, so a dangling AW+ pointer changes
nothing about what boots. Read the running build from `show system` / `show version`, never from
`show boot`.

Addressing unchanged: vlan1 SVI `10.38.215.10/27`, vlan10 SVI `10.10.10.1/27`. Front-panel
member-to-member cables remain on ports 23–26 (LLDP shows intra-stack links; STP-managed) — residue
from the earlier star/ring.

### Per-member flash — MEASURED 2026-09-15 (bench_probe.py `dir awplus-N/flash:` per member)

Relayed stack consoles only show the **master's** flash, so the probe now lists each member's own
flash directly. **All four members hold exactly one release — `IE520-awplus_main-20260913-1734.rel`
(40052759 B), the build they run.** Terrence finished flashing every member; the old
`IE520-tb470.rel` is gone fleet-wide. Each member also carries `default.cfg` and this week's
stack-forming debug `.tgz` + `exception.log`. The fleet is **uniform — no intra-stack image
mismatch** (the split hazard), confirmed member-by-member rather than only from the master.

### u6 — standalone x230-52GT V2 (separate device, not L3-joined)

S/N A10723G261600010, Base `AT-x230-52GT V2`, Bootloader 6.2.37, software
`x230_52-awplus_main-20260605-1491` (build Jun 4), boot `flash:/x230_52-awplus_main-20260605-1491.rel
(file exists)`, boot config `qual.cfg`. Its own standalone master. vlan1 unassigned; vlan100
`198.18.100.2/24`, vlan101 `198.18.101.2/24` (admin-up, protocol down). Flash 95.6 MB (58.3 free).

### Host NIC ↔ member-port map — MEASURED 2026-09-15 (bench_probe.py host-edge derivation)

`bench_probe.py` now derives this itself: it pings out each up host NIC to force ARP, then greps
every console's `show mac address-table` for that NIC's MAC and keeps the **physical `portN.0.x`**
hit (a trunk/`saN` hit is arrival via aggregation, not the edge). Result 2026-09-15:

```
  tb eth1  10.38.215.1/27   00f0.4d00.7716  <->  member 1  port1.0.2   (carrier up)
  tb eth2  10.38.215.33/27  00f0.4d00.7717  <->  member 4  port4.0.2   (carrier up)
  tb eth3  10.38.215.65/27  00f0.4d00.7718   --  NOT learned (carrier DOWN — cabling in flux)
```

So the stack's only live host edges are **eth1→member 1** and **eth2→member 4**; eth3 is dark. (On
2026-09-14 eth3 reached member 3 `port3.0.2`; the probe re-derives this every run, so re-read once
eth3 is back up.)

## Current state — 2026-09-14 (single 4-member VCStack ring — Terrence rebuilt; new 8-stack build) — SUPERSEDED 2026-09-15 (re-flashed + re-formed, above)

> **Terrence rebuilt the bench into ONE 4-member IE520 VCStack** on 2026-09-13/14, enabled by a new
> mainline build (`awplus_main-20260913-1734`) that lifts the old 2-member VCStack cap. The four
> IE520s that were a 2-member stack (u2/u3) plus two standalones (u4/u5) on 2026-09-11 are now a
> single stack. Everything below is MEASURED 2026-09-14 (`show stack detail`, `show system
> serialnumber`, MAC learning, config reads); nothing inferred. The AR4050S/x230 are not part of this
> bench. **The ```setup fences further down are still the STALE 2026-09-03 tree and were NOT
> rewritten** — that remains the standing OPEN item (now larger: a 4-member stack `.setup`). Do not
> trust the fences, and do not `bench_setup.py apply` from this file until they are rebuilt.

### The stack — MEASURED 2026-09-14

4-member VCStack, `Operational Status: Normal operation`, all members `Ready`. Virtual Chassis ID
3439 (0xd6f); Stack (virtual) MAC `0000.cd37.0d6f`; `stack virtual-mac` on.

| member ID | S/N | console | base MAC | role | priority |
| --- | --- | --- | --- | --- | --- |
| 1 | 264A23061 | `/dev/u2` | 84e3.2787.0ac0 | Backup | 128 |
| **2** | 264A23068 | `/dev/u3` | 84e3.2787.0780 | **Active Master** | 2 |
| 3 | 264A23066 | `/dev/u5` | 84e3.2787.0740 | Backup | 128 |
| 4 | 264A23052 | `/dev/u4` | 84e3.2787.09c0 | Backup | 128 |

- Console→member is by **S/N** (USB cabling unchanged); the member IDs were reassigned across all four
  when the stack was formed, so the ID↔console map is NOT the same as the old 2-stack. Member 2
  (priority 2) wins the boot election → Active Master; roles move after any failover and never
  pre-empt — always read `show stack`. (S/N 264A23066 = the historical suspect-hardware unit, now
  member 3 on `/dev/u5`.)

### Stacking ring — MEASURED 2026-09-14

Ports 27/28 on each member form a ring (all "Learnt neighbor", all up):

```
  m1 port1.0.28 <-> m2 port2.0.27
  m2 port2.0.28 <-> m4 port4.0.27
  m4 port4.0.28 <-> m3 port3.0.27
  m3 port3.0.28 <-> m1 port1.0.27
  ring order: 1 — 2 — 4 — 3 — 1
```

### Testbox edges — MEASURED 2026-09-14 (MAC learning: host NIC MAC seen on a physical port)

```
  tb eth1 10.38.215.1/27   (.0/27)   00f0.4d00.7716  <->  member 1  port1.0.2   (vlan1 untagged)
  tb eth2 10.38.215.33/27  (.32/27)  00f0.4d00.7717  <->  member 4  port4.0.2   (vlan1 untagged)
  tb eth3 10.38.215.65/27  (.64/27)  00f0.4d00.7718  <->  member 3  port3.0.2   (vlan1 untagged)
  (all three carrier up 2026-09-14; member 2 / master has NO direct TB NIC)
```

vlan1 is ONE bridged L2 domain spanning the three /27s; the stack's only vlan1 SVI is
`10.38.215.10/27` (in eth1's .0/27), so **at L3 the stack reaches only eth1 (.1)** — eth2 (.33) and
eth3 (.65) are bridged at L2 but have no SVI. (This is why firmware TFTP only worked from `.1`.)

### Addressing / VLANs — MEASURED 2026-09-14

- **vlan1** SVI `10.38.215.10/27` (ipv6 enable + dhcp-client); nearly all front-panel ports untagged
  vlan1. Host ports with forced speed/duplex: `port1.0.2` (1000/full).
- **vlan10 "data"** SVI `10.10.10.1/27`; `port2.0.1` access vlan10 (1000/full); `port1.0.25-26` +
  `port2.0.23-24` tagged trunk vlan10. (vlan10 is residue from the 2026-09-11 star; no external
  vlan10 neighbours now.)

### Build & boot — MEASURED 2026-09-14

- **Running build (all four members): `awplus_main-20260913-1734`** (Build name
  `IE520-awplus_main-20260913-1734.rel`, 09/13/26 11:21) — the new build that supports up to 8 stack
  members. The stack is **netbooted** (bootloader TFTP from tb470 `/tftproot/IE520-tb470.rel`, which
  IS 20260913-1734: md5 `f60317e8…`, 40052759 B, staged 2026-09-14 07:34).
- AW+ `show boot`: `Current boot image : flash:/IE520-tb470.rel (file exists)`, autoboot disabled —
  cosmetic under netboot.
- **Flash contents 2026-09-14:**
  - **Master (member 2):** `IE520-awplus_main-20260913-1734.rel` (NEW, 40052759 B — copied via local
    TFTP this session) **+** `IE520-tb470.rel` (OLD, 40050847 B, Sep 09).
  - **Members 1, 3, 4:** `IE520-tb470.rel` (OLD, last week's, 40050847 B) only. **Terrence is putting
    the new build onto members 1/3/4 himself** (2026-09-14) — the cross-member/remote-login copy paths
    are dead ends on this build (see "Firmware-copy findings" below).
  - ~65 MB free/member (master less, holding two `.rel`).
- No new unexpected reboots; last stack role changes Sep 13 (stack forming).

### PDU outlets (by physical unit / console — unchanged; NOT by member ID)

| outlet | console | member now |
| --- | --- | --- |
| 6 (F) | `/dev/u2` | member 1 |
| 8 (H) | `/dev/u3` | member 2 (master) |
| 4 (D) | `/dev/u4` | member 4 |
| 5 (E) | `/dev/u5` | member 3 |

PDU `10.36.150.14`; letters A–H = 1–8.

### Firmware-copy findings on this build — MEASURED 2026-09-14 (durable; also in [[ie520-4stack-flashprep]])

- **A large file can only be written to a member's flash while that member IS the master** (local
  TFTP). Confirmed dead ends for a *non-master* member on this build:
  - master → `awplus-N/flash:<file>` (flash-to-flash push) and `tftp:` → `awplus-N/flash:` both fail:
    `nfs: server 192.168.255.N not responding, timed out` → `% Input/Output error due to external
    media removal`. SMALL cross-member writes succeed and ICMP to `192.168.255.N` is clean — only the
    large transfer stalls (member SPIFlash write over the internal NFS). The only proven large
    cross-member copy is a PULL (member→master), never a large push.
  - `remote-login N` then `copy tftp:` → `% Copying to/from remote file systems is only supported from
    the stack master`.
- Cross-member path syntax for SMALL files is `awplus-N/flash:<file>` (**no slash** after `flash:`);
  the `awplus-N/flash:/<file>` form also NFS-times-out.
- AW+ refuses to overwrite OR delete the file configured as the current boot image
  (`% Cannot overwrite/delete flash:/IE520-tb470.rel as it is configured as the current boot image`);
  `boot system tftp://…` is rejected (`% Invalid format for file URL`). So the new build was staged
  under its dated name `IE520-awplus_main-20260913-1734.rel`, not by overwriting `IE520-tb470.rel`.

## Current state — 2026-09-11 (EPSR REMOVED → loop-free vlan10 star; flash boot) — SUPERSEDED 2026-09-14 (single 4-member stack, above)

> **2026-09-11, later same day — AWPTCM T11427 ran on this baseline and RESTORED it.** A PIM-SM
> multicast + 300-route failover campaign temporarily added PIM/multicast-routing, source/receiver
> VLANs (81/82), a loopback RP and 300 statics; **none was saved**, and the stack + u4 were rebooted
> from startup to return to exactly the state described below (u5 untouched). Verified: no PIM, no
> test VLANs, port1.0.2 back to access vlan1, u4 FIB back to 1, OSPF Full stack↔u4, all `show boot`
> `(file exists)`. **Only role snapshot changed: after the full reboot member 2 (u3) is Active
> Master, member 1 (u2) Backup** (member 2 priority 2 wins the boot election — expected; roles are
> not a health signal). Log: `IE520/ipv4-routing/11427.log`; handover: session-2 block in
> `IE520/SESSION-HANDOVER-2026-09-11.md`.

**Supersedes the 2026-09-09 EPSR-ring section below.** The EPSR ring was torn down this session
(Terrence's call) and the inter-switch cabling reduced to a **loop-free star with the DUT stack
as hub**, so inter-device L3 (OSPF/PIM) works. Boot is now **flash**, not TFTP. The DUT stack has
**`stack virtual-mac`** enabled. Everything here is MEASURED 2026-09-11 (LLDP on both ends, pings,
`show` output); nothing inferred. **The ```setup fences further down are still STALE** (they
describe the 2026-09-03 tree) and are NOT rewritten here — that needs the framework `.setup`
schema decisions noted in the 09-09 section, out of scope for this topology capture.

### Devices, consoles, serials — unchanged from 09-09, re-confirmed 2026-09-11

| console | unit | role now | S/N | base MAC |
| --- | --- | --- | --- | --- |
| `/dev/u2` | IE520 VCStack member **ID 1** | **DUT stack** | 264A23061 | `84e3.2787.0ac0` |
| `/dev/u3` | IE520 VCStack member **ID 2** | **DUT stack** | 264A23068 | `84e3.2787.0780` |
| `/dev/u4` | standalone IE520 | L3 neighbour (OSPF) | 264A23052 | `84e3.2787.09c0` |
| `/dev/u5` | standalone IE520 | L3 neighbour | 264A23066 | `84e3.2787.0740` |

- DUT **stack MAC is now the virtual MAC `0000.cd37.0d6f`** (`stack virtual-mac`, Virtual Chassis
  ID 0xd6f). Member 2 (u3) is `stack 2 priority 2` (wins master at boot). **After the T11427
  restore reboot (see the note at the top of this section): member 2 (u3) Active Master, member 1
  (u2) Backup, both `Ready`, `Normal operation`** — member 2's priority won the boot election, as
  designed. (Earlier this day, before T11427, member 1 was Active Master.)
  Roles move after every failover and never pre-empt — read `show stack`. (S/N 264A23066 on u5 is
  still the suspect-hardware unit from the header item 3 — the fault tracks the S/N, now standalone.)
- **Builds at wrap:** stack `awplus_main-20260910-1726` (build Wed Sep 9 12:05 UTC), same on both
  members (S/W auto-sync On); u4 and u5 `awplus_main-20260911-1730` (build Thu Sep 10 12:05 UTC).
  The standalones being one build newer than the stack is not a hazard (only *intra*-stack mismatch
  splits a stack). Bootloaders differ per unit and are not a hazard either: m1 `9.1.0`,
  m2 `master-20260822-535`, u4 `pauld`, u5 `9.1.0`. Flash: one `.rel` (`IE520-tb470.rel`, 40 MB)
  per unit, ~65 MB free; all `pre-*.cfg` backups deleted 2026-09-11 (Terrence: no backups wanted).
- **No new `Unexpected` reboots on either member since 2026-09-08 (m1) / 2026-09-09 19:10 (m2);**
  every 2026-09-10 entry is an `Expected User Request` from the T10623 failover runs.

### Cabling — LLDP-confirmed BOTH ENDS, 2026-09-11

`show lldp neighbors` on the stack, u4 and u5 (LLDP enabled on all three this session). Chassis
IDs: stack `0000.cd37.0d6f`, u4 `84e3.2787.09c0`, u5 `84e3.2787.0740`.

```
DUT stack (hub)                       INTER-SWITCH LINKS (all physically present)
  member1 u2 port1.0.26  <->  u4 port1.0.25   ACTIVE  (u4 sa1)  ─┐ stack<->u4
  member2 u3 port2.0.24  <->  u4 port1.0.23   admin-shut (u4)   ─┘  (redundant m2 leg)
  member1 u2 port1.0.25  <->  u5 port2.0.25   ACTIVE  (u5 sa2)  ─┐ stack<->u5
  member2 u3 port2.0.23  <->  u5 port2.0.23   admin-shut (u5)   ─┘  (redundant m2 leg)
  u4 port1.0.24  <->  u5 port2.0.24   admin-shut (u4/u5 sa3)    ─┐ u4<->u5 direct
  u4 port1.0.26  <->  u5 port2.0.26   admin-shut (u4/u5 sa3)    ─┘  (the old ring's 3rd edge)

Testbox edges -- ALL THREE measured 2026-09-11 by MAC learning (host NIC MAC seen on the port
directly, not via a trunk):
  tb eth1 10.38.215.1/27   00f0.4d00.7716  <->  stack member1 port1.0.2   (untagged vlan1)
  tb eth2 10.38.215.33/27  00f0.4d00.7717  <->  u4 port1.0.2              (untagged vlan1)
  tb eth3 10.38.215.65/27  00f0.4d00.7718  <->  u5 port2.0.2              (untagged vlan1)
  (all three copper 1000BASE-T, linked a-1000/a-full -- no forced speed/duplex needed today)
```

**vlan1 is ONE bridged L2 domain across the stack, u4 and u5** — the inter-switch trunks carry
vlan1 untagged as native, so each switch learns all three host NIC MACs (u4 sees eth1/eth3 via
`sa1`, the stack sees eth2/eth3 via its u4/u5 trunks). Three different /27s share that domain;
at L3 only same-/27 pairs talk. It is a star (hub = stack member 1), not a loop.

The three edges above formed the old EPSR triangle (stack—u4—u5—stack). To make a loop-free star
**with a single active link per leg**, both u4↔u5 links (sa3) and both redundant *member-2* legs
(u4 port1.0.23, u5 port2.0.23) are **admin-shut**; each device now reaches the stack over ONE
member-1 link. This also removed the DUP flooding caused by the asymmetric LAG (u4/u5 aggregate
two links into sa1/sa2; the stack has NO channel-groups, so it flooded between the two).

### Addressing / VLANs — MEASURED 2026-09-11

- **vlan10 `10.10.10.0/27`** (the inter-device transit): stack SVI `.1`, u4 `.2`, u5 `.3`. Hub =
  stack member 1. Clean pings stack→u4 and stack→u5 (0% loss, **no DUPs**, no storm).
- **vlan1** (per Terrence's rule "native vlan1 matches the connected testbox eth port's subnet"):
  stack `10.38.215.10/27` (eth1's .0–.31 ✓), u4 `10.38.215.36/27` (eth2's .32–.63 ✓),
  u5 `10.38.215.12/27` (**.0–.31 — but u5 is cabled to eth3, whose /27 is .64–.95**). Do NOT
  reconfigure these away without Terrence. **OPEN (2026-09-11):** by the rule u5's vlan1 belongs
  in eth3's /27 (e.g. `.66–.94`); the host can reach u5's `.12` today only because vlan1 is bridged
  through to eth1's segment. Terrence to decide — not changed at wrap.
- **vlan2** ("epsr-control") still exists as a named-but-unused VLAN on u4/u5 (harmless residue).

### EPSR — REMOVED 2026-09-11

`no epsr ring1` (datavlan removed first, then the instance) on u4 and u5; `no service epsr` set
(takes full effect on next reboot). The stack never ran an EPSR *ring* (only `service epsr`, still
present, inert). Removal order that works on this build: `epsr configuration` → `epsr <ring>
state disabled` → `no epsr <ring> datavlan <vid>` → `no epsr <ring>`.

### Boot — FLASH (not TFTP), 2026-09-11

All IE520s default-boot from a flash `.rel` (Terrence set flash default boot from the bootloader
config). `reload` is safe; the old TFTP-boot/eth3 dependency no longer applies to a normal reload
(`/tftproot/IE520-tb470.rel` on tb470 still exists, refreshed 2026-09-11 07:41, but nothing boots
from it now). **All three units' `show boot` read `Current boot image : flash:/IE520-tb470.rel
(file exists)` as at wrap** — the stack's pointer was fixed before its reboot, u4's and u5's
(both dangling at `flash:/IE520-20260825.rel`) at wrap, with `boot system flash:/IE520-tb470.rel`
+ `write`. On a stack that command syncs the 40 MB image to the other member (console dark
~10–12 min). Always confirm `(file exists)` before any reload. (Memory
`tb470-ie520-flash-boot-reboots-ok`.)

### Configuration KEPT at wrap 2026-09-11 (Terrence's decisions) — all SAVED to startup

- **Stack:** `stack virtual-mac`, `stack 2 priority 2`, `boot system flash:/IE520-tb470.rel`,
  `lldp run`, and **OSPF kept**: `service ospf`, `router ospf 1` with `network 10.10.10.0/27 area 0`
  + `network 10.38.215.0/27 area 0` (router-id 10.38.215.10). The dead `vlan 210` / `vlan210` SVI
  from the first Part 2b attempt was removed (`no vlan 210`; `no interface vlan210` is refused on
  this build but removing the VLAN takes the SVI). Startup == running.
- **u4:** EPSR removed (`no service epsr`, no ring), `sa3` + `port1.0.23` `shutdown`, `service ospf`
  + `router ospf 1 / network 10.10.10.0/27 area 0` (router-id 10.10.10.2), `lldp run`.
  Adjacency to the stack **Full** on vlan10 (stack DR, u4 BDR).
- **u5:** EPSR removed, `sa3` + `port2.0.23` `shutdown`, `lldp run`. No OSPF on u5.
- Pre-existing `service epsr` on the stack (no ring) left as found. `vlan 2 name epsr-control`
  remains on u4/u5 as an unused named VLAN.

## Current state — 2026-09-09 (EPSR ring; SUPERSEDED 2026-09-11 — see above)

**Supersedes the 2026-09-03 flat tree.** The bench was recabled into an **EPSR ring** for the
AWPTCM **T5648** (stack *master* failure) / **T5649** (stack *slave* failure) L2-continuity
campaign. This is a live rebuild, not a cleanly characterised state — see the degraded-state
note. **The ```setup fences further down still describe the 2026-09-03 tree and are STALE — they
have NOT been rewritten; see "Why the fences below are NOT updated yet".**

### Devices, consoles, serials — MEASURED 2026-09-09

Re-derived from `show stack` / `show system serialnumber` on every console this session; not
trusted from any record — the record had these on the wrong consoles.

| console | unit | ring role | S/N | base MAC |
| --- | --- | --- | --- | --- |
| `/dev/u2` | IE520 VCStack member **ID 1** | **DUT stack** (EPSR **master**) | **264A23061** | `84e3.2787.0ac0` |
| `/dev/u3` | IE520 VCStack member **ID 2** | **DUT stack** (EPSR **master**) | **264A23068** | `84e3.2787.0780` |
| `/dev/u4` | standalone IE520 | EPSR **transit** | **264A23052** | `84e3.2787.09c0` |
| `/dev/u5` | standalone IE520 | EPSR **transit** | **264A23066** | `84e3.2787.0740` |
| `/dev/u1` | AR4050S-5G | powered OFF (still cabled) | A10401G214000005¹ | `0000.cd40.0394`¹ |
| `/dev/u0` | x230-10GP | powered OFF (still cabled) | G26ZE80EN¹ | `001a.eb91.cca1`¹ |

¹ carried from the prior record; not re-verified this session (units are off).

- **u2 and u3 both relay to the stack master CLI** (any formed AW+ VCStack), so both show the
  same `show stack`; when whole, both members read `Ready`.
- The old record put the DUT stack on u4/u5 (…052/…066). That is now WRONG: **…052/…066 are the
  two *standalone transit* IE520s (u4/u5); the DUT stack is a different pair, …061 + …068, on
  u2/u3.** The whole device population moved.

### PDU outlets — MEASURED / confirmed 2026-09-09

PDU `10.36.150.14`; letters A–H = 1–8 (D=4, E=5, F=6, H=8).

| outlet | unit | how known |
| --- | --- | --- |
| **6 (F)** | `/dev/u2` — stack member 1 (…061) | **verified** — cutting F dropped u2; power-off silenced u2 while its peer stayed master |
| **8 (H)** | `/dev/u3` — stack member 2 (…068) | **verified** — the T5648 cut, and a later power-off silenced u3 with u2 still up |
| **4 (D)** | `/dev/u4` — transit | unchanged from prior record; Terrence-confirmed 2026-09-09 |
| **5 (E)** | `/dev/u5` — transit | unchanged from prior record; Terrence-confirmed 2026-09-09 |
| — | `/dev/u0`, `/dev/u1` | **TBD** — the old record put them on 6/8, now held by the DUT stack; Terrence to reconcile. Both off. |

### Ring, edges, boot — MEASURED 2026-09-09

- **EPSR:** DUT stack = **master** (`ring1`, control **vlan2**, data **vlan10**); u4, u5 =
  **transit**. Ring aggregation is cross-member on the stack: `sa1` = port1.0.26(m1)+port2.0.24(m2),
  `sa2` = port1.0.25(m1)+port2.0.23(m2). Full port-level ring cabling not yet re-mapped (below).
- **Testbox edges (data vlan10):** `tb eth1` (10.38.215.1) → stack **member 1** `port1.0.2`;
  `tb eth2` (10.38.215.33) → `u4 port1.0.2`. Both **1000BASE-T copper SFP**, and they only link
  when **forced `speed 1000`/`duplex full` on both ends** — plain autoneg leaves them
  `notconnect` (measured repeatedly this session).
- **Boot is TFTP, not flash.** The IE520s **netboot** `tftp://10.38.215.65/IE520-tb470.rel`
  (`tb eth3` = TFTP server, `in.tftpd` on `/tftproot`). **A power-cut member cannot rejoin
  unless `eth3`/TFTP is up.** (Supersedes the `[boot_from_flash]` fence below.)

### Degraded state right now (2026-09-09) — not steady-state

- **member 2 (u3 / …068): POWERED OFF** — it was boot-looping on `Failed to load
  tftp://10.38.215.65/IE520-tb470.rel` because **`eth3` is link-down**; powered off to stop the loop.
- **member 1 (u2 / …061): standalone Active Master**; EPSR `ring1` = **Failed**, L2 down (expected
  while member 2 is out).
- **`tb eth3` is down (carrier 0)** — TFTP boot path dead; restoring it (physical SFP/cable on
  eth3) is the prerequisite to booting member 2 back in.

### Open findings from this campaign (confirm before recording as defects)

1. Copper-SFP↔Intel-igc edge links need **forced 1000/full**; autoneg does not link them.
2. IE520 **TFTP-over-eth3 boot** means a hard power-cut of a member strands it if eth3/TFTP is
   down — prefer `reload stack-member` over a PDU cut for failover, or make eth3/TFTP solid first.
3. **OPEN:** after the master-member power-cut, EPSR did **not** reconverge on the surviving
   member — `ring1` stayed `Failed`, L2 stayed down (member 1's `sa1`/`sa2` legs were up). Real
   EPSR-over-VCStack defect vs. a ring-cabling gap is **unresolved** — needs a clean re-test.

### Why the fences below are NOT updated yet

The generated `​```setup` fences still describe the 2026-09-03 tree. They are not rewritten
because (a) a correct rewrite needs the **full port-level ring cabling**, measurable only with
the bench **whole** (member 2 booted, eth3 up) — a probe now captures a broken state, against
this file's "measured, nothing inferred" rule; and (b) the framework `.setup` schema for a
multi-node ring + TFTP boot (transit-node roles, ring `[portlink]`, replacing `[boot_from_flash]`)
needs confirming before it goes into the source-of-truth. **Until then, do not trust the fences
below for the current bench.**

## The bench as at 2026-09-03 (SUPERSEDED 2026-09-09 — see "Current state" above)

Flat single vlan1 (`.64/27`), a loop-free TREE with the IE520 stack as the hub. Rebuilt
2026-09-03 out of the messy state left by an inter-session recabling. Every link is
confirmed by LLDP on BOTH ends (and the testbox leg by the IE520's LLDP frame captured on
tb470 eth3). Nothing here is inferred.

```
tb470 eth3  10.38.215.65/27   (also the DHCP server for this /27: ISC dhcpd, range .68-.94)
  └─ stk_a port1.0.1 (member 1 / swi_b)     IE520 stack "awplus"  -- RSTP root
       stk_a vlan1 10.38.215.66/27 (static), ntp server .65 -> stratum 3
       ├─ port2.0.1 ── swi_c port1.0.3      AR4050S-5G "4050-5g" (ROUTER; role 802.1X)
       │                                    vlan1 10.38.215.70/27 (static)
       └─ port2.0.9 ── swi_d port1.0.4      x230-10GP "x230-10GP"
                                            vlan1 10.38.215.71/27 (static)

admin-shut: swi_c port1.0.2 <-> swi_d port1.0.2 -- cable present, both ends `shutdown` on
            purpose so the IE520-4050-x230 triangle stays a tree (no loop).
not links:  swi_a port2.0.6 / 2.0.8 / 2.0.14 / 2.0.16 are SFP LOOPBACK plugs. They read
            "connected" with no neighbour; RSTP holds them Discarding.
```

## Evidence — all measured 2026-09-03 (nothing inferred)

Raw captures: `~/old test runs/IE520/stack-tests/bench-probe-2026-09-03/`
  - `capture.json`    — `bench_probe.py`, all three devices, nine commands each (clean state)
  - `lldp-clean.json` — `show lldp neighbors`, all three devices

Every inter-device link is confirmed by LLDP on **both** ends:
- `stk_a port2.0.1 <-> swi_c port1.0.3` — IE520 sees `0000.cd40.0394 / port1.0.3`; the 4050
  sees `0000.cd37.0d6f / port2.0.1` (System Name `awplus`, cap `--B-R---`).
- `stk_a port2.0.9 <-> swi_d port1.0.4` — IE520 sees `001a.eb91.cca1 / port1.0.4`; the x230
  sees `0000.cd37.0d6f / port2.0.9`.
- `tb eth3 <-> stk_a port1.0.1` — tb470 is a Linux host (no LLDP tx), so proven from the host
  side: the IE520's own LLDP frame (chassis `0000.cd37.0d6f`, Port ID `port1.0.1`) was
  captured on tb470 eth3 (`tcpdump ether proto 0x88cc`, 2026-09-03).

Reachability proven the same day: tb470 pings `.66` (IE520), `.70` (4050), `.71` (x230); all
ARP-resolve on eth3 with the correct base MACs. RSTP is enabled on all three switches; the
bench is a tree, so every inter-device port is Designated/Forwarding and RSTP only holds the
four IE520 loopback plugs Discarding.

**Permanent 4050 property (kept for the record; no aggregation exists now).** The AR4050S runs
`lacp global-passive-mode enable`. It never *initiates* an aggregation but will passively bond
anything presenting LACP, and such a passive `po` is **not in the 4050's running-config** — only
`show etherchannel detail` reveals it. Two links to the 4050 that are *not* aggregated on the
other end stay independent and **loop** (measured 2026-09-01 as the 4050's MAC thrashing across
two IE520 ports). Present multiple links to the 4050 ONLY as a single LACP channel, or shut all
but one — which is what the admin-shut `swi_c port1.0.2` does today.

## Open items

- The `swi_c <-> swi_d` cable is **admin-shut** (both ends `shutdown`) to keep the topology a
  loop-free tree. Un-shutting it re-creates the IE520–4050–x230 triangle; only do so with RSTP
  confirmed active on all three (it is, 2026-09-03), which will then block one leg.
- A **direct testbox↔DUT link now exists** (`tb eth3 <-> IE520 port1.0.1`), so the `tblink`
  topology profile is now satisfiable. `ck_profile` is still left empty (§2) — declaring a
  profile is a separate decision, not taken here. The DUT-side port is `stk_a port1.0.1`
  (member 1 / swi_b).
- LLDP was enabled on `swi_c` and `swi_d` on 2026-09-03 (running-config only) for discovery;
  the IE520 already ran it. Harmless; reverts on reload.
- Everything now sits in one vlan1 `.64/27` domain. The IE520 (`.66`), 4050 (`.70`) and x230
  (`.71`) all carry **STATIC** addresses. tb470 also runs ISC dhcpd on eth3 (range `.68-.94`)
  for the segment, but the switches no longer use it: their AW+ DHCP clients wedged under the
  repeated port1.0.1 flaps of the DoS campaign, so they were pinned static on 2026-09-03.
  (`.70`/`.71` sit inside the dhcpd pool range but there are no other DHCP clients here, so no
  conflict; exclude them from the pool if that ever changes.)
- Member 1 (S/N 264A23066) is suspect hardware — see §1, trap 3.

### 🐛 OPEN PRODUCT DEFECT — the resiliency link does not work on this build

Moved here 2026-09-02 from the `tb470-topology-and-setup` memory: it is a property of this
bench's software, so it belongs with the bench record rather than in an auto-loaded memory.

Whichever member holds the **backup role** receives 100% of the master's healthcheck multicasts
error-free and registers none of them: `show stack resiliencylink` reads `Failed` on the backup
while it transmits **zero** replies. Reproduced across **4 port pairs** (1000BASE-SX 1G,
10GBASE-SR 10G matched *and* mismatched numbering, and the 10G copper stacking PHYs), **both
units**, **both roles**, **both bootloader builds**, 4 reboots — so port, media, unit and
bootloader are all excluded; **the fault tracks the ROLE.**

Consequence: pulling the stacking cables yields **TWO ACTIVE MASTERS sharing one VMAC and one
IP**, not a Disabled-Master; the neighbour switch then sees the same bridge ID on two ports and
blackholes one. **Blocks TEST 17688 steps 3–7.** Software `IE520-tb470.rel`,
`tomahawk_ie520-continuous`. Full evidence and verdict table:
`~/old test runs/IE520/stack-tests/resiliency-link/after-action-17688.md`.

Note both members currently read `Resiliency link status: Not configured` (2026-09-02), so this
is dormant rather than active — but it is why a resiliency link cannot be relied on here, and
why the split observed on 2026-09-02 presented as it did rather than as a clean Disabled-Master.

---

# The generated file

Everything below this line becomes `tb470.setup`.

## §1. Read this before you bind anything

Five live traps, each of which has already cost bench time. They are emitted as the
file's own header so they are unmissable at the point of use.

```setup
###
### !! GENERATED FILE -- DO NOT HAND-EDIT.
###    Source: claude/device-testing/bench-setup/bench-state.md on the NFS lab home
###    (/media/terrenceb/mnt/testbox_home/... from the dev host). Edit THERE, then run
###    `bench_setup.py apply`, which writes this file in place and verifies by readback.
###    An edit made here is discarded by the next apply, silently and without warning.
###    Every previous version is snapshotted in that directory's backups/ -- which is
###    why there are no longer .bak files sitting beside this one.
###
### ============================================================================
### tb470.setup -- REWRITTEN 2026-09-18: the 4-MEMBER IE520 VCStack (stk_a) plus an
### AR4050S-5G (swi_e) joined to it over ONE LACP aggregate, static routing between
### them, three testbox edges. Measured by bench_probe.py sweeping /dev/u0-u6, LLDP on
### BOTH ends of every inter-device link, and raw-frame injection captured on the far
### TB NIC. Supersedes the 2026-09-15 4-member-only file; previous versions are dated
### in the bench-setup backups/ dir named above. Read items 1-5 before binding anything.
###
###  1. !! THE FOUR IE520s ARE ONE STACK (stk_a), not four devices. Read live
###     2026-09-18 (`show stack`, `show stack detail`):
###         ID 1  S/N 264A23061  MAC 84e3.2787.0ac0  /dev/u2  Backup Member  prio 128
###         ID 2  S/N 264A23068  MAC 84e3.2787.0780  /dev/u3  Backup Member  prio 2
###         ID 3  S/N 264A23066  MAC 84e3.2787.0740  /dev/u5  ACTIVE MASTER  prio 128
###         ID 4  S/N 264A23052  MAC 84e3.2787.09c0  /dev/u4  Backup Member  prio 128
###         Virtual Chassis ID 3439 (0xd6f); Stack MAC 0000.cd37.0d6f (Virtual MAC)
###         Operational Status: Normal operation; all four Ready
###         Ring 27/28: m1.28<->m2.27, m2.28<->m4.27, m4.28<->m3.27, m3.28<->m1.27
###         ==> ring order 1 - 2 - 4 - 3 - 1
###     ==> All four members are declared in [switch] because Setup.py's __checkMember
###         requires it, and [stack] stk_a lists all four. On a formed VCStack every
###         member console is relayed to the master CLI, so init_swi() on ANY member
###         reaches the SAME CLI -- never bind two members as DUT + link partner, that
###         measures one device against itself. The link partner on this bench is swi_e.
###     ==> MASTER IS NOT PINNED BY PRIORITY HERE. Member 2 is priority 2 (lowest, so it
###         wins a FRESH election) yet member 3 is Active Master today -- a running
###         master is never pre-empted, so mastership stays where the last failover left
###         it. READ `show stack` before any step that depends on which member is master;
###         it moves after every failover.
###
###  2. !! PORT NUMBERING IS BY MEMBER ID, and a wrong range fails SILENTLY. Member N's
###     ports are portN.0.x: member 1 = port1.0.x (/dev/u2), member 2 = port2.0.x
###     (/dev/u3), member 3 = port3.0.x (/dev/u5), member 4 = port4.0.x (/dev/u4).
###     Config naming the wrong member's range is ACCEPTED with no error (this once
###     presented as a DHCP option-61 defect that did not exist). Confirm the member ID
###     before any step that names a port.
###
###  3. !! MEMBER 3 (S/N 264A23066, /dev/u5) IS THE SUSPECT-HARDWARE UNIT -- AND TODAY
###     THE MASTER. It carries a long run of "Unexpected System reboot" entries. All
###     fleet units take unattended reboots (member 2 logged a NEW signature on
###     2026-09-15: "critical process (marvell) failure"). Check `show reboot history`
###     on EVERY member before calling any unexplained stack event a defect.
###
###  4. !! AW+ `show boot` IS NOT A USABLE FIELD -- THE BOOTLOADER OVERRIDES IT. Every
###     member RUNS IE520-awplus_main-20260913-1734.rel (read from `show system`), while
###     `show boot` reads "Current boot image : flash:/IE520-tb470.rel (file not found)".
###     That is EXPECTED and NOT an action item. Read the running build from `show
###     system` / `show version`, never from `show boot`.
###
###  5. !! swi_e (AR4050S-5G, /dev/u1) IS THE ONLY OTHER DEVICE, AND IT IS A ROUTER
###     joined to the stack by ONE LACP AGGREGATE (po1 on both ends; `channel-group 1
###     mode active` on stack port1.0.2 + port4.0.2 and on 4050 port1.0.2 + port1.0.4).
###     The two [portlink] swi_a-swi_e / swi_d-swi_e lines below are the two MEMBER LINKS
###     of that one aggregate -- they are NOT two independent DUT<->partner paths, and
###     the .setup format has no section for aggregation. The LAG carries ONLY transit
###     vlan10 (10.10.10.0/27: stack .1, 4050 .2) with static routes each way; vlan1 is
###     NOT bridged across it. Spanning tree is DISABLED on both devices (`no
###     spanning-tree rstp enable`) -- the LAG is what keeps this loop-free, so do NOT
###     break the aggregate on one end only while RSTP is off. Full L2/L3 design and the
###     end-to-end verification: bench-state.md "Current state -- 2026-09-18".
###
### ============================================================================
### PERMANENT PLATFORM FACTS -- these have each cost hardware time; do not re-derive.
###
### IE520 HAS NO ONBOARD MANAGEMENT ETHERNET. `show interface eth0` answers
### "% Can't find interface eth0". The "eth0" a bootloader offers for TFTP boot is an
### ASIX USB-to-Ethernet dongle in the switch's USB port, visible ONLY to the
### bootloader and only DURING BOOT. ==> TESTBOX-SIDE CARRIER IS NOT A VALID
### PRE-FLIGHT CHECK: a correctly cabled TFTP boot path is indistinguishable from an
### unplugged one until the DUT is power-cycled.
###
### ONLY 10.38.215.0/24 HAS AN UPSTREAM RETURN PATH, and tb470 has NO NAT
### (`nft list ruleset` is 0 bytes, iptables not installed). Never move a lab segment
### off it. Proven 2026-08-04.
###
### FLASH IS SPIFlash AND IS EXTRAORDINARILY SLOW: a 41 MB flash-to-flash copy takes
### ~12 minutes, during which the unit answers NOTHING -- console silent even to a
### bare CR. That looks exactly like a crash. Never power-cycle mid-write.
###
### OPENING OR CLOSING A SERIAL PORT DROPS DTR AND THE IE520 READS THAT AS A BREAK,
### which can park a unit in the bootloader. Drive these consoles with a tool that
### does `stty -hupcl` first (failover-300/console.py does); leave minicom with
### Ctrl-A Q, never by closing the window.
###
### init_portlink() RETURNS (None, None) SILENTLY when no link matches, so a missing
### cable grades as a script defect. Check with tool/pt_preflight.py BEFORE booking
### bench time.
### ============================================================================

```

## §2. Topology profiles and verified capabilities

`ck_profile` is deliberately empty. An inter-device link now exists (the stack↔4050 LAG), so
`base` is satisfiable for the first time — declaring it is a decision, not a measurement.

```setup
### TOPOLOGY PROFILES this bench implements -- the contract generated scripts target.
### Spec: ask-ck/pytest-create/TOPOLOGY-PROFILES.md ; checker: tool/pt_profiles.py
###
### !! ck_profile IS DELIBERATELY EMPTY. As at 2026-09-18 the hardware could implement:
###      - `base` (an inter-DEVICE swi<->swi copper link): the stack<->swi_e LAG member
###        links exist (swi_a port1.0.2 <-> swi_e port1.0.2, swi_d port4.0.2 <-> swi_e
###        port1.0.4). NOTE they are two legs of ONE aggregate carrying vlan10 only.
###      - `tblink` (a DIRECT testbox<->DUT link): three exist (tb eth1 <-> member 3
###        port3.0.2, tb eth2 <-> member 2 port2.0.2, tb eth3 <-> swi_e port1.0.1).
###    Declaring a profile is Terrence's decision and has NOT been taken. Do not add a
###    profile the hardware does not implement, and do not add one without that decision.
###
### ck_cap_* records capabilities VERIFIED ON THE DEVICE, never inferred from docs.
### `polarity` is documented for 29 products NOT including ie520, yet the IE520 supports
### it (confirmed at the console 2026-07-30 via `polarity ?`). Absence from the harvested
### CLI reference means UNKNOWN, not unsupported. swi_a..swi_d are IE520. swi_e (AR4050S)
### has had NO capability verified on the device yet, so it has no ck_cap_ line.
### Keep these values COMMA-FREE except ck_profile: the framework turns a
### comma-bearing [misc] value into a list.
[misc]
ck_profile     =
ck_role_dut    = stk_a
ck_cap_swi_a   = polarity
ck_cap_swi_b   = polarity
ck_cap_swi_c   = polarity
ck_cap_swi_d   = polarity

```

## §3. Power — PDU outlets

The outlet field is parsed with `int()`, so the PDU front-panel *letter* is a label only.
The AR4050S's outlet is not known, so it is deliberately absent here and in §6.

```setup
### PDU/sentry outlets. Format: pwr_X = (pdu, <IP>, <outlet>)
### The outlet field is parsed with int() (Setup.py: int(outTuple[2]) for any
### non-awplus type), so it MUST be the numeric outlet -- the PDU front-panel LETTER
### is a label only. A-H = 1-8: D = 4, E = 5, F = 6, H = 8.
### PDU 10.36.150.14. Outlet map is per PHYSICAL UNIT / console (NOT per member ID),
### measured 2026-09-14, Terrence-confirmed 2026-09-15, unchanged 2026-09-18:
###   F/6 = /dev/u2 = member 1 (swi_a)      E/5 = /dev/u5 = member 3 (swi_c, master)
###   H/8 = /dev/u3 = member 2 (swi_b)      D/4 = /dev/u4 = member 4 (swi_d)
### !! swi_e (AR4050S, /dev/u1): OUTLET UNKNOWN as at 2026-09-18 -- no pwr_e declared.
###    Add it here AND in [powerlink] once Terrence identifies it.
[power]
pwr_a = (pdu, 10.36.150.14, 6)
pwr_b = (pdu, 10.36.150.14, 8)
pwr_c = (pdu, 10.36.150.14, 5)
pwr_d = (pdu, 10.36.150.14, 4)

```

## §4. Devices and consoles

The console-to-unit mapping is re-derived from login banners and `show system
serialnumber`, never trusted from a record — this file has had the IE520 serials on
the wrong consoles before.

```setup
### swi_a = IE520 stack member 1 (S/N 264A23061, /dev/u2) -- PDU F/6 -- port1.0.x
### swi_b = IE520 stack member 2 (S/N 264A23068, /dev/u3) -- PDU H/8 -- port2.0.x  prio 2
### swi_c = IE520 stack member 3 (S/N 264A23066, /dev/u5) -- PDU E/5 -- port3.0.x
###         !! SUSPECT HARDWARE (header item 3) and ACTIVE MASTER at 2026-09-18
###         (mastership moves after every failover -- read `show stack`).
### swi_d = IE520 stack member 4 (S/N 264A23052, /dev/u4) -- PDU D/4 -- port4.0.x
### swi_e = AR4050S-5G "4050-5g" (S/N A10401G214000005, base MAC 0000.cd40.0394,
###         /dev/u1) -- PDU outlet UNKNOWN -- port1.0.1-1.0.8 switch ports + eth1/eth2
###         WAN (unused). Standalone router; vlan1 10.38.215.70/27 STATIC, vlan10
###         10.10.10.2/27 on po1. Running awplus_main-20260918-7 (AR4050S-tb470.rel),
###         bootloader 5.2.8, boot config flash:/default.cfg. See header item 5.
### swi_f = x230-10GP "x230-10GP" (S/N G26ZE80EN, base MAC 001a.eb91.cca1, /dev/u0)
###         !! CONSOLE IS 9600 BAUD -- every other console here is 115200. At 115200 the
###         port returns NUL bytes and reads exactly like a dead or still-booting device.
###         AW+ 5.5.5 (awplus_5.5.5_2-20260918-7), bootloader 3.2.16, boot config
###         flash:/default.cfg. All ports access vlan 100; SVI 10.38.215.2/27.
###         Joined to the stack by static LAG sa2 (port1.0.3 + port1.0.4). PDU outlet
###         UNKNOWN -- not declared in [power]/[powerlink].
###         NO MRP SUPPORT (`show mrp`/`mrp` unrecognised) -- see Open items.
### NOT DECLARED: /dev/u6 = ABSENT since 2026-09-18 (the x230-52GT V2 of 09-15 is gone).
### Console<->unit is re-derived EVERY RUN by bench_probe.py from the login banners
### (`awplus` bare = Active Master, `awplus-N` = member N, `4050-5g` = swi_e) and
### `show system serialnumber`. Do NOT trust a recorded mapping: this file has had
### IE520 S/Ns on the opposite consoles before, and /dev/uN enumeration shifts.
[switch]
swi_a = /dev/u2
swi_b = /dev/u3
swi_c = /dev/u5
swi_d = /dev/u4
swi_e = /dev/u1
swi_f = /dev/u0

[baudrates]
swi_a = 115200
swi_b = 115200
swi_c = 115200
swi_d = 115200
swi_e = 115200

```

## §5. The stack

`stk_a` is the four IE520s as one virtual chassis. `[configured_stackport]` stays empty
because ports 27/28 are the dedicated defaults and all eight are in use as the ring.

```setup
### The four IE520s as one virtual chassis. Members are listed by their [switch] names,
### which Setup.py validates with __checkMember. The list order here is NOT the member
### ID and does not set it (member IDs are 1/2/3/4 -> swi_a/swi_b/swi_c/swi_d, header
### item 1). swi_e is NOT a member -- it is the stack's link partner.
[stack]
stk_a = swi_a, swi_b, swi_c, swi_d

### NON-DEFAULT stacking ports only -- deliberately EMPTY. IE520 ports 27 and 28 are the
### DEDICATED defaults and all eight (four members x 27/28) are in use as the ring:
###   m1.28<->m2.27, m2.28<->m4.27, m4.28<->m3.27, m3.28<->m1.27  (ring 1-2-4-3-1),
###   all "Learnt neighbor", re-measured 2026-09-18.
### Notes carried forward:
###   - `no stackport` DOES stick on 27/28 across a reboot (verified 2026-08-18).
###     It needs `write` + reboot to take effect, and `switchport resiliencylink` is
###     rejected while a port is still a stackport, so repurposing is a two-pass job.
###   - `stack virtual-chassis-id` has NO `no` form.
###   - The "never cable 27/28 between two units" hazard applies to STANDALONE units
###     both claiming ID 1 with a shared chassis-id; it does not apply to a properly
###     formed stack, which is what is cabled now.
[configured_stackport]

```

## §6. Power links

A device with no powerlink does **not** fail fast — it logs and returns `False`, then the
suite waits 1800 s for a bootloader banner that can never appear. **`swi_e` is in exactly
that position until its outlet is known.**

```setup
### Maps each device to its [power] outlet -- what lets a test power-cycle a device.
### A device with no powerlink does NOT fail fast: ATSwitch.__power() logs
### "Power object is not available" and returns False WITHOUT raising, so a suite
### calling dut.off() carries on and then waits for a bootloader banner that can
### never appear, at AWPConsoleCore's flat 1800 s default.
### !! Power-cycling ANY of swi_a..swi_d cycles ONE MEMBER OF A LIVE 4-MEMBER STACK --
###    a stack failover event, not a standalone reboot. A test written for a standalone
###    DUT will not measure what it thinks it is measuring.
### !! swi_e (AR4050S) HAS NO POWERLINK because its PDU outlet is unknown (2026-09-18).
###    Any test that power-cycles swi_e will hit the silent-False path above.
[powerlink]
swi_a = pwr_a
swi_b = pwr_b
swi_c = pwr_c
swi_d = pwr_d

```

## §7. Boot source

All five devices boot from flash; the IE520s' AW+ `show boot` pointer is
bootloader-overridden and must be ignored (header item 4).

```setup
### All four IE520 members boot from flash (IE520-awplus_main-20260913-1734.rel -- the
### only .rel in each member's flash). Setup.py applies a stack-level value to every
### member, so stk_a is declared too. swi_e boots AR4050S-tb470.rel from its own flash
### (`show system`: Current software AR4050S-tb470.rel, boot config flash:/default.cfg).
### !! AW+ `show boot` on the IE520s IS NOT A USABLE FIELD -- THE BOOTLOADER OVERRIDES
###    IT (header item 4). `show boot` reads "Current boot image : flash:/IE520-tb470.rel
###    (file not found)" while every member RUNS IE520-awplus_main-20260913-1734.rel.
###    That is EXPECTED; do NOT chase the "(file not found)". Read the build from
###    `show system`/`show version`. [boot_from_flash]=True here declares that these
###    units boot from flash (they do, via the bootloader), not the old TFTP netboot path.
[boot_from_flash]
stk_a = True
swi_a = True
swi_b = True
swi_c = True
swi_d = True
swi_e = True

```

## §8. Cabling — the portlink map

This is the section that goes stale fastest, and the one every other document now points
at. Every line below is backed by the evidence block that precedes it in the emitted
file; nothing is declared without it.

```setup
### <devA>-<devB> = <portOnA>-<portOnB>, comma-separated. The literal device "tb" =
### the testbox itself. Each declared link is CONSUMED by one init_portlink() call,
### so two calls between the same pair need two links declared here.
###
### A portlink names the MEMBER switch, never the stack: Setup.py keys links on the
### member and `get_temporary_testbox_portlink()` walks the other stack members
### itself when the queried member has no direct link.
###
### ===== MEASURED 2026-09-23 -- LLDP both ends, host-MAC learning per port, ping =====
### Terrence recabled 2026-09-23. TWO STATIC LAGs now, and every TB NIC lands DIRECTLY
### on the stack -- neither partner device is in a host path any more.
###
### Inter-device links:
###   stack member 3 (swi_c) port3.0.2  <->  swi_e port1.0.3   ┐ STATIC LAG sa1, vlan10
###   stack member 4 (swi_d) port4.0.2  <->  swi_e port1.0.4   ┘ STRADDLES stack units 3+4
###   stack member 1 (swi_a) port1.0.2  <->  swi_f port1.0.3   ┐ STATIC LAG sa2, vlan1
###   stack member 1 (swi_a) port1.0.9  <->  swi_f port1.0.4   ┘ (swi_f side vlan100)
###
### Testbox edges (each host MAC learned on a PHYSICAL stack port):
###   tb eth1 10.38.215.1/27   00f0.4d00.7716  <->  member 3 (swi_c) port3.0.13 (vlan1)
###   tb eth2 10.38.215.33/27  00f0.4d00.7717  <->  member 2 (swi_b) port2.0.2  (vlan1)
###   tb eth3 10.38.215.65/27  00f0.4d00.7718  <->  member 3 (swi_c) port3.0.9  (vlan1)
### These eight links plus the eight 27/28 stackport cables are the ONLY cables here.
###
### !! BOTH LAGs ARE AGGREGATES, NOT INDEPENDENT PATHS. Consuming one member with
###    init_portlink() and treating it as its own path is wrong -- traffic hashes across
###    both members. For sa2 it is worse than wrong: the two stack<->swi_f links are
###    PARALLEL, RSTP is disabled on every device here, and the ONLY thing stopping that
###    being a broadcast loop is that they are aggregated. Do not un-bundle one end.
###    There is no .setup section for aggregation, hence this note.
###
### !! `lacp global-passive-mode` silently enrols a freed port into a new aggregation.
###    It has caused a failure on all three devices (stack 09-21, swi_e 09-22 -- a ring
###    with NO blocking port, because STP runs on the aggregator and that aggregator was
###    down -- and swi_f 09-23). It is now DISABLED on all three. Leave it off.
###
### ADDRESSING as at 2026-09-23 (details: "Current state -- 2026-09-23"):
###   stack vlan1 10.38.215.10/27 primary + 10.38.215.40/27 + 10.38.215.66/27 secondary
###   (eth1's, eth2's and eth3's /27s, one bridged L2 domain);
###   stack vlan10 10.10.10.1/27 on sa1; swi_e vlan10 10.10.10.2/27 on sa1.
###   swi_e vlan1 10.38.215.70/27 -- NO LONGER has a TB edge (eth3 moved to the stack).
###   swi_f all ports vlan100, SVI 10.38.215.2/27.
###   RSTP disabled on all three. Verified end to end 2026-09-23: eth1/eth2/eth3 0% loss,
###   vlan10 transit 3/3, transit THROUGH the DUT (inject eth2, capture eth1) 10/10.
[portlink]
### tb- lines first, then inter-switch links (SETUP-FILE-REFERENCE.md checklist).
### Two tb-swi_c lines: eth1 and eth3 both land on member 3, on different ports.
tb-swi_c = eth1-port3.0.13
tb-swi_b = eth2-port2.0.2
tb-swi_c = eth3-port3.0.9
swi_c-swi_e = port3.0.2-port1.0.3
swi_d-swi_e = port4.0.2-port1.0.4
swi_a-swi_f = port1.0.2-port1.0.3
swi_a-swi_f = port1.0.9-port1.0.4
```
