# Guest VLAN forwarding (ER-3353) on the x230v2 — 2026-10-27, tb470

**What this is.** A measurement for the guest-VLAN CR (`CR-gen/T28128-CR-DRAFT.md`, other session).
It repeats the T28128 / T28129 three IPv6 variants and the T28126 IPv4 control on the
x230v2. It also tests the S3353.1.6 IPv4 rules in both modes. Terrence asked for it in
this session ("run it", 2026-10-27 ~14:30). It is not a `/create-logs` case log: there is no
queue and no case verdict. The IE520 runs (`IE520/auth-2026-09-22/2812[6-9].log`) are not
changed.

## Device

```
Base       706  Base    AT-x230-28GS V2                   A-0   A10783G262900002
Bootloader version : 6.2.40
Current software   : x230v2_28GS-awplus_main-20261019-75.rel
Software version   : awplus_main-20261019-75
Build date         : Mon Oct 19 08:39:33 UTC 2026
```
Full `show system`: `device/prerun.txt`. Licences: Base, ACCESS, FULL.

## Setup

- tb470 eth1 (00:f0:4d:00:77:16) -> x230 port1.0.2 = sender.
- tb470 eth2 (00:f0:4d:00:77:17) -> x230 port1.0.10 = receiver. A tcpdump runs on eth2 for every send.
- Both ports are on the same unit. The x230 is not stacked.
- Guest VLAN config (from `show running-config`, `device/off-v6a-pre.txt`):
  ```
  aaa authentication dot1x default group radius      (no RADIUS server: nobody authenticates)
  interface port1.0.2,port1.0.10
   switchport
   switchport mode access
   dot1x port-control auto
   dot1x control-direction both
   auth guest-vlan 200
  ```
  `show vlan 200`: `port1.0.2(u) port1.0.10(u)`. `show auth supplicant`: both ports dot1x, "No supplicants".
  For the hw-forwarding-ON runs, `auth guest-vlan hw-forwarding` is added on both ports.
- Traffic per variant (`tools/vsend.py`, about 220 frames per second):
  1. 1 frame eth2 -> eth1 and 1 frame eth1 -> eth2, so the switch learns both MACs.
  2. 500 frames eth1 -> eth2's MAC ("known").
  3. 100 frames eth1 -> 02:00:00:00:99:99, a MAC nobody owns ("unknown").
  - Every frame carries a marker, and `tools/vcount.py` counts the markers in the eth2 pcap.
  - IPv6: 2001:db8:200::65 -> 2001:db8:200::1, UDP. IPv4: 192.168.200.65 -> the destination in the table, UDP.
- CPU path: `show platform counter sdma` ("RX packet counter" / "TX packet counter") is read
  just before and just after each send. Background traffic over one window is about +0 to +4 RX
  and +15 to +19 TX (see the baseline rows).

## Results

Delivered = frames that arrived on eth2, out of the number sent.

