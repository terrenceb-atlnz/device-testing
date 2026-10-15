# Session handover — tb277 / x960-56YSQ — 2026-10-16

## Session facts
Test Engineer: bidhanc@bidhanc-dl
Testbox: tb277
Consoles: u2 = swi_d (DUT), u3 = swi_b, u5 = swi_a
PDU: 10.36.230.212 outlets u2=1, u3=7; 10.36.230.35 outlet u5=3
Constraints: None (full authority within tests; power cycles allowed). The run itself was
**unattended** by the Test Engineer's instruction — *"I will be away so won't be able to answer
any prompts"* — so no question was ever put to them; every one became a notice in the queue.

## TL;DR

**13 of 13 AWPTCM routing + ARP cases attempted, 13 PASS, 0 FAIL.** The bench is **whole**, not
parked: the shared L3 underlay is gone, every port is back in VLAN 1, both deliberately-shut
ports are up, the DUT boots `flash:/default.cfg`, and `rcdiff` against the pre-campaign captures
prints nothing on all three devices. Final logs and `.cfg` files are created and committed.

Two things want a human: **F-9**, where a removed inter-VRF route left the dataplane forwarding
(security-relevant), and **F-7**, where `show running-config` disagrees with both the saved file
and the wire about `bgp graceful-restart`. Neither changes a verdict.

## Current bench state, and how to verify it

Regenerated from the hardware at the wrap: `bench-setup/tb277/bench-state.md`,
**Generated 2026-10-15T200610Z**, Advisories: **none**. All six inter-switch links are visible by
LLDP again. tb277 still has **no `.setup`**, so the probe reports `no template -- diff skipped`
and there is no MATCH/MISMATCH verdict to quote; the generated bench-state.md is the only
description of the box. `apply` was NOT run — that is the Test Engineer's call.

```bash
sock=/run/user/$(id -u)/keyring/ssh
# occupancy, opening NO console
SSH_AUTH_SOCK=$sock ssh -o BatchMode=yes tb277 \
  'cd ~/claude/device-testing/bench-setup && python3.8 bench_probe.py --box tb277 precheck --consoles u2,u3,u5'
# regenerate bench-state.md from the hardware
SSH_AUTH_SOCK=$sock ssh -o BatchMode=yes tb277 \
  'cd ~/claude/device-testing/bench-setup && python3.8 bench_probe.py --box tb277 run --consoles u2,u3,u5'
# DUT final state
SSH_AUTH_SOCK=$sock ssh -o BatchMode=yes tb277 'cd ~/claude/device-testing/tools && python3.8 ckcon.py \
  /dev/u2 115200 /tmp/ck.log "show boot" "show running-config | include service|vrf|router|ip route"'
```

Read back at the wrap (09:07 NZDT, from the hardware, not from memory):

| unit | console | power | boot image | boot config | left as |
| --- | --- | --- | --- | --- | --- |
| swi_d (DUT) AT-x960-56YSQ | u2 @115200 | on | `flash:/x960-tb277.rel` **(file exists)** | `flash:/default.cfg` **(file exists)** | no `router`/`vrf`/`ip route`/`no service <proto>` lines; all ports untagged VLAN 1; `port1.0.2`, `port1.0.14` **up**; no `ck*.cfg` on flash |
| swi_b AT-x960-28YSQ | u3 @9600 | on | `flash:/backup.rel` | — | byte-identical to pre-campaign; `sa1`, vlan 100, `port1.0.2/4/8` never touched |
| swi_a AT-x950 GEN2-52XSTQm | u5 @9600 | on | **Not set**, netboots | `flash:/default.cfg` **(file NOT found)** | byte-identical to pre-campaign; **never reloaded or power-cycled** (RISK-1) |

Nothing is powered off. Nothing is left `shutdown`. Nothing is running-only: this campaign wrote
**nothing** to startup-config on any device.

## What was accomplished

Thirteen cases in four groups, run unattended overnight by four `bench-runner` subagents with this
session as sentinel. Every verdict rests on **counted frames with a control flow that must not be
forwarded and an instrument control in the same leg** — no `show` output was used as evidence and
no ping carried a verdict (STANDING-ORDERS §7).

Groups B, C and D shared **one L3 underlay built once** at the start of group B and left up
through D, so three groups paid no bench-setup cost. That is the single best cost decision of the
campaign and the pattern to repeat.

## Results

From the queue's `## Results` table. All runs **clean**; none confounded.

