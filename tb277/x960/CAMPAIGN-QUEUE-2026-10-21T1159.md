# Campaign queue — tb277 x960-56YSQ, 14 AWPTCM Management cases, from 2026-10-21 11:59 NZDT

The ask, verbatim: *"Okay lets run these test"* with the AWPTCM "Not Executed" panel for
x960-56YSQ, then *"Ignore the last 4 ids - just run the 14 test case"*. The panel header said
18; the screenshot showed 14; the Test Engineer dropped the other 4.

**This file is the resume point.** `/test-mode --resume tb277/x960/CAMPAIGN-QUEUE-2026-10-21T1159.md`
picks up at the first row that is not DONE or BLOCKED.

## Session facts

Recorded 2026-10-21 11:5x NZDT from the Test Engineer's own answers to `/test-mode` §1.

Test Engineer: bidhanc@bidhanc-dl
Testbox: tb277
Consoles: u2 = swi_d (DUT), u3 = swi_b, u5 = swi_a
PDU: 10.36.230.212 outlets u2=1, u3=7; 10.36.230.35 outlet u5=3
Constraints: None beyond standing orders. Window: **partly attended** — the Test Engineer is
             intermittently available, so a `NEEDS TEST ENGINEER:` may wait.
             🔴 **swi_a (u5) must NOT be rebooted or power-cycled** — see below.

Answer given as **"Same as 2026-10-20"**, confirmed by the Test Engineer for this campaign.

**New session facts, given 2026-10-21 and NOT present in the 2026-10-20 campaign:**

- **Console passwords changed.** u3 (swi_b) and u5 (swi_a) now use a **non-default** password;
  u2 (swi_d) keeps the factory default. The password is **not in this repo and must never be
  put in it**. `bench_probe.py` reads it per console from the environment:
  `CK_PASSWORD_U3` / `CK_PASSWORD_U5` (added 2026-10-21, commit `a1faab7`). Pass it over
  **stdin, never on a command line** — `ps` is readable by other users on this shared box.
- **Release files were updated on all three units** (Test Engineer, 2026-10-21). Measured after:
  swi_d `sin_x96056-20261019-27` (was `-20261012-24`); swi_b `awplus_main-20261020-78`
  (was `sin_x96056-20260921-9` — a **different build train**, and its hostname changed to
  `awplus`); swi_a `awplus_main-20261019-73`, **unchanged**.

## 🔴 swi_a must not be rebooted (Test Engineer, 2026-10-21)

swi_a reads **`Current boot image : Not set`** where swi_d reads `flash:/x960-tb277.rel (file
exists)`. A reload may not bring it back. Asked at setup, the Test Engineer chose
**"Do not reboot swi_a"**:

> Use swi_a as a live partner for LLDP/NTP but never reload or power-cycle it. Any case needing
> a swi_a reboot is reported BLOCKED rather than risking a unit that may not come back.

This **tightens** STANDING-ORDERS §1 for this session, which it is allowed to do. swi_b and
swi_d remain fully in play.

## 🔴 Open bench questions the Test Engineer did NOT settle at setup

Both were offered as constraints and neither was taken, so **triage must measure and report
them** rather than assume:

1. **A possible forwarding loop.** The 2026-10-21 probe raised four advisories: the testbox NIC
   MACs `eth3` and `eth4` are each learned on **two switches at once** (swi_d AND swi_b; swi_d
   AND swi_a). This is new since the image update. The bench has **six** inter-switch links in a
   triangle, so if spanning tree came up differently on the new images, redundant paths are no
   longer blocked. **A counted traffic leg on a looping bench measures the loop, not the
   feature** — so triage reports STP state on all three units before any counted leg.
2. **swi_b's build train.** It is now `awplus_main-*`, not the `sin_x96056-*` train swi_d runs.
   If unintended, every LLDP and NTP partner result is against the wrong image.

## Occupancy — checked before anything, 2026-10-21 11:59 NZDT

`tools/tb precheck tb277 u2,u3,u5`: **u2, u3, u5 all free.** One FOUND item, `ser2net`
(pid 744, root, up 40 days) — the box's own console daemon, the identical item the Test
Engineer adjudicated "Proceed" for the 2026-10-20 campaign. Treated as still standing; nothing
was displaced. The Test Engineer's own logins on pts/0 and pts/1 are information only.

## Rules

- Verdicts, working logs, the `RESULT` line, the results list and the final log template:
  **[logged-output.md](../../logged-output.md)**. Final logs are made only by `/create-logs`,
  on the Test Engineer's request.
- **STANDING-ORDERS §7**: traffic tests use **scapy**, not ping — the exact frame plus a control
  flow that must NOT match, both counted. LLDP and NTP cases are traffic cases.
- **STANDING-ORDERS §8**: health-check the DUT **twice per case**, before step 1 and after the
  last step. Never chain `| exclude` onto `| include` — on AW+ it is silently swallowed
  (`platforms/x960.md` §7G).
- **`platforms/x960.md`** holds this family's measured behaviour, including §7E (AAA), §7F
  (management) and §7G (the filter defect). Read it before designing a step.
- None of the 14 is in **MANUAL-ONLY.md**.

## 🔴 CORRECTED at triage — ALL 14 cases have NO authored text at all

The queue first said "thirteen have one authored step". **That overstated it.** Measured from
`ck.db` `zephyr_cases` at triage:

- **`has_objective = 0` on all 14** — not one case has objective text.
- T44296: `steps = []`, `num_steps = 0`.
- The other 13: `num_steps = 1`, but the step is an **empty placeholder** —
  `[{"description": "", "testData": "", "expected": ""}]`, 53 characters of JSON with nothing
  in it.

**There is not one word of authored procedure, test data or expected result anywhere in this
campaign.** Every case is designed from the TFS, the TPS row and the DUT's own CLI surface, and
**every final log must say that no authored authority exists beyond the title.**

### The authority that DOES exist: the X960 TPS (fetched at triage, last modified 2026-10-19)

`wiki.atlnz.lc/awpwiki/index.php?title=X960_platform_support_TPS&action=raw`

| TPS row | feature | supported |
| --- | --- | --- |
| 228 Telnet Client(IPv4) · 229 SSH Server(IPv4) · 230 SSH Client(IPv4) | | **Yes** |
| 233 Auto boot from External Media · 291 External Media (SD/USB) | | **Yes** |
| 235 Management ACLs | | **Yes** |
| **236 Management Stacking** | *"not necessary as these units support VCS"* | **🔴 No** |
| 237 Hardware Watchdog · 238 Software Watchdog | | **Yes** |
| 241 Dynamic configuration (Change, Delete) | | **Yes** |
| 257 LLDP · 258 LLDP-Med | | **Yes** |
| 260 NTP Server(IPv4) · 261 NTP Client(IPv4) · 262 IPv6 NTP Server | | **Yes** |

Requirement rows that decide verdicts:
- **TPS 5.3.6** *"The Watchdog function can be enabled or disabled by user command"* — **No**.
- **TPS 6.1.1** — the real statement of what T33386 must prove: *"Access filter for management
  I/F, which denies all packets addressed to the management I/F other than those packets that
  come from user specified network(s) or host(s). Also TCP/UDP port number of all services such
  as telnet, SNMP, ICMP and etc. is configurable."*
- **TPS line 894** — the real statement of what T47192 must prove: *"Support a Dynamic
  configuration. Even during in operation, addition, change and deletion of a configuration must
  be effected dynamically unless a chip set or another hardware component requires restart…"*
- TPS Default Configuration says *"Stacking is enabled by default"*; this DUT reads `Stacking
  hardware disabled`. A deviation worth one line in T33387's log.

## ✅ TRIAGE ANSWER — there is NO forwarding loop. Counted traffic legs are safe.

`spanning-tree mode rstp` on all three, single instance, **root is swi_b**
(`8000.0000.cd42.3029`). Exactly **2 of the 6** inter-switch links are in the active tree, and
the tree is a line: **swi_d —(1.0.2)— swi_b —(1.0.1)— swi_a**.

| unit | port | peer | role | state |
| --- | --- | --- | --- | --- |
| swi_d (DUT) | port1.0.2 | swi_b 1.0.2 | **Rootport** | **Forwarding** |
| swi_d | port1.0.16 | swi_b 1.0.16 | Alternate | Discarding |
| swi_d | port1.0.4 | swi_a 1.0.4 | Alternate | Discarding |
| swi_d | port1.0.14 | swi_a 1.0.14 | Alternate | Discarding |
| swi_a | port1.0.1 | swi_b 1.0.1 | **Rootport** | **Forwarding** |
| swi_a | port1.0.11 | swi_b 1.0.11 | Alternate | Discarding |
| swi_a | port1.0.4 / 1.0.14 | swi_d | Designated | Forwarding (far end discards) |

Read swi_a↔swi_d as a pair: swi_a forwards, swi_d discards, so **neither link carries data**.
The four probe advisories are ordinary transit learning on that tree — swi_d floods the testbox
MACs to swi_b on 1.0.2, swi_b floods them to swi_a on 1.0.1 — not a loop. **Record this table in
each group's working log so a later flap is visible.**

## 🔴 The layer-3 underlay is GONE on all three units — rebuild it as group setup

`vlan10 10.38.22.34/27` and `vlan48 10.38.22.66/27` no longer exist on swi_d: not the addresses,
not the VLANs. `show vlan brief` shows **one VLAN, `1 default`, every port untagged in it**.
swi_b has only `eth0 169.254.42.42/16` (the documented no-DHCP default); swi_a has none. All
three boot `flash:/default.cfg`, and swi_d and swi_b rebooted this morning, so running-config
died with them.

The testbox NICs are now in a **flat vlan1** with both switches: eth3 `10.38.22.33/27` and eth4
`10.38.22.65/27`, two /27s sharing one broadcast domain until the VLANs are recreated. **A
tester that assumes the 2026-10-20 topology will get wrong answers.**

### ✅ DECISION (Test Engineer, 2026-10-21 12:2x): write the underlay to startup-config

Asked directly, the Test Engineer chose **"Yes, write it to startup-config"**:

> The tester rebuilds vlan10/vlan48 and saves it. Survives the reboots in group E, stops every
> group paying setup cost again, and unblocks reboot-persistence limbs that have been NOT
> MEASURED for two campaigns.

