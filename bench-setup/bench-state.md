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

## Current state — 2026-09-15 (4-member stack re-formed, flash boot; captured by bench_probe.py)

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

Four live traps, each of which has already cost bench time. They are emitted as the
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
### tb470.setup -- REWRITTEN 2026-09-15 for the single 4-MEMBER IE520 VCStack, measured
### by bench_probe.py sweeping /dev/u0-u6 (host edges from its own host-NIC mapping).
### Supersedes the 2026-09-03 2-member tree; previous versions are dated in the
### bench-setup backups/ dir named above. Read items 1-4 before binding anything.
###
###  1. !! THE FOUR IE520s ARE ONE STACK (stk_a), not four devices. A new mainline build
###     (awplus_main-20260913-1734) lifted the old 2-member VCStack cap, and the four
###     units were re-formed into ONE 4-member ring stack on 2026-09-13/14. Read live
###     2026-09-15 (`show stack`):
###         ID 1  S/N 264A23061  MAC 84e3.2787.0ac0  /dev/u2  Backup Member  prio 128
###         ID 2  S/N 264A23068  MAC 84e3.2787.0780  /dev/u3  Backup Member  prio 2
###         ID 3  S/N 264A23066  MAC 84e3.2787.0740  /dev/u5  Backup Member  prio 128
###         ID 4  S/N 264A23052  MAC 84e3.2787.09c0  /dev/u4  ACTIVE MASTER  prio 128
###         Virtual Chassis ID 3439 (0xd6f); Stack MAC 0000.cd37.0d6f (Virtual MAC)
###         Operational Status: Normal operation; all four Ready
###         Ring 27/28: m1.28<->m2.27, m2.28<->m4.27, m4.28<->m3.27, m3.28<->m1.27
###         ==> ring order 1 - 2 - 4 - 3 - 1
###     ==> All four members are declared in [switch] because Setup.py's __checkMember
###         requires it, and [stack] stk_a lists all four. On a formed VCStack every
###         member console is relayed to the master CLI, so init_swi() on ANY member
###         reaches the SAME CLI -- never bind two members as DUT + link partner, that
###         measures one device against itself.
###     ==> MASTER IS NOT PINNED BY PRIORITY HERE. Member 2 is priority 2 (lowest, so it
###         wins a FRESH election) yet member 4 is Active Master today -- a running
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
###  3. !! MEMBER 3 (S/N 264A23066, /dev/u5) IS THE SUSPECT-HARDWARE UNIT. It carries a
###     long run of "Unexpected System reboot" entries the other members do not share.
###     Treat it as suspect: check `show reboot history` before calling any unexplained
###     stack event a defect. (All fleet units have taken unattended reboots -- watch
###     every member, not only this one.)
###
###  4. !! AW+ `show boot` IS NOT A USABLE FIELD -- THE BOOTLOADER OVERRIDES IT. Every
###     member RUNS IE520-awplus_main-20260913-1734.rel (read from `show system`), while
###     `show boot` reads "Current boot image : flash:/IE520-tb470.rel (file not found)".
###     That is EXPECTED and NOT an action item: the bootloader boots the image at its
###     own prompt regardless of the AW+ boot pointer. Do NOT chase the "(file not
###     found)"; read the running build from `show system`/`show version`.
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

`ck_profile` is deliberately empty. Restoring a profile needs **cabling**, not an edit
here — see §8 for what is actually connected.

