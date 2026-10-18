# Session handover — tb277 / x960-56YSQ — campaign 2026-10-16T1406, wrapped 2026-10-19

## Session facts

Test Engineer: bidhanc@bidhanc-dl
Testbox: tb277
Consoles: u2 = swi_d (DUT), u3 = swi_b, u5 = swi_a
PDU: 10.36.230.212 outlets u2=1, u3=7; 10.36.230.35 outlet u5=3
Constraints: None (full authority within tests; power cycles allowed). The campaign ran
**unattended** — the Test Engineer was away and could not answer prompts.

Bench work ran **2026-10-16 14:06–19:32 NZDT**. `/create-logs` ran 2026-10-19; this wrap is
2026-10-19. Nothing has touched the bench between 10-16 19:32 and this wrap.

## TL;DR

The bench is **whole and re-runnable**. Ten AWPTCM cases, **9 PASS + 1 UNSUPPORTED**, none
BLOCKED, none NOT TESTED. All three devices were verified byte-identical to their pre-campaign
state by `rcdiff` at group hand-back, the boot baseline is restored on every unit, and all ten
final logs and their `.cfg` files are written and committed.

**Nothing is parked. Nothing is left shut. No unit was powered off.**

⚠️ **At wrap time `/dev/u2` is held by someone else** — `minicom -D /dev/ttyUSB2`, root for
bidhanc, started ~10:36 on 2026-10-19. That is NOT this campaign's: all three consoles were
released at 19:32 on 10-16 and verified sitting at `login:`. It was not touched. A second
long-standing `minicom -D /dev/ttyUSB1` (u1, up 3 days) is also present and was never in this
session's console list.

## Current bench state, and how to verify it

`bench-state.md` was regenerated **2026-10-16T062418Z** from the hardware by the group D tester
at hand-back (probe exit 0, no advisories beyond the `lldp run` note below), and is committed.
**This wrap did NOT re-run the probe**: `/dev/u2` is held by another user, and nothing has run on
the bench since that probe, so re-running would displace someone to learn nothing.

```bash
sock=/run/user/$(id -u)/keyring/ssh
# occupancy, opening NO console — expect u2/u3/u5 free once the other minicoms are gone
SSH_AUTH_SOCK=$sock ssh -o BatchMode=yes tb277 \
  'cd ~/claude/device-testing/bench-setup && python3.8 bench_probe.py --box tb277 precheck --consoles u2,u3,u5'

# regenerate bench-state.md from the hardware (only when u2 is free)
SSH_AUTH_SOCK=$sock ssh -o BatchMode=yes tb277 \
  'cd ~/claude/device-testing/bench-setup && python3.8 bench_probe.py --box tb277 run \
     --consoles u2,u3,u5 --pdu 10.36.230.212 --outlet u2=1,u3=7 --name u2=swi_d,u3=swi_b,u5=swi_a'

# DUT final state
tools/tb ckcon tb277 ckcheck u2 115200 'show boot' 'show running-config | include service' \
  'show spanning-tree brief' 'show ip interface brief' 'dir flash:/*.cfg'
```

Expected from those reads, as left on 2026-10-16:

- **swi_d (DUT, u2)** — AT-x960-56YSQ, S/N `A2WQS700B`, standalone Active Master,
  `sin_x96056-20261012-24`, boots `flash:/x960-tb277.rel` **(file exists)**, boot config
  `flash:/default.cfg` **(file exists)**, autoboot disabled. **flash holds only `default.cfg`** —
  all four staged `ck4386*.cfg` and `ckT47873.cfg` were deleted. Services back to baseline
  (`service ssh`, `no service telnet`, `service http`, `no service dhcp-server`) with **no sticky
  `no service` line of any kind** — the end-of-group reload cleared them.
- **swi_b (u3)** — AT-x960-28YSQ, S/N `A10737A261700021`, `sin_x96056-20260921-9`, boots
  `flash:/backup.rel`. Restored by configuration alone; **never reloaded, never power-cycled.**
