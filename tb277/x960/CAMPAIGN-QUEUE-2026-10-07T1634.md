# Campaign queue — tb277 x960-56YSQ, 17 AWPTCM cases, from 2026-10-07 16:34 NZDT

The ask, verbatim (Test Engineer, 2026-10-07): *"Okay run these test cases"* followed by the case
list, then the titles. **"Device under test is x960-56YSQ. This is the device we are testing. The
other three devices are link partners."** (Clarified same day: just the two partners.)

**Case content is NOT from AWPTCM.** The Ask-CK / `ck.db` tree is not mounted in this session, so
the steps and expected results below are **drafted by Claude from the case titles alone** and were
approved by the Test Engineer before the run (option chosen: *"Titles only — I draft the steps"*).
Any verdict here is against these drafted steps, not against AWPTCM's text. If a case's real steps
differ, the verdict must be revisited.

Shape: ONE session (orient-dt §10 A, `/test-mode`): this session is the sentinel, `bench-runner`
subagents are the tester.

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-07 16:34 NZDT. These are the Test Engineer's answers, word for word:
Test Engineer: bidhanc@bidhanc-dl
Testbox: tb277 (named by the Test Engineer; no prior record of this box in the repo)
Consoles: u2,u3,u5 — "we will be using three devices for our setup"; "All console are ours to use"
PDU: 10.36.230.212 outlet A=1 (u2), outlet G=7 (u3); 10.36.230.35 outlet C=3 (u5)
Constraints: None
Durability: session is in tmux/screen (confirmed 2026-10-07)

Devices (measured, bench-setup/tb277/bench-state.md generated 2026-10-07T030931Z):
- **DUT — swi_c, /dev/u2, AT-x960-56YSQ, S/N A2WQS7004**, standalone member 1, 115200 baud,
  software `sin_x96056-20260921-9`, bootloader `benb` (a dev build), netboots (`Current boot
  image: Not set`, flash essentially empty).
- partner — swi_b, /dev/u3, AT-x960-28YSQ, S/N A10737A261700021, 9600 baud, same software,
  bootloader 8.24.0, boots `flash:/backup.rel`.
- partner — swi_a, /dev/u5, AT-x950 GEN2-52XSTQm, S/N A10713A262600012, 9600 baud,
  `awplus_main-20260920-12`, netboots.

Cabling (measured 2026-10-07, not declared):
```
tb eth2 ──── swi_c eth0   (management)
tb eth3 ──── swi_b eth0   (management)
tb eth4 ──── swi_c port1.0.48          vlan 1
swi_a port1.0.1 ──── port1.0.1 swi_b   vlan 1
swi_b port1.0.2 ──── port1.0.2 swi_c   vlan 100, both in static-channel-group 1 (sa1)
swi_c port1.0.4 / 1.0.8 / 1.0.40 ──── OFF-BENCH, far ends unidentified
swi_b port1.0.8                  ──── OFF-BENCH
```
Proof of the off-bench three: each was shut in turn (2026-10-07 16:21) and nothing on swi_a,
swi_b or any host NIC changed state. All restored and verified back to baseline.

**No platform file exists for x960 or x950** (`platforms/` holds only IE520.md). An expected
UNSUPPORTED cannot be read off a platform file here; each must be reasoned from the DUT itself.

## Rules carried with the queue

- Verdicts, the tester's working logs, the `RESULT` line, the results list and the final log
  template: **`logged-output.md`**. Final logs are made only by `/create-logs`, on request.
- `STANDING-ORDERS.md` applies in full. Constraints are "None", so the tester has full authority
  within the tests, including power-cycling the three units.
- Nothing is written to startup-config unless a case requires it.
- Teardown verified by diffing `show running-config` against the pre-case copy.
- Stop on any `% ` CLI line; gate each dependent step on proven state.
- AW+ routing daemons are service-gated: `service rip` / `service bfd` before configuring them,
  or they report "daemon is not running" (memory `awplus-service-gated-routing-daemons`).

## Known risk carried into the run