```setup
### TOPOLOGY PROFILES this bench implements -- the contract generated scripts target.
### Spec: ask-ck/pytest-create/TOPOLOGY-PROFILES.md ; checker: tool/pt_profiles.py
###
### !! ck_profile IS DELIBERATELY EMPTY. The bench implements NO generation profile at
###    present, and declaring one would be false:
###      - `base`/`fibre` require an inter-DEVICE swi<->swi copper/fibre link. The four
###        IE520s are ONE stack, so a cable between two members is a loop inside a single
###        L2 device, not a DUT-to-partner path; and the x230 on /dev/u6 is a SEPARATE
###        device that is NOT L3-joined to the stack. There is no inter-device link to bind.
###      - `tblink` requires a DIRECT testbox<->DUT link, and two now exist (measured
###        2026-09-15): tb eth1 <-> member 1 port1.0.2, and tb eth2 <-> member 4 port4.0.2.
###        So tblink is satisfiable, but ck_profile is left empty -- declaring a profile is
###        a separate decision, not taken here.
###    Do not add a profile the hardware does not implement.
###
### ck_cap_* records capabilities VERIFIED ON THE DEVICE, never inferred from docs.
### `polarity` is documented for 29 products NOT including ie520, yet the IE520 supports
### it (confirmed at the console 2026-07-30 via `polarity ?`). Absence from the harvested
### CLI reference means UNKNOWN, not unsupported. All four members are IE520.
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

```setup
### PDU/sentry outlets. Format: pwr_X = (pdu, <IP>, <outlet>)
### The outlet field is parsed with int() (Setup.py: int(outTuple[2]) for any
### non-awplus type), so it MUST be the numeric outlet -- the PDU front-panel LETTER
### is a label only. A-H = 1-8: D = 4, E = 5, F = 6, H = 8.
### PDU 10.36.150.14. Outlet map is per PHYSICAL UNIT / console (NOT per member ID),
### measured 2026-09-14 and Terrence-confirmed still valid 2026-09-15:
###   F/6 = /dev/u2 = member 1 (swi_a)      E/5 = /dev/u5 = member 3 (swi_c)
###   H/8 = /dev/u3 = member 2 (swi_b)      D/4 = /dev/u4 = member 4 (swi_d, master)
[power]
pwr_a = (pdu, 10.36.150.14, 6)
pwr_b = (pdu, 10.36.150.14, 8)
pwr_c = (pdu, 10.36.150.14, 5)
pwr_d = (pdu, 10.36.150.14, 4)

```

## §4. Devices and consoles

The console-to-unit mapping is re-derived from login banners and `show system
serialnumber`, never trusted from a record — this file has had the two IE520 serials on
the opposite consoles before.

```setup
### swi_a = IE520 stack member 1 (S/N 264A23061, /dev/u2) -- PDU F/6 -- port1.0.x
### swi_b = IE520 stack member 2 (S/N 264A23068, /dev/u3) -- PDU H/8 -- port2.0.x  prio 2
### swi_c = IE520 stack member 3 (S/N 264A23066, /dev/u5) -- PDU E/5 -- port3.0.x
###         !! SUSPECT HARDWARE -- see item 3 of the header.
### swi_d = IE520 stack member 4 (S/N 264A23052, /dev/u4) -- PDU D/4 -- port4.0.x
###         ACTIVE MASTER at 2026-09-15 (mastership moves after every failover -- read
###         `show stack`; it is NOT pinned by priority here, see header item 1).
### NOT DECLARED: /dev/u6 = standalone x230-52GT V2 (S/N A10723G261600010) -- a SEPARATE
###   device, not a stack member, not L3-joined, no PDU outlet mapped. See the prose
###   "u6 -- standalone x230-52GT V2" section. /dev/u0, /dev/u1 = POWERED OFF 2026-09-15.
### Console<->unit is re-derived EVERY RUN by bench_probe.py from the login banners
### (`awplus` bare = Active Master, `awplus-N` = member N) and `show system
### serialnumber`. Do NOT trust a recorded mapping: this file has had IE520 S/Ns on the
### opposite consoles before, and the /dev/uN enumeration shifts across restacks.
[switch]
swi_a = /dev/u2
swi_b = /dev/u3
swi_c = /dev/u5
swi_d = /dev/u4

[baudrates]
swi_a = 115200
swi_b = 115200
swi_c = 115200
swi_d = 115200

```

## §5. The stack

`stk_a` is the four IE520s as one virtual chassis. `[configured_stackport]` stays empty
because ports 27/28 are the dedicated defaults and all eight are in use as the ring.

```setup
### The four IE520s as one virtual chassis. Members are listed by their [switch] names,
### which Setup.py validates with __checkMember. The list order here is NOT the member
### ID and does not set it (member IDs are 1/2/3/4 -> swi_a/swi_b/swi_c/swi_d, header
### item 1).
[stack]
stk_a = swi_a, swi_b, swi_c, swi_d