- **swi_a (u5)** — AT-x950 GEN2-52XSTQm, S/N `A10713A262600012`, `awplus_main-20261008-56`.
  **Never touched at all in groups A, B and D; in group C configured and restored by
  configuration only — never reloaded, never power-cycled** (RISK-1 honoured end to end).
- **STP is at the campaign baseline**: swi_b is root (`8000:0000cd423029`), and the DUT's
  `port1.0.16` reads **Alternate / Discarding**. ⚠️ **That means NEW-RISK-8 is live again** for
  whoever runs the next VRRP or two-router case on that port — see Recipes.
- **The shared L3 underlay is up and forwarding**: `vlan10 10.38.22.34/27` on `port1.0.10` ↔ host
  `eth3 10.38.22.33/27`; `vlan48 10.38.22.66/27` on `port1.0.48` ↔ host `eth4 10.38.22.65/27`.
  ICMP eth3→eth4 measured **5/5 at ttl 63** at hand-back. **It is running-config only — a reload
  loses it.** Rebuild recipe below.
- **Host NICs**: eth3 and eth4 in use as above; eth2 (`10.38.22.1/27`) carrier up, MAC not
  learned, unused by this campaign.
- One standing advisory from the probe: **`lldp run` was OFF on swi_d; the probe switched it on
  and left it on** (running-config only). That is how the pre-campaign state had it, and it is
  why swi_d's restore diff is empty.

## What was accomplished

Ten AWPTCM cases on the AT-x960-56YSQ, run unattended in four groups by `bench-runner`
subagents under a sentinel, from the list the Test Engineer supplied as a screenshot.

| group | cases | window |
| --- | --- | --- |
| A `snmp-2026-10-16T1406` | T43870 | 14:33–14:53 |
| B `ipv4svc-2026-10-16T1406` | T44181, T44378, T44182 | 15:04–16:12 |
| C `mcast-2026-10-16T1406` | T43863, T43864, T43865, T43866 | 16:10–18:05 |
| D `bfd-vrrp-2026-10-16T1406` | T47201, T47873 | 18:24–19:25 |

**Five of the ten had no authored step text at all** (T44378, T44182, T43863, T43866, T47201 —
the last with a steps array holding one completely empty step). Each was designed from the
feature guide, the TPS row and the DUT's own CLI surface, and **says so in its log**. T43864 had
an authored objective and topology but no steps; T43865 had 3 authored steps; T44181 had 11;
T43870 had a full 9-step procedure in its precondition; T47873 had authored text.

A **two-router multicast topology** was built for group C after `service pim` and `service pdm`
on swi_b both answered `% Service is not currently licensed on this platform` — swi_a became the
PIM partner. That overturned the earlier assumption that this bench cannot test real multicast
routing.

## Results

All from the queue's `## Results` table. **Final logs created** — `/create-logs` commits
`edf2c3d` (snmp), `bf6c3cf` (ipv4svc), `e8a1741` (mcast), `0fef9ae` (bfd-vrrp).
Every run labelled **clean**; no run in this campaign was confounded.

| case | title | verdict |
| --- | --- | --- |
| T43870 | IPv4_SNMP - SNMPv3 | **PASS** |
| T44181 | IPv4 - Ping Polling | **PASS** |
| T44378 | IPv4 - UDP Broadcast Helper | **PASS** |
| T44182 | IPv4 - Directed Broadcast Forwarding | **PASS** |
| T43863 | IPv4_MulticastRouting - PIM-SM | **PASS** |
| T43864 | IPv4_MulticastRouting - PIM-DM | **PASS** |
| T43865 | IPv4_MulticastRouting - PIM-SSM | **PASS** |
| T43866 | IPv4_MulticastRouting - VRF-Lite | **PASS** |
| T47201 | IPv4_BFD - With RIP v1/v2 | **UNSUPPORTED** |
| T47873 | VRRP(v3) | **PASS** |

