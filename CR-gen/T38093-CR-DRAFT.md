# CR draft — T38093 → (CR key to come)

Source: [IE520/mrp-2026-09-29/38093-fail.log](../IE520/mrp-2026-09-29/38093-fail.log) and
[evidence/38093/](../IE520/mrp-2026-09-29/evidence/38093/) (run 2026-09-30 14:32–14:59 NZDT, tb470), with
the same symptom in [38098.log](../IE520/mrp-2026-09-29/38098.log), [38097.log](../IE520/mrp-2026-09-29/38097.log),
[38099.log](../IE520/mrp-2026-09-29/38099.log) and [28863.log](../IE520/mrp-2026-09-29/28863.log) (same day, same ring).
Build: awplus_main-20260923-20. Structure and rules: [TEMPLATE.md](TEMPLATE.md). **RCA not filled.**

## Decisions before filing
1. **Two-node ring.** tb470 has only one other MRP-capable unit (the x230 and AR4050S have no
   MRP CLI), so every run used a ring of two nodes joined by two links. The case asks for three
   (step 4, "sw2", NOT RUN). A developer may ask whether it reproduces with three or more nodes;
   we can't answer that on this bench. The draft says so plainly.
2. **Priority**: drafted as `3 - Major` (S: loss of function in one area, MRP; the device is not
   locked up; the loop clears by itself). The 500 ms profile mostly avoids it (1 out of 8
   closures looped), but that is a partial workaround at the cost of slower recovery, so I
   haven't used it to argue for `4 - Minor`.
3. **New feature/platform `Y`**: same caveat as before. MRP on another platform wasn't compared;
   tb470 has no other MRP unit.
4. **Profile change loops too** (T38099 O-1: `profile 500` on a live MRM restarts the manager,
   with a 79 ms loop and 8 EXFX `Failed to delete STARGV entry` errors at local7.err). This is
   a separate symptom. Own CR, a line in this one, or leave out? Not in the draft.
5. **Duplicate search**: yours.

## Before creating — duplicate check
Search terms: `MRP ring opened`, `MRP loop ring closed`, `MRP_ProtEvTestTimerExpired`, `MRM test timer`,
`MRP broadcast storm link up`. Hits: _(to fill)_

---
## Main tab

### Summary
```
[IE520-28GSX] MRP manager falsely declares the ring open and loops traffic when a ring link is restored or the ring comes up after boot
```

### Priority
`3 - Major` (see Decisions 2).

### Basic Analysis
```
# Repeatable: Y
#- frequency: Run 1 (T38093, stack MRM, 200ms profile; attached 38093-fail.log): 3 out of 3 ring closures; Run 2 (T38098, stack MRM, 200ms; attached 38098.log): 8 out of 8; Run 3 (T38097, standalone IE520 MRM, 200ms; attached 38097.log): 4 out of 4; Run 4 (T38099, stack MRM, 500ms profile; attached 38099.log): 1 out of 8; Total: 16 out of 23
# Degradation or regression keyword set: N
#- Regression/Degradation process followed: N - Issue is specific to a new platform (IE520) so degradation check is not required; IE520 has no GA release to perform a regression check against.
#- All builds tested that contain this issue: awplus_main-20260923-20
#- All builds tested that do not contain this issue: none
# Binary search performed: N - Only one build tested; IE520 is a new platform with no release in which the issue is known to be absent.
#- All mainline builds tested that contain this issue: awplus_main-20260923-20
#- All mainline builds tested that do not contain this issue: none
#- Changelog link:
# Blocks Testing keyword set: N
#- number of tests blocked: 0
# New feature/platform: Y - IE520-28GSX (new platform). Not compared against an existing platform (no other MRP-capable unit on the bench).
```

### Keywords
None.