This **closes handover OPEN 2** and overrides STANDING-ORDERS §1's "nothing is written unless
the case requires it" for the underlay only. **Group A rebuilds it and saves it; B, C and D
inherit it.** Reboot-persistence limbs are now measurable for the first time in three campaigns.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| A | T33379 Telnet Client; T33380 SSH Server; T33381 SSH Client | `access-2026-10-21T1159` | **DONE** -- 3 PASS. Underlay built and SAVED; vlan 60 left in place as campaign infrastructure; swi_b's throwaway account and telnet server removed. T33380's reboot-persistence limb NOT MEASURED (see Issues) | **Rebuilds the underlay and SAVES it** — B, C, D inherit. T33379 is the DUT originating outward; its server half is NOT under test and `no service telnet` on the DUT is left alone. Far end swi_b needs `service telnet` enabled in group setup and removed in teardown. **T33381: use a throwaway account on swi_b, never type the real password down u2** |
| B | T33386 Management ACL; T47192 dynamic config; **T33387 Management Stacking** | `mgmt-2026-10-21T1159` | **DONE** -- 2 PASS + 1 UNSUPPORTED. Closing probe exit 0 MATCH; running-config diff empty after BOTH bench cases; nothing written to startup-config; u2 and u3 left logged out at `awplus login:`; u5 never opened. Bench left exactly as group A handed it over -- underlay intact and saved, vlan 60 intact and unsaved. `tools/arpleg.py` gained a `--tcp` leg | 🔴 **No `access-class` under `line vty` on this platform** — `acc ?` offers only `login`. `ip access-list ?` is `% Unrecognized command`. Use `access-list`+`access-group`, `snmp-server community <n>`, `ssh server allow-users/deny-users`, `service telnet\|ssh ip`. **Hardware ACLs implicitly PERMIT, software/standard implicitly DENY** (§5) — grading the wrong default round is the easy false pass. T33387 is a desk verdict: UNSUPPORTED on TPS row 236 |
| C | T44296 LLDP; T33398 LLDP-Med | `lldp-2026-10-21T1159` | **DONE** -- 2 PASS, both with reboot persistence MEASURED (the first in three campaigns). Bench returned byte-for-byte to the state group C inherited; closing probe exit 0 MATCH; u2 logged out; swi_a never opened. 🔴 `lldp run` proven to be swi_d's SAVED baseline, not probe residue. 🔴 startup-config now holds vlan 60 -- the Test Engineer's to remove at wrap. swi_a.cfg/swi_b.cfg absent: both partner consoles locked out. New tools `lldpsend.py` + `lldpwire.py` | ✅ Loop question settled, safe to run. 🔴 **Run the probe with `--read-only` first** — the 11:59 probe toggled `lldp run` itself and may be the reason it is on. Record `show running-config \| include lldp` as the first act. `show lldp neighbors brief` does not exist. Run `.setup` carries swi_a **with no `[powerlink]`** so the post-failure cycle cannot reach it |
| D | T33399 IPv4 NTP Server; T33400 IPv4 NTP Client; T44298 IPv6 NTP Server | `ntp-2026-10-21T1159` | **DONE — 3 of 3 PASS, all with reboot persistence measured** | 🔴 **`show ntp status` and `show ntp counters` return EMPTY output**, not an error — read them before and after configuring and report if they stay empty. 🔴 **The DUT clock is UTC, 13 h behind the box** — record the pair once per group. Expect the longest-running group |
| E | T33384 Auto boot from external media | `eom-2026-10-21T1159` | **DEFERRED to after hours** | Test Engineer, 2026-10-21: run A–D now, E after hours. MANUAL-ONLY (commit `4349a50`): a person must insert a FAT32 USB stick carrying `autoboot.txt` plus the release and config it names. **Automatable part gives a PARTIAL**: `autoboot enable` accepted and stored, `show boot` status change, and the negative limb (enabled, no media, still boots `flash:/x960-tb277.rel`) costing one DUT reboot |
| — | T33388 Hardware Watchdog; T33389 Software Watchdog | — | **NOT TESTED** | Test Engineer's decision, 2026-10-21: *"Drop them — NOT TESTED"*. See Issues |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| T33379 | (230) Management - Telnet Client (IPv4) | access-2026-10-21T1159 | PASS | the DUT originates IPv4 telnet as a client, proven on the wire (SYN to TCP/23 from its own SVI, full RFC 854 option negotiation captured at the far end) and end to end (authenticated login to swi_b, commands run there, swi_b logging the session from 10.38.22.97); server-off, bad-credential and wrong-port controls all failed correctly. The DUT's own `no service telnet` was never touched — its server is not under test | T33379/work/run1.log | tester |
| T33380 | (231) Management - SSH Server (IPv4) | access-2026-10-21T1159 | PASS | the DUT serves SSH over IPv4, graded on the wire: 83-packet ESTABLISHED+DATA session for a real `manager` authentication against a 0-packet control; 2-packet REFUSED with `no service ssh ip` **while `show ssh server` still read Enabled**; same for the whole server off; the arc closed both times. 🔴 **REBOOT PERSISTENCE NOW MEASURED (run 2)**: `no service ssh ip` saved as `service ssh ipv6`, survived a 60 s cold boot and was still refusing IPv4 TCP/22 (4/4 SYNs answered RA, ICMP 4/4 to the same address) before anything was typed into the device. **🔴 /create-logs: MERGE run1 + run2 — see Issues** | T33380/work/run1.log + run2.log | tester |
| T33381 | (232) Management - SSH Client (IPv4) | access-2026-10-21T1159 | PASS | the DUT originates IPv4 SSH as a client, proven at the far end where ONE capture holds both the control (SYN to a dead port, answered RST) and the real session (the DUT sending `SSH-2.0-OpenSSH_10.5` from its own SVI, then key exchange); plus host-key verification, authentication, commands run on swi_b, the non-interactive LINE form and a server-off control | T33381/work/run1.log | tester |
| T33387 | (238) EnhancedOperationManagement - Management Stacking | mgmt-2026-10-21T1159 | **UNSUPPORTED** | X960 TPS row 236 states the platform does not implement it (*"not necessary as these units support VCS"*), and the DUT agrees: `% Warning: Stacking is currently disabled`, one member ID 1 Ready Active Master, `Operational Status: Stacking hardware disabled`, VC ID 403, resiliency link Not configured, with a full VCS config surface offered instead. No device state was changed. **Deviation recorded**: the TPS Default Configuration section says *"Stacking is enabled by default"* while this DUT reads the hardware disabled | T33387/work/run1.log | tester |
| T33386 | (237) EnhancedOperationManagement - Management ACL | mgmt-2026-10-21T1159 | PASS | both halves of TPS 6.1.1 proven in the dataplane, never from a `show`: a named hardware ACL gave the specified host 4/4 SYN-ACK while the non-specified host got 0 replies to 4 SYNs, with an ICMP control from that same denied host answered 4/4 in the SAME leg and the DUT's counters agreeing frame for frame (permit 8, deny 4); a standard ACL on an SNMP community failed exactly one cell of a 2x2; `ssh server 2222` moved the service on the wire and back. 🔴 **REBOOT PERSISTENCE NOW MEASURED (run 2)**: after a 60 s cold boot with nothing typed, the non-specified host's 4 SYNs got 0 replies while its ICMP was answered 4/4, and the specified host still completed its handshake — **so TPS 6.1.1 holds across a restart, not only within a session**. **🔴 /create-logs: MERGE run1 + run2** | T33386/work/run1.log + run2.log | tester |
| T47192 | (243) Config_File - A dynamic configuration while operating (Change, Delete) | mgmt-2026-10-21T1159 | PASS | **all three operations TPS line 894 names — addition, change AND deletion, not just the title's two** — take effect dynamically, proven on two unrelated subsystems: a bound hardware filter took an add, an in-place edit that made two flows swap state in opposite directions, and a delete restoring the baseline frame-for-frame; vlan48's address took a change, a delete and an add with every ARP/ICMP signature inverting each time. **Nine operations, zero restarts** — uptime advanced by exactly the elapsed 6 m 14 s. Reboot persistence NOT MEASURED | T47192/work/run1.log | tester |
| T44296 | (259) Management_LLDP - LLDP | lldp-2026-10-21T1159 | PASS | twelve designed steps (the case has **zero** authored steps), all graded on frames and never on `show lldp`: transmit/receive proven independent across all four on/off combinations; ageing timed against a TTL the SENDER chose, with a longer-TTL neighbour on the same port as control; `lldpRemTablesChange` traps caught on the wire against a zero-trap control; neighbours confirmed on the RSTP **Alternate/Discarding** ports 1.0.4, 1.0.14 and 1.0.16 as well as the forwarding 1.0.2. 🔴 **REBOOT PERSISTENCE MEASURED — the first time in three campaigns**: a 15 s timer, 45 s TTL and a System Name TLV all survived a cold boot and were proven on the wire (15 s inter-frame gaps), then defaults restored and re-proven at 30.03 s. Bench returned byte-for-byte, closing probe exit 0 MATCH | T44296/work/run1.log | tester |
| T33398 | (260) Management_LLDP - LLDP-Med | lldp-2026-10-21T1159 | PASS | graded on frames: **the §5 read-back trap caught in the honest direction** — a fully configured voice policy that `show lldp local-info med` reports in full while 40 s of capture carries **zero** MED TLVs, because no MED endpoint is on the port yet; a real Class III endpoint then drew a 7-TLV reply carrying exactly the configured Voice/vlan 70/tagged/priority/dscp policy; Class III classified against a plain Station-only neighbour **on the same port at the same instant**; Fast Start measured at exactly 3 frames 1.00 s apart with its trigger pinned to a NEW endpoint; both removal paths proven independently. 🔴 **REBOOT PERSISTENCE MEASURED** — a non-default priority 6 survived a cold boot | T33398/work/run1.log | tester |
| T33399 | (262) Management_NTP - IPv4 NTP Server | ntp-2026-10-21T1159 | PASS | IPv4 NTP server proven on the wire — mode-4 replies at the configured stratum, **nothing before configuration and nothing after removal**, and per-client `ntp restrict` denial discriminating two clients of the same server in the same run (0 replies vs 2). 🔴 **REBOOT PERSISTENCE MEASURED**: serving 13 s after the login prompt with nothing typed, at the non-default stratum 10 | T33399/work/run1.log | tester |
| T33400 | (263) Management_NTP - IPv4 NTP Client | ntp-2026-10-21T1159 | PASS | IPv4 NTP client proven on the wire — 7 polls / 7 replies / 7 paired, **zero packets to an unreachable control server**, silence after removal — and a real clock error of **14.836 s removed**. 🔴 **REBOOT PERSISTENCE MEASURED**: polling resumed 9 s after the login prompt with nothing typed. A manual `clock set` under a running chronyd is separately graded and its recovery explicitly **NOT MEASURED** | T33400/work/run1.log | tester |
| T44298 | (264) Management_NTP - IPv6 NTP Server | ntp-2026-10-21T1159 | PASS | IPv6 NTP server proven on the wire — mode-4 replies at the configured stratum 7 over IPv6, **nothing before configuration or after removal while the leg still pinged**; **one `ntp master` shown to serve IPv4 and IPv6 at once in a single capture** (IPv4=4, IPv6=6 frames, 5 requests / 5 replies / 5 paired, same stratum, same refid). 🔴 **REBOOT PERSISTENCE MEASURED**: serving over IPv6 11 s after the login prompt with nothing typed | T44298/work/run1.log | tester |
| T33388 | (239) EnhancedOperationManagement - Hardware Watchdog | — | NOT TESTED | Dropped by the Test Engineer 2026-10-21. No user-facing watchdog CLI exists on this platform and **TPS 5.3.6 says so deliberately** (*"can be enabled or disabled by user command"* = No): no `show watchdog`, nothing in config mode. The only trigger available was deliberate crash injection via `start-shell`, which was not authorised | — | Test Engineer |
| T33389 | (240) EnhancedOperationManagement - Software Watchdog | — | NOT TESTED | Dropped by the Test Engineer 2026-10-21, same reason as T33388 | — | Test Engineer |