| case | title | group | verdict |
| --- | --- | --- | --- |
| T33248 | IPv4_ARP - Static ARP | arp | PASS |
| T33247 | IPv4_ARP - Clear ARP | arp | PASS |
| T33249 | IPv4_ARP - ARP Logging | arp | PASS |
| T43848 | IPv4_ARP - Proxy ARP | arp | PASS |
| T43849 | IPv4_ARP - Local Proxy ARP: Functionality | arp | PASS |
| T33246 | IPv4_ARP - ARP Polling | arp | PASS |
| T43855 | IPv4_UnicastRouting - IPv4 Static | static | PASS |
| T43861 | IPv4_UnicastRouting - ECMP Routing | static | PASS |
| T43862 | IPv4_UnicastRouting - Secondary IP Address (Multi homing) | static | PASS |
| T43857 | IPv4_UnicastRouting - OSPFv2 | igp | PASS |
| T43856 | IPv4_UnicastRouting - RIP v1/v2 | igp | PASS |
| T43858 | IPv4_UnicastRouting - BGPv4 | bgp-vrf | PASS |
| T43859 | IPv4_UnicastRouting - VRF-Lite | bgp-vrf | PASS |

**Final logs created** for all four groups: `fbf12da` (arp, 6), `6a5979d` (static, 3),
`85d21d1` (igp, 2), `941d2a6` (bgp-vrf, 2). Each case folder holds its `<id>.log`, its `.cfg`
files and its `<id>-review.md`; each group has a `README.md` and a `REVIEW.md`. No `work/`
remains.

## Findings

### Measured — product behaviour

- **F-9 (T43859), security-relevant, wants a developer.** After `no ip route vrf red
  192.168.48.0/24 vlan48`, with the line gone from running-config and `show ip route vrf red
  192.168.48.2` answering `% Network not in table`, **5/5 crafted frames still crossed the VRF
  boundary**, reproduced over three legs and ~2 minutes. Mechanism pinned, not guessed: a
  never-used host on the same /24 was correctly blocked 0/5, so the route really is gone and a
  **stale ARP-derived per-host forwarding entry** is what survives; `clear arp-cache vrf blue`
  stops it at once. Cold-start isolation is complete and immediate, so T43859 is a PASS — but
  VRF-Lite is documented as *securely isolated*, and an operator closing a path would see config
  and RIB agree it is shut while traffic flows. **The unaided lifetime of the stale entry was not
  measured.**
- **F-7 (T43858), wants a developer.** On a fresh `router bgp`, `show running-config` renders
  ` bgp graceful-restart` while `copy running-config` writes ` no bgp graceful-restart` and the
  DUT's own OPEN advertises **no** Graceful Restart capability. Two of three agree, so the
  *display* is the outlier. Which is intended was not established here.
- **F-6 (T43858): BGPv4 is NOT service-gated on this build**, the opposite of OSPFv2 and RIP.
  `bgpd` runs from boot on both the licensed x960-56 and the Base-licensed x960-28,
  `router bgp <asn>` is accepted immediately, and `service bgp` is a different command whose only
  completion is `evpn` (bare form: `% Incomplete command.`).
- **F-5 (T43857/T43856): `no service <proto>` sticks as a config line** on a unit that booted with
  the service, and configuration cannot remove it. Measured remedy, applied at the end of group D:
  one reload from `flash:/default.cfg` clears it. Verified gone at 23:49.
- **F-8 (T43859): a direct VRF-to-VRF interface move is refused** (`% vlan48: VRF is already
  associated`) although the guide describes it as supported. Working sequence is
  `no ip vrf forwarding <old>` → `ip vrf forwarding <new>` → **re-apply the address**.
- **F-1..F-4 (group B)**: ECMP on this x960 is **per-flow, not per-packet** (the Route Selection
  guide is wrong); the hash uses **IPv4 source and destination addresses only**; an ECMP next hop
  with unresolved ARP is silently absent from the dataplane while `show ip route database` still
  marks it `*>`; and the DUT answers ARP for an interface address only when the sender is in that
  address's own subnet.
- **O-8 (T43859)**: the VRF-lite guide p.17 overstates the inter-VRF static syntax — the VLAN-only
  form works, and the guide's own worked example uses it.
- **Platform fact (T43859):** a VRF change **strips the interface's addressing**, in both
  directions and on VRF deletion. Any teardown that moves an SVI out of a VRF must re-apply the
  address **before** deleting the VRF.

All of the above are in `platforms/x960.md` §7 (group B), §7A (group C) and §7B (group D).

### Measured — instrument and method, all ours