### Issue Description
```
h4. +Description:+
Found by AWPTCM-T38093 "MRP ring with DUT as MRM" on a 3-member IE520-28GSX VCStack, awplus_main-20260923-20 (attached 38093-fail.log), and seen in every MRP case run the same day: T38098, T38097, T38099 (attached 38098.log, 38097.log, 38099.log) and T28863 (attached 28863.log), where the same false "Ring opened" followed a stack master failover and a member rejoining the stack.

Ring: MRP ring 1 in VLAN 1, profile 200ms (default), React on Link Change: No. The DUT is the MRM; a standalone IE520-28GSX is the MRC. The ring has two nodes joined by two links (copper SFP+ at 1000, and 1000BASE-SX); a third node was not available.

Working correctly: the ring is Closed with one MRM port Blocking; shutting a forwarding ring port switches over in 70-108 ms with no duplicated frames; after save and reboot the ring comes back and traffic flows.

*Expected:* when the broken link is restored, the MRM detects the closed ring and keeps one ring port blocked, so the ring never forms a loop.
*Actual:* on every ring closure (a restored link, or the ring coming up after boot) the MRM logs "Ring closed", sets the returning port Forwarding, then logs {{CHK_RC -> CHK_RO evt=MRP_ProtEvTestTimerExpired}} and "Ring opened" while the other ring port is also Forwarding. The MRC has its ports Forwarding too, so the ring loops until the MRM blocks the port again (~1 s later in the log; MRM syslog attached as 38093-mrm-log-link-restore.txt and 38093-mrm-log-post-boot.txt). During that time VLAN 1 loops (per-run measurements attached as 38093-loop-windows.txt):
* loop windows of 42-62 ms after a link restore, and 303 ms + 81 ms at the post-boot ring-up
* one broadcast frame received up to 410 times; each host NIC received its own frames back
* after the reboot the DUT logged {{EXFX: Thrash-limiting: Disabled learning on sa2 ... on vlan 1}} (and port1.0.2, port1.0.9; on members 1 and 4 too)

Also: 39 s after the post-boot ring closed, with no link, stack or configuration event, the MRM again logged TestTimerExpired / "Ring opened", set port1.0.13 Forwarding, and blocked it again 1 s later (01:49:30 in 38093-mrm-log-post-boot.txt).

It is not caused by stacking: the same happens with the standalone IE520 as MRM (T38097: 4 out of 4 closures, 26-40 ms; 38097.log). It depends on the profile: with profile 500ms, 1 out of 8 closures looped, the first after the profile change (T38099; 38099.log).

{{show mrp ring}} never shows it: every sample reads Closed or Open as expected, and Topology Change Count does not move (1 s polling across the shut and restore attached as 38093-show-mrp-ring-poll.txt). Only traffic and the syslog show the loop.

Network impact: a short broadcast storm across the ring on every ring closure — every link repair and every reboot of the MRM — with duplicated frames, frames looped back to their senders, MAC-learning thrash and unicast holes of up to 180 ms (1688 ms in one post-boot window).

h4. +Consequences:+
Lose traffic / unexpected traffic flow: each ring closure loops VLAN traffic for tens to hundreds of milliseconds (broadcast storm, duplicated frames, frames sent back to their source, MAC thrash-limiting) and leaves unicast holes up to 180 ms. It recovers by itself within about a second, without a reboot. It recurs on every closure, and once with no event at all.

h4. +Reproduction Method:+
Topology and configuration as in Network Configuration and Device Configuration.
# Build MRP ring 1 in VLAN 1: DUT = manager on port1.0.13 and port4.0.26, standalone IE520 = client on port1.0.13 and port1.0.26; profile left at the default 200ms. No other path between the two (STP off, the other inter-switch links shut).
# Run continuous traffic across the ring in both directions (here 500 pps broadcast and unicast per direction, with sequence numbers). Check {{show mrp ring}}: Manager, Closed, one port Blocking. No duplicates.
# {{shutdown}} the DUT's forwarding ring port. The ring opens and traffic switches over in under 200 ms, with no duplicates. Correct.
# {{no shutdown}} the same port. Within a second of link-up: duplicated frames, frames returned to their sender, and in {{show log}} "Ring closed" -> port Forwarding -> "MRP_ProtEvTestTimerExpired" -> "Ring opened".
# Repeat 3-4 with the other ring port: same.
# {{write memory}} and {{reload}} the DUT: at ring-up after boot the same loop, plus "Thrash-limiting: Disabled learning" in the log.
```

### Network Configuration
```
DUT (IE520-28GSX VCStack, members 1/3/4) : IE520-28GSX standalone (MRC)
port1.0.13 : port1.0.13 (MRP ring port; AT-SP10TM SFP+, linked at 1000)
port4.0.26 : port1.0.26 (MRP ring port; AT-SPSX, 1000BASE-SX)
port4.0.9 : port1.0.9 (shut at the DUT end, so the ring is the only path)

DUT : x230-10GP (traffic source path, vlan1)
sa2 = port1.0.2 + port1.0.9 : sa2 = port1.0.3 + port1.0.4

x230-10GP port1.0.1 : Traffic host eth3 (vlan1)
IE520 standalone port1.0.2 : Traffic host eth2 (vlan1)
Traffic eth3 -> x230 -> DUT -> ring -> IE520 standalone -> eth2, and the reverse, so it crosses the ring.
```

