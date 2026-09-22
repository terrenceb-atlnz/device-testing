# Session handover — tb470 IE520 — 2026-09-23

## TL;DR

**Bench is WHOLE and re-runnable.** The 72-case IE520 campaign is **complete** (39 PASS ·
1 PARTIAL · 32 UNMEASURED). Afterwards Terrence recabled and the bench was reconfigured
into **two static LAGs**, with all three TB NICs now landing **directly on the stack**.
Everything is **saved to startup-config** and recorded in `bench-setup/bench-state.md`
("Current state — 2026-09-23"); `tb470.setup` regenerated and applied.

Nothing is parked, nothing is powered off, nothing is left `shutdown` except one
deliberate link (below).

## Verify the bench in one block

```bash
ssh tb470
# stack whole, master (moves after any failover -- read it, never assume)
#   expect: 4/4 Ready, "Normal operation", Stack MAC 0000.cd37.0d6f
minicom --wrap -D /dev/u5     # or drive with pyserial; see Recipes
#   show stack ; show static-channel-group ; show interface status
#   show boot        -> "flash:/IE520-tb470.rel (file not found)" is EXPECTED
#                       (bootloader overrides it; read the real build from show system)
#   show system      -> awplus_main-20260913-1734 on ALL FOUR members

# host edges -- all three must be 0% loss
for s in "eth1 10.38.215.10" "eth2 10.38.215.40" "eth3 10.38.215.66"; do set -- $s
  echo "$1 -> $2: $(ping -I $1 -c2 -W2 $2 | grep -oE '[0-9]+% packet loss')"; done
# vlan10 transit across sa1
#   from the stack CLI: ping 10.10.10.2 repeat 3
```

## Current bench state

**Topology (measured 2026-09-23 — LLDP both ends, host-MAC learning, ping):**

| link | |
| --- | --- |
| **`sa1`** stack `port3.0.2` + `port4.0.2` ↔ 4050 `port1.0.3` + `port1.0.4` | static LAG, vlan 10. **Straddles stack units 3 and 4.** |
| **`sa2`** stack `port1.0.2` + `port1.0.9` ↔ x230 `port1.0.3` + `port1.0.4` | static LAG, vlan 1 (x230 side vlan 100) |
| tb `eth1` → stack `port3.0.13` · `eth2` → `port2.0.2` · `eth3` → `port3.0.9` | all three hosts direct on the stack |
| 4050 `port1.0.2` ↔ x230 `port1.0.2` | **deliberately `shutdown`** — see hazard below |

**Addressing:** stack vlan1 `10.38.215.10/27` + `.40/27` + `.66/27` secondary; stack
vlan10 `10.10.10.1/27` on `sa1`; 4050 vlan10 `10.10.10.2/27` on `sa1`; 4050 vlan1
`10.38.215.70/27` (**no TB edge any more**); x230 all ports vlan 100, SVI `10.38.215.2/27`.

**Third device:** x230-10GP on `/dev/u0` — **console is 9600 baud**, every other console
here is 115200. At 115200 it returns NUL bytes and reads as a dead device.

**RSTP is disabled on all three devices** (bench design). Saved to startup on the stack.

## !! The one standing hazard

**Do not un-bundle `sa2`, and do not bring up 4050 `port1.0.2`.** The two stack↔x230
links are parallel; with RSTP off the *only* thing making them safe is that they are
aggregated. Bringing up the 4050↔x230 leg additionally closes a stack/4050/x230 triangle.
Both were verified inert at wrap time.

This was demonstrated the hard way on 2026-09-22: closing that triangle produced a ring
with **no port anywhere in Discarding**, because `lacp global-passive-mode` had silently
enrolled the 4050 port into a channel-group, and **STP runs on the aggregator** — which
was down. Rule: before closing any redundant leg, confirm the port appears in
`show spanning-tree brief` **as a port with a real state**. "Spanning Tree Enabled" is not
the check.

## What was accomplished

1. **72-case IE520 campaign, all seven groups** — ACL, Authentication, MRP, QoS,
   STP & storm control, switching, IPv6 routing & protocol. Per-case `<case-id>.log` in
   dated group directories under `IE520/`, each with a README carrying the group verdict.
2. **Bench rebuild** after Terrence's recable — two static LAGs, hosts moved onto the
   stack, config saved, records updated. See `IE520/bench-rebuild-2026-09-23/`.

## Results

| group | verdict | directory |
| --- | --- | --- |
| ACL (13) | 11 PASS · 2 UNMEASURED | `IE520/acl-2026-09-22/` |
| Authentication (7) | 1 PASS · 6 UNMEASURED | `IE520/auth-2026-09-22/` |
| MRP (5) | 5 UNMEASURED | `IE520/mrp-2026-09-22/` |
| QoS (12) | 9 PASS · 3 UNMEASURED | `IE520/qos-2026-09-22/` |
| STP & storm (8) | 6 PASS · 2 UNMEASURED | `IE520/stp-2026-09-22/` |
| switching (11) | 6 PASS · 1 PARTIAL · 4 UNMEASURED | `IE520/switching-2026-09-22/` |
| IPv6 routing (16) | 6 PASS · 10 UNMEASURED | `IE520/ipv6-2026-09-22/` |

**All runs are CLEAN unless the log says otherwise.** Every measurement is on traffic that
**transits** the DUT (inject on one TB NIC, capture on another) with a **baseline taken
first with the feature off**, so a drop is provably the feature.

**Runs that were CONFOUNDED and are labelled as such in their logs:**
- The first IGMP/MLD snooping pass — the observation path ran **through the x230**, which
  has its own snooping on by default and was pruning the DUT's flood downstream. Re-run
  with x230 snooping off. *(This is now structurally fixed: eth1 is direct on the stack.)*