`work/` has been deleted by `/create-logs`; the working logs remain in git history.

## Findings

### Measured — for a developer

- **F-12 (T43870) — an SNMPv3 GetNext at a MIB-view boundary gets NO response at all.** Not an
  error PDU, not `endOfMibView` — silence. RFC 3416 §4.2.2 requires a response. Proven with five
  matched legs at 5 s / 3 retries and a known-good GET control before and after each silence.
  Consequence: `snmpwalk` hangs at the edge of a view rather than ending.
- **F-13 (T43863) — `ip pim sparse-mode` does NOT enable router-side IGMP**, and snooping makes
  this hard to see: `show ip igmp groups` shows the membership with a live timer while
  `show ip pim sparse-mode local-members` is empty and **nothing forwards**. Two read-backs
  disagree and the dataplane follows the pessimistic one. The IGMP report was confirmed
  well-formed on the wire before the platform was blamed.
  **Addendum (T43864):** a membership learned while the interface was snoop-only does **not**
  migrate when `ip igmp` is later enabled — it must be re-sent. Measured: first leg 0/10,
  identical leg after a re-join 10/10, nothing else changed.
- **F-14 (T43865) — the IGMPv2 any-source-join rejection is bound to the hardcoded IANA 232/8
  range ONLY**, not to a range configured with `ip pim ssm range <acl>`. One
  `show ip igmp groups` shows `239.20.20.20` (inside the configured SSM range) ACCEPTED and
  `232.7.7.7` REJECTED, 40 s apart on the same interface. The 232/8 rejection also persists with
  no SSM configuration at all, so `ip pim ssm default` is not what enforces it. RFC 4607 §4.2
  expects the configured range to carry SSM semantics too. **Impact measured before being
  characterised**: the wrongly-accepted membership is inert (0/10 in the dataplane, no RP
  configured), so this is a spec-conformance gap, not a forwarding hole.
- **F-15 (T47201) — AW+ has no RIP↔BFD binding, and the cost is measured.** BFD detected a silent
  neighbour failure in **~1.4 s** (RIPv2) / **~1.1 s** (RIPv1) with
  `Diagnostics: control detection time expired`, while RIP kept the dead prefix in the FIB marked
  **`best`** for **~171.6 s**; a counted leg read **0/5** on both subjects with its in-leg
  instrument control at **5/5**. Absence established by enumeration with both daemons running —
  five CLI probes, the RIP guide (0 hits for "bfd" in 1045 lines), and `ip ospf bfd` accepted on
  the **same interface in the same minute**.
- **F-17 (T47873) — two components of one firmware image disagree about the checksum of its own
  default VRRPv3 advertisement, and the vendor ships a command that makes them agree.** Stated
  deliberately at that bound: **which mode is RFC 5798 §5.2.8-conformant is NOT claimed**,
  because that rests on the validator being correct and the validator was not independently
  verified. Bounded by two measured controls — default↔default fine, alternate↔alternate fine;
  **only the MISMATCH splits the pair**, with priority 100 displacing priority 150, both routers
  advertising from the same virtual MAC `00:00:5e:00:01:0a`, and ten ARP replies to five
  requests. The third-party-peer limb is **NOT MEASURED**, instrument named.

### Measured — F-9 answered

**F-9's shape does NOT occur in the multicast path** (T43866). Tested in its sharpest form: an
(S,G) actively forwarding with its OIF holding vlan48, the interface moved out of the VRF, and
re-measured immediately with no re-join and no `clear`. The OIF emptied in the same instant and
the dataplane went to 0/10. F-9 (a removed inter-VRF route that kept forwarding from a stale
ARP-derived host entry, 2026-10-15) is therefore **specific to the unicast inter-VRF path**.

### Measured — platform observations