### Device Configuration
```
DUT (stack), added to the bench baseline config (attached as IE520-stk-baseline-running-config.txt):
{noformat}
service mrp
mrp ring 1
 role manager
interface port1.0.13
 no static-channel-group
 mrp ring 1
interface port4.0.26
 no switchport access vlan
 mrp ring 1
interface port4.0.9
 shutdown
{noformat}
show mrp ring (DUT): Role Manager, Profile 200ms, Default Test Frame Interval 20ms, Test Monitoring Interval Count 3, React on Link Change: No.

IE520 standalone (MRC), added to its baseline config (attached as IE520-sa-baseline-running-config.txt):
{noformat}
service mrp
mrp ring 1
 role client
interface port1.0.13
 no static-channel-group
 mrp ring 1
interface port1.0.26
 no switchport access vlan
 mrp ring 1
{noformat}
Ring ports are access ports in VLAN 1. Spanning tree is off on both.
```

### Linked Issues
None known (pending the duplicate search).

### Attachment
- `38093-fail.log` — `IE520/mrp-2026-09-29/38093-fail.log`: the full case (every closure, the reboot, results table)
- `38098.log` — `IE520/mrp-2026-09-29/38098.log`: 8 out of 8 restores looped (200ms profile)
- `38097.log` — `IE520/mrp-2026-09-29/38097.log`: same with the standalone IE520 as MRM (4 out of 4)
- `38099.log` — `IE520/mrp-2026-09-29/38099.log`: profile 500ms, 1 out of 8
- `28863.log` — `IE520/mrp-2026-09-29/28863.log`: the same false "Ring opened" after a stack master failover and a member rejoin (graded PASS against its title; kept as an observation)
- `38093-mrm-log-link-restore.txt` — `evidence/38093/s7-log-u4.out`: MRM syslog across the shut and restore
- `38093-mrm-log-post-boot.txt` — `evidence/38093/s9-postboot-u5.out`: MRM syslog at the post-boot ring-up, thrash-limiting, and the stray "Ring opened" at 01:49:30
- `38093-show-mrp-ring-poll.txt` — `evidence/38093/t93fo/poll-u2.out`: `show mrp ring` on the MRM about every second across the shut and restore
- `38093-loop-windows.txt` — `evidence/38093/t93fo/loopwin.txt` + `flowstat.txt`, `t93fo2/`, `t93boot/` (the per-run loop measurements)
- `IE520-stk-baseline-running-config.txt`, `IE520-sa-baseline-running-config.txt` — `bench-setup/captures/2026-09-30T013300Z/u2.show_running-config.txt`, `u3.show_running-config.txt`