## 🔧 Group A bench setup and its EXACT restore recipe (written before group A's first case)

Written 2026-10-21 12:5x NZDT by the group-A tester **before** the first case, so a tester that
dies mid-group leaves a recoverable bench (dispatch requirement). Run `.setup` bound by this
group: `tb277/x960/access-2026-10-21T1159/tb277-u2u3.setup` — **swi_d and swi_b only**, swi_a
deliberately absent so the framework's post-failure power cycle can never reach it.

### What group A puts on the bench

**(a) The layer-3 underlay — swi_d only, and it IS SAVED (`write`).** The Test Engineer's
2026-10-21 decision, overriding STANDING-ORDERS §1 for the underlay only. B, C and D inherit it;
**group A does not tear it down.**

```
! swi_d (u2), config mode
vlan database
 vlan 10 name ckUNDERLAY-eth3
 vlan 48 name ckUNDERLAY-eth4
 vlan 10,48 state enable
interface port1.0.10
 switchport mode access
 switchport access vlan 10
interface port1.0.48
 switchport mode access
 switchport access vlan 48
interface vlan10
 ip address 10.38.22.34/27
interface vlan48
 ip address 10.38.22.66/27
! then, at exec:   write
```
Testbox side, already in place and unchanged: eth3 `10.38.22.33/27`, eth4 `10.38.22.65/27`.

**(b) A swi_d↔swi_b management VLAN — CAMPAIGN INFRASTRUCTURE, NOT saved, removed by the
LAST group that runs.** (Sentinel decision relayed 2026-10-21, after group A had built it:
*"treat it as campaign infrastructure, the same as the underlay, not as group A's own setup"* —
group D (NTP) needs DUT↔partner IPv4/IPv6 reachability and group C (LLDP) benefits from it, so
A removing it would only make D rebuild the same thing. Group A therefore **leaves it in
place**. Unlike the underlay it is **not** written to startup-config, so any reload clears it
and the group that next needs it re-applies the block below. **Each group's working log must
say vlan 60 is inherited campaign infrastructure, not that group's own setup**, so no final log
claims it as part of its case.)
The three group-A cases all need the DUT to originate telnet/SSH **to a far end**, and swi_b
had no IPv4 address on any SVI (only `eth0 169.254.42.42/16`, which the testbox cannot reach
and swi_d is not cabled to). swi_d port1.0.2 ↔ swi_b port1.0.2 is the one inter-switch link
RSTP leaves **Forwarding**, so vlan 60 is carried as a *tagged* VLAN on that link with vlan1
left as the native VLAN — the flat vlan1 domain, LLDP and the RSTP tree are untouched.

```
! BOTH swi_d (u2) and swi_b (u3), config mode
vlan database
 vlan 60 name ckMGMT-A
 vlan 60 state enable
interface port1.0.2
 switchport mode trunk
 switchport trunk allowed vlan add 60
 switchport trunk native vlan 1
interface vlan60
 ip address 10.38.22.97/27     ! swi_d
 ip address 10.38.22.98/27     ! swi_b
! NOT written to startup-config on either unit.
```

**(c) Far-end services on swi_b — NOT saved, removed at group end.**
```
! swi_b (u3), config mode
service telnet                       ! T33379 needs a telnet SERVER to connect to
username cktmp privilege 1 password <throwaway, >= 8 chars, never in this repo>
ssh server allow-users cktmp         ! swi_b carries `ssh server allow-users manager`,
                                     ! so a new account is refused without this line
```
🔴 **swi_d's own `no service telnet` is left exactly as found** — the DUT's telnet *server* is
not under test in group A (T33378 covered it on 2026-10-20).

### Restore recipe

**At the end of GROUP A — undo (c) only, on swi_b. Keep (a) and (b).**
```
! swi_b (u3), config mode
no ssh server allow-users cktmp
no username cktmp
no service telnet
! swi_b: never `write`. Its startup-config must stay exactly as found.
```

**At the end of the LAST group to run (group D on the current plan) — undo (b) on BOTH units.**
If group D is BLOCKED, whichever group runs last does this instead; a tester that cannot run it
says so in its hand-back.
```
! swi_d (u2) AND swi_b (u3), config mode
interface port1.0.2
 switchport trunk allowed vlan remove 60
 switchport mode access
 switchport access vlan 1
no interface vlan60
vlan database
 no vlan 60
! swi_d: do NOT `write` after this — startup-config must keep (a) and nothing else.
```

**(a) is never undone.** It is the Test Engineer's deliberate startup-config change.

Neither unit is reloaded by group A except for T33380's reboot-persistence step, which reloads
**swi_d only**. Any reload clears (b) and (c), because neither is saved; the tester that caused
the reload re-applies whichever of them the next case needs, and says so in its working log.

### Baseline this group must return to

| unit | boot image | boot config | telnet server | ssh server |
| --- | --- | --- | --- | --- |
| swi_d (u2) | `flash:/x960-tb277.rel` | `flash:/default.cfg` | Disabled (`no service telnet`) | Enabled, `ssh server allow-users manager` |
| swi_b (u3) | `flash:/backup.rel` | `flash:/default.cfg` | Disabled (`no service telnet`) | Enabled, `ssh server allow-users manager` |

Both units' `flash:/default.cfg` already carried `service ssh`, `no service telnet`,
`ssh server allow-users manager`, `aaa authentication login default local`,
`security-password minimum-length 8` and `security-password history 1` **before** group A
touched anything — measured 2026-10-21 12:42/12:43 NZDT. The `write` in (a) adds the underlay
to that file and changes nothing else.

## 🔧 Group B bench setup and its EXACT restore recipe (written before group B's first case)

Written 2026-10-21 13:5x NZDT by the group-B tester **before** any case changed device state,
so a tester that dies mid-group leaves a recoverable bench (dispatch requirement). Run `.setup`
bound by this group: `tb277/x960/mgmt-2026-10-21T1159/tb277-u2u3.setup` — **swi_d and swi_b
only**, swi_a deliberately absent so the framework's post-failure power cycle can never reach
it. (The box has **no** deployed `/home/st-art/configs/tb277.setup`; the run file is cut from
the generated fence of `bench-setup/tb277/bench-state.md`, capture 2026-10-20T230259Z.)

### What group B INHERITS and does not touch

- **(a) The layer-3 underlay on swi_d**, saved to startup-config by group A at the Test
  Engineer's decision: `vlan 10 ckUNDERLAY-eth3` / `vlan10 10.38.22.34/27` on access port
  `port1.0.10`, and `vlan 48 ckUNDERLAY-eth4` / `vlan48 10.38.22.66/27` on access port
  `port1.0.48`. Testbox side `eth3 10.38.22.33/27`, `eth4 10.38.22.65/27`. **Group B never
  removes it.** Confirmed present at 13:48 NZDT.
- **(b) vlan 60, campaign infrastructure, NOT saved** — swi_d `10.38.22.97/27` and swi_b
  `10.38.22.98/27`, tagged on `port1.0.2` with vlan 1 native. **Group B leaves it in place**;
  the LAST group to run removes it. Confirmed present at 13:48 NZDT.
- 🔴 **Group B issues no `write` / `copy running-config startup-config` on any unit**, for the
  same reason group A's T33380 could not: a `write` on swi_d would save vlan 60, which must stay
  unsaved. Every reboot-persistence limb in this group is therefore **NOT MEASURED, with that
  reason stated**, not skipped.

### What group B puts on the bench (all UNSAVED, all removed by the case that added it)

Group B adds nothing that outlives its own case. Each case applies its configuration, measures,
removes it, and proves the removal against the running-config captured before the case.

**T33386 (Management ACL), on swi_d (u2) only:**
```
! numbered hardware ACL + access-group — the TPS 6.1.1 limb
access-list 3010 <permit/deny rules, source-based, management ports only>
interface port1.0.10
 access-group 3010
interface port1.0.48
 access-group 3010
! standard ACL bound to an SNMP community — the second, independent limb
access-list 10 permit <the permitted host>
snmp-server community <throwaway, ro> 10
snmp-server enable       ! only if it is found off; restored to whatever it was
```
**T47192 (dynamic configuration), on swi_d (u2) only:** transient changes to
`interface vlan48`'s IPv4 address (delete, add a different address, change back to
`10.38.22.66/27`) and a transient hardware ACL, each measured in the dataplane and then undone
inside the case.

**swi_b (u3)** is configured by group B only if the optional third ACL source leg is run
(a device-originated SSH from swi_b `10.38.22.98` to swi_d `10.38.22.97`); that leg adds no
configuration to swi_b at all — it only drives swi_b's own SSH client from its console.

### Restore recipe — run this if a group-B tester dies mid-case

```
! swi_d (u2), config mode — remove anything group B may have left
interface port1.0.10
 no access-group 3010
interface port1.0.48
 no access-group 3010
interface port1.0.2
 no access-group 3011
no access-list 3010
no access-list 3011
no snmp-server community ckacl
no access-list 10
! T47192 only — put vlan48 back to the inherited underlay address
interface vlan48
 no ip address
 ip address 10.38.22.66/27
! swi_d: do NOT `write`. startup-config must keep ONLY group A's underlay.
```
Then confirm with `show ip interface brief` (vlan10 `.34`, vlan48 `.66`, vlan60 `.97`, all
`admin up / running`), `show access-list` (empty) and `show running-config | include snmp-server`
(nothing of ours).

### Baseline group B must return to

| unit | boot image | boot config | running-config |
| --- | --- | --- | --- |
| swi_d (u2) | `flash:/x960-tb277.rel` | `flash:/default.cfg`, Autoboot disabled | exactly `tb277/x960/mgmt-2026-10-21T1159/T33387/swi_d.cfg` (captured 13:48 NZDT, the bench as found) |
| swi_b (u3) | `flash:/backup.rel` | `flash:/default.cfg` | untouched by group B |

`T33387/swi_d.cfg` is the group's reference copy: any group-B teardown is checked by diffing a
fresh `show running-config` against it.


### 🔧 What group B left on the bench (written at hand-back, 2026-10-21 14:2x NZDT)

**Nothing.** Group B added no configuration that outlived its own case, and its restore recipe
above was never needed.

- Both bench cases (T33386, T47192) ended with `tools/rcdiff.py` between the running-config
  captured before step 1 and the one captured after the last step producing **no output** --
  the DUT is byte-for-byte as group A handed it over.
- **Nothing was written to startup-config.** `show boot` closes as it opened:
  `Current boot image : flash:/x960-tb277.rel`, `Current boot config: flash:/default.cfg`,
  `Autoboot status : disabled`.