O-9 (the authored T43870 precondition omits the group's read view and typos an OID — a Zephyr
fix, not a bench one), O-10, O-11, O-12 (SNMP); O-13, O-15, O-16, O-17, O-18, O-19 (IPv4
services); O-20 (`service ?` lists `pim`/`pdm` identically on a unit that cannot run them — the
read-only surface probe can never settle licensing; only `service <x>` names it), O-21, O-22
(`no interface vlanN` is refused), O-24, O-25, O-26, O-27, O-28, O-29, O-30 (multicast); O-31
(`show bfd session` does not exist), O-32, O-33 (**a BFD state change writes nothing to the
device log — there is no audit trail of a failure**), O-34 (`no service bfd` silently drops you
out of config mode, so it must go LAST in any stop-on-error batch), O-35, O-37
(`circuit-failover` and `transition-mode` are refused while the VRRP session is enabled), O-38
(there is no VRRP `version` command), O-39, O-40 (BFD/VRRP). All are in the queue's `## Issues`
with their evidence.

**O-24 deserves naming here because it was proven in both directions in one session.** A
`no service <proto>` line is sticky **only on a unit that BOOTED with the service** — the
discriminator is the boot, not the daemon and not the protocol. Confirmed for `pim` and `pdm`
(sticky, the DUT having booted from a config containing them), and in the negative for `rip`,
`bfd` and `vrrp` applied at runtime. The sharpest instance: `no service vrrp` sent to both
devices in the same minute left a sticky line on the DUT (which had booted with it) and **nothing
on swi_b**. Cleared only by booting a config that never contained the service.

### Measured — instrument and method, all ours

- **`tools/console.py` prompt-splice defect, fixed.** AW+ switch-driver port-state messages
  bypass the logging subsystem entirely (neither `terminal no monitor` nor `no log console`
  suppresses them) and can splice *inside* the prompt, leaving `)#` alone on a line. Before the
  fix the command ran to its full timeout and `cfg.py` silently abandoned the rest of the batch
  although the command had taken effect — **measured at 90 s per `shutdown`/`no shutdown`, used
  eight times in group C alone.** Fixed structurally, self-tested on 6 buffers, validated on
  hardware.
- **Three `console.py` ADVISORY entries added** (`% All IP addresses configured on interface …`,
  `% Save the config and restart …`), each preventing one silently-truncated batch.
- **`tools/arpleg.py`**: derives the IANA link-layer address for an IPv4 multicast destination
  (so one leg can carry subject and control groups, each correctly addressed); gained
  `--show-ttl` and a per-spec `%L2DST` on `--udp`.
- **`tools/igmp.py`**: IGMPv3 source-list mode (`-3`, `--source`, `--record`), without which
  T43865's authored step 1 was not expressible at all.
- **A real `arpleg.py` marker defect was found and fixed**, with retrospective reach: scapy
  dissects ports 69→TFTP, 67/68→BOOTP, 53→DNS into their own layers, so the marker search in
  `pkt[Raw].load` under-counted its own frames. **Any leg run before 2026-10-16 on such a port
  under-counted, so a historic "counter disagreement" on one is unproven — re-read the pcap, not
  the summary.** High-port legs (7777, 9) are unaffected.

### Inferred, not measured

- **The DUT logs `Received SNMP Packet from illegal server 10.38.22.33` on the SUCCESS path**
  (T43870 STEP 9, recorded as expected output). Observed; cause not established. Whether it is a
  defect or a misleading log string needs a developer. Nothing in the campaign rests on it.
- **F-17's real-world exposure** is inferred, not measured: a mismatched pair splits, and a
  third-party RFC-conformant VRRPv3 peer would plausibly be in the same position as the
  non-conformant side — but no third-party router was on this bench.

### Infrastructure (unchanged by this campaign, still open)

- `/tmp` on tb277 was ~95% full at the 10-15 campaign; **1.8 GB of `wireshark_eth4*.pcapng`
  belongs to someone else and is not ours to delete.**
