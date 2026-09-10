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

## Current state — 2026-09-11 (EPSR REMOVED → loop-free vlan10 star; flash boot)

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
  ID 0xd6f). Member 2 (u3) is `stack 2 priority 2` (wins master at boot). After the last failover
  test member 1 (u2) is Active Master; member 2 is Backup. (S/N 264A23066 on u5 is still the
  suspect-hardware unit from the header item 3 — the fault tracks the S/N, now standalone.)

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

Testbox edge used/proven this session:
  tb eth1 10.38.215.1/27  <->  stack member1 port1.0.2  (untagged vlan1)  -- the failover path
```

The three edges above formed the old EPSR triangle (stack—u4—u5—stack). To make a loop-free star
**with a single active link per leg**, both u4↔u5 links (sa3) and both redundant *member-2* legs
(u4 port1.0.23, u5 port2.0.23) are **admin-shut**; each device now reaches the stack over ONE
member-1 link. This also removed the DUP flooding caused by the asymmetric LAG (u4/u5 aggregate
two links into sa1/sa2; the stack has NO channel-groups, so it flooded between the two).

### Addressing / VLANs — MEASURED 2026-09-11

- **vlan10 `10.10.10.0/27`** (the inter-device transit): stack SVI `.1`, u4 `.2`, u5 `.3`. Hub =
  stack member 1. Clean pings stack→u4 and stack→u5 (0% loss, **no DUPs**, no storm).
- **vlan1** (per Terrence's rule "native vlan1 matches the connected testbox eth port's subnet"):
  stack `10.38.215.10/27` (host eth1 side, .0–.31), u5 `10.38.215.12/27` (same .0–.31 side),
  u4 `10.38.215.36/27` (eth2 side, .32–.63). Do NOT reconfigure these away.
- **vlan2** ("epsr-control") still exists as a named-but-unused VLAN on u4/u5 (harmless residue).

### EPSR — REMOVED 2026-09-11

`no epsr ring1` (datavlan removed first, then the instance) on u4 and u5; `no service epsr` set
(takes full effect on next reboot). The stack never ran an EPSR *ring* (only `service epsr`, still
present, inert). Removal order that works on this build: `epsr configuration` → `epsr <ring>
state disabled` → `no epsr <ring> datavlan <vid>` → `no epsr <ring>`.

### Boot — FLASH (not TFTP), 2026-09-11

All IE520s default-boot from a flash `.rel` (Terrence set flash default boot from the bootloader
config). `reload` is safe; the old TFTP-boot/eth3 dependency no longer applies to a normal reload.
**Gotcha:** the stack's `show boot` had a stale `Current boot image` pointing at a deleted
`tomahawk` .rel while running `IE520-tb470.rel`; corrected with `boot system flash:/IE520-tb470.rel`
(syncs the 40 MB image to the other member — console dark ~12 min) BEFORE rebooting. Always confirm
`show boot` reads `(file exists)` first. (See memory `tb470-ie520-flash-boot-reboots-ok`.)

### Test scaffolding currently live (may be torn down)

- OSPF: `service ospf` + `router ospf 1` on the stack (`network 10.10.10.0/27` + `10.38.215.0/27`
  area 0, router-id 10.38.215.10) and on u4 (`network 10.10.10.0/27` area 0, router-id 10.10.10.2).
  Adjacency **Full** on vlan10 (stack DR, u4 BDR). Added for AWPTCM T10623 Part 2b / T11427.

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

Three live traps, each of which has already cost bench time. They are emitted as the
file's own header so they are unmissable at the point of use.

```setup
###
### !! GENERATED FILE -- DO NOT HAND-EDIT.
###    Source: ~/claude/IE520-testing/bench-setup/bench-state.md on the NFS lab home
###    (/media/terrenceb/mnt/testbox_home/... from the dev host). Edit THERE, then run
###    `bench_setup.py apply`, which writes this file in place and verifies by readback.
###    An edit made here is discarded by the next apply, silently and without warning.
###    Every previous version is snapshotted in that directory's backups/ -- which is
###    why there are no longer .bak files sitting beside this one.
###
### ============================================================================
### tb470.setup -- REBUILT 2026-09-03: flat single-vlan1 loop-free TREE, the IE520 stack
### as hub (tb eth3 - IE520 - {4050, x230}); all links LLDP-confirmed on both ends.
### Supersedes the 2026-08-31 rebuild; previous versions are dated in the bench-setup
### backups/ dir named above. Read items 1-3 before binding anything.
###
###  1. !! THE TWO IE520s ARE ONE STACK. The previous file declared them as two
###     INDEPENDENT STANDALONE switches and deliberately carried NO [stack]
###     section ("the two IE520s were deliberately de-stacked 2026-07-30"). That
###     stopped being true on 2026-08-18 and they have been stacked for every run
###     since, including the 2026-08-26 failover-300 campaign. Read live today:
###         ID 1  S/N 264A23066  MAC 84e3.2787.0740  /dev/u5  Backup Member  prio 128
###         ID 2  S/N 264A23052  MAC 84e3.2787.09c0  /dev/u4  Active Master  prio 1
###         Virtual Chassis ID 3439 (0xd6f); Stack MAC 0000.cd37.0d6f (Virtual MAC)
###         Operational Status: Normal operation; both members Ready
###         All four stackports up: port1.0.27<->port2.0.28, port1.0.28<->port2.0.27
###     ==> [stack] stk_a is now declared. swi_a/swi_b REMAIN in [switch] because
###         Setup.py requires every stack member to be declared there
###         (`__checkMember`), but THEY ARE NO LONGER TWO DEVICES. On a formed AW+
###         VCStack the backup member's console is relayed to the master, so
###         init_swi('swi_a') and init_swi('swi_b') reach the SAME CLI. Do not bind
###         them as DUT + link partner -- that measures one device against itself.
###     ==> Mastership is PINNED by priority, not by chance: member 2 is priority 1
###         and wins every election, so /dev/u4 is the master until someone changes
###         it. The roles were the other way round at the 2026-08-18 session end.
###
###  2. !! PORT NUMBERING MOVED BY A MEMBER, and it fails SILENTLY. swi_a is
###     /dev/u4 = stack member **2**, so ITS ports are port2.0.x. The previous file
###     named port1.0.1 / port1.0.7 / port1.0.23 as swi_a's ports; those now belong
###     to the OTHER physical unit. Config naming the wrong range is ACCEPTED with
###     no error (this previously presented as a DHCP option-61 defect that did not
###     exist). Before any step that names a port, confirm which ID the unit holds.
###
###  3. !! THE UNIT WITH THE REBOOT FAULT IS BACK IN THE BENCH -- member 1 is
###     S/N 264A23066. The 2026-08-26 handover
###     (~/old test runs/IE520/stack-tests/failover-300/SESSION-HANDOVER.md, §2)
###     records that this unit wedged twice, was PHYSICALLY REMOVED, and was
###     replaced by S/N 264A23061. 264A23061 is NOT in the bench today; 264A23066
###     is, in the same member-1 position, carrying its own pre-swap reboot history
###     (continuous 2026-08-11 -> 2026-08-26, then a gap, then 2026-08-30). It has a
###     long run of "Unexpected System reboot" entries that member 2 does not share,
###     including one at 2026-08-30 19:53:33 with nobody driving its console.
###     ==> Treat member 1 as SUSPECT HARDWARE. Any unexplained stack event should
###         be checked against `show reboot history` before it is called a defect,
###         and the handover's conclusion that "the suspect hardware is out of the
###         bench" does not describe the bench as it stands.
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
### !! ck_profile IS DELIBERATELY EMPTY AS OF 2026-08-31. The bench implements NO
###    generation profile at present, and declaring one would be false:
###      - `base` and `fibre` both required a swi_a<->swi_b copper/fibre link. Those
###        two IE520s are now ONE stack, so there is no inter-DEVICE link to bind --
###        a cable between member 1 and member 2 front panels is a loop inside a
###        single L2 device, not a DUT-to-partner path. Measured today: the old
###        copper pair (port1.0.1 <-> port1.0.1) and fibre pair (port1.0.7 <->
###        port1.0.7) do NOT exist as declared; port1.0.7 and every other fibre cage
###        on member 2 reads `notconnect`.
###      - `tblink` required a DIRECT testbox<->DUT link. As of 2026-09-03 ONE EXISTS:
###        tb470 eth3 <-> IE520 port1.0.1 (proven by the IE520's own LLDP frame captured
###        on eth3, and by tb470 pinging 10.38.215.66). So tblink is now satisfiable; the
###        DUT-side port is stk_a port1.0.1 (member 1 / swi_b). ck_profile is nonetheless
###        left empty -- declaring a profile is a separate decision, not taken here.
###    Restoring `base`/`fibre` still needs cabling (the two IE520s are one stack -- no
###    inter-device link). Do not add a profile the hardware does not implement.
###
### ck_cap_* records capabilities VERIFIED ON THE DEVICE, never inferred from docs.
### `polarity` is documented for 29 products NOT including ie520, yet both IE520s
### support it (confirmed at the console 2026-07-30 via `polarity ?`). Absence from
### the harvested CLI reference means UNKNOWN, not unsupported.
### Keep these values COMMA-FREE except ck_profile: the framework turns a
### comma-bearing [misc] value into a list.
[misc]
ck_profile     =
ck_role_dut    = stk_a
ck_cap_swi_a   = polarity
ck_cap_swi_b   = polarity