### NON-DEFAULT stacking ports only -- deliberately EMPTY. IE520 ports 27 and 28 are the
### DEDICATED defaults and all eight (four members x 27/28) are in use as the ring:
###   m1.28<->m2.27, m2.28<->m4.27, m4.28<->m3.27, m3.28<->m1.27  (ring 1-2-4-3-1),
###   all "Learnt neighbor", measured 2026-09-15.
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
suite waits 1800 s for a bootloader banner that can never appear.

```setup
### Maps each device to its [power] outlet -- what lets a test power-cycle a device.
### A device with no powerlink does NOT fail fast: ATSwitch.__power() logs
### "Power object is not available" and returns False WITHOUT raising, so a suite
### calling dut.off() carries on and then waits for a bootloader banner that can
### never appear, at AWPConsoleCore's flat 1800 s default.
### !! Power-cycling ANY of swi_a..swi_d cycles ONE MEMBER OF A LIVE 4-MEMBER STACK --
###    a stack failover event, not a standalone reboot. A test written for a standalone
###    DUT will not measure what it thinks it is measuring. (The x230 on /dev/u6 has NO
###    powerlink on purpose: no outlet mapped, and it is not a bench device.)
[powerlink]
swi_a = pwr_a
swi_b = pwr_b
swi_c = pwr_c
swi_d = pwr_d

```

## §7. Boot source

All four members boot from flash; the AW+ `show boot` pointer is bootloader-overridden and
must be ignored (header item 4).

```setup
### All four members boot from flash (IE520-awplus_main-20260913-1734.rel -- the only
### .rel in each member's flash, verified per member by bench_probe.py 2026-09-15).
### Setup.py applies a stack-level value to every member, so stk_a is declared too.
### !! AW+ `show boot` IS NOT A USABLE FIELD -- THE BOOTLOADER OVERRIDES IT (header item
###    4). `show boot` reads "Current boot image : flash:/IE520-tb470.rel (file not
###    found)" while every member RUNS IE520-awplus_main-20260913-1734.rel. That is
###    EXPECTED; do NOT chase the "(file not found)". Read the build from `show system`/
###    `show version`. [boot_from_flash]=True here just declares that these units boot
###    from flash (they do, via the bootloader), not from the old TFTP netboot path.
[boot_from_flash]
stk_a = True
swi_a = True
swi_b = True
swi_c = True
swi_d = True

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
### ===== MEASURED 2026-09-15 by bench_probe.py host-edge derivation =====
### Method: ping out each up host NIC to force one ARP broadcast, then grep every
### console's `show mac address-table` for that NIC's MAC; the PHYSICAL portN.0.x hit is
### the cabled edge (a trunk/saN hit is arrival via aggregation, not the edge). Nothing
### below is inferred.
###
###   tb eth1 10.38.215.1/27   00f0.4d00.7716  <->  member 1 (swi_a) port1.0.2  (carrier up)
###   tb eth2 10.38.215.33/27  00f0.4d00.7717  <->  member 4 (swi_d) port4.0.2  (carrier up)
###   tb eth3 10.38.215.65/27  00f0.4d00.7718  --  carrier DOWN 2026-09-15, edge NOT learned.
###       (Reached member 3 port3.0.2 on 2026-09-14; re-derive when eth3 is back up --
###        the probe does this every run.)
###
### NO inter-device portlinks: the four IE520s are ONE stack (an inter-member cable is a
### loop inside one L2 device, not a DUT-to-partner path), and the x230 on /dev/u6 is a
### separate device that is NOT L3-joined. If an inter-device link is added later, declare
### it here from a fresh measurement.
###
### ADDRESSING as at 2026-09-15 -- vlan1 is ONE bridged L2 domain across the three host
### /27s; the stack's only vlan1 SVI is 10.38.215.10/27 (in eth1's .0/27), so AT L3 the
### stack reaches only eth1 (.1). eth2 (.33) and eth3 (.65) are bridged at L2 but have no
### SVI. vlan10 "data" SVI 10.10.10.1/27. (This is why firmware TFTP only worked from .1.)
[portlink]
### Physical links only. A portlink names the MEMBER switch, never the stack, and the
### literal device "tb" is the testbox. Both lines below are MEASURED 2026-09-15 by host
### MAC learning (the NIC's MAC seen on a physical member port, not via a trunk). eth3 is
### omitted because it is carrier-down (its edge could not be learned).
tb-swi_a = eth1-port1.0.2
tb-swi_d = eth2-port4.0.2
```