**Netboot vs the framework's post-failure power cycle.** The DUT (u2) and swi_a (u5) have empty
flash and netboot. `isc-dhcp-server` on tb277 has been **disabled since 17 June** (last lease
1 July), yet both booted ~2 October onto exactly the builds in `/tftproot`
(`x960-tb277.rel` = `sin_x96056-20260921-9`; `x950GEN2-tb277.rel` = `awplus_main-20260920-12`).
⇒ netboot does not depend on DHCP here; the bootloaders must hold static addresses. Inferred,
not directly read. `in.tftpd` runs without `-v`, so there are no transfer logs to close the gap.
The framework PDU-cycles every bound device after any FAIL/UNSUPPORTED/ERROR case
(STANDING-ORDERS §6), so **the first such cycle is the real confirmation — watch u2's console
through it.** If the DUT does not come back, park it at the boot menu and set the boot source by
hand; do not leave it looping.

## Campaign setup and restore (set ONCE before group 2, restored ONCE at the end)

Groups 2 and 3 need traffic to **transit the DUT** and be measured on the far side. No recabling
is required: swi_b is the far-end source and the testbox the receiver, with the DUT in between.

```
swi_b ──sa1(port1.0.2)──▶ [ DUT x960-56YSQ ] ──port1.0.48──▶ tb eth4
   source                      under test                    receiver
```

Blocking today: port1.0.48 is in vlan 1 and sa1 is in vlan 100, so no path exists. Setup:

1. DUT: `vlan database` → `vlan 210 state enable`; `interface port1.0.48` → `switchport access
   vlan 210`; `interface vlan210` → `ip address 10.38.22.66/27` (host eth4 is 10.38.22.65/27, so
   the testbox is directly connected and needs **no host route**).
2. DUT: `interface vlan100` → `ip address 192.168.100.1/24` (sa1 is already access vlan 100).
3. swi_b: `interface vlan100` → `ip address 192.168.100.2/24`; `ip route 10.38.22.64/27
   192.168.100.1`.
4. VLAN 210 is free on all three units (only 1 and 100 exist) — checked against the capture.
5. swi_a is not needed by any case as drafted; it stays as it is.

Restore: remove vlan 210, the two vlan interfaces, swi_b's route, and return port1.0.48 to
vlan 1. Verify by diff against the pre-campaign `show running-config` of each unit.

**Open — may need the Test Engineer (STANDING-ORDERS §4):** if any case turns out to need the
testbox to *originate* toward 192.168.100.0/24, that is a host route (`ip route add`), which is
root on the box and theirs, not the tester's. The setup above avoids it; T44378 is the one most
likely to reopen it (see its note).

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | T44967 T44968 T44969 T44973 T44974 | mirror-2026-10-07T1634 | PENDING APPROVAL | DUT-only, CLI + `show mirror`; no partner, no traffic, no campaign setup needed |
| 2 | T44979 T44986 T44988 T44989 T44990 T44991 T44992 | acl-2026-10-07T1634 | PENDING APPROVAL | needs the transit path above; T44990 also needs group 1's mirror config |
| 3 | T43870 T47201 T44181 T44378 T44182 | ipv4-2026-10-07T1634 | PENDING APPROVAL | L3 services; T44378 and T44182 have open verification questions (I-2, I-3) |
| — | T44987 | — | NOT TESTED | in the Test Engineer's first list, no title in the second; **dropped at their request** 2026-10-07 |

## Drafted case steps — PENDING TEST ENGINEER APPROVAL

Exact CLI forms are to be confirmed against the DUT at triage (`<command> ?` through a driver that
does NOT append CR — memory `never-send-cli-help-through-a-cr-driver`). The x960 is a different
platform from the IE520 these methods were developed on; where a form differs, the tester records
the DUT's actual syntax in the working log and uses it.

### Group 1 — port mirroring CLI (DUT only)

Uses two unused DUT ports: **port1.0.10 = mirror source**, **port1.0.11 = mirror destination**.
Neither is cabled, so nothing else on the bench is disturbed.