```

## §3. Power — PDU outlets

The outlet field is parsed with `int()`, so the PDU front-panel *letter* is a label only.

```setup
### PDU/sentry outlets. Format: pwr_X = (pdu, <IP>, <outlet>)
### The outlet field is parsed with int() (Setup.py: int(outTuple[2]) for any
### non-awplus type), so it MUST be the numeric outlet -- the PDU front-panel LETTER
### is a label only. A-H = 1-8: D = 4, E = 5, F = 6, H = 8.
### PDU 10.36.150.14 confirmed reachable 2026-08-31.
[power]
pwr_a = (pdu, 10.36.150.14, 4)
pwr_b = (pdu, 10.36.150.14, 5)
pwr_c = (pdu, 10.36.150.14, 8)
pwr_d = (pdu, 10.36.150.14, 6)

```

## §4. Devices and consoles

The console-to-unit mapping is re-derived from login banners and `show system
serialnumber`, never trusted from a record — this file has had the two IE520 serials on
the opposite consoles before.

```setup
### swi_a = IE520 stack member 2 (Active Master, S/N 264A23052) -- PDU outlet 4 "D"
### swi_b = IE520 stack member 1 (Backup Member, S/N 264A23066) -- PDU outlet 5 "E"
###         !! SUSPECT HARDWARE -- see item 3 of the header.
### swi_c = AR4050S-5G, S/N A10401G214000005, MAC 0000.cd40.0394 -- PDU outlet 8 "H"
### swi_d = x230-10GP,  S/N G26ZE80EN,        MAC 001a.eb91.cca1 -- PDU outlet 6 "F"
### u2, u3 = POWERED OFF (as at 2026-07-29).
### Console<->unit mapping re-confirmed 2026-08-31 from the login banners
### (`awplus` bare = Active Master, `awplus-1` = member 1) and `show system
### serialnumber`. Do NOT trust a recorded mapping: this file has had the two IE520
### S/Ns on the opposite consoles before.
[switch]
swi_a = /dev/u4
swi_b = /dev/u5
swi_c = /dev/u1
swi_d = /dev/u0

