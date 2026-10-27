# CR draft — T28128 → (CR key to come)

Source: [IE520/auth-2026-09-22/28128.log](../IE520/auth-2026-09-22/28128.log), with controls
[28126.log](../IE520/auth-2026-09-22/28126.log) (IPv4, same ports and state) and
[28129.log](../IE520/auth-2026-09-22/28129.log) (IPv6, hw-forwarding on). Run 2026-09-24, tb470
(device clock 2026-09-23 ~21:40–22:05 UTC; rate half ~16:40 NZST). Build: awplus_main-20260923-20.
Structure and rules: [TEMPLATE.md](TEMPLATE.md). **RCA not filled.**

Spec read 2026-10-27 (wiki via tb470): [Suppress_unicast_flooding_on_Guest_VLAN_TFS](https://wiki.atlnz.lc/awpwiki/index.php/Suppress_unicast_flooding_on_Guest_VLAN_TFS)
(ER-3353, the feature these cases are filed under) and its follow-on
[Support_auth_guest-vlan_forward_option_on_all_AW+_switches_TFS](https://wiki.atlnz.lc/awpwiki/index.php/Support_auth_guest-vlan_forward_option_on_all_AW%2B_switches_TFS)
(ER-3855, turns it on for all AW+ switches). The IE520 Software TPS lists "Suppress unicast
flooding on Guest VLAN (MRS-728)".

## Decisions before filing
1. **One CR, not three. 28126/28127 are not drafted, and I recommend no CR for them.**
   - **What they failed on.** Step 2 ("completely blocked") was read as *unknown unicast between
     supplicants must not flood*, from the ck.db folder name "ER-3353: Suppress unicast flooding on
     Guest VLAN". You ruled that reading FAIL on 09-24 (CAMPAIGN-QUEUE-2026-09-24 I-4).
   - **What ER-3353 actually is.** Its TFS, despite the name, is the `auth guest-vlan hw-forwarding`
     feature: guest-VLAN traffic in silicon instead of the CPU, for throughput. Nothing in it says
     unknown unicast between supplicants is blocked. The docs team called it "a corner case" and
     documented only the command, with no Feature Overview Guide.
   - **What step 2 more likely means.** S3353.1.6: with an IPv4 address on the guest VLAN, traffic
     to the VLAN's own address or to a destination outside its subnet is dropped. That is "completely
     blocked", and it was never tested: 28126/28127 ran with no IPv4 address on vlan200.
   - So the flooding we measured contradicts no spec I can find. The FAIL grade is your ruling and
     I have not touched the logs. Re-grade or re-run step 2 against S3353.1.6?
2. **What "expected" rests on.** The TFS fixes the rule for the *hardware* path only. S3353.1.7 says
   "For IPv6 traffic there are no restrictions", and the DUT honours it (28129: all three variants
   forward). It says nothing about the *CPU* path, the default. On that path the expectation comes
   from:
   - the case itself, which expects all three variants to be CPU-forwarded;
   - IPv4 parity. S3353.1.6: "If there is no IPv4 address on the interface then these restrictions
     do not apply". IPv4 on the CPU path with no address forwarded 500/500 (28126).
   - **Variant 1 (no address) is the strong half:** it is blocked although neither IPv4 rule would
     block it. **Variant 3 (different subnet) is weaker:** it matches the IPv4 out-of-subnet rule, so
     a developer could call it intended for the CPU path. The draft states both and lets them say.
3. **Priority.** Drafted as `4 - Minor`. By S it is a Sev 3 loss of function, because the default
   guest VLAN carries no IPv6 between supplicants. But S's Minor clause covers "a Sev 3 with a
   workaround", and there are two: `auth guest-vlan hw-forwarding`, or an IPv6 address on the guest
   VLAN in the clients' prefix. `3 - Major` if you weigh it as a default-config IPv6 outage.
4. **New platform, and how old the evidence is.** IE520 is a new platform. M counts that only if the
   issue is shown NOT to occur on an existing platform. tb470's x230v2 is the platform ER-3353 was
   built for, so the same three variants could be run there. The evidence also has gaps:
   - The build is 5 weeks old.
   - The run's console captures and frame captures were on tb470's tmpfs, and are gone.
   - The counts below come from the run log.

   A re-run is not possible now: the IE520 stack has been taken down at tb470 (the units are on
   tb101). Terrence decided 2026-10-27 not to re-run, so the CR goes with the 09-24 counts. The
   x230v2 comparison (could run on tb470) was dropped with it.
5. **Not measured:** whether IPv6 Neighbour Discovery between the two hosts works in the guest VLAN.
   The test frames were addressed by MAC, so ND was not involved.
6. **Duplicate search** (G §2.1), not done yet. Terms: `guest vlan IPv6`, `guest-vlan hw-forwarding`,
   `guest vlan CPU forward IPv6`, `ER-3353`.

## Before creating — duplicate check
Search http://bugsearch.atlnz.lc/ and Jira `project = CR AND text ~ "guest vlan" AND text ~ "IPv6"`.
Hits: (to fill).

---
## Main tab

### Summary
```
[IE520-28GSX] IPv6 traffic between guest VLAN supplicants is dropped when guest VLAN hw-forwarding is disabled (default) unless the guest VLAN has an IPv6 address in the clients' subnet
```

### Priority
`4 - Minor` (suggested; see Decisions 3). S: Sev 3 "loss of function in one area" with a simple
workaround → Minor.

### Basic Analysis
```
# Repeatable: Y
#- frequency: Run 1 (50 pps, 600 frames per variant): 2 out of 2 affected variants dropped every frame (no guest VLAN address 0/600, different-subnet address 0/600) / Run 2 (1 Mbps, 413 frames per variant): 2 out of 2 (0/413, 0/413) / Total: 4 out of 4 (attached 28128.log). Controls in the same runs: same-subnet address 600/600 (28128.log), IPv4 with no address 600/600 (attached 28126.log), hw-forwarding enabled 600/600 in all three variants (attached 28129.log).
# Degradation or regression keyword set: N
#- Regression/Degradation process followed: N - Analysis not performed as I believe this CR will not be a must fix because simple workarounds exist (enable guest VLAN hw-forwarding, or put an IPv6 address in the clients' prefix on the guest VLAN); also IE520 is a new platform with no GA release.
#- All builds tested that contain this issue: awplus_main-20260923-20
#- All builds tested that do not contain this issue: none
# Binary search performed: N - Analysis not performed as I believe this CR will not be a must fix (see above).
#- All mainline builds tested that contain this issue: awplus_main-20260923-20
#- All mainline builds tested that do not contain this issue: none
#- Changelog link:
# Blocks Testing keyword set: N
#- number of tests blocked: 0
# New feature/platform: Y - IE520-28GSX (new platform). Not yet compared against an existing platform.
```

### Keywords
None.

### Issue Description
```
h4. +Description:+
Two hosts on two guest VLAN ports of an IE520 stack (no supplicant authenticated, so both ports are untagged members of guest VLAN 200), with guest VLAN hardware forwarding at its default (disabled), so traffic between them is CPU-forwarded.

IPv6 traffic between the two hosts (2001:db8:200::65 to 2001:db8:200::1, both in 2001:db8:200::/64) is dropped completely (AWPTCM-T28128, attached 28128.log):
* guest VLAN with no IPv6 address: 0 of 600 frames delivered, and the CPU (sdma) counters do not rise - the frames are dropped, not CPU-forwarded;
* guest VLAN with an IPv6 address in a different subnet (2001:db8:300::10/64): 0 of 600 delivered, same.
Only with an address in the hosts' own subnet (2001:db8:200::10/64) is IPv6 CPU-forwarded (600/600, sdma counters rise by the frames sent).

The same ports in the same state forward:
* IPv4 between the hosts with no guest VLAN address: 600/600 (CPU-forwarded; AWPTCM-T28126, attached 28126.log);
* IPv6 in all three variants once "auth guest-vlan hw-forwarding" is configured: 600/600, and at line rate with no loss (AWPTCM-T28129, attached 28129.log).

Expected: IPv6 between supplicants is forwarded (via the CPU) with no guest VLAN address and with an address in another subnet, as the test case (AWPTCM-T28128) expects for all three variants. The hardware path follows S3353.1.7 of the Suppress_unicast_flooding_on_Guest_VLAN TFS ("For IPv6 traffic there are no restrictions"), and IPv4 with no address is not restricted (S3353.1.6); the CPU path applies a restriction to IPv6 that neither rule describes.

Network impact: guest VLAN clients cannot exchange any IPv6 traffic in the default configuration. No other traffic was affected; the stack stayed in Normal operation.

h4. +Consequences:+
All IPv6 between guest VLAN supplicants is lost for as long as the configuration stays; it does not recover by itself. It is restored by enabling "auth guest-vlan hw-forwarding" on the ports, or by giving the guest VLAN an IPv6 address in the clients' prefix.

h4. +Reproduction Method:+
# Connect two hosts to two ports of the DUT (here port3.0.9 and port3.0.13, both on the master).
# Create VLAN 200. Configure "aaa authentication dot1x default group radius" with no RADIUS server reachable, so no supplicant can authenticate.
# On both ports configure "dot1x port-control auto" and "auth guest-vlan 200". Leave guest VLAN hw-forwarding at its default (disabled).
# Check {{show vlan 200}} lists both ports untagged and {{show auth supplicant}} shows no supplicants.
# Give the hosts 2001:db8:200::65/64 and 2001:db8:200::1/64. Send one frame from each host so the DUT learns both MACs. Send IPv6 UDP from the first host to the second (addressed to its MAC). Nothing is delivered.
# Send IPv4 UDP the same way (192.168.200.65 to 192.168.200.1). It is delivered.
# Configure {{ipv6 address 2001:db8:200::10/64}} on vlan200 and repeat the IPv6 send. It is delivered, and {{show platform counter sdma}} on the member rises by about the frames sent.
# Change the vlan200 address to {{2001:db8:300::10/64}} and repeat. Nothing is delivered.
# Remove the vlan200 address and configure "auth guest-vlan hw-forwarding" on both ports. Repeat the IPv6 send: it is delivered.
```

### Network Configuration
```
DUT (IE520-28GSX VCStack, members 1/3/4, master 3) : Traffic host (testbox)
port3.0.9  : eth3 (guest VLAN 200 untagged; sender, 2001:db8:200::65 / 192.168.200.65)
port3.0.13 : eth1 (guest VLAN 200 untagged; receiver, 2001:db8:200::1 / 192.168.200.1)
```

### Device Configuration
```
! added to the stack's baseline config (attached as IE520-stk-running-config.txt)
vlan database
 vlan 200 state enable
!
aaa authentication dot1x default group radius
! (no RADIUS server reachable: no supplicant authenticates, both ports stay in guest VLAN 200)
!
interface port3.0.9,port3.0.13
 switchport mode access
 dot1x port-control auto
 auth guest-vlan 200
! guest VLAN hw-forwarding left at default (disabled)
!
! variant 2 (forwards):     interface vlan200 / ipv6 address 2001:db8:200::10/64
! variant 3 (dropped):      interface vlan200 / ipv6 address 2001:db8:300::10/64
! variant 1 (dropped):      no address on vlan200
! control (all forward):    interface port3.0.9,port3.0.13 / auth guest-vlan hw-forwarding
```

### Linked Issues
None known.

### Attachment
- `28128.log`: the run (three variants, CPU counters, rate half).
- `28129.log`: the same three variants with hw-forwarding enabled (all forward).
- `28126.log`: IPv4 on the same ports and in the same state (forwards with no address).
- `IE520-stk-running-config.txt`: the stack's baseline config, same build
  (`bench-setup/captures/2026-09-24T225534Z/u2.show_running-config.txt`).
- No pcaps: the run's captures were on tb470's tmpfs and are gone (Decisions 4).

---
## Debug Output tab

### Debug Output
Counts from the run log (frames delivered to the receiving host, and stack member 3's
`show platform counter sdma` TX packet delta over the send). Verbatim device output for this run
did not survive (Decisions 4).
```
{noformat}
Issue NOT seen - guest VLAN hw-forwarding enabled, IPv6, 600 frames per variant (500 to the receiver's MAC + 100 to an unlearned MAC) [28129.log]:
  vlan200 IPv6 address              delivered    member 3 sdma (rx, tx)
  none                              600/600      (913, 1094)
  2001:db8:200::10/64 (same)        600/600      (828, 1005)
  2001:db8:300::10/64 (different)   599/600      (923, 1122)
  idle 14 s, for reference                       (793, 944)
  line rate 10 s, each variant      812001-812501 of the same, 100.0%

Issue NOT seen - hw-forwarding disabled, IPv4, no vlan200 address [28126.log]:
  192.168.200.65 -> .1              600/600      sdma rx/tx +621/+625 over the hw-forwarding-on run (CPU-forwarded)

Issue seen - hw-forwarding disabled (default), IPv6 [28128.log]:
  vlan200 IPv6 address              delivered    member 3 sdma tx
  none                              0/600        1116                <=====
  2001:db8:200::10/64 (same)        600/600      1695
  2001:db8:300::10/64 (different)   0/600        1130                <=====
  1 Mbps, 413 frames, no address        0/413                        <=====
  1 Mbps, 413 frames, different         0/413                        <=====
  (variant 2's tx is ~580 above variants 1 and 3 = the 600 frames CPU-forwarded;
   variants 1 and 3 add nothing: the frames are dropped, not forwarded)
{noformat}
```

### Core File Output
`-`

---
## Found On tab
- **Found Stage**: blank.
- **Affects Version/s**: `Mainline` (awplus_main-20260923-20).
- **Component/s**: best guess `Port Authentication` + `IPv6`.
- **Show System**: captured 2026-09-24 22:56 UTC by the bench probe, the same build and stack
  (members 1/3/4) as the run (`bench-setup/captures/2026-09-24T225534Z/u2.show_system.txt`):
```
{noformat}
System Status                                           Thu Sep 24 22:56:57 2026

Stack member 1

Board      ID   Bay     Board Name                        Rev   Serial number
--------------------------------------------------------------------------------
Base       717  Base    AT-IE520-28GSX                    X1-0  264A23061
--------------------------------------------------------------------------------
RAM: Total: 506724 kB Free: 281012 kB
Flash: 106.3MB Used: 40.9MB Available: 65.4MB
--------------------------------------------------------------------------------
Environment Status : Normal
Uptime             : 0 days 00:21:21
Bootloader version : 9.1.0


Stack member 3

Board      ID   Bay     Board Name                        Rev   Serial number
--------------------------------------------------------------------------------
Base       717  Base    AT-IE520-28GSX                    X1-0  264A23066
--------------------------------------------------------------------------------
RAM: Total: 506724 kB Free: 256376 kB
Flash: 106.3MB Used: 40.9MB Available: 65.4MB
--------------------------------------------------------------------------------
Environment Status : Normal
Uptime             : 0 days 00:21:19
Bootloader version : 9.1.0


Stack member 4

Board      ID   Bay     Board Name                        Rev   Serial number
--------------------------------------------------------------------------------
Base       717  Base    AT-IE520-28GSX                    X1-0  264A23052
--------------------------------------------------------------------------------
RAM: Total: 506724 kB Free: 279648 kB
Flash: 106.3MB Used: 40.9MB Available: 65.4MB
--------------------------------------------------------------------------------
Environment Status : Normal
Uptime             : 0 days 00:21:19
Bootloader version : pauld


Current software   : IE520-tb470.rel
Software version   : awplus_main-20260923-20
Build date         : Tue Sep 22 14:25:56 UTC 2026

Current boot config: flash:/tb470-bench.cfg (file exists)

System Name
 IE520-stk
System Contact

System Location
{noformat}
```

---
## Not ours
RCA (company AI), Mitigation, Resolution Details, Verification, ISSU, RED *, Decision, Risk,
Release Notes.