- **T44967 — CLI show mirror interface direction set to transmit.** Configure the mirror with
  direction `transmit`; `show mirror` and `show mirror interface port1.0.11`.
  *Expected:* the mirror is listed with direction `transmit` and the correct source/destination.
- **T44968 — … direction set to receive.** As above with `receive`. *Expected:* direction reads
  `receive`.
- **T44969 — … direction set to both.** As above with `both`. *Expected:* direction reads `both`.
- **T44973 — CLI Remove mirror interface.** With a mirror configured, remove it
  (`no mirror interface …`). *Expected:* `show mirror` no longer lists it; the destination port
  returns to normal switching; no residue in `show running-config`.
- **T44974 — Mirror set to interface none.** Set the mirror source to `none`.
  *Expected:* accepted, and `show mirror` reports no active mirror — distinct from T44973's
  removal in that the mirror destination config may persist. If the DUT does not offer a `none`
  form, that is UNSUPPORTED with the help output as evidence, not a FAIL.

### Group 2 — hardware ACLs (needs the campaign setup)

Traffic: testbox `ping`/`tcpreplay` on eth4 toward 10.38.22.66 or 192.168.100.2, and swi_b
`ping` toward 10.38.22.65, so both directions through the DUT are available.

- **T44979 — ACL: Named Hardware on port - Proto.** `access-list hardware <name>` with a rule
  matching an IP **protocol** (e.g. `deny proto 1 any any` for ICMP); apply to port1.0.48 with
  `access-group`. *Expected:* matching traffic is dropped and non-matching passes; the ACL's
  counters increment. Re-run with `permit` to show the inverse.
- **T44986 — Deny/permit statements for standard IPv4 access list.** Numbered standard list
  (1–99): add permit and deny entries for specific sources and `any`; `show access-list`.
  *Expected:* entries accepted, listed in the order entered, and the implicit behaviour matches
  AW+ documentation. If the case is purely CLI this is a config/verify case; if traffic is
  needed, apply it where a standard list is valid on this platform and show the effect.
- **T44988 — ACL: Hardware MAC 4000 range - applied to ports.** Numbered hardware MAC ACL in the
  **4000–4699** range matching a source MAC; apply to port1.0.48. Source the frames from the
  testbox with a known MAC. *Expected:* the 4000-range list is accepted, applies to the port, and
  matching frames are permitted/denied as written with counters incrementing.
- **T44989 — ACL: Named Hardware on port send-to-cpu IP.** Named hardware ACL with
  `send-to-cpu ip <src> <dst>` on port1.0.48. *Expected:* matching traffic is delivered to the
  DUT's CPU and is **not** forwarded onward (swi_b stops seeing it). Observe the DUT's CPU queue
  counters. *Hint, to verify not assume:* on IE520/Marvell, send-to-cpu lands on queue 6 and
  copy-to-cpu on queue 0, exactly one packet on the wire per match (memory
  `ie520-is-marvell-cpu-queues`). The x960 may differ — read the platform's own counters.
- **T44990 — ACL: Named Hardware on port copy-to-mirror IP.** Requires a mirror destination; use
  **port1.0.48 as the mirror destination** and swi_b as the traffic source into sa1, so the
  testbox receives the mirrored copies on eth4 (`tcpdump`). Named hardware ACL with
  `copy-to-mirror ip …` on the sa1 ingress. *Expected:* matched traffic appears at the mirror
  destination **and** is still forwarded normally.
- **T44991 — ACL: Named Hardware on port copy-to-cpu IP.** As T44989 but `copy-to-cpu`.
  *Expected:* matched traffic reaches the CPU **and** is still forwarded (the difference from
  send-to-cpu is the whole point of the pair; run them back to back and contrast).
- **T44992 — ACL: Named Hardware on static LAG - IP.** Apply a named hardware ACL to the
  aggregator **sa1** rather than a physical port. *Expected:* accepted on the aggregator and
  effective on its member ports. **Caveat:** sa1 has two configured members, port1.0.2 (in-bench,
  to swi_b) and port1.0.4 (off-bench). Only one member carries testable traffic, so
  "effective on every member" cannot be shown — likely PARTIAL unless the case only requires the
  aggregator to accept and apply the ACL. Recorded as I-1.