- **A capture file's SIZE is not a measurement until its writer has exited.** A finding was raised
  against the port mirror on the strength of a 0-byte capture and **retracted before hand-back**:
  the `ls -la` ran in the same command line as a `kill -INT` that never reached tcpdump (`$!` was
  the wrapper), so the capture was still running with its buffer unflushed. Reading the same file
  after stopping the real process showed 14 mirrored TCP/179 frames and mirrored ICMP, every
  timestamp inside the mirror's own window. **`platforms/x960.md` §5's M1/M2/M3 are untouched and
  still stand.** Confirm the process has exited, or read tcpdump's own `N packets captured` line.
- **`tools/arpleg.py` was passing `-p` to tcpdump**, so a frame carrying a next-hop MAC that was
  not the NIC's own was invisible and a working leg read `0 forwarded`. Found and fixed inside
  T33248; both its baseline and measurement legs were re-run on the fixed instrument.
- **An ECMP flow generator that varies all four 5-tuple fields by the same index** correlates the
  two addresses the hash consumes and produced a misleading 81/19 split. Decorrelated spans gave
  ~50/50, and T43861's verdict rests on the corrected legs.
- **The DUT's own `tcpdump` at privileged exec is the right instrument** for a unicast
  control-plane protocol on this platform. BGP is TCP between two router addresses and never
  reaches a host NIC on another segment.
- **`cfg.py` stops at the first `% ` line** and abandons the rest of its batch. It cost a shut
  `port1.0.48` for ~2 minutes in T43858, caught by reading the batch output rather than the exit
  code. `rcdiff.py` prints differences but **exits 0** — gate on its output, never its code.

### Inferred, not measured

- F-9's stale entry is **inferred** to be an ARP-derived per-host forwarding entry, from the fact
  that a never-used host on the same /24 was blocked while the used one forwarded, and that
  clearing the VRF's ARP cache stopped it. What would prove it: a developer's view of the hardware
  table, or a timed observation of the entry ageing out unaided.

### Infrastructure (unchanged by this campaign, still open)

- An **unrecorded device, `10.38.22.41` / `00:0c:25:2a:a5:53`**, is live on the box's eth3 segment
  and was seen again in T43859's baseline capture. Present since at least 2026-10-09; it attempted
  web authentication on `port1.0.10` during the DHCP campaign. Not confounding — every counted leg
  matched on both MACs — but it is not ours and not recorded.
- **swi_d `port1.0.8` and `port1.0.40`** are up and Forwarding with no LLDP neighbour and are
  absent from bench-state.md's link table.
- **tb277 `/tmp` is 95% full**, 1.8 GB of someone else's `wireshark_eth4*.pcapng`. **Not ours to
  delete.** Our whole campaign footprint was under 5 MB.
- **tb277 has no `.setup`** (RISK-6), so there is no framework and no MATCH/MISMATCH verdict.

## OPEN questions

1. **F-9: is the stale inter-VRF forwarding entry intended?** Evidence path: the three legs in
   `bgp-vrf-2026-10-15T1747/T43859/T43859.log` STEP 6, plus the 0/5 never-used-host control.
   What would settle it: a developer's answer on whether route removal is expected to invalidate
   the per-host entry, and a measurement of the entry's unaided lifetime.
2. **F-7: which of `show running-config` and the saved file is right about `bgp
   graceful-restart`?** The wire agrees with the file. Evidence path: `T43858.log` STEP 9.
3. **Should `arp <ip> <mac> alias` ever answer?** It installs but never answers (T33248,
   recorded UNMEASURED). Wants a developer.
4. **Is `10.38.22.41` supposed to be on the eth3 segment?** If yes it belongs in `tb277.static`;
   if no it wants finding.
5. **Should tb277 get a `.setup`?** Without one there is no framework, no post-failure power
   cycle and no MATCH/MISMATCH. `bench_probe.py apply` would write one — the Test Engineer's call.

## Ordered next steps

1. **Push.** Everything is committed locally and nothing is pushed: `git push origin main`.
2. **Attach the thirteen logs in Zephyr** from `tb277/x960/<group>-2026-10-15T1747/<id>/`.
3. **Raise F-9 and F-7 with a developer**, in that order.
4. Decide on `bench_probe.py apply` for tb277 (OPEN 5).
5. Ask whoever owns the 1.8 GB in `/tmp` to clear it before the next capture-heavy campaign.
6. If T43855 is ever re-run, **save `swi_a.cfg`** — see the deliverable caveats below.

## Deliverable caveats, declared

- **`T43855/swi_a.cfg` is missing.** swi_a carries that case's floating-backup proof, but its
  config was never saved and the bench has since been restored, so it cannot be reconstructed
  honestly. The log's `Configs:` line names only what exists.