[baudrates]
swi_a = 115200
swi_b = 115200
swi_c = 115200
swi_d = 9600

```

## §5. The stack

`stk_a` is the two IE520s as one virtual chassis. `[configured_stackport]` stays empty
because ports 27/28 are the dedicated defaults and all four are in use.

```setup
### The two IE520s as one virtual chassis. Members are listed by their [switch]
### names, which Setup.py validates with __checkMember.
### swi_a is member ID 2 and swi_b is member ID 1 -- the list order here is NOT the
### member ID and does not set it.
[stack]
stk_a = swi_a, swi_b

### NON-DEFAULT stacking ports only -- deliberately EMPTY. IE520 port 27 and 28 are
### the DEDICATED defaults and all four are in use as stackports today
### (port1.0.27<->port2.0.28 and port1.0.28<->port2.0.27, both "Learnt neighbor").
### Notes carried forward, both corrected since this file last claimed otherwise:
###   - `no stackport` DOES stick on 27/28 across a reboot (verified 2026-08-18).
###     It needs `write` + reboot to take effect, and `switchport resiliencylink` is
###     rejected while a port is still a stackport, so repurposing is a two-pass job.
###   - `stack virtual-chassis-id` has NO `no` form.
###   - The "never cable 27/28 between the two units" hazard applies to two
###     STANDALONE units both claiming ID 1 with a shared chassis-id. It does not
###     apply to a properly formed stack, which is what is cabled now.
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
### !! Power-cycling swi_a or swi_b now cycles ONE MEMBER OF A LIVE STACK, which is
###    a stack failover event, not a standalone reboot. A test written for a
###    standalone DUT will not measure what it thinks it is measuring.
[powerlink]
swi_a = pwr_a
swi_b = pwr_b
swi_c = pwr_c
swi_d = pwr_d