- The unrecorded device `10.38.22.41 / 00:0c:25:2a:a5:53` on the eth3 segment.
- swi_d `port1.0.8` and `port1.0.40` have unknown far ends.
- Carried from 10-15 and still open: **F-7** (`bgp graceful-restart` display disagrees with the
  file and the wire) and **F-9** (now bounded to the unicast inter-VRF path, above).

## OPEN questions

1. **Is the `illegal server` log line on a successful SNMP read a defect?** Evidence path:
   `snmp-2026-10-16T1406/T43870/T43870.log` STEP 9. Needs a developer.
2. **Which VRRPv3 checksum mode is RFC 5798 §5.2.8-conformant?** Not claimed by this campaign.
   Evidence path: `bfd-vrrp-2026-10-16T1406/T47873/T47873.log` STEP 4 (F-17). Settling it needs
   either an independent checksum implementation (`tools/vrrpwire.py`, proposed in that group's
   `REVIEW.md`) or a third-party VRRPv3 peer.
3. **Does F-14's gap extend to IGMPv3 as well as IGMPv2?** Only the IGMPv2 any-source join was
   tested against a configured SSM range.
4. **Was u1 meant to be in this campaign?** It was excluded as the Test Engineer's own console
   and never touched. If it had been available it would have given group C a third candidate
   partner. Reported four times during the run and never actioned — this is the standing answer
   needed, not a bench problem.
5. **T44181's trigger-script-CONTENT limb is still unmeasured** — it needs a root write to the
   box's `/tftproot` (STANDING-ORDERS §4, never done unattended).
6. **T43864's FLOOD half of flood-and-prune is still unmeasured** (O-25), instrument named:
   a line-rate stimulus with per-frame timestamps on the transit VLAN.

## Ordered next steps

1. **Push.** Everything below is committed and NOT pushed: `git push origin main`.
2. **Attach the ten logs in Zephyr** from `tb277/x960/<group>-2026-10-16T1406/<id>/`.
3. **Raise F-12, F-13 (+addendum), F-14, F-15 and F-17 with a developer.** They are the campaign's
   substantive output; the PASSes mostly confirm the platform works.
4. **Fix AWPTCM-T43870's precondition** (O-9: missing read view, typo'd OID). It will mislead the
   next person to run it.
5. **Consider `platforms/x960.md` §7D for multicast** — the file has §7, §7A, §7B, §7C then §8,
   and every measured multicast fact from this campaign currently lives only in the queue and the
   four logs. The four cases' "expected outputs" tables in
   `mcast-2026-10-16T1406/REVIEW.md` are the content.
6. **Before the next VRRP or two-router case on `port1.0.16`: apply the NEW-RISK-8 remedy** below
   and confirm it, or "no advertisements seen" will look like a product defect.

## Recipes

