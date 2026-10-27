# CR draft — T8770 → (CR key to come)

Source: [IE520/ipv6-bgp-2026-09-29/8770-fail.log](../IE520/ipv6-bgp-2026-09-29/8770-fail.log) and
[evidence/8770/](../IE520/ipv6-bgp-2026-09-29/evidence/8770/) (run 2026-09-30 17:39–18:05 NZDT, tb470).
Build: awplus_main-20260923-20. Structure and rules: [TEMPLATE.md](TEMPLATE.md). **RCA not filled.**

## Decisions before filing
1. **What this CR claims.** The case FAILed on two counts, and only one is a provable defect:
   - **Drafted below:** IPv6 neighbours beyond the hardware table are still learned in software,
     so traffic to them is lost and the table churns. This holds whatever the limit is. IPv4 on
     the same build behaves correctly: the ARP table refuses new entries at its cap (T6057).
   - **Not drafted: capacity (~1.9K measured vs the case's "approximately 5000").** The IE520
     Software TPS limits table has NO IPv6-neighbour row. Its "ARP / IPv6 neighbours" group lists
     only ARP (dynamic: required 4,000, actual **2,044** in red) and static ARP. The ART LID
     page is a stub. So there is no spec to fail against; this is a question for the TPS owner,
     not a CR. Should we ask them, or add a line to this CR?
2. **Two side findings**, not in this draft:
   - **Neighbour Advertisements dropped on the CPU path at modest rates.** At 300 pps ~50 % of
     answered destinations never became neighbours. At 50 pps, 58 of 1000 were solicited 3 times,
     answered 3 times, and still not learned. This could be CPU rate limiting by design. Own CR,
     or a question for a developer first?
   - **193 learned neighbours with no hardware row and no "Table full"**, with 1098 learned (below
     capacity). The CLI doesn't show their ND state, so this is not graded. Leave out?
3. **Priority**: drafted as `4 - Minor`. By S it is a Sev 3 loss of function (IPv6 forwarding to
   some neighbours), but only past ~1.9K IPv6 neighbours on one switch, which S's Minor clause
   covers ("would not occur on normal users' network environment"). If the intended limit is
   nearer the 4,000 that the TPS requires for ARP, `3 - Major`.
4. **New feature/platform `Y`**: same caveat as T12589. Not compared on an existing platform.
5. **Duplicate search**: yours (bugsearch.atlnz.lc).

## Before creating — duplicate check
Search terms: `Unable to add NH Route entry`, `IPv6 neighbor table full`, `ipv6 neighbour hardware`,
`EXFX Table full`. Hits: _(to fill)_

---
## Main tab

### Summary
```
[IE520-28GSX] IPv6 neighbours are learned but not programmed in hardware, and traffic to them is lost, when the hardware neighbour table is full
```

### Priority
`4 - Minor` (see Decisions 3).

### Basic Analysis
```
# Repeatable: Y
#- frequency: 3 out of 3 reads taken with more than ~1.9K neighbours learned (learned/hardware: 2632/1904, 2055/1855, 3030/1567; attached 8770-fail.log)
# Degradation or regression keyword set: N
#- Regression/Degradation process followed: N - Analysis not performed as I believe this CR will not be a must fix because it only occurs beyond ~1.9K IPv6 neighbours on one switch; also IE520 is a new platform with no GA release.
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
Found by AWPTCM-T8770 "IPv6 Neighbors - in silicon" on a 3-member IE520-28GSX VCStack, awplus_main-20260923-20 (full run attached as 8770-fail.log).

The DUT learns IPv6 neighbours by Neighbour Discovery and programs each as a /128 entry in the hardware route table on every stack member. Traffic to them is forwarded at line rate. This works up to about 1.9K neighbours (most hardware /128 rows seen: 1904 per member).

*Expected:* when the hardware table is full, a new neighbour is either not admitted, or admitted and still forwarded. IPv4 on the same build refuses: the ARP table stops at ~2045 entries, sends no further ARP requests, and existing entries keep working (T6057; attached 6057.log).
*Actual:* the DUT keeps admitting IPv6 neighbours it cannot program. Each failure logs, on every member:
{{EXFX: Unable to add NH Route entry nh=<addr>/128 mac=<mac> vid:3971 port=port3.0.13. Table full}}
With routed traffic to 5000 destinations, {{show ipv6 neighbors}} listed 3030 neighbours and {{show platform table ipv6}} held 1567 /128 rows per member (both outputs attached as 8770-tables-5000-destinations.txt). 3718 "Table full" messages covered 1893 distinct addresses (attached as 8770-table-full-log.txt). Only 40.2 % of the line-rate stream was delivered (37-45 % per second throughout, never converging). In the last 2 s, frames reached 3661 different neighbours: the forwarded set churns instead of staying fixed.

The table also churns while it fills. Past ~2.1K neighbours, adding destinations evicted existing entries (one batch of 1000 new destinations kept only 1260 of the previous 1934 neighbours), and the DUT re-solicited old entries at a high rate (9344 NS in that batch).

Network impact: traffic to the neighbours that do not fit in hardware is lost, with only a log warning. Because entries are evicted and re-learned, which neighbours lose traffic keeps changing, rather than a stable set working and the rest being refused.

h4. +Consequences:+
Lose traffic: while more IPv6 neighbours are active than the hardware table holds (~1.9K), a varying share of traffic to them is dropped (60 % at 5000 destinations). Neighbour churn adds sustained ND load on the CPU. It recovers when the number of active neighbours falls back under the hardware limit. No reboot is needed.

h4. +Reproduction Method:+
Topology and configuration as in Network Configuration and Device Configuration.
# On the DUT: VLAN 3971 on port3.0.13 with {{ipv6 address 2001:db8:8770:1::1/64}}, and {{ipv6 forwarding}}.
# On the host on port3.0.13, answer every Neighbour Solicitation for 2001:db8:8770:1::/64 with a solicited NA (S=1, O=1), each target with its own MAC. The DUT only learns neighbours it resolves itself.
# From another routed port, send IPv6 traffic to the DUT's router MAC, destined to 2001:db8:8770:1::1:1 onwards. With 10 destinations: {{show ipv6 neighbors}} and {{show platform table ipv6}} match (10/10 on every member). Correct.
# Raise the number of destinations past ~2000 (here 5000, at line rate). {{show ipv6 neighbors}} now lists more neighbours than {{show platform table ipv6}} holds; {{show log}} shows "Unable to add NH Route entry ... Table full"; only part of the traffic is delivered.
```

### Network Configuration
```
DUT (IE520-28GSX VCStack, members 1/3/4, master 3) : Traffic host (testbox)
port3.0.13 : eth1 (vlan3971 access; emulated IPv6 neighbours 2001:db8:8770:1::1:<n>, MAC 02:87:70:<n>)

DUT : IE520-28GSX standalone (traffic source path, vlan1)
sa3 = port1.0.13 + port4.0.9 : sa3 = port1.0.13 + port1.0.9

IE520 standalone port1.0.2 : Traffic host eth2 (vlan1; IPv6 traffic source 2001:db8:8770:ff::2, sent to the DUT's router MAC)
```

### Device Configuration
```
DUT (stack), added to the bench baseline config (attached as IE520-stk-baseline-running-config.txt):
{noformat}
vlan database
 vlan 3971 name ck8770
interface port3.0.13
 switchport access vlan 3971
interface vlan3971
 ipv6 address 2001:db8:8770:1::1/64
ipv6 forwarding
{noformat}
The standalone IE520 was not configured by this case (it only bridges the source traffic in vlan1).
```

### Linked Issues
None known (pending the duplicate search).

### Attachment
- `8770-fail.log` — `IE520/ipv6-bgp-2026-09-29/8770-fail.log`: the full run (fill batches, both traffic runs, teardown)
- `8770-tables-5000-destinations.txt` — `evidence/8770/8770-st5000-tables.out.gz` (gunzipped): `show ipv6 neighbors` (3030 rows) and `show platform table ipv6` (1567 /128 rows per member) after the 5000-destination run
- `8770-table-full-log.txt` — `evidence/8770/8770-s3-tablefull.out.gz` (gunzipped): all 3718 "Table full" messages
- `6057.log` — `IE520/switching-2026-09-22/6057.log`: the IPv4 contrast on the same build (ARP table caps at 2045 and refuses new neighbours; existing entries keep working)
- `IE520-stk-baseline-running-config.txt` — `bench-setup/captures/2026-09-30T043141Z/u2.show_running-config.txt`

Missing per G: no tech-support from the run. The NS/NA pcap of fill batch 3 (`p/nd-k3.pcap`) was on tb470's tmpfs and is gone.

---
## Debug Output tab

### Debug Output
```
{noformat}
=== Issue NOT seen: 10 neighbours (17:40) [8770-fail.log] ===
IE520-stk#show ipv6 neighbors
IPv6 Address                            MAC Address    Interface          Port       Type
2001:db8:8770:1::1:4                    0287.7001.0004 vlan3971           port3.0.13  dynamic
2001:db8:8770:1::1:8                    0287.7001.0008 vlan3971           port3.0.13  dynamic
... (10 rows: ::1:1 to ::1:a)
IE520-stk#show platform table ipv6
Stack member 1:
RE-Idx               IP address/prefLen    Route-Entry   EnCap Dev Port Tr VID
0                                ::/  0 *  trap to cpu  *  -    -   -    -  -
2                 2001:db8:8770:1::/ 64 *  trap to cpu  *  -    -   -    -  -
5              2001:db8:8770:1::1:1/128 0287.7001.0001     LL   2   13   -  3971
6              2001:db8:8770:1::1:2/128 0287.7001.0002     LL   2   13   -  3971
... (10 /128 rows: ::1:1 to ::1:a; identical on members 3 and 4)
2                            fe80::/ 64 *  trap to cpu  *  -    -   -    -  -
-> 10 learned, 10 in hardware on every member.

Traffic to 2000 destinations, 1514 B, 30 s at 984 Mbps: last 8 s delivered 96.5-99.2 % per second;
1998 of 2000 neighbours received frames in the last 2 s.

=== Issue seen: traffic to 5000 destinations, 1514 B, 60 s (17:55-17:56) [traffic: 8770-fail.log; tables: 8770-tables-5000-destinations.txt; log: 8770-table-full-log.txt] ===
tcpreplay: 4810001 packets sent in 60.05 s, 970.07 Mbps, 0 failed
delivered to the neighbours' port: 1933476 packets (40.2 %)        <=====
per second: 37-45 % throughout, never converging                    <=====
distinct neighbours receiving frames in the last 2 s: 3661          <===== forwarded set churns

IE520-stk#show ipv6 neighbors
-> 3030 rows in 2001:db8:8770:1::/64                                 <=====
IE520-stk#show platform table ipv6
-> 1567 /128 rows on member 1, 1567 on member 3, 1567 on member 4    <===== 1463 learned neighbours not in hardware

IE520-stk#show log | include Table full
2026 Sep 30 04:54:02 local6.warning IE520-stk EXFX[717]: Unable to add NH Route entry nh=2001:db8:8770:1::1:584/128 mac=0287.7001.0584 vid:3971 port=port3.0.13. Table full   <=====
2026 Sep 30 04:54:02 local6.warning IE520-stk-4 EXFX[681]: Unable to add NH Route entry nh=2001:db8:8770:1::1:584/128 mac=0287.7001.0584 vid:3971 port=port3.0.13. Table full
...
-> 3718 messages (all three members), 1893 distinct addresses; first at 04:54:02 UTC.

=== Fill: 1000 new destinations per batch, neighbours read 5 s after each [8770-fail.log] ===
batch  destinations  neighbours  hw /128 rows (per member)
  1        1000          505         505
  2        2000         1010        1010
  3        3000         1934           -
  4        4000         2140           -     <===== kept only 1260 of batch 3's 1934 (eviction); 9344 NS sent
  5        5000         2150           -
  6        6000         1984           -
  7        7000         2352           -
  8        8000         2632        1904     <===== learned > hardware

=== Contrast: IPv4 on the same build (T6057, 2026-09-24) [6057.log] ===
ARP table stops at ~2045 entries; past it the DUT sends no ARP request and a ping to a new neighbour
fails with "sendmsg: No buffer space available"; existing entries keep working.
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
- **Component/s**: best guess `IPv6` + the hardware-table component if there is one (e.g. `EXFX` / `Switch table`); else `IPv6` alone.
- **Show System**: captured 2026-09-30 17:32 NZDT, 7 minutes before the run (`bench-setup/captures/2026-09-30T043141Z/u2.show_system.txt`):
```
{noformat}
System Status                                           Wed Sep 30 04:32:28 2026

Stack member 1

Board      ID   Bay     Board Name                        Rev   Serial number
--------------------------------------------------------------------------------
Base       717  Base    AT-IE520-28GSX                    X1-0  264A23061
--------------------------------------------------------------------------------
RAM: Total: 506724 kB Free: 279648 kB
Flash: 106.3MB Used: 41.0MB Available: 65.4MB
--------------------------------------------------------------------------------
Environment Status : Normal
Uptime             : 0 days 00:15:36
Bootloader version : 9.1.0


Stack member 3

Board      ID   Bay     Board Name                        Rev   Serial number
--------------------------------------------------------------------------------
Base       717  Base    AT-IE520-28GSX                    X1-0  264A23066
--------------------------------------------------------------------------------
RAM: Total: 506724 kB Free: 258932 kB
Flash: 106.3MB Used: 40.9MB Available: 65.4MB
--------------------------------------------------------------------------------
Environment Status : Normal
Uptime             : 0 days 00:15:37
Bootloader version : 9.1.0


Stack member 4

Board      ID   Bay     Board Name                        Rev   Serial number
--------------------------------------------------------------------------------
Base       717  Base    AT-IE520-28GSX                    X1-0  264A23052
--------------------------------------------------------------------------------
RAM: Total: 506724 kB Free: 280876 kB
Flash: 106.3MB Used: 41.0MB Available: 65.3MB
--------------------------------------------------------------------------------
Environment Status : Normal
Uptime             : 0 days 00:15:34
Bootloader version : pauld


Current software   : IE520-tb470.rel
Software version   : awplus_main-20260923-20
Build date         : Tue Sep 22 14:25:56 UTC 2026

Current boot config: flash:/tb470-bench.cfg (file exists)

System Name
 IE520-stk
{noformat}
```

---
## Not ours
RCA, Mitigation (Must Fix process), Resolution Details, Verification, ISSU, RED, Decision, Risk, Release Notes.