- T3111 (BGP default route) — filtered by **T3112's own prefix-list**, still bound to the
  same neighbour, containing `deny ::/0 le 128`. Two cases sharing one live session.
- T16453 (loop-protection link-down) — the ring never actually closed, so **no loop
  protection action was an incomplete stimulus, not a failure**.

**The 32 UNMEASURED are almost entirely bench limits, not product results**: needs a
line-rate generator (9) · needs more cabled ports or hosts (14, several now unblocked by
today's recable) · needs a peer device the bench lacks (6) · case has no steps in `ck.db`
(3) · the feature's subject does not exist on this platform (4).

## Findings

**Measured:**
- No implicit deny on a hardware IPv6 ACL via `ipv6 traffic-filter` — unmatched traffic
  forwards 10/10; `deny ipv6 any any` must be written explicitly.
- MAC-auth sends the MAC to RADIUS as **`00-f0-4d-00-77-17`** (lowercase, hyphenated);
  no `auth-mac username-format` command exists on this build.
- Default auth `host-mode` is single-host: one **failed** supplicant occupies the port so a
  good MAC behind it never authenticates.
- Changing `spanning-tree mode` **silently re-enables spanning tree**, discarding a prior
  `no spanning-tree <mode> enable`.
- `lacp global-passive-mode` silently enrols freed ports into aggregations — hit on **all
  three devices**; now disabled on all three.
- A static LAG refuses members whose properties differ; align VLAN/mode **before**
  `static-channel-group`.
- The DUT does not learn ARP from unsolicited/gratuitous ARP (6000 → 0 entries), while a
  single ping creates an entry immediately.
- `atmf cleanup` is **refused on a VCStack** (`% This command cannot be run when another
  stack member is present`) — this blocks AWPTCM-T38474 and T38475 entirely.
- Each IE520-28GSX member has **three** copper ports (`portN.0.2/.9/.13`), not one.
  **Correcting an earlier record**; the campaign logs that cite "one copper port per
  member" as a blocker overstate it — the real limits were uncabled ports and host count.

**Inferred (not proven):**
- ATMF secure mode not re-forming a 2-node network (T38472) is scoped to **"over an LACP
  aggregate"** — a single-physical-link control was never run. Cause unknown.
- The 2026-09-18 member-1 boot hang (`Starting kernel …` then silence) remains **n=1, no
  root cause**; a 20-cycle pinned re-run did not reproduce it.

## OPEN questions

1. **Is ATMF secure mode broken, or only over an aggregate?** Evidence path: remove
   `atmf-link` from `po1`/`sa1`, put `switchport atmf-link` on ONE physical port with the
   other member shut, re-run `atmf secure-mode enable-all`. → `IE520/atmf-2026-09-21/38472.log`
2. **Should T38474/T38475 be run by destacking to a single IE520?** That changes the DUT
   from a VCStack to a standalone switch. Terrence's call.
3. **Three cases have no steps in `ck.db`** (`38435`, `38148`, and `6005`/`38151`/`38487`
   which I interpreted from their titles and said so). Do they need defining?
4. **The AR4050S lists MRP as a licensed feature but exposes no MRP CLI.** A licence entry
   is not a capability — worth raising.
5. **`show arp counter` and `show platform table ipv6route` do not exist on this build**
   though they appear in case methods.

## Ordered next steps

1. **Re-run the cases the recable unblocked** — now buildable and not previously possible:
   ACL `881/885/890/889` and QoS `13604` against **`sa1`, which now straddles stack units
   3 and 4**; the mirror-delivery half of ACL `943`/`830` using `eth3`; the IPv6
   multicast/PIM set with three hosts direct on the stack.
2. **STP `38152`/`38153` alternate-path half** — `sa2` gives a redundant stack↔x230 path.
3. Answer OPEN #1 (one physical atmf-link) — cheap and settles a real finding.
4. Anything needing line rate waits for the ixia.

## Recipes

```bash
# drive a console (pyserial, NOT minicom -- minicom needs a TTY)
#   maintained driver: IE520/stack-tests/linkflap-38378-2026-09-18/console.py
#   x230 on /dev/u0 is 9600; everything else 115200
#   ALWAYS stty -F $(readlink -f /dev/uN) -hupcl first, or closing the port BREAKs the DUT

# campaign harness (recreate in tmpfs; it is NOT in the repo -- no-stray-py hook)
#   design + rebuild instructions: IE520/test-harness/README.md
mkdir -p /tmp/acl && scp bench.py qosbench.py peer.py tb470:/tmp/acl/
ssh tb470 'cd /tmp/acl && CAMPAIGN_RUN=<group-dir> python3 -u <case>.py'

# look up CLI syntax WITHOUT probing a live box (avoids the "? plus CR executes it" trap)
command grep -rl "<command>" \
  claude/github-copilot-awplus-wiki/awplus_cli_wiki/commands/   # 3437 pages

# regenerate and apply the .setup after editing bench-state.md
cd bench-setup && ./bench_setup.py check && ./bench_setup.py apply
```

## Pointers

- Topology, addressing, consoles, PDU: **`bench-setup/bench-state.md`** — do not duplicate.
- Rebuild detail: `IE520/bench-rebuild-2026-09-23/README.md`
- Campaign resume record (superseded by this handover): `IE520/RESUME-CAMPAIGN-2026-09-22.md`
- Earlier ATMF work and the secure-mode finding: `IE520/atmf-2026-09-21/`
- Harness design: `IE520/test-harness/README.md`