- The inherited underlay (`vlan10 10.38.22.34/27`, `vlan48 10.38.22.66/27`) and the inherited
  campaign `vlan 60` (swi_d `.97`) are present and `admin up / running`. **vlan 60 is still
  unsaved, as directed** -- the last group to run still removes it.
- swi_b was never configured by group B. swi_a was never opened by group B.
- Closing `tools/tb probe tb277 --consoles u2,u3 ... --template <the run .setup>`: **exit 0
  MATCH**.
- u2 and u3 are at `awplus login:`; nothing of this group's is running on the box
  (`tools/tb ps` for `arpleg|tcpdump|console|ckcon|cfg.py|bench_probe` is empty).

**Open, carried forward (all reported to the sentinel, none blocking):**
1. **Reboot persistence is NOT MEASURED in T33386 and T47192**, the same bind as T33380: proving
   it needs a `write` on swi_d, which would save vlan 60. The campaign-end teardown, which
   removes vlan 60 anyway, remains the cheap place to run all three.
2. **A TPS deviation** recorded in T33387: the TPS Default Configuration section says *"Stacking
   is enabled by default"* while this DUT reads `Stacking hardware disabled`, with no `stack`
   line in its running-config at all.
3. **Two product findings** for `platforms/x960.md`, both new today and both in the case logs:
   a **numbered** hardware ACL holds exactly ONE rule (each `access-list <n> <rule>` silently
   replaces the previous, with an `err`-severity `EXFX ... pclIdActionUpdate` line from the
   driver at the instant of the loss), and **NSM logs an address installation but never a
   removal**. Plus: `access-class` does not exist under `line vty` and `ip access-list` does not
   exist in global config on this build, contrary to the generic AW+ ACL guide.


## Issues

### 🔴🔥 CAMPAIGN METHOD RULE — after ANY reload, ping to 4/4 on every leg BEFORE reading that leg

**Three sightings today, and the third would have INVERTED a verdict.**

1. Group C read a spurious `CHECK_CABLE` straight after a reload.
2. T33380 run 2: the first post-boot leg, 9 s after the login prompt, showed **no TCP reply rows
   and 1 of 4 ICMP**. Discarded, re-taken at 41 s.
3. **T33386 run 2: eth3's first post-boot ping was 0 of 4, the second 4 of 4.** Taken at the
   first attempt, **the host the filter is supposed to PERMIT would have shown no TCP replies
   and read as blocked** — the verdict inverted, and in the direction that looks like a working
   filter.

**Why it is so dangerous with `arpleg --tcp`:** *no reply row at all* means **silently dropped**,
which is exactly what a working filter looks like. A unit still coming up is indistinguishable
from a filter doing its job.

**The rule: a login prompt is not readiness.** After any reload, ping each leg to **4/4** before
taking any measurement on it, and say in the log that you did. This belongs in
`platforms/x960.md` at wrap.

### 🔬 FINDINGS (T33386 run 2)

- **Hardware ACL counters are ZEROED by a reboot**, and afterwards accounted for the post-boot
  legs exactly (permit 8 = 4 SYN + 4 RST from the permitted host, deny 4 = the denied host's 4
  SYNs). **A post-reload counter read is therefore a clean second witness with no residue to
  subtract** — unlike `show ssh server`, which §7F.2 shows cannot carry a verdict at all.
- **No `exfx_cExt_dxch_rules_pclIdActionUpdate` driver error appeared**, where run 1 captured it
  when the NUMBERED form silently lost a rule. That narrows the defect further: **the NAMED form
  survives a full save-and-restore cycle with both rules intact and a silent driver.**


### 🔴🔴 INSTRUCTION TO `/create-logs` — T33380 **and T33386** must MERGE run 1 and run 2

**Both cases have the same shape. If this is missed, each deliverable loses almost all its
steps.** Measured: T33380 `run1.log` 8 STEP headings / `run2.log` **0**; T33386 `run1.log` 9
STEP headings / `run2.log` **0**. Each run 2 is a focused single-limb run with its own two
health samples and its own `VERDICT:` line.

**If this is missed, T33380's deliverable loses eight of its nine steps.**

`/create-logs` §3 step 1 says the final log describes **the latest run only**. That rule assumes
a re-run repeats the whole case. **T33380's run 2 does not.** Measured:

- `run1.log` — **8 STEP headings**, the whole case.
- `run2.log` — **0 STEP headings**. It is a focused single-limb run that measured only the
  reboot persistence that run 1 had to record as NOT MEASURED, plus its own two health samples
  and its own `VERDICT:` line.

Taking run 2 alone would produce a final log containing the persistence limb and nothing else.

**Apply `logged-output.md` §3 "Merging TestCase re-runs" by analogy:** run 1 is the base; run 2's
evidence **replaces** run 1's `NOT RUN:` / NOT MEASURED entry for the persistence limb and is
added as its own step; everything else in run 1 stays verbatim. The header's `Run:` line then
names both dates and what ran on each, as that section requires.

**The verdict does not change** — PASS either way. What changes is that the deliverable stops
saying "reboot persistence NOT MEASURED".

Note `swi_d.cfg` in that folder was overwritten by run 2, which is correct per
`logged-output.md` §2 ("a re-run overwrites them"). Run 1's copy is in git history.

### ⚠️ METHOD NOTE (T33380 run 2) — the post-reload transient, and how it nearly read as a filter

The tester **discarded its first post-boot measurement rather than grading it**, and said so.
Taken 9 s after the login prompt it showed **no TCP reply rows at all and 1 of 4 ICMP** — and
with `arpleg --tcp`, *no reply row* means **silently dropped**, which is the exact signature of
a working filter. It would have read as "the access filter persisted" when the unit was simply
still coming up.

It pinged to 4/4 first and re-took the measurement **41 s after the login prompt**.

This is the same post-reload transient group C saw as a spurious `CHECK_CABLE`. **It is a trap
for any limb measured straight after a reload**, and it is now the second independent sighting
in this campaign. A reload-persistence limb needs a reachability gate before the measurement,
not just a login prompt.


### 🔬 FINDINGS (T44298)

1. **There is no separate IPv6 enable for the NTP server, and none is offered** — a single
   `ntp master` serves both families. Proven in **one** capture: IPv4=4 and IPv6=6 frames,
   5 requests / 5 replies / 5 paired, same stratum, same refid.
2. **`ntp restrict default-v6 serve deny` silences every IPv6 client while IPv4 keeps being
   served**, measured on both legs against one live server seconds apart. Its negation is
   `no ntp restrict default-v6` — **the third `ntp` command in this group whose stored
   running-config line cannot be typed back with `no`**. That is a small pattern of its own and
   worth naming: the stored form and the removal form differ, so a config-driven teardown
   generated from running-config will fail.
3. **An unplanned continuity check worth keeping.** With T33400's NTP client removed for five
   minutes, the DUT's clock still measured **-122 microseconds** against the box, down from
   **-14.269 s** before T33400 ran. The discipline outlived the configuration — which
   independently confirms that T33400's 14.836 s step was real and not an artefact of the
   instrument that measured it.


### 🔥 THE SENTINEL'S 180-SECOND CALL WAS RIGHT, AND THE CAUSE IS OUR BENCH, NOT THE DUT

T33400's post-reload re-sync poll timed out at 180 s with the DUT unsynchronised. The obvious
write-up — *"NTP does not resume after a reboot"* — would have been a **false finding against the
product**. The sentinel asked for a longer window on the grounds that the same DUT had synced in
~45 s from configuration, so 180 s of silence was not self-consistent.

Extended, it **converged at 10 min 55 s** from the login prompt, and the reason is measured
rather than guessed:

> `ntpwire` flagged a **kiss-o'-death, refid RATE**, in the post-boot capture. The DUT's
> boot-time burst — **two polls in the same millisecond from two source ports** — tripped
> **tb277's own ntpd `limited kod` restriction**, and the DUT correctly backed off for about
> nine minutes. The DUT's own log agrees: `Received KoD RATE from 10.38.22.33`.

**That is a property of our bench's NTP server, not a DUT defect.** For contrast, the same DUT
syncs in **~75 s from configuration** and **~24 s on a daemon restart**.

**The lesson, which generalises past NTP:** a timeout is not a measurement. When a wait ends
without the thing you were waiting for, the window itself is a variable — and if an earlier leg
of the same case did it faster, the inconsistency is the finding, not the silence.

### 🔬 FINDINGS (T33400) — two that would mislead anyone grading NTP from a capture

1. **The client randomises its UDP source port on every poll** — seven consecutive polls, seven
   different ports. **A capture filter written for `udp port 123` as the source misses every
   packet.** Filter on the destination, or on the host pair.
2. **The client randomises the transmit timestamp in its requests.** Reading that field as "the
   DUT's clock" gives a wildly wrong answer. It is an anti-spoofing measure, not a clock.

### 🔬 BEST CROSS-CHECK OF THE CAMPAIGN (T33399 + T33400)

The DUT's own chronyd logged `System clock was stepped by 14.836050 seconds`. T33399 had
measured that same clock **from the box, in the opposite direction**, as **-14.835 s**. Two
independent instruments, agreeing to about **1 ms**. That is what an instrument control looks
like when it works.


### 🔥 CROSS-CASE PATTERN — this platform has at least TWO CLI surfaces that silently keep only the LAST value

Two independent instances measured today, in unrelated subsystems, by two different testers:

1. **A numbered hardware ACL (3000–3699) holds exactly ONE rule** (T33386). Each
   `access-list <n> <rule>` silently replaces the previous. Three entered, one kept.
2. **`ntp rate-limit` holds exactly ONE keyword** (T33399). Setting a second **silently discards
   the first** — no message, no `% ` line, and **the device's own log records the discarded
   command as accepted.**

**Neither reports an error and neither shows the loss in running-config.** One instance is a
quirk; two in unrelated subsystems is a pattern worth a developer's attention, because the
failure mode is identical: an operator composes a multi-part policy, the device keeps only the
last part, and nothing anywhere says so. For the ACL that means a management filter collapsing
to its deny and locking the administrator out.

### 🔬 FINDINGS (T33399) — read these before grading any NTP result on this platform

1. **`show ntp status` and `show ntp counters` print COMPLETELY EMPTY output when NTP is not
   configured** — not an error, not a "not configured" message. Confirmed in both directions:
   they populate the instant `ntp master` is applied and go empty again on `no ntp master`. This
   settles the question triage raised. An empty read is a *state*, not a hung command.
2. 🔴 **NTP server rate limiting is ON BY DEFAULT and invisible in running-config** — burst 8,
   interval 8 s, leak 4, visible only in the `ntp rate-limit ?` help text. A 20-packet burst
   0.5 s apart gets **11** answers; `ntp rate-limit burst 64` makes the identical burst
   **20/20**. **Without knowing this, normal product behaviour reads as a bench fault or a
   failing server**, and a tester would chase packet loss that is not there.