| mode | variant | vlan200 address | destination | known | unknown | CPU RX | CPU TX | meaning |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline (no dot1x, plain vlan200) | IPv6 | none | 2001:db8:200::1 | 500/500 | 100/100 | +0 | +15 | hardware forwards |
| baseline | IPv4 | none | 192.168.200.1 | 500/500 | 100/100 | +2 | +15 | hardware forwards |
| **hw-fwd OFF (default)** | **IPv6 a** | none | 2001:db8:200::1 | **0/500** | **0/100** | +604 | +16 | **the CPU receives every frame and drops it** |
| hw-fwd OFF | IPv6 b | 2001:db8:200::10/64 (same subnet) | 2001:db8:200::1 | 500/500 | 100/100 | +602 | +621 | the CPU forwards |
| **hw-fwd OFF** | **IPv6 c** | 2001:db8:300::10/64 (other subnet) | 2001:db8:200::1 | **0/500** | **0/100** | +604 | +15 | **the CPU receives and drops** |
| hw-fwd OFF | IPv4 | none | 192.168.200.1 | 500/500 | 100/100 | +604 | +621 | the CPU forwards (no restriction) |
| hw-fwd OFF | IPv4 | 192.168.200.10/24 | 192.168.200.1 (in subnet) | 500/500 | 100/100 | +602 | +619 | the CPU forwards |
| hw-fwd OFF | IPv4 | 192.168.200.10/24 | 192.168.200.10 (the VLAN's IP) | 0/500 | 0/100 | +606 | +19 | dropped, as S3353.1.6 says |
| hw-fwd OFF | IPv4 | 192.168.200.10/24 | 192.168.201.1 (outside) | 0/500 | 0/100 | +604 | +18 | dropped, as S3353.1.6 says |
| hw-fwd ON | IPv6 a | none | 2001:db8:200::1 | 500/500 | 100/100 | +4 | +17 | hardware forwards |
| hw-fwd ON | IPv6 b | 2001:db8:200::10/64 | 2001:db8:200::1 | 500/500 | 100/100 | +0 | +17 | hardware forwards |
| hw-fwd ON | IPv6 c | 2001:db8:300::10/64 | 2001:db8:200::1 | 500/500 | 100/100 | +4 | +18 | hardware forwards |
| hw-fwd ON | IPv4 | none | 192.168.200.1 | 500/500 | 100/100 | +2 | +19 | hardware forwards |
| hw-fwd ON | IPv4 | 192.168.200.10/24 | 192.168.200.1 (in subnet) | 500/500 | 100/100 | +2 | +16 | hardware forwards |
| hw-fwd ON | IPv4 | 192.168.200.10/24 | 192.168.200.10 (the VLAN's IP) | 0/500 | 0/100 | +2 | +18 | dropped, as S3353.1.6 says |
| hw-fwd ON | IPv4 | 192.168.200.10/24 | 192.168.201.1 (outside) | 0/500 | 0/100 | +4 | +17 | dropped, as S3353.1.6 says |

Each row's raw output: `device/<mode>-<variant>-pre.txt` (the config commands, `show vlan 200`,
`show auth supplicant`, `show running-config`, sdma before), `device/<mode>-<variant>-post.txt`
(sdma after), `traffic/<mode>-<variant>-vcount.txt` (counts per marker), `traffic/...-send.txt`
(send times), `pcap/<mode>-<variant>-eth2.pcap`. The file names use `off-v6a`, `off-v4n` (no
address), `off-v4s` (in subnet), `off-v4o` (the VLAN's own IP), `off-v4x` (outside), and the
same with `on-` and `base-`. Every command with its prompt: `device/console-u1-transcript.log`.

## What the numbers show

1. **The x230v2 behaves the same as the IE520 did on 2026-09-24.** With hw-forwarding OFF,
   IPv6 between two guest-VLAN supplicants is delivered only when vlan200 has an IPv6
   address in the traffic's subnet. With no address, or an address in another subnet,
   nothing is delivered. ER-3353 was developed on the x230, so this is not specific to the
   IE520 platform.
2. **The CPU receives the frames and drops them itself.** In every OFF variant, CPU RX rises by
   about 604, which is the 602 frames sent. CPU TX rises by about 620 only when the frames are
   delivered. (The 2026-09-24 IE520 log compared TX only.)
3. **IPv4 in the CPU path follows S3353.1.6 exactly.** With no address there is no restriction.
   With an address, traffic in the subnet is forwarded, and traffic to the VLAN's own IP or
   outside the subnet is dropped.
4. **IPv6 in the CPU path follows the IPv4-with-an-address rule, but without the
   "no address = no restrictions" part.** The spec says "For IPv6 traffic there are no
   restrictions" (S3353.1.7). The hardware path does that (all three ON variants delivered).
   The CPU path does not.
5. **The TFS says the hardware path is meant to do the same as the CPU path, only faster:**
   "Currently traffic on a Guest VLAN is forwarded by the CPU. ... This enhancement is to allow
   the user to configure the Guest VLAN traffic to instead be forwarded by silicon, ensuring high
   throughput." and "AUTHD will tell HSL to ... add some ACLs to ensure that only the allowed
   traffic is forwarded" (wiki `Suppress_unicast_flooding_on_Guest_VLAN_TFS`, read 2026-10-27).
   So the default (CPU) and hw-forwarding modes should give the same delivered/dropped result.
   For IPv6 they do not.
6. **S3353.1.6 (the reading asked for, for T28126/T28127 step 2):** both modes
   drop traffic to the VLAN's own IP (with dst MAC = the other supplicant) and traffic outside the
   subnet. Both modes forward traffic in the subnet, and traffic when the VLAN has no IPv4 address.
   All of this agrees with the spec.
7. **Unknown unicast between supplicants is flooded to the other guest-VLAN port** in every
   variant that forwards, in both modes (100/100). The TFS does not say it should be blocked.

## Observed, not explained

- In on-v6a and on-v6c, the single eth1 -> eth2 MAC-learning frame sent before the known stream
  was not delivered, although the 500 frames after it were (`traffic/on-v6a-vcount.txt`: markers
  K 500, L2 1, U 100, no L1). In the other forwarding variants it was delivered. This does not
  change any result row.
- The restore's `no aaa authentication dot1x default` logged
  `user.err x230-28GSv2 IMI[656]: AAA: failed to update method-list default (unknown type 3).`
  (2026 Oct 27 01:58:56 UTC; `device/health-u1-before-after.txt`). The console showed no `% `
  error, and the `aaa authentication dot1x` line is gone from the running-config.

## Health and restore

- Health before 14:40 and after 15:00 NZDT (`device/health-u1-before-after.txt`): no new reboot (newest stays
  2026-10-26 22:11:30, Expected), exception log None -> None, 0 new kernel/crash lines,
  CPU 0% -> 1%. Verdict CLEAN.
- Restore (`device/restore.txt`): `no auth guest-vlan hw-forwarding`, `no auth guest-vlan`,
  `no dot1x port-control` on both ports; port1.0.2 back to `switchport access vlan 1000`;
  `no aaa authentication dot1x default`; `no vlan 200`. The running-config after equals the one before
  (134 lines each, `diff` with the header comment lines removed: identical). Nothing was written to
  startup-config. No reload, no power cycle.
- The x230 console was logged out at the end. tb470 host: no change (scapy and tcpdump only).