```

## §7. Boot source

Both members boot from flash with autoboot disabled.

```setup
### Both members boot from flash: `flash:/IE520-20260825.rel`, autoboot disabled.
### Setup.py applies a stack-level value to every member, so stk_a is declared too.
### Cosmetic oddity, do NOT chase it: `show boot` reads
### "Current software : IE520-tb470.rel" while "Current boot image" is
### flash:/IE520-20260825.rel. Those are two different files in flash (Aug 18 vs
### Aug 25); `show version` returns the same build on BOTH members
### (AlliedWare Plus 0.0.0 08/19/26 02:20:43, tomahawk_ie520-continuous), so this is
### stale labelling, not a version mismatch. Recorded in the 2026-08-26 handover.
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
### ===== MEASURED 2026-09-03 -- flat vlan1 TREE, LLDP-confirmed on BOTH ENDS =====
### Method: `show lldp neighbors` on every device (LLDP enabled on all three today),
### cross-checked with `show mac address-table` / `show arp` and host-side tcpdump.
### Nothing below is inferred; each link is seen from both ends (the testbox leg from
### the host). Raw captures (bench_probe.py, all three devices):
###   ~/old test runs/IE520/stack-tests/bench-probe-2026-09-03/capture.json
###   ~/old test runs/IE520/stack-tests/bench-probe-2026-09-03/lldp-clean.json
###
###   tb eth3 <-> swi_b port1.0.1   (IE520 stack MEMBER 1)
###     tb470 is a Linux host and sends no LLDP, so proven host-side: the IE520's own
###     LLDP frame (chassis 0000.cd37.0d6f, Port ID port1.0.1) was captured on eth3
###     (tcpdump ether proto 0x88cc). tb470 pings the IE520 at 10.38.215.66.
###
###   swi_a port2.0.1 <-> swi_c port1.0.3   (untagged vlan1)
###     IE520 LLDP sees 0000.cd40.0394 / port1.0.3; the 4050 sees 0000.cd37.0d6f /
###     port2.0.1 (System Name awplus, cap --B-R---).
###
###   swi_a port2.0.9 <-> swi_d port1.0.4   (untagged vlan1)
###     IE520 LLDP sees 001a.eb91.cca1 / port1.0.4; the x230 sees 0000.cd37.0d6f /
###     port2.0.9.
###
### ADMIN-SHUT, NOT A PORTLINK: swi_c port1.0.2 <-> swi_d port1.0.2. The cable is still
### plugged but BOTH ends are `shutdown`, so the three-switch triangle stays a tree. It
### is deliberately NOT declared below -- init_portlink() needs the link UP and would
### grade a shut link as (None, None). Un-shut it only with RSTP active on all three.
###
### swi_c IS A ROUTER (AR4050S), bench role 802.1X -- not a switch. See the permanent
### `lacp global-passive-mode enable` warning in the prose "Evidence" section above:
### never present two non-aggregated links to it, they loop.
###
### SEGMENTS / ADDRESSING as at 2026-09-03 -- one flat vlan1 .64/27 domain:
###   tb eth3 10.38.215.65/27  -- ALSO the DHCP server for this /27 (ISC dhcpd on eth3,
###                               range .68-.94, router .65; .66/.67 held for statics).
###   stk_a vlan1 10.38.215.66/27  static   (ntp server 10.38.215.65 -> stratum 3)
###   swi_c vlan1 10.38.215.70/27  static
###   swi_d vlan1 10.38.215.71/27  static  (re-addressed off the old vlan100 .2/27)
###   tb eth1 10.38.215.1/27 and tb eth2 10.38.215.33/27 have NO carrier (down).
###
### Four SFP LOOPBACK modules are fitted and linked on swi_a port2.0.6, 2.0.8, 2.0.14
### and 2.0.16. They loop a port to itself and are NOT links to another device, so they
### are not portlinks -- but they are why those ports read "connected" with no
### neighbour. RSTP holds them Discarding.
[portlink]
### Physical links only. A portlink names the MEMBER switch, never the stack, and the
### literal device "tb" is the testbox. Every line is LLDP-confirmed both ends (the tb
### leg host-side); evidence is in the MEASURED 2026-09-03 block above. The admin-shut
### swi_c<->swi_d cable is intentionally omitted (it is down).
tb-swi_b = eth3-port1.0.1
swi_a-swi_c = port2.0.1-port1.0.3
swi_a-swi_d = port2.0.9-port1.0.4
```