- **`T33246/swi_d.cfg` is NOT an in-run capture.** The save point before step 1 was missed and the
  file was produced afterwards by re-applying the identical setup command set. The log says so in
  its `Configs:` line. The RADIUS key hash is the one field that cannot match.

## Recipes

```bash
# THE SHARED B/C/D L3 UNDERLAY (built once at group B, left up through D)
DUT vlan10 port1.0.10 192.168.10.1/24   (host eth3)
DUT vlan48 port1.0.48 192.168.48.1/24   (host eth4)
DUT vlan41 port1.0.4  10.0.41.1/30  <-> swi_a port1.0.4  10.0.41.2/30
DUT vlan61 port1.0.16 10.0.61.1/30  <-> swi_b port1.0.16 10.0.61.2/30
plus both partner loopbacks and their return routes to 192.168.10.0/24 and 192.168.48.0/24
DUT: spanning-tree priority 0 (DUT becomes root); port1.0.2 and port1.0.14 SHUT

# WHY port1.0.2 AND port1.0.14 MUST BE SHUT, and why "a VLAN per leg" does NOT help:
# RSTP here is SINGLE-INSTANCE on all three devices. It computes ONE tree over the PHYSICAL
# topology, so a Discarding port is blocked for EVERY VLAN. Two parallel links between the same
# pair of bridges are a loop RSTP must break at one end whichever bridge is root.

# RESTORE (corrected 2026-10-15: `no interface vlanN` is REFUSED on this build with
# `% Removal of interface not allowed`, even with the address gone and ports moved out)
interface port1.0.X / switchport access vlan 1      # every member port out of the VLAN FIRST
interface vlanN / no ip address
vlan database / no vlan N                           # this is what removes the SVI
interface port1.0.2 / no shutdown ; interface port1.0.14 / no shutdown
no spanning-tree priority
# then, LAST, one reload of swi_d from flash:/default.cfg to clear F-5's sticky lines.
# NEVER before the underlay restore: default.cfg does not contain the underlay.
# swi_d ONLY. swi_a must never be reloaded or power-cycled (RISK-1).

# REBOOT-PERSISTENCE LIMB (nothing is written to startup-config)
copy running-config flash:/ck<ID>.cfg
configure terminal / boot config-file flash:/ck<ID>.cfg / end
reload                                        ! answers (y/n) -- send `y\r`
# ... re-measure on the wire ...
configure terminal / boot config-file flash:/default.cfg / end
delete flash:/ck<ID>.cfg                      ! answers (y/n)[n] -- send `y\r` or it ABORTS

# CAPTURES: local tmpfs as root, then copy and chown. NEVER tcpdump -Z to the NFS lab home.
sudo tcpdump -i ethN -w /tmp/leg.pcap ...
cp /tmp/leg.pcap <case>/work/ && sudo chown $(id -u):$(id -g) <case>/work/leg.pcap
# and confirm the writer EXITED before reading the file's size (see Findings).

# THE DUT'S OWN tcpdump -- the instrument for a unicast control-plane protocol
awplus# tcpdump -i vlan61 -c 20 -nn -v tcp port 179
# `greater N` counts the 14-byte Ethernet header: a 19-byte BGP Keepalive is an 85-byte frame,
# so `greater 75` still matches keepalives and `greater 90` isolates UPDATEs.
```

## Pointers

- Campaign queue and the full issues list: [CAMPAIGN-QUEUE-2026-10-15T1747.md](CAMPAIGN-QUEUE-2026-10-15T1747.md)
- Product facts: `platforms/x960.md` §5 (read-back vs dataplane), §6 (DHCP), §7, §7A, §7B
- Group verdict tables: each group's `README.md`; process reviews: each group's `REVIEW.md`
- Previous session on this bench: [SESSION-HANDOVER-2026-10-15.md](SESSION-HANDOVER-2026-10-15.md)
- Bench topology: `bench-setup/tb277/bench-state.md` (generated 2026-10-15T200610Z)

## Sentinel

Stood down at **2026-10-16 09:00 NZDT** as briefed. The Monitor reached its `UNTIL` and exited on
its own; cron `d0981037` was deleted; no `sentinel.sh` process remains; no `bench-runner` subagent
is running. Thirty arms over the campaign, each preceded by a separate-call stray sweep — the
sweep is kept in its own Bash call because putting the script's name anywhere else in the same
command makes `ps` show it inline and the grep kills its own shell (that happened at 17:51 on
2026-10-15).