Missing per G: no pcap (per-frame receive files were on tb470's tmpfs and are gone), no tech-support.

---
## Debug Output tab

### Debug Output
```
{noformat}
=== Issue NOT seen: steady state, ring Closed (14:38:55, before the shut) [38093-show-mrp-ring-poll.txt; traffic from 38093-fail.log] ===
IE520-stk#show mrp ring
 Role:                                Manager
 Network Status:                      Closed
 Port1:                               port1.0.13
  Status:                             Forwarding
 Port2:                               port4.0.26
  Status:                             Blocking
 React on Link Change:                No
 Profile:                             200ms
  Default Test Frame Interval:        20ms
  Test Monitoring Interval Count:     3
Traffic, 60 s, 4 flows x 30000 frames: 0 lost, 0 duplicates, 0 frames returned to sender.

=== Shut a forwarding ring port (port1.0.13): correct [38093-mrm-log-link-restore.txt, 38093-loop-windows.txt] ===
01:40:00 mrpd: FSM: ring_id=1 CHK_RC -> PRM_UP evt=MRP_ProtEvMAUTypeChangeInd
01:40:00 mrpd: PORT: port 5013 set Blocked
01:40:00 mrpd: PORT: port 20026 set Forwarding
Traffic: one 108 ms outage, no duplicates.

=== Issue seen: no shutdown port1.0.13 (link up 01:40:34) [38093-mrm-log-link-restore.txt; traffic from 38093-loop-windows.txt] ===
2026 Sep 30 01:40:34 user.notice IE520-stk mrpd: PORT: port1.0.13 link UP (0x11043)
2026 Sep 30 01:40:34 user.notice IE520-stk mrpd: ffffffff-ffff-ffff-ffff-ffffffffffff: Ring-id[1]: Ring closed
2026 Sep 30 01:40:34 user.notice IE520-stk mrpd: FSM: ring_id=1 PRM_UP -> CHK_RC evt=MRP_ProtEvMAUTypeChangeInd
2026 Sep 30 01:40:34 user.notice IE520-stk mrpd: FSM: PRM_RPort 20026 SEC_RPort 5013
2026 Sep 30 01:40:34 user.notice IE520-stk mrpd: FSM: port 5013 state Up
2026 Sep 30 01:40:34 user.notice IE520-stk mrpd: PORT: Update ring port port1.0.13 with state to Forwarding   <=====
2026 Sep 30 01:40:34 user.notice IE520-stk mrpd: PORT: port 5013 set Forwarding                               <===== both ring ports forwarding
2026 Sep 30 01:40:34 user.notice IE520-stk mrpd: ffffffff-ffff-ffff-ffff-ffffffffffff: Ring-id[1]: Ring opened   <=====
2026 Sep 30 01:40:34 user.notice IE520-stk mrpd: FSM: ring_id=1 CHK_RC -> CHK_RO evt=MRP_ProtEvTestTimerExpired   <=====
2026 Sep 30 01:40:35 user.notice IE520-stk mrpd: PORT: Update ring port port1.0.13 with state to Blocked
2026 Sep 30 01:40:35 user.notice IE520-stk mrpd: ffffffff-ffff-ffff-ffff-ffffffffffff: Ring-id[1]: Ring closed
2026 Sep 30 01:40:35 user.notice IE520-stk mrpd: FSM: ring_id=1 CHK_RO -> CHK_RC evt=MRP_ProtEvTestRingInd
2026 Sep 30 01:40:35 user.notice IE520-stk mrpd: FDB: Flush FDB entries for the ring ports with ifindices: {5013, 20026}
Traffic at the restore:
  loop window 62 ms: 2434 duplicate receptions                    <=====
  max copies of one frame: 410                                    <=====
  frames returned to sender: eth2 611, eth3 1272                  <=====

=== Issue seen: ring-up after save + reload (01:48:51) [38093-mrm-log-post-boot.txt; traffic from 38093-loop-windows.txt] ===
2026 Sep 30 01:48:51 user.notice IE520-stk mrpd: ffffffff-ffff-ffff-ffff-ffffffffffff: Ring-id[1]: Ring closed
2026 Sep 30 01:48:51 user.notice IE520-stk mrpd: FSM: ring_id=1 PRM_UP -> CHK_RC evt=MRP_ProtEvMAUTypeChangeInd
2026 Sep 30 01:48:51 user.notice IE520-stk mrpd: PORT: Update ring port port1.0.13 with state to Forwarding   <=====
2026 Sep 30 01:48:51 user.notice IE520-stk mrpd: ffffffff-ffff-ffff-ffff-ffffffffffff: Ring-id[1]: Ring opened   <=====
2026 Sep 30 01:48:51 user.notice IE520-stk mrpd: FSM: ring_id=1 CHK_RC -> CHK_RO evt=MRP_ProtEvTestTimerExpired   <=====
2026 Sep 30 01:48:51 local6.warning IE520-stk EXFX[731]: Thrash-limiting: Disabled learning on sa2 by 00f0.4d00.7718 on vlan 1   <=====
2026 Sep 30 01:48:51 local6.warning IE520-stk EXFX[731]: Thrash-limiting: Disabled learning on port1.0.2 on vlan 1
2026 Sep 30 01:48:51 local6.warning IE520-stk EXFX[731]: Thrash-limiting: Disabled learning on port1.0.9 on vlan 1
2026 Sep 30 01:48:51 local6.warning IE520-stk-1 EXFX[664]: Thrash-limiting: Disabled learning on sa2 by 00f0.4d00.7718 on vlan 1
Traffic: loop windows 303 ms (1735 duplicates, 396 copies of one frame) and 81 ms (3010 duplicates).

=== Issue seen: no event at all, 39 s after the ring closed [38093-mrm-log-post-boot.txt] ===
2026 Sep 30 01:49:30 user.notice IE520-stk mrpd: PORT: Update ring port port1.0.13 with state to Forwarding   <=====
2026 Sep 30 01:49:30 user.notice IE520-stk mrpd: ffffffff-ffff-ffff-ffff-ffffffffffff: Ring-id[1]: Ring opened   <=====
2026 Sep 30 01:49:30 user.notice IE520-stk mrpd: FSM: ring_id=1 CHK_RC -> CHK_RO evt=MRP_ProtEvTestTimerExpired   <=====
2026 Sep 30 01:49:31 user.notice IE520-stk mrpd: PORT: Update ring port port1.0.13 with state to Blocked
2026 Sep 30 01:49:31 user.notice IE520-stk mrpd: ffffffff-ffff-ffff-ffff-ffffffffffff: Ring-id[1]: Ring closed

=== All ring closures ===
case    MRM               profile  closures that looped  loop window                                    attached
T38093  stack             200ms    3 out of 3            42-62 ms (restore), 303 + 81 ms (boot)         38093-fail.log, 38093-loop-windows.txt
T38098  stack             200ms    8 out of 8            31-62 ms                                       38098.log
T38097  standalone IE520  200ms    4 out of 4            26-40 ms                                       38097.log
T38099  stack             500ms    1 out of 8            29 ms (first restore after the profile change) 38099.log
{noformat}
```

### Core File Output
```
-
```

---
## Found On tab
- **Found Stage**: blank.
- **Affects Version/s**: `Mainline` (awplus_main-20260923-20).
- **Component/s**: best guess `MRP` if it is in the list, else `zFeature Not In This List`.
- **Show System**: DUT (stack) captured 2026-09-30 14:33 NZDT, minutes before the run (`bench-setup/captures/2026-09-30T013300Z/u2.show_system.txt`), then the MRC (`u3.show_system.txt`, same time):
```
{noformat}
System Status                                           Wed Sep 30 01:33:50 2026

Stack member 1

Board      ID   Bay     Board Name                        Rev   Serial number
--------------------------------------------------------------------------------
Base       717  Base    AT-IE520-28GSX                    X1-0  264A23061
--------------------------------------------------------------------------------
RAM: Total: 506724 kB Free: 273288 kB
Flash: 106.3MB Used: 41.0MB Available: 65.4MB
--------------------------------------------------------------------------------
Environment Status : Normal
Uptime             : 1 days 01:37:00
Bootloader version : 9.1.0


Stack member 3

Board      ID   Bay     Board Name                        Rev   Serial number
--------------------------------------------------------------------------------
Base       717  Base    AT-IE520-28GSX                    X1-0  264A23066
--------------------------------------------------------------------------------
RAM: Total: 506724 kB Free: 277524 kB
Flash: 106.3MB Used: 40.9MB Available: 65.4MB
--------------------------------------------------------------------------------
Environment Status : Normal
Uptime             : 0 days 00:15:52
Bootloader version : 9.1.0


Stack member 4

Board      ID   Bay     Board Name                        Rev   Serial number
--------------------------------------------------------------------------------
Base       717  Base    AT-IE520-28GSX                    X1-0  264A23052
--------------------------------------------------------------------------------
RAM: Total: 506724 kB Free: 257672 kB
Flash: 106.3MB Used: 41.0MB Available: 65.4MB
--------------------------------------------------------------------------------
Environment Status : Normal
Uptime             : 0 days 00:22:27
Bootloader version : pauld


Current software   : IE520-tb470.rel
Software version   : awplus_main-20260923-20
Build date         : Tue Sep 22 14:25:56 UTC 2026

Current boot config: flash:/tb470-bench.cfg (file exists)

System Name
 IE520-stk
{noformat}
MRC (IE520 standalone):
{noformat}
System Status                                           Wed Sep 30 01:33:49 2026

Stack member 1

Board      ID   Bay     Board Name                        Rev   Serial number
--------------------------------------------------------------------------------
Base       717  Base    AT-IE520-28GSX                    X1-0  264A23068
--------------------------------------------------------------------------------
RAM: Total: 506724 kB Free: 270540 kB
Flash: 106.3MB Used: 40.9MB Available: 65.5MB
--------------------------------------------------------------------------------
Environment Status : Normal
Uptime             : 1 days 01:37:02
Bootloader version : master-20260822-535


Current software   : IE520-tb470.rel
Software version   : awplus_main-20260923-20
Build date         : Tue Sep 22 14:25:56 UTC 2026

Current boot config: flash:/tb470-bench.cfg (file exists)

System Name
 IE520-sa
{noformat}
```

---
## Not ours
RCA, Mitigation (Must Fix process), Resolution Details, Verification, ISSU, RED, Decision, Risk, Release Notes.