### Group 3 — IPv4 services

- **T43870 — (46) IPv4_SNMP - SNMPv3.** Configure an SNMPv3 view, group and user with auth and
  privacy on the DUT; query from the testbox over eth4 (`snmpget`/`snmpwalk -v3 -l authPriv`).
  *Expected:* the authPriv query succeeds and returns the expected OID; a query with wrong
  credentials or no privacy fails. Confirm net-snmp client tools exist on tb277 first.
- **T47201 — (48) IPv4_BFD - With RIP v1/v2.** `service rip` and `service bfd` on **both** the DUT
  and swi_b first. Bring up RIP over vlan 100 between them, confirm the route exchange, then
  enable BFD for the RIP neighbour. *Expected:* `show bfd peer` reports the session **Up**, RIP
  learns routes over it, and when the link is failed the RIP route is withdrawn on BFD's
  timescale rather than RIP's own timers. Run v1 and v2 as the case title asks.
- **T44181 — (51) IPv4 - Ping Polling.** Configure a ping-poll on the DUT targeting the testbox
  (10.38.22.65) or swi_b (192.168.100.2); `active`. *Expected:* `show ping-poll` reaches state
  **Up**; when the target stops answering (shut the relevant port, or stop swi_b responding) the
  poll transitions to **Down** within its configured timers, and back to Up on recovery. Prefer
  swi_b as the target so the failure can be induced with a port shut rather than a host firewall
  change.
- **T44378 — (52) IPv4 - UDP Broadcast Helper.** `ip forward-protocol udp <port>` plus
  `ip helper-address <server>` on the DUT's receiving VLAN interface; broadcast UDP from the
  testbox on vlan 210. *Expected:* the DUT relays the broadcast as unicast to the helper address
  on vlan 100. **Open (I-2):** the far side is swi_b, a switch, which cannot simply capture UDP.
  Candidate verifications, to be settled at triage: a hardware ACL with copy-to-cpu on swi_b
  matching the relayed UDP, or the DUT's own forwarding counters. If no honest verification
  exists on this bench, the case is UNMEASURED with the reason, never a guessed PASS.
- **T44182 — (53) IPv4 - Directed Broadcast Forwarding.** **Baseline the feature OFF first**
  (memory `campaign-measurement-discipline`): with `no ip directed-broadcast` on vlan 210, have
  swi_b send to 10.38.22.95 (the directed broadcast of the testbox subnet) and confirm the
  testbox receives **nothing**. Then enable `ip directed-broadcast` and repeat.
  *Expected:* off = not forwarded; on = the testbox's `tcpdump` on eth4 sees the forwarded
  broadcast. **Open (I-3):** confirm swi_b can source to an arbitrary directed-broadcast address;
  if not, source from the testbox instead and receive on swi_b, which reopens I-2's problem.

## Results

| case | verdict | reason | graded by | working log |
| --- | --- | --- | --- | --- |
| T44987 | NOT TESTED | no title supplied; dropped by the Test Engineer 2026-10-07 | Test Engineer | — |

## Issues

Status: OPEN (waiting on the Test Engineer), CHOSEN (a blocker; recommendation applied for
review), NOTED (no decision needed now).

- **I-1 T44992 static-LAG ACL cannot be shown across members.** sa1's second member (port1.0.4)
  runs off-bench, so only port1.0.2 carries testable traffic. NOTED — may force PARTIAL.
- **I-2 T44378 has no clean far-end receiver.** The helper target is swi_b, a switch. OPEN —
  settle at triage; UNMEASURED is the honest outcome if nothing works.
- **I-3 T44182 source selection.** Needs swi_b to source to a directed-broadcast address. OPEN.
- **I-4 Case steps are drafted, not authoritative.** Every verdict in this campaign is against
  Claude's reconstruction from the case titles, because `ck.db` is not reachable from this
  session. NOTED — stated at the top of this file and to be repeated in every final log.
- **I-5 Netboot confirmation.** See "Known risk" above. NOTED.