### 🔁 CORRECTION to the sentinel's own dispatches — the "13 hour" clock gap is a DISPLAY artefact

Every group dispatch this campaign told the tester *"the DUT clock is UTC, about 13 hours behind
the box"*. **That is wrong and it mattered for an NTP case.** Both ends are on **UTC** and agree
to about 15 s; the 13 hours is the **box's NZDT display**, not a clock difference. T33399
measured the real offset as **-14.269 s**. Any earlier log that applied a 13-hour correction to
a DUT-vs-box comparison should be read with that in mind.


### 🔴 FINDING (T33398) — `switchport voice vlan` SILENTLY adds `spanning-tree portfast`

Measured 2026-10-21. Configuring a voice VLAN on an interface **silently adds
`spanning-tree portfast` to that interface**. Nobody types it, nothing announces it, and a
`write` saves it.

**Why it bites a tester and an operator alike:** a teardown that removes only the voice lines
leaves `spanning-tree portfast` behind, and the running-config diff then fails **for a reason
that looks unrelated to the case**. An operator removing a voice VLAN is left with portfast on a
port they never enabled it on — which changes that port's spanning-tree behaviour.

Two smaller siblings from the same case:
- **`no switchport voice vlan` does NOT remove `switchport voice vlan priority` or
  `switchport voice dscp`.** They survive the parent command and must be removed by name.
- `switchport voice vlan priority 5` is accepted but **never written back**, because 5 is the
  default.

### 🔬 METHOD NOTE (T33398) — the §5 read-back trap, caught in the honest direction

Worth keeping as a worked example. A fully configured LLDP-MED voice policy is reported **in
full** by `show lldp local-info med` while 40 s of capture carries **zero** MED TLVs — because
MED TLVs do not appear until a MED-capable endpoint is seen on that port. The `show` is not
lying and the device is not broken; the read-back simply describes **configuration**, not **what
is on the wire**. A case graded on the `show` alone would PASS without a single MED frame ever
being sent.


### ✅ ANSWERED (T44296) — `lldp run` was NOT probe residue

The queue's group-C note warned that `lldp run` might have been set by the 11:59 triage probe,
which runs without `--read-only`. **It was not.** `lldp run` is in swi_d's **startup-config**
(`flash:/default.cfg` line 46), so it predates every probe this campaign ran. Read from
`show startup-config`, which no probe writes — that is the instrument that settles a
"did our tooling cause this?" question about running-config.

### 🔴 CONFIRMED — swi_d's startup-config now contains vlan 60

Exactly as the Test Engineer's 14:0x decision anticipated. T44296's `write` diff is in its log
line by line: `vlan 60 name ckMGMT-A`, `interface vlan60 / ip address 10.38.22.97/27`, and
port1.0.2's trunk lines.

🔴 **Wrap action, Test Engineer's own hands:** removing it needs `no interface vlan60` /
`no vlan 60`, which the permission system refuses for a tester ("Modify Shared Resources").

### 🔬 FINDINGS (T44296) — the two most likely to mislead a later reader

1. **By default this platform advertises only the three mandatory TLVs** plus one Allied Telesis
   OUI TLV. That is why **`show lldp neighbors` has an empty Sys Name column for every AW+
   partner** — correct behaviour that reads as a defect to anyone who has not captured the
   frames.
2. **`no lldp receive` drops the frame BEFORE the packet counter.** So `In` counts frames
   **accepted**, not frames **arrived**, and cannot be used to prove a frame reached a port.
   Grading a receive-off limb on the In counter would show "no frames arrived" when they did.

Also measured: an x960-56YSQ **cold-boots to its login prompt in 60 s**, so `ckreload.py`'s
720 s default is wildly conservative on this platform.


### 🔴🔥 TOOLING DEFECT (ours, not the product) — `tools/awlogin.py:login()` is a lockout generator

Measured 2026-10-21 15:00. **One `login()` call put FIVE failed logins on swi_b's `manager` in
40 seconds.** AW+ locks an account at five, so swi_b is now locked as well as swi_a.

Verified in the source:

```python
def login(c, tries=5, username=None, password=None):   # awlogin.py:30
    for _ in range(tries):                              # :35  up to 5 iterations
        if p == LOGIN:
            c.s.write(user + b"\r")                     # :42
            c.s.write(pw + b"\r")                       # :44
            if p3 in (None, BAD): continue              # :46  -> another FULL attempt
```

**The driver's retry count equals the platform's lockout threshold.** Any account it fails once
against, it locks. Line 51 does the same at a bare `Password:` prompt.

**What triggered it was NOT a wrong password.** At 9600 the device echoed `ma` and `manag`
instead of `manager` and went straight to `Password:` — a single fast `write(b"manager\r")` is
**truncated on the wire at 9600**. `bench_probe.py` had logged into the same console with the
same password at 14:46, which is the control: the credential is right, the driver's write is
not. The loop then re-sent a **correct** credential four more times into a desynced dialog.