```bash
# THE SHARED L3 UNDERLAY (running-config only — a reload loses it; rebuild before any case
# that needs host-to-host routing through the DUT)
tools/tb cfg tb277 ck u2 115200 'configure terminal' \
  'vlan database' 'vlan 10 name ckUNDERLAY-eth3' 'vlan 48 name ckUNDERLAY-eth4' 'exit' \
  'interface port1.0.10' 'switchport access vlan 10' 'exit' \
  'interface port1.0.48' 'switchport access vlan 48' 'exit' \
  'interface vlan10' 'ip address 10.38.22.34/27' 'exit' \
  'interface vlan48' 'ip address 10.38.22.66/27' 'exit' 'end'
# verify: ICMP eth3 -> eth4 should be 5/5 at ttl 63

# NEW-RISK-8 REMEDY — unblocking DUT port1.0.16 for a two-router case.
# RSTP here is SINGLE-INSTANCE on all three devices: one tree over the PHYSICAL topology, so a
# Discarding port is blocked for EVERY VLAN and "a VLAN per leg" does not help. swi_b is root at
# baseline, and the DUT therefore blocks one of its two parallel links to it.
# A root bridge never blocks its own ports, so make the DUT root and remove the competing paths:
tools/tb cfg tb277 ck u2 115200 'configure terminal' \
  'spanning-tree priority 0' \
  'interface port1.0.2' 'shutdown' 'interface port1.0.14' 'shutdown' 'exit' 'end'
# CONFIRM BEFORE MEASURING: port1.0.16 must read Designated/Forwarding
tools/tb ckcon tb277 ck u2 115200 'show spanning-tree brief'
# REVERSE IT AFTERWARDS — un-shutting the ports matters as much as the priority, because
# shutting them takes swi_b's sa1 aggregator down:
tools/tb cfg tb277 ck u2 115200 'configure terminal' \
  'interface port1.0.2' 'no shutdown' 'interface port1.0.14' 'no shutdown' 'exit' \
  'no spanning-tree priority' 'end'

# CLEARING A STICKY `no service <proto>` LINE (O-24)
# It appears only on a unit that BOOTED with the service, and configuration cannot remove it.
# Point the boot config at a file that never contained it, delete the staged config, reload:
tools/tb cfg tb277 ck u2 115200 'configure terminal' 'boot config-file flash:/default.cfg' 'end'
tools/tb ckcon tb277 ck u2 115200 'delete flash:/<staged>.cfg' 'show boot' 'dir flash:/*.cfg'
# then reload; afterwards `show running-config | include service` is clean.

# CAPTURING ON A SWITCHED VLAN OF THIS DUT (O-26)
# A 1 Hz loop-protection LDF stream competes for a short -c budget. Those frames are 802.3/LLC
# with no IP header, so a bare `ip` qualifier drops every one of them:
tcpdump -i vlanN -c 30 -nn ip
# (`proto 103` works when only PIM is wanted, but excludes the multicast data.)
```

## Pointers

- Queue / resume record: [CAMPAIGN-QUEUE-2026-10-16T1406.md](CAMPAIGN-QUEUE-2026-10-16T1406.md)
  — `## Results`, `## Issues` (F-12..F-17, O-9..O-40), triage and the per-group restore recipes.
- Final logs and `.cfg` files: `tb277/x960/{snmp,ipv4svc,mcast,bfd-vrrp}-2026-10-16T1406/<id>/`.
- Process reviews (for the next tester, never for Zephyr): each group's `REVIEW.md` and each
  case's `<id>-review.md`. The three campaign-level lessons are: an idle gap longer than the
  prompt cache's lifetime costs a full context re-write (one call cost 327 k tokens); cache-read
  per call rises ~4.9× from the start of a group to its last case, so front-load all reading; and
  a group brief should be readable alone, because ~115 kB of overhead across two groups went on
  slicing the campaign-wide queue to reconstruct what the dispatch already said.
- Bench topology: [bench-setup/tb277/bench-state.md](../../bench-setup/tb277/bench-state.md),
  generated 2026-10-16T062418Z.
- Platform facts: `platforms/x960.md` (§5 read-back vs dataplane, §6 DHCP, §7B VRF-Lite, §7C BFD
  and VRRP).
- Previous campaign's wrap: [SESSION-HANDOVER-2026-10-16.md](SESSION-HANDOVER-2026-10-16.md).

## Sentinel stand-down

The sentinel ran as `/test-mode` shape A (this session = sentinel, `bench-runner` subagents =
testers, one per group) across 37 Monitor arms with a 15-minute cron backstop. It **stood down at
08:54 on 2026-10-17** — seven minutes before its 09:00 deadline, because arm 37 expired then and
re-arming a seven-minute watch over a finished, idle bench would have been churn. Monitor expired
naturally, cron `72263fae` deleted, stray sweep clean, heartbeat removed. Re-verified at this
wrap: no `sentinel.sh` process, no scheduled job, no bench-runner subagent running.
