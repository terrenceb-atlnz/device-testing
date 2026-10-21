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
| B | T33386 Management ACL; T47192 dynamic config; **T33387 Management Stacking** | `mgmt-2026-10-21T1159` | PENDING | 🔴 **No `access-class` under `line vty` on this platform** — `acc ?` offers only `login`. `ip access-list ?` is `% Unrecognized command`. Use `access-list`+`access-group`, `snmp-server community <n>`, `ssh server allow-users/deny-users`, `service telnet\|ssh ip`. **Hardware ACLs implicitly PERMIT, software/standard implicitly DENY** (§5) — grading the wrong default round is the easy false pass. T33387 is a desk verdict: UNSUPPORTED on TPS row 236 |
| C | T44296 LLDP; T33398 LLDP-Med | `lldp-2026-10-21T1159` | PENDING | ✅ Loop question settled, safe to run. 🔴 **Run the probe with `--read-only` first** — the 11:59 probe toggled `lldp run` itself and may be the reason it is on. Record `show running-config \| include lldp` as the first act. `show lldp neighbors brief` does not exist. Run `.setup` carries swi_a **with no `[powerlink]`** so the post-failure cycle cannot reach it |
| D | T33399 IPv4 NTP Server; T33400 IPv4 NTP Client; T44298 IPv6 NTP Server | `ntp-2026-10-21T1159` | PENDING | 🔴 **`show ntp status` and `show ntp counters` return EMPTY output**, not an error — read them before and after configuring and report if they stay empty. 🔴 **The DUT clock is UTC, 13 h behind the box** — record the pair once per group. Expect the longest-running group |
| E | T33384 Auto boot from external media | `eom-2026-10-21T1159` | **DEFERRED to after hours** | Test Engineer, 2026-10-21: run A–D now, E after hours. MANUAL-ONLY (commit `4349a50`): a person must insert a FAT32 USB stick carrying `autoboot.txt` plus the release and config it names. **Automatable part gives a PARTIAL**: `autoboot enable` accepted and stored, `show boot` status change, and the negative limb (enabled, no media, still boots `flash:/x960-tb277.rel`) costing one DUT reboot |
| — | T33388 Hardware Watchdog; T33389 Software Watchdog | — | **NOT TESTED** | Test Engineer's decision, 2026-10-21: *"Drop them — NOT TESTED"*. See Issues |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| T33379 | (230) Management - Telnet Client (IPv4) | access-2026-10-21T1159 | PASS | the DUT originates IPv4 telnet as a client, proven on the wire (SYN to TCP/23 from its own SVI, full RFC 854 option negotiation captured at the far end) and end to end (authenticated login to swi_b, commands run there, swi_b logging the session from 10.38.22.97); server-off, bad-credential and wrong-port controls all failed correctly. The DUT's own `no service telnet` was never touched — its server is not under test | T33379/work/run1.log | tester |
| T33380 | (231) Management - SSH Server (IPv4) | access-2026-10-21T1159 | PASS | the DUT serves SSH over IPv4, graded on the wire: 83-packet ESTABLISHED+DATA session for a real `manager` authentication against a 0-packet control; 2-packet REFUSED with `no service ssh ip` **while `show ssh server` still read Enabled**; same for the whole server off; the arc closed both times. **STEP 8 reboot persistence is NOT MEASURED, not skipped** — see Issues. Nothing was written to startup-config | T33380/work/run1.log | tester |
| T33381 | (232) Management - SSH Client (IPv4) | access-2026-10-21T1159 | PASS | the DUT originates IPv4 SSH as a client, proven at the far end where ONE capture holds both the control (SYN to a dead port, answered RST) and the real session (the DUT sending `SSH-2.0-OpenSSH_10.5` from its own SVI, then key exchange); plus host-key verification, authentication, commands run on swi_b, the non-interactive LINE form and a server-off control | T33381/work/run1.log | tester |
| T33387 | (238) EnhancedOperationManagement - Management Stacking | mgmt-2026-10-21T1159 | **UNSUPPORTED** | X960 TPS row 236 states the platform does not implement it (*"not necessary as these units support VCS"*), and the DUT agrees: `% Warning: Stacking is currently disabled`, one member ID 1 Ready Active Master, `Operational Status: Stacking hardware disabled`, VC ID 403, resiliency link Not configured, with a full VCS config surface offered instead. No device state was changed. **Deviation recorded**: the TPS Default Configuration section says *"Stacking is enabled by default"* while this DUT reads the hardware disabled | T33387/work/run1.log | tester |
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


## Issues

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