**This is a different mechanism from the group-A finding** (*"recovery must never type a word at
a credential prompt"*). That one typed a stray word; this one re-sends a correct credential
after a transport-level truncation. Both end in the same place.

**The fix, NOT applied mid-case** (it cannot be tested without spending more attempts on the
only two accounts that matter — it belongs with the Test Engineer's unlock):
- an explicitly supplied password is tried **ONCE**, never looped;
- a truncated-echo username is re-sent only after **proving the echo**, never by restarting the
  credential dialog;
- at 9600, write the username a character at a time or verify the echo before sending the
  password.

### 🔴 Both partners are now locked; group C continues on a better instrument

swi_a (u5) locked from yesterday, re-armed by one correct-password probe at 14:47.
swi_b (u3) locked at 15:00 by the defect above. **swi_d (the DUT) is unaffected** — 115200,
factory password, at `awplus#`.

**Clearing either needs an interactive login by the Test Engineer**; nothing automated can do it
without spending attempts that re-arm the 5-minute timer.

**Group C is NOT blocked.** The tester replaced swi_b as the driven partner with **the testbox
itself**, sending crafted LLDPDUs from eth3 into swi_d port1.0.10 with scapy. That is **better
evidence** than swi_b's console would have given: the chassis ID, port ID and TTL are all
chosen, and transmission can be stopped on command, so the neighbour-ageing limb is graded
against a TTL the tester sets rather than waiting out a 120 s one. swi_a and swi_b remain
**passive** partners, measured from the DUT side.

**Consequence for deliverables:** neither `swi_a.cfg` nor `swi_b.cfg` can be produced for group
C, for console-lockout reasons and **not** bench gaps. Both logs say so.


### ✅ DECISION (Test Engineer, 2026-10-21 14:0x) — testers MAY `write`; vlan 60 is removed by hand at the end

Asked because reboot persistence was coming back NOT MEASURED in case after case (T33380,
T33386, T47192), the Test Engineer chose **"Let them write; you remove vlan 60 at the end"**:

> Testers `write` freely, so every persistence limb gets measured for the first time in three
> campaigns. vlan 60 lands in swi_d's startup-config and the Test Engineer removes it at
> campaign end, since VLAN deletion is permission-blocked for the tester.

**This supersedes the sentinel's earlier "keep vlan 60 unsaved" direction.** It applies from
group C onward. Groups A and B are already complete and their persistence limbs stay NOT
MEASURED — the campaign-end run the queue proposes can still pick up T33380, T33386 and T47192.

🔴 **Campaign-end action for the Test Engineer, do not lose this:** swi_d's startup-config will
contain **vlan 60** (`10.38.22.97/27`, tagged on port1.0.2). Removing it needs
`no interface vlan60` / `no vlan 60`, which the permission system refuses for the tester
("Modify Shared Resources"), so it is the Test Engineer's own hands at wrap.

### 🔥 FINDING (T33386) — a NUMBERED hardware ACL holds exactly ONE rule, silently

Measured 2026-10-21. On this platform a numbered hardware ACL (3000–3699) keeps **one** rule:
each `access-list <n> <rule>` **silently REPLACES** the previous one. No error, no warning, and
**nothing in running-config shows a rule was discarded**. Three rules entered, one kept — the
last. The **named** sub-mode keeps them all, in order; the A/B is in T33386's log.

**Why this is a customer-facing hazard, not a curiosity.** Every management filter is
permit-then-deny. Written the obvious way with a numbered list it **collapses to the deny** and
locks out the administrator's own host, and the only warning is a `show access-list` nobody
runs.

**The product corroborates it from inside**, at the instant of the loss:
```
local7.err ... EXFX[1015]: DBG:exfx_cExt_dxch_rules_pclIdActionUpdate 7076:
  Didn't find matching rule (to id 1) for the copying from one (from id 0)
```
T47192 later showed the **named** form taking an add, an in-place edit and a delete with a clean
log, which **narrows the finding to the numbered form specifically** rather than to hardware-ACL
editing in general.

Confirmed first-hand alongside it: **`access-class` does not exist under `line vty`** (`acc ?`
offers only `login`) and **`ip access-list` does not exist in global config**, so the generic AW+
ACL guide's "standard lists still bind to vty access-class" does **not** hold on this build.

### 🔬 More findings for `platforms/x960.md` (T47192)

- **`ip address A.B.C.D/M` on an SVI that already has one REPLACES it in place** — no error, no
  `% ...already...`, no secondary created, and the whole L3 identity moves, including the source
  address of that interface's own ICMP unreachables.
- **NSM logs an address INSTALLATION but never a removal.** `no ip address` writes no log line at
  all, so a test looking for the deletion in the device log finds nothing.
- `snmp-server community <c> ro <acl>` stores as `snmp-server community <c> <acl>` (`ro` is the
  default and is not written back); `ssh server <port>` is stored only when it is not 22.


### 🔬 FINDING (T33381) — the SSH client's host-key trust is PERSISTENT and invisible

Measured 2026-10-21. The DUT's SSH client stores host-key trust for a server it has connected
to, and **no CLI can show it or remove it**:
- `clear ssh` clears **sessions**, not known hosts.
- `show ssh` offers only client and server **configuration**.
- `crypto key` manages the **device's own** keys, not remembered host keys.
- It does **not** appear in running-config, so a configuration diff cannot see it either.

**Why it matters to a later case:** if any case re-keys swi_b, the DUT will meet a host-key
mismatch for 10.38.22.98 with no documented way to clear the stale trust. Groups C and D use
swi_b as a partner. Anyone hitting an unexplained SSH client failure to a partner should suspect
this first.


### 🔬 TOOLING TRAP, measured 2026-10-21 — a recovery loop at a password prompt IS a password guess

Self-reported by the group-A tester after it put **4 failed logins** on swi_b's throwaway
account `cktmp`. **AW+ locks at 5**, so this missed a lockout by one attempt. Zero failures on
`manager` on any unit, zero on swi_d; the next attempt was `Accepted`.

**Root cause, and it is not AW+:** `subprocess.run(input=...)` **REPLACES** stdin, it does not
prepend to it. When `tools/tb` began forwarding a `CK_PASSWORD*` secret over stdin, the far-end
password piped in behind it was swallowed, so the client sent an **empty** password. The driver
then re-prompted and its recovery loop typed `exit` at the password prompt — **which the device
reads as another password guess.** One bug produced four attempts.

**The durable rule: a console driver's error recovery must never type a WORD while the device is
at a login or password prompt.** At a credential prompt the only safe keystrokes are the
protocol escape. Any recovery loop that sends text there is silently generating authentication
attempts, and on a platform that locks accounts it is a lockout generator.

**Fixes, committed with T33381:**
1. `tools/tb` appends the caller's own stdin **after** the secret lines instead of discarding it.
2. `devclient.py` gained `--password-env NAME` — the password rides the same stdin channel as
   the other secrets and arrives as an environment variable, so there is no collision to get
   wrong. `tools/tb`'s secret pattern now carries any `CK_PASSWORD*` / `CK_USER*` name.
3. `devclient.py` **refuses to send an empty password** when one was requested, never types a
   word at a credential prompt, and re-checks once after the escape (the tool had reported the
   console stuck when it was already back at `awplus#`).

**For the wrap:** this belongs in a memory and in `tools/README.md`, not only in a case commit.
The stdin-replacement half is a generic Python trap; the recovery-loop half is a generic
console-driver trap.


### 🟠 NEEDS TEST ENGINEER (recorded 2026-10-21 13:2x) — T33380's reboot-persistence limb

**Nothing is blocked by this; the tester moved on.** Everything else in T33380 is measured.

**The bind.** Proving `no service ssh ip` survives a reboot needs a `write`. `write` saves the
whole running-config, which includes **vlan 60**, the swi_d<->swi_b management VLAN the sentinel
directed be kept **unsaved** as campaign infrastructure.

**A mechanical block sits in the way.** Removing vlan 60 first is the clean route, and
`no interface vlan60` / `no vlan 60` were **refused twice by the permission system**
("Modify Shared Resources"). STANDING-ORDERS/`test-mode` §7: a mechanical block is not a consent
question and a relay cannot lift it — it routes to the Test Engineer to run themselves.
`tools/tb cfg` is otherwise working; adds and `service ssh ip` went through straight after.

**Bench state is sound.** The half-applied batch had taken port1.0.2 out of trunk mode, leaving
vlan 60 `admin up / protocol down`. The tester re-added it; swi_d pings swi_b 3/3. **Nothing
reached startup-config beyond the underlay the Test Engineer approved.**

**Sentinel's recommendation: defer, do not spend a reload now.** The last group removes vlan 60
at campaign end anyway, so that tester runs the sequence for free — write, reload, verify,
restore, write — as a short **T33380 run 2**, giving the case its own second working log instead
of burying the evidence in another group's teardown. T33380 is then re-graded from PASS to
PASS-with-the-limb-measured. The alternative costs a ~3 min DUT reload now AND still needs the
permission block cleared.

### 🔬 Product findings (T33380, measured 2026-10-21) — for `platforms/x960.md`

1. 🔴 **`no service ssh ip` REPLACES the running-config line.** `service ssh` becomes
   `service ssh ipv6`, and `show ssh server` reads `Enabled / Protocol : IPv6`. This is **NOT**
   the telnet rule recorded in §7F.1, where `service telnet` stays and a negation
   (`no service telnet ipv6`) is added. **A grep for a negation finds nothing on a unit with
   IPv4 SSH switched off**, so the obvious check reports the opposite of the truth.
2. **`no service ssh ip` makes the DUT log `IMI: SSH server enabled`** — misleading wording; the
   server was reconfigured, not enabled.
3. **A TCP-level refusal reaches no authentication**: the DUT logged no sshd entry for the
   refused connection, so that leg cost zero failed logins. Useful when designing negative legs
   against a platform that locks accounts.



## 🔧 Group C bench setup and its EXACT restore recipe (written before group C's first case)

Written 2026-10-21 14:5x NZDT by the group-C tester **before** any case changed device state,
so a tester that dies mid-group leaves a recoverable bench (dispatch requirement). Run `.setup`
bound by this group: `tb277/x960/lldp-2026-10-21T1159/tb277-u2u3u5.setup` — **swi_d, swi_b AND
swi_a**, because both partners are the LLDP neighbours these cases measure against. swi_a is
declared with **no `[powerlink]` and no `[power]` outlet**, deliberately: the framework's
post-failure power cycle reaches every unit that has a powerlink (STANDING-ORDERS §6), and the
session constraint forbids rebooting or power-cycling swi_a. With no powerlink the cycle returns
a silent False for swi_a and the unit is never touched. (The box has **no** deployed
`/home/st-art/configs/tb277.setup`; the run file is cut from the generated fence of
`bench-setup/tb277/bench-state.md`, capture 2026-10-20T230259Z.)

### 🔴 swi_a's console could not be opened — group C runs it as a PASSIVE partner

The group-C opening probe (`--read-only`, 2026-10-21 14:46 NZDT) logged in on u2 and u3 and
**failed on u5** with the correct per-console password: `login = "no prompt after login.
tail=''"` — no `Login incorrect`, no prompt, silence. The sentinel reports swi_a's `manager`
account reached 7 failed logins on 2026-10-20 and that every further failure re-arms the
5-minute lock; this one attempt re-armed it. **u5 is not retried by this group.** It was left
at `awplus login:` (checked with a bare-CR `peek`, which types no word).

Consequences, all recorded in both case logs:
- **swi_a is still a live LLDP partner** — it transmits LLDPDUs and swi_d holds its neighbour
  entries on port1.0.4 and port1.0.14. Those are the **Alternate/Discarding** ports, so swi_a
  is exactly the blocked-port contrast this group wants, and reading it needs no swi_a console.
- **`swi_a.cfg` cannot be produced** for either case. That is stated in each working log with
  this reason, rather than silently omitted.
- swi_b (u3) is the fully-driven partner, on the one **Forwarding** inter-switch link
  (swi_d port1.0.2 ↔ swi_b port1.0.2).

Probe result otherwise: **zero MISMATCH rows.** Five NEEDS-CHECK rows, all `CONSOLE_DOWN` for
swi_a, are consequences of that failed login and not bench movement. Exit 4 USER-CONFLICT, line
verbatim: `- the session gives facts for /dev/u5 (outlet 3@10.36.230.35, name swi_a), but no
device was read on /dev/u5 this run`. Nothing in `tb277.static` was edited.

### What group C INHERITS and does not touch

- **(a) The layer-3 underlay on swi_d**, saved to startup-config by group A: `vlan 10
  ckUNDERLAY-eth3` / `vlan10 10.38.22.34/27` on access port `port1.0.10`, and `vlan 48
  ckUNDERLAY-eth4` / `vlan48 10.38.22.66/27` on access port `port1.0.48`. Testbox side
  `eth3 10.38.22.33/27`, `eth4 10.38.22.65/27`. **Group C never removes it.**
- **(b) vlan 60, campaign infrastructure** — swi_d `10.38.22.97/27` and swi_b `10.38.22.98/27`,
  tagged on `port1.0.2` with vlan 1 native. **Group C leaves it in place**; the Test Engineer
  removes it at campaign end.
- Both confirmed present in the 14:46 probe capture of swi_d's running-config.

### 🔴 What group C does differently: it MAY `write`, and it DOES reload swi_d

Test Engineer's decision of 2026-10-21 14:0x (Issues, below): testers `write` freely from group
C onward, and vlan 60 landing in swi_d's startup-config is accepted — the Test Engineer removes
it at campaign end. Group C therefore **measures reboot persistence properly**, which has been
NOT MEASURED for three campaigns.

- Every `write` and every `reload` in this group is on **swi_d only**. swi_b is never written
  and never reloaded. swi_a is never touched at all.
- After each persistence limb the tester restores swi_d's running-config to the pre-case
  baseline and `write`s again, so startup-config ends holding the inherited underlay, vlan 60,
  and the LLDP baseline as found — and nothing of the case's own.
- **Recorded before the first write:** swi_d's startup-config (`flash:/default.cfg`) is read and
  diffed against running-config, so the exact set of lines a `write` adds is known and stated,
  not guessed. In particular `lldp run` is in swi_d's RUNNING config and may be residue of the
  11:59 triage probe, which ran without `--read-only`; whether it is also in startup-config is
  read and reported, never assumed.

### What group C puts on the bench (all removed by the case that added it)

**T44296 (LLDP), swi_d (u2) and swi_b (u3):**
```
! swi_d — global, per-interface and timer configuration, each applied, measured and removed:
[no] lldp run
interface port1.0.10 / port1.0.2
 [no] lldp transmit | lldp receive | lldp notification
lldp timer <s> | lldp holdtime-multiplier <n> | lldp notification-interval <s>
lldp tx-delay <s> | lldp reinit <s>
snmp-server host / snmp-server enable trap lldp      ! notification leg only, removed in-case
! swi_b — only `[no] lldp transmit` on port1.0.2 for the ageing leg; removed in-case.
```
**T33398 (LLDP-MED), swi_d (u2) only:** a voice VLAN and an LLDP-MED network policy on
`port1.0.10` (the testbox eth3 leg), plus `lldp med-tlv-select` selections, all removed in-case.

### Restore recipe — run this if a group-C tester dies mid-case

```
! swi_d (u2), config mode — remove anything group C may have left
interface port1.0.10
 lldp transmit
 lldp receive
 no lldp notification
 no switchport voice vlan
 no switchport voice vlan priority
interface port1.0.2
 lldp transmit
 lldp receive
 no lldp notification
no lldp timer
no lldp holdtime-multiplier
no lldp notification-interval
no lldp tx-delay
no lldp reinit
no lldp med-tlv-select               ! only if a med-tlv-select line is present
no snmp-server host 10.38.22.33
no snmp-server enable trap lldp
no snmp-server community cklldp
lldp run                             ! the state found at 14:46; see the note above
vlan database
 no vlan 70                          ! the T33398 voice VLAN, if present
! then at exec:  write      (startup-config must hold underlay + vlan 60 + the LLDP baseline)

! swi_b (u3), config mode — the only line group C can leave there
interface port1.0.2
 lldp transmit
! swi_b: never `write`. Its startup-config must stay exactly as found.
```
Then confirm on swi_d with `show running-config | include lldp`, `show lldp`,
`show ip interface brief` (vlan10 `.34`, vlan48 `.66`, vlan60 `.97`, all `admin up / running`)
and `show lldp neighbors` (4 neighbours: 1.0.2 and 1.0.16 → swi_b `0000.cd42.3029`, 1.0.4 and
1.0.14 → swi_a `889d.98df.2602`).

### Baseline group C must return to

| unit | boot image | boot config | running-config |
| --- | --- | --- | --- |
| swi_d (u2) | `flash:/x960-tb277.rel` | `flash:/default.cfg`, Autoboot disabled | the capture taken before each case's step 1, diffed with `tools/rcdiff.py` after the last step |
| swi_b (u3) | `flash:/backup.rel` | `flash:/default.cfg` | untouched except the transient ageing-leg line above |
| swi_a (u5) | — | — | never opened; console login refused (above) |

Startup-config on swi_d ends as: group A's underlay + vlan 60 + the LLDP baseline, and nothing
of group C's own. The Test Engineer removes vlan 60 at campaign end.

### 🔧 What group C left on the bench (written at hand-back, 2026-10-21 16:1x NZDT)

**On swi_d, in running-config: nothing.** Both cases ended with the DUT's `show running-config`
**byte-for-byte identical** to the state group C inherited at 14:52 NZDT — verified twice over,
against each case's own pre-case capture and against group C's starting capture. 112 lines both
ways, after two cases, **two reloads** and four `write`s.

**In startup-config, three things, all intended:**
1. group A's layer-3 underlay (`vlan10 10.38.22.34/27`, `vlan48 10.38.22.66/27`);
2. `lldp run` — 🔴 **proven to be swi_d's own SAVED baseline, present in `flash:/default.cfg`
   before this campaign began, and NOT residue of the 11:59 probe.** The dispatch asked for
   this to be settled rather than assumed; it is settled by reading `show startup-config`, which
   no probe writes. See T44296's log;
3. 🔴 **vlan 60** (`ckMGMT-A`, `10.38.22.97/27`, tagged on port1.0.2), which landed there by the
   Test Engineer's own 14:0x decision. **Removing it needs `no interface vlan60` / `no vlan 60`,
   which the permission system refuses for a tester — it is the Test Engineer's own hands at
   campaign wrap.** The `write` diffs that put it there are quoted line by line in T44296's log.

Nothing of either case's own survives in startup-config: every test line was removed and the
removal written.

- **Boot pointers close as they opened** on swi_d: `flash:/x960-tb277.rel`,
  `flash:/default.cfg`, Autoboot disabled.
- **Two reloads, both swi_d only**, both `Expected CLI(user request)` in `show reboot history`,
  both 60 s from `reload` to the login prompt. **swi_a was never opened, never configured and
  never rebooted** — the session constraint was never approached. swi_b was never configured.
- **Closing probe** (`--consoles u2`, swi_d-only template, `--read-only`): **exit 0 MATCH**.
  The repo's `bench-state.md` was not overwritten; both probes wrote to `/tmp`.
- **u2 is at `awplus login:`**, confirmed from the console transcript rather than from a tool's
  stdout. u3 and u5 were not opened after the incidents below. Nothing of this group's is
  running on the box.
- **Host legs:** eth3 → 10.38.22.34 and eth4 → 10.38.22.66 both 3/3, 0% loss, after each reload.
  (A probe run immediately after a reload reports `CHECK_CABLE` on both legs — that is the
  DUT's MAC table being empty after the boot, not a cable fault. Ping first, then re-probe.)

**Open, carried forward (all reported to the sentinel, none blocking):**

1. 🔴 **Both partner consoles are locked out, and one of them was locked by this repo's own
   driver.** swi_a's `manager` was already locked before group C began (the opening probe's
   single attempt with the correct password returned silence, and re-armed the timer). swi_b's
   `manager` was locked **by `tools/awlogin.py`** at 14:59:58 — five failed logins in forty
   seconds from one `ckcon` call. Neither console was retried. Clearing them needs a successful
   interactive login, which only the Test Engineer can do.
2. 🔴 **`tools/awlogin.py:login()` is an account-lockout generator and is still unfixed.** Its
   signature is `login(c, tries=5, ...)` and the loop body sends a complete username and
   password on every iteration, `continue`-ing past `Login incorrect`. AW+ locks at **five**.
   The first failure was not a wrong credential: at 9600 the username write is **truncated**
   (the device echoed `ma` and `manag`, not `manager`), and the control that proves it is
   `bench_probe.py` logging into the same console with the same password at 14:46. **A
   dropped-character write makes one failure; the retry loop turns it into five.** Not fixed
   mid-case deliberately — a login fix cannot be validated without spending more attempts on
   the only two accounts that matter. Same family as group A's finding, different mechanism;
   the durable rule covering both is **an explicitly supplied credential is tried once, and a
   credential dialog is never re-entered by a loop.**
3. **`swi_a.cfg` and `swi_b.cfg` are absent from both cases**, because capturing a running-config
   means logging in. A console-lockout limitation, not a bench gap. Both logs say so with the
   reason.
4. **Twenty product findings for `platforms/x960.md`**, ten per case, in the case logs. The ones
   most likely to mislead a later reader:
   - **by default this platform advertises only the three mandatory LLDP TLVs** plus one Allied
     Telesis OUI TLV, which is why `show lldp neighbors` has an **empty Sys Name column for
     every AW+ partner** — correct behaviour that reads as a defect to anyone who has not
     captured the frames;
   - 🔥 **`switchport voice vlan` silently adds `spanning-tree portfast`**, and a `write` saves
     it — a teardown hazard that makes a running-config diff fail for an unrelated-looking
     reason. `no switchport voice vlan` also leaves `switchport voice vlan priority` and
     `switchport voice dscp` behind;
   - **`no lldp receive` drops the frame BEFORE the packet counter**, so `In` counts frames
     *accepted*, not frames *arrived*;
   - **an x960-56YSQ cold-boots to its login prompt in 60 s**, measured twice.
5. **Three tools changed, all committed with their README entries:** `tools/lldpsend.py` and
   `tools/lldpwire.py` are new (there was no plain LLDP sender and no LLDP decoder in `tools/`);
   `tools/lldpmed_phone.py` is **hardware-verified for the first time** since it was generalised
   on 2026-10-02; `tools/rcdiff.py` gains a measured limit (an "empty" diff can print one
   spurious `-HH:MM:SS` line). `tools/tb` learns `lldpsend` as a root traffic tool.

## 🔧 Group D bench setup and its EXACT restore recipe (written before group D's first case)

Written 2026-10-21 16:3x NZDT by the group-D tester **before** any case changed device state,
so a tester that dies mid-group leaves a recoverable bench (dispatch requirement).

Run `.setup` bound by this group: `tb277/x960/ntp-2026-10-21T1159/tb277-u2.setup` — **swi_d
ONLY**. Group D's dispatch gives `consoles: u2 ONLY`, because swi_b (u3) and swi_a (u5) both
have a **locked `manager` account** and every further login attempt re-arms the five-minute
timer. Neither partner appears in the run `.setup` in any section, so the framework's
post-failure power cycle cannot reach either one. The box has **no** deployed
`/home/st-art/configs/tb277.setup`; this file is cut from the generated fence of
`bench-setup/tb277/bench-state.md` (capture 2026-10-20T230259Z).

### 🔴 The NTP partner is the TESTBOX, not a switch

Group C's answer to the console lockout — replace the driven partner with tb277 itself — is
group D's design too, and for NTP it is strictly better evidence than a partner switch:

- **T33399 / T44298 (DUT as NTP server):** the testbox is the **client**. It sends crafted NTP
  client packets (mode 3) from `eth3` and reads the DUT's mode-4 replies field by field. A
  switch partner would only have given `show ntp associations` on the far end.
- **T33400 (DUT as NTP client):** the testbox is the **server**. tb277 runs the system `ntpd`
  (pid 23898, root, `-g -c /run/ntp.conf.dhcp`), a real NTP implementation, on 10.38.22.33.
- **No `swi_b.cfg` and no `swi_a.cfg` for any case in this group** — not a bench gap, a console
  lockout. Each working log says so with the reason.

### What group D INHERITS and does not touch

- **(a) The layer-3 underlay on swi_d**, saved to startup-config by group A: `vlan 10
  ckUNDERLAY-eth3` / `vlan10 10.38.22.34/27` on access port `port1.0.10`, and `vlan 48
  ckUNDERLAY-eth4` / `vlan48 10.38.22.66/27` on access port `port1.0.48`. Testbox side
  `eth3 10.38.22.33/27`, `eth4 10.38.22.65/27`.
- **(b) vlan 60, campaign infrastructure** — swi_d `10.38.22.97/27`, tagged on `port1.0.2`.
  **Group D leaves it in place**, in running-config AND in startup-config. The earlier plan had
  the last group remove it; that changed when it reached startup-config, and `no interface
  vlan60` / `no vlan 60` is permission-blocked for a tester. **It is the Test Engineer's at wrap.**
- **(c) `lldp run`** — proven by group C to be swi_d's own saved baseline. Left alone.
- Opening probe, 2026-10-21 16:22 NZDT, `--consoles u2 --read-only --baud 115200` against the
  swi_d-only template: **exit 0 MATCH**, zero MISMATCH rows. `bench-state.md` in the repo was
  not overwritten (the probe wrote to `/tmp/ntp1021/bench-state-open.md`).
- **Baseline running-config: 112 lines**, and it differs from startup-config by exactly the two
  lines `! Startup-config saved on Wed Oct 21 03:01:22 2026 +0000 by manager via con0 (ttyS0)`
  and a following `!`. **There are no `ntp` lines anywhere in either.** That is the state every
  case in this group returns to.

### 🔴 The clock fact, corrected and measured (group-wide, recorded once here)

The dispatch said *"the DUT's clock is UTC, about 13 hours behind the box"*. **Measured, that
is a display artefact, not a clock offset**, and for an NTP group the distinction is the whole
point:

| | reading |
| --- | --- |
| box `date -u` | 2026-10-21 **03:23:58 UTC** |
| DUT `show clock` | `UTC Time: Wed, 21 Oct 2026 **03:23:49 +0000**`, `Timezone: UTC`, offset `+00:00` |
| box local | 16:24 NZDT = UTC+13 |

**Both clocks are on UTC and agreed to within about 15 seconds** (the DUT trailing). The 13-hour
figure is the box's *local* NZDT display compared against the DUT's UTC. Every NTP measurement
in this group is taken in **UTC on both ends**, and the ~15 s starting offset is the quantity
T33400 watches close.

### What group D puts on the bench (every line removed by the case that added it)

```
! swi_d (u2) only. swi_b and swi_a are never opened.
! T33399 -- IPv4 NTP server
ntp master <stratum>                 ! and `no ntp master`
ntp restrict <...>                   ! only if the surface allows it; removed in-case
! T33400 -- IPv4 NTP client
ntp server 10.38.22.33               ! the testbox's own ntpd
ntp server 10.38.22.40               ! the unreachable control; removed in-case
clock set <t>                        ! a deliberate, bounded clock offset for the sync limb
! T44298 -- IPv6 NTP server
interface vlan10
 ipv6 enable
 ipv6 address fd32:b1f0:dff8:1603::34/64
ntp master <stratum>
```

### 🔴 Group D `write`s, and it reloads swi_d — three times

Test Engineer's decision of 2026-10-21 14:0x: testers `write` freely. Group C used it to measure
reboot persistence for the first time in three campaigns; **group D measures NTP persistence
the same way, and on the wire** — a persisted server or client configuration that still serves
or still polls after a cold boot, proven by packets and not by `show running-config`.

- Every `write` and every `reload` is on **swi_d only**.
- An x960-56YSQ cold-boots to its login prompt in **60 s** (group C, measured twice).
  `ckreload.py`'s 720 s default is wildly conservative; 180 s is used, with a poll.
- After each persistence limb the case removes its own lines and `write`s again, so
  startup-config ends holding the inherited underlay, vlan 60 and the LLDP baseline **and
  nothing of group D's own**.

### Restore recipe — run this if a group-D tester dies mid-case

```
! swi_d (u2), config mode -- remove anything group D may have left
no ntp master
no ntp server 10.38.22.33
no ntp server 10.38.22.40
no ntp peer 10.38.22.33
no ntp restrict 10.38.22.33
no ntp source
no ntp authentication-key 1
interface vlan10
 no ipv6 address fd32:b1f0:dff8:1603::34/64
 no ipv6 enable
! then at exec:
!   show running-config | include ntp       -> must print NOTHING
!   show running-config | include ipv6      -> only the vlan1/eth0 dhcp lines
!   write                                   -> startup-config back to underlay + vlan 60 + lldp run
```
Then confirm on swi_d with `show ip interface brief` (vlan10 `.34`, vlan48 `.66`, vlan60 `.97`,
all `admin up / running`), `show running-config` = **112 lines**, and ping both host legs from
the box (`10.38.22.34` from eth3, `10.38.22.66` from eth4).

If the DUT's clock was left wrong by a `clock set` and NTP is gone, put it back by hand with
`clock set <HH:MM:SS> <D> <Mon> <YYYY>` against the box's `date -u` — the DUT is on UTC with a
`+00:00` offset and no summer time, so the box's **UTC** reading is the value to type.

### Baseline group D must return to

| unit | boot image | boot config | running-config |
| --- | --- | --- | --- |
| swi_d (u2) | `flash:/x960-tb277.rel` | `flash:/default.cfg`, Autoboot disabled | the 112-line capture taken before each case's step 1, diffed after the last step |
| swi_b (u3) | — | — | never opened: `manager` locked |
| swi_a (u5) | — | — | never opened: `manager` locked |

Startup-config on swi_d ends as: group A's underlay + vlan 60 + `lldp run`, and nothing of
group D's own.

### 🔧 What group D left on the bench (written at hand-back, 2026-10-21 18:0x NZDT)

**On swi_d, in running-config: nothing.** All three group-D cases **and** the three campaign-end
limbs ended with `show running-config` **byte-for-byte identical** to the state group D
inherited at 16:24 NZDT — **112 lines**, verified by `diff` of the extracted bodies after every
single one of the six. That is six cases, **six reloads** and eleven `write`s with zero drift.
(A direct `diff` was used rather than `tools/rcdiff.py`, because of rcdiff's measured
spurious-`-HH:MM:SS` limit recorded by group C.)

**In startup-config: exactly what group C left, and nothing else.** Every `write` group D did is
accounted for, and the final `show startup-config` differs from the campaign baseline by **one
line only** — the `! Startup-config saved on Wed Oct 21 04:56:08 2026 +0000 by manager via con0
(ttyS0)` comment. Still present, all three intended:
1. group A's layer-3 underlay (`vlan10 10.38.22.34/27`, `vlan48 10.38.22.66/27`);
2. `lldp run`, swi_d's own saved baseline;
3. 🔴 **vlan 60** — **left in place deliberately**, per this dispatch. The earlier plan had the
   last group remove it; that changed when it reached startup-config, and `no interface vlan60`
   / `no vlan 60` is permission-blocked for a tester. **It is the Test Engineer's at wrap.**

- **Boot pointers close as they opened** on swi_d: `flash:/x960-tb277.rel`,
  `flash:/default.cfg`, Autoboot disabled — re-read after every case.
- **Six reloads, all swi_d only**, all `Expected CLI(user request)` in `show reboot history`,
  all 60–61 s from `reload` to the login prompt. **swi_b and swi_a were never opened — not one
  byte, not a bare CR, no probe, no `ckcon`, no credential of any kind.** The locked accounts
  were never approached.
- 🔴 **The DUT's clock was deliberately skewed during T33400 and is NOT left that way.** It was
  moved -58 min 42 s, hand-corrected to within ~2 s, and then corrected by **NTP itself**
  (`chronyd: System clock was stepped by 0.592688 seconds`); the NTP client was removed only
  afterwards. Final read `04:21:17 UTC` against the box's `04:21:20` — inside the console's own
  round-trip. **The next session inherits a correct clock.**
- **Closing probe** (`--consoles u2`, swi_d-only template, `--read-only`, `--baud 115200`):
  **exit 0 MATCH**, run twice (16:34 and 17:58). The repo's `bench-state.md` was never
  overwritten; all three probes wrote to `/tmp`.
- **u2 is at `awplus login:`**, confirmed from the console transcript
  (`tools/tb tail tb277 /tmp/ntp1021/console-u2.log`), not from a tool's stdout.
- **Host legs:** eth3 → 10.38.22.34 and eth4 → 10.38.22.66, both 3/3, 0% loss at hand-back.
- Nothing of group D's is running on the box (`tools/tb ps` for tcpdump/arpleg/console tools:
  empty). Every capture was a bounded `timeout <secs> tcpdump`.

**Campaign-end job 1 is COMPLETE.** All three deferred reboot-persistence limbs were run, each
as a proper **run 2** with its own working log beside the original run 1, and each graded on the
wire:

| case | limb | result |
| --- | --- | --- |
| **T33380** run 2 | `no service ssh ip` surviving a reload | **PASS** — saved as `service ssh ipv6`; after a 60 s cold boot IPv4 TCP/22 answered `RA` to 4 of 4 SYNs while ICMP answered 4 of 4, before anything was typed |
| **T33386** run 2 | a management `access-group` surviving a reload | **PASS** — **both halves**: the non-specified host's 4 SYNs dropped silently in hardware (ICMP 4 of 4), the user-specified host still got 4 `SA`. TPS 6.1.1 now satisfied across a restart |
| **T47192** run 2 | a DYNAMIC change surviving a reload | **PASS** — vlan48 `.66`→`.70` applied while operating, saved, and back after the boot with its full L3 identity including the source of its own ICMP unreachables. "Dynamic" does not mean "temporary" |

**No case in this campaign now carries an unmeasured reboot-persistence limb.** T47192's other
two NOT MEASURED items are untouched and still NOT MEASURED, deliberately: file-driven
configuration needs a root write to the box's `/tftproot` (STANDING-ORDERS §4), and the mid-flow
frames-lost timing number needs a tool that does not exist in `tools/`. Neither was improvised.

**Open, carried forward (all reported to the sentinel, none blocking):**

1. 🔴 **vlan 60 is still in swi_d's running-config AND startup-config**, by instruction.
   Removing it needs `no interface vlan60` / `no vlan 60`, which the permission system refuses
   for a tester. **The Test Engineer's own hands at campaign wrap.**
2. 🔴 **Both partner consoles are still locked** (swi_b and swi_a `manager`). Group D designed
   around them completely and never approached them, so nothing in this group re-armed either
   timer. `tools/awlogin.py:login()` is **still unfixed** — group C's finding stands unchanged.
3. **No `swi_b.cfg` or `swi_a.cfg` for any of group D's six cases**, for that reason. Every log
   says so with the reason, as a console-lockout limitation and not a bench gap.
4. 🔬 **A post-reload leg must be settled before it is read — this bit three times in one hour**
   and once it would have **inverted a verdict**. T33380 run 2: a leg 9 s after the login prompt
   showed no TCP reply rows and 1 of 4 ICMP. T33386 run 2: eth3's first ping was 0 of 4, the
   second 4 of 4 — taken at the first attempt, the permitted host's leg would have read as *the
   filter blocking the host it is meant to permit*. T47192 run 2: first ping 1 of 4, second
   4 of 4. **With `arpleg --tcp`, "no reply row" means *silently dropped*, which is
   indistinguishable from a unit still coming up.** Ping every leg to 4/4 first, then measure.
   Same family as group C's spurious `CHECK_CABLE`.
5. **Two new tools, both committed with their README entries and both instrument-controlled
   before use:** `tools/ntpc.py` (crafted NTP client, IPv4+IPv6, no root — deliberately a plain
   UDP socket rather than scapy, because the box's own `ntpd` owns UDP/123) and
   `tools/ntpwire.py` (pcap decoder and counter, IPv4+IPv6, with request/reply pairing on the
   origin timestamp). `ntpc` was proved against the box's own `ntpd` on 127.0.0.1 before the DUT
   was touched; `ntpwire` was proved on a capture whose answer was already known. Both are now
   IPv6-verified on hardware.
6. 🔴 **tb277's own `ntpd` kiss-o'-death-rate-limits a booting DUT.** The DUT's boot-time poll
   burst (two polls in the same millisecond from two source ports) tripped the box's stock
   `limited kod` restriction; the DUT got a stratum-0 `RATE` reply and correctly backed off for
   about **nine minutes**. It is a property of **our server**, not of the DUT, but it will
   happen again — budget for it in any NTP client case on this bench, and read the KoD off the
   capture (`ntpwire` flags it) rather than guessing at a stall.
7. 🔴 **A manual `clock set` leaves a RUNNING `chronyd` unsynchronised** on the DUT, while it
   keeps polling successfully at `reach 377` and reports the true offset. Not recovered within
   the windows measured (90 s at a 3523 s offset, 75 s at a 2.12 s offset); whether it would
   eventually slew is **NOT MEASURED**. A client restart steps the clock in 2 s. Worth a
   developer's eye.
8. **Thirty-odd product findings across the six logs**, listed per case. The ones most likely to
   mislead a later reader:
   - **`show ntp status` and `show ntp counters` print COMPLETELY EMPTY output when NTP is not
     configured** — no error, no message; on a 115200 console it looks exactly like a hung
     command. Confirmed in both directions;
   - 🔥 **NTP server rate limiting is ON BY DEFAULT and invisible in running-config**
     (burst 8, interval 8 s, leak 4): a 20-packet burst 0.5 s apart legitimately returns 11
     answers, and `ntp rate-limit burst 64` makes the identical burst 20/20;
   - 🔥 **`ntp rate-limit` holds exactly ONE keyword** — setting a second silently discards the
     first, with no message and no `% ` line. Same family as group B's numbered-ACL finding;
   - 🔥 **the NTP client randomises BOTH its UDP source port and its request transmit
     timestamp** on every poll, so a filter written for source port 123 misses every packet and
     that timestamp read as "the DUT's clock" gives a wildly wrong answer;
   - **`show ntp counters` counts the CLIENT role only** — all three counters read 0 after the
     DUT had served more than sixty requests as a server;
   - **three more `ntp` commands whose stored running-config line cannot be typed back with
     `no`** (`ntp restrict <addr> serve deny`, `ntp rate-limit <keyword>`,
     `ntp restrict default-v6 serve deny`).
