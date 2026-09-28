# IE520 campaign queue and issue log — tb470, from 2026-09-24 15:55 NZST

Terrence, 2026-09-24: *"continue as far as you can with executing the remaining test-cases. If
there is a non-test-case decision to be made, annotate it as an issue immediately. If that issue
is a blocker, make your recommended choice and further annotate that choice (and the options)
for later review. Collate the notes … with the other unsorted issues … then make a plan to solve
them AFTER you finish testing."* Then run `/wrap-dt`.

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Rules carried with the queue

- One `<case-id>.log` per case, holding only the latest run — and since 2026-09-28 its NAME states
  the outcome (`<id>.log` = PASS only; `-fail`, `-partial`, `-skip` otherwise): `STANDING-ORDERS.md`
  §2, which every queue inherits. Teardown is verified by diffing
  against a pre-test `show running-config` copy.
- Nothing is `write`n to startup-config unless a case requires it.
- Root changes on tb470, and device trust changes (keys, knownhosts), go through Terrence. If
  a case needs one, it is logged here as an issue and the case moves on.
- Stop on any `% ` CLI line. Gate each dependent step on proven state.

## Queue

| # | case | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | IPv6 mcast 38144 11724 11740 11722 11736 30681 20930 | ipv6-2026-09-22 | DONE — 7 PASS | torn down; diff clean vs pre |
| 2 | 38430 BGP4+ BFD fall-over | ipv6-2026-09-22 | DONE — PASS (I-14) | IE520-sa as peer (I-13); torn down, both diffs IDENTICAL |
| 3 | QoS 13549 / 13553 | qos-2026-09-22 | DONE — 2 PASS | tcpreplay line rate, tagged vlan50; finding I-17; torn down, both diffs IDENTICAL |
| 4 | 38435 (redrafted: stack-master failover with the master as auth server) | auth-2026-09-22 | DONE — PASS | design I-20; 2 member reloads; master back on member 3; diff IDENTICAL |
| 5 | ATMF 38474 | atmf-2026-09-23 | BLOCKED | needs tb470 root changes (route, `/tmp/atmfbk`, sshd) that only Terrence can make (I-2), and the knownhosts fetch (I-1); see I-21 |
| 6 | 28126–28129 rate halves ("ixia loss / line rate") | auth-2026-09-22 | DONE | 28129 → PASS; 28126/28127 step 1 rate PASS (step 2 FAIL stands); 28128 FAIL stands; diff IDENTICAL |
| 7 | 16452 / 16453 loop-protection | stp-2026-09-22 | DONE — 2 PASS | loop from sa2's legs in an empty vlan 60 (I-23); restored, x230 IDENTICAL, stack config identical |
| — | 38152 38153 EPSR 45788 45789 | ring / SFP cases | BLOCKED | SA↔x230 SFP+ link never comes up (I-3); needs hands |
| — | MRP | — | BLOCKED | the partners have no MRP CLI (I-7) |

## Issues (non-test-case decisions), in the order found

Status: OPEN (waiting on Terrence), CHOSEN (a blocker; my recommendation applied, for review),
NOTED (no decision needed now; carried into the plan).

- **I-1 38474: 4050 knownhosts fetch fails.** `crypto key pubkey-chain knownhosts ip 10.38.215.1`
  answers `% Cannot retrieve public key`. OPEN (asked 09-24). Case parked by Terrence.
- **I-2 tb470 host state for 38474.** The runtime route `10.10.10.0/27 via 10.38.215.10 dev eth1`
  and `/tmp/atmfbk` were lost in the reset. Re-adding them is root (Terrence pastes). The sshd
  drop-in and the 4050 userkey are still in place for 38474 and need reverting after it.
  OPEN.
- **I-3 SFP+ link SA port1.0.25 ↔ x230 port1.0.10 down.** Both optics show light (Rx ~0.6 mW)
  and both ends are admin up; forcing 10G does not help. Suspected dead SA cage. Fix: move the
  module to SA port1.0.26 (hands). Blocks the ring cases. OPEN.
- **I-4 28126/28127 step-2 interpretation.** Ruled FAIL by Terrence 09-24; kept here for the
  record. NOTED.
- **I-5 Raise as defects?** 6057: a full ARP table (cap ~2045) refuses new neighbours with
  ENOBUFS, and removing an IP secondary flushes the whole VLAN's neighbour table. 28128: guest
  VLAN forwarding. OPEN.
- **I-6 Cases with no steps in ck.db** (38435, 38148, 6005/38151/38487). They were interpreted
  from their titles. Do they need defining? OPEN.
- **I-7 AR4050S lists MRP as licensed but exposes no MRP CLI.** Worth raising? OPEN.
- **I-8 Case methods name commands that do not exist or are IPv4-only on the IE520.**
  - `show arp counter` and `show platform table ipv6route` do not exist.
  - `show platform table ipmulti` has no IPv6 section, yet 30681 names it for IPv6. On this
    platform `show hsl fib` shows the IPv6 hardware entries.

  Case-text fix? NOTED.
- **I-9 The 2026-09-22 38430 verdict was built on an incomplete attempt.** `service bfd` was
  never enabled on either end, and `show bfd session` is not an AW+ command (it is
  `show bfd peer`). Being re-run (queue #2). NOTED.
- **I-10 `bench_topology.py generate` mis-models tb470.** It treats the standalone SA as
  `stk_b` and uses a stale 09-15 scaffold. It is not used; bench-state.md is edited by hand.
  Tool fix? NOTED. **RESOLVED 2026-09-25:** `bench_topology.py` and `bench_setup.py` retired;
  the consolidated `bench_probe.py` (plan E-11) models the standalone correctly and read MATCH
  against the deployed `.setup` on its first live run.
- **I-11 Daemons that need a restart to go away.** `no service pim6` (09-24) and
  `no service ospf6` (09-22) both answer "Save the config and restart for this change to
  take effect". Nothing references the daemons, so the stack is left unrebooted. NOTED.
- **I-12 An IPv6 static mroute takes all its downstreams in ONE command.** A second line is
  refused with "already exists". Documentation? NOTED (20930.log).

- **I-13 38430 needs a BFD-capable BGP4+ peer (a BLOCKER, so CHOSEN).** Measured 2026-09-24:
  - The AR4050S has no `bfd` commands at all (`show bfd peer` → `% Invalid input`).
  - The x230 has neither BFD nor a BGP licence.
  - IE520-sa has `BGP4+` in its licence, and its BFD daemon is only service-gated
    (`% BFD protocol daemon is not running`).

  Options: (a) peer with IE520-sa over vlan1 via sa3; (b) record UNMEASURED again.
  **Chosen: (a)**, using temporary addresses `2001:db8:1::1` (stack) / `::2` (SA) on vlan1,
  torn down after the case. Caveat for review: the peer is the same platform and build as the
  DUT, so it is not an interop peer.

- **I-14 38430 step 2's premise contradicts BFD (a verdict call, so CHOSEN).**
  - The case's ACL "stops TCP traffic" and expects BFD to detect the neighbour as
    unreachable. BFD runs over UDP 3784, so it correctly stays up, and BGP ends on its hold
    timer (+114.5 s).
  - With BFD's UDP also denied, BFD goes down ("control detection time expired") and
    fall-over terminates BGP within ~2 s.

  Options: (a) PASS, graded on the DUT's behaviour, with the case text flagged for a fix;
  (b) FAIL as written (the 28126/28127 precedent); (c) UNMEASURED until the case is
  rewritten. **Chosen: (a).** Unlike 28126/28127, no DUT behaviour here departs from the
  protocol. Suggested case fix: "an access-list on the peer that drops all traffic from the
  DUT (including BFD UDP 3784/3785)".
- **I-15 Hardware-ACL rule ordering on the IE520.** A rule added later without a sequence
  number is appended AFTER an existing `permit any any`, so it never matches. Worth a CLI
  note or warning? NOTED.
- **I-16 No BGP or BFD state-change messages in `show log`** on the IE520: session drop,
  hold-timer expiry and BFD down are all silent. Expected? NOTED.

- **I-17 QoS queue assignment on the stack looks wrong (a possible defect; evidence in
  qos-2026-09-22/13549.log).** Measured 2026-09-24 with `show mls qos interface port3.0.13
  queue-counters`:
  - Untagged traffic that enters on a REMOTE member (sa3 on members 1/4, egress on member 3)
    is transmitted from **queue 0**, with QoS off or on. The same CoS-0 traffic entering on
    member 3 goes to **queue 2**, which is what `show mls qos maps cos-queue` says (0→2).
  - `mls qos cos 5` on port3.0.9 (`show mls qos interface` reads "Default CoS: 5", trust
    "Ports default priority") did NOT move that port's untagged traffic out of queue 2.

  Under strict priority, the first point means a remote member's traffic always loses to local
  traffic of the same CoS. TAGGED traffic follows the map from either member (13549 runs
  R0-RC), so this is specific to untagged/default-CoS handling. Raise? OPEN.
- **I-18 The IE520 has no interface `wrr-queue weight`.** WRR goes through
  `mls qos scheduler-set N wrr-queue group G weight W queues Q` plus `mls qos scheduler-set N`
  on the port, and `show mls qos scheduler-set 1` is `% Invalid input`. The 13553 case text
  (and the AW+ wiki's interface-command page) do not match this platform. Case-text fix?
  NOTED.
- **I-19 Terrence ruled 3116 skip (09-23).** Its 09-22 blocker ("harness peaks at ~26 Mbps")
  no longer holds: tcpreplay on tb470 sends ~983 Mbps per NIC. Re-open 3116? OPEN (not run;
  the ruling stands).

- **I-20 38435 test design (the case has no steps; the redraft is "stack-master failover with
  the master as auth server"), so CHOSEN.**
  - The only host-facing stack ports (port3.0.13 eth1, port3.0.9 eth3) are on member 3, and
    member 3 is the master. A master failover would take the supplicants' own ports down with
    it, so it could only show re-authentication, not continuity.
  - Options: (a) reload member 3 first so mastership moves to member 1 or 4, then
    authenticate eth1 (dot1x) and eth3 (auth-mac) on member 3's ports and reload the new
    master; (b) run it on sa3 through the SA (EAPOL does not cross the SA, so auth-mac only);
    (c) leave UNMEASURED.
  - **Chosen: (a).** It costs one extra member reload (flash boot, `show boot` checked first).
    After the case the master is whichever member won, not member 3 (rejoin never
    re-elects); bench-state is updated to match.

- **I-21 38474 cannot proceed unattended (a BLOCKER, so CHOSEN).** It needs root changes on
  tb470, which go through Terrence: the return route `10.10.10.0/27 via 10.38.215.10 dev eth1`
  and the backup directory `/tmp/atmfbk` (both lost in the reset). It also needs I-1 (the
  4050 cannot fetch tb470's host key) resolved. Options: (a) stop the queue here and leave
  38474 for Terrence's return; (b) work around the root route by having the AR4050S reach
  tb470 some other way (it has only vlan10 via sa1, so no). **Chosen: (a).** 38474's
  existing log (the parked attempt) is left as it is.

- **I-22 Rate halves of 28126–28129 on a CPU path (a safety choice, so CHOSEN).** With
  hardware forwarding off, the frames are CPU-forwarded. Offering ~1 Gbps to the master's
  CPU risks starving VCS keepalives; this stack has a history of "VCS duplicate master"
  reboots. Options: (a) line rate as an Ixia would; (b) a ramp of 1 → 5 → 20 → 100 Mbps
  that stops at the first rate losing >10%, with a stack-health gate after every burst;
  (c) skip. **Chosen: (b).** Hardware-forwarding-ON runs go at line rate (~983 Mbps).

- **I-23 16452/16453 do not need the SFP+ ring (test design, so CHOSEN).** The loop is two
  parallel links: sa2's legs (stack port1.0.2/1.0.9 ↔ x230 port1.0.3/1.0.4) taken out of both
  LAGs into an otherwise empty vlan 60, so a storm cannot reach vlan 1.
  - The 2026-09-22 16452 block ("port-disable not supported with fast blocking"; fast-block
    looked sticky) is handled with `no loop-protection loop-detect`, then
    `loop-protection loop-detect ldf-interval 1` WITHOUT fast-block. The baseline
    (`... fast-block`) is restored afterwards.
  - Options: (a) this; (b) wait for the SFP+ fix. **Chosen: (a).**
  - The bench-state hazard "don't un-bundle sa2 with RSTP off" is respected by the empty-VLAN
    containment and by keeping the loop open except while measuring.

- **I-24 4050 `port1.0.2` is recorded as access vlan 10, but that is INFERRED** (no pre-AMF
  capture; the port is shut). Verify when the 4050 is next touched. NOTED.
- **I-25 Stack member 3's USB stick still holds the `atmf/tb470/` backup tree from 38475.**
  Keep it as evidence or delete it? OPEN.
- **I-26 Superseded logs in older run directories.** `atmf-2026-09-21/38475.log` (UNMEASURED)
  sits beside the current `atmf-2026-09-23/38475.log` (PASS), against the one-log-per-case
  rule. Its README row now points at the current log; the old file was NOT deleted. Delete,
  or keep as history? OPEN.
- **I-27 `switch 2 provision ie520-28` is still in the stack's config.** Member 2 left to become
  IE520-sa, and its phantom port2.0.x range shows up in listings (e.g. every-port MLD
  static groups, 20930). Remove the provision line? OPEN.

## Plan (written 2026-09-24 ~17:00 NZST, after the queue finished)

**Where testing ended.** Every row is DONE or BLOCKED. 17 case results were produced or
changed today: 7 IPv6 multicast, 38430, 13549, 13553, 38435, the rate halves of 28126–28129,
16452 and 16453 (all PASS apart from the FAIL verdicts that stand), plus 38432 re-labelled
UNSUPPORTED under Terrence's 09-23 ruling. What remains needs hands, root, or a decision.

### A. Decisions for Terrence (nothing else can move these)

1. **Review the CHOSEN calls** (made so testing could continue):
   - **I-13:** the IE520-sa as the BFD peer.
   - **I-14:** 38430 graded PASS, not FAIL-as-written. This is the one most likely to be
     overturned, given the 28126/28127 precedent.
   - **I-20:** the 38435 design (two member reloads).
   - **I-22:** the CPU-path rate ramp capped at 100 Mbps.
   - **I-23:** the sa2 loop in an empty VLAN.

   Each lists its options, so any one can be flipped without re-running unless noted.
2. **Raise as defects?** In order of strength:
   - **I-17 (strongest):** untagged traffic from a remote stack member lands in queue 0,
     and a port's default CoS is ignored. Measured on egress counters; a clear
     strict-priority impact.
   - **I-5:** the 6057 ARP cap and whole-VLAN flush; 28128's IPv6 blocking with
     hw-forwarding off.
   - **28126/28127:** unknown unicast flooding between guest-VLAN supplicants.
   - **I-16:** no BGP/BFD state logging.
   - **I-15:** ACL rules appended after a permit.

   If yes, I draft each report from its log (evidence and repro steps are already there).
3. **Case-definition questions:** I-6 (no-steps cases). I-19: 3116 and 12067 were skipped
   because the harness lacked line rate; tcpreplay now gives ~983 Mbps per NIC, so reopen
   them?
4. **Housekeeping calls:** I-25 USB tree, I-26 superseded logs, I-27 `switch 2 provision`,
   I-7 MRP licence entry.

### B. Needs hands on the bench

5. **I-3:** move the SA's SFP+ module from `port1.0.25` to `port1.0.26` (the cage is suspect),
   and re-seat. Then, in one session:
   1. Verify the SA↔x230 link comes up.
   2. Run the remaining 38152/38153 steps (alternate path, portfast, BPDU filter, root guard)
      on the DUT–x230–SA ring.
   3. Run EPSR 45788/45789 if the SFP/SFP+ ports they need are free.

   Recipe: the 09-24 handover §7-A. RSTP must be re-disabled and the x230 `port1.0.10` shut
   again afterwards.

### C. Needs root on tb470 (Terrence pastes)

6. **38474 (I-1, I-2, I-21):**
   1. Terrence re-adds `ip route 10.10.10.0/27 via 10.38.215.10 dev eth1` and `/tmp/atmfbk`.
   2. Debug the 4050's `Cannot retrieve public key`: try the `rsa`/`ecdsa` keyword, or the
      4050's own debug output.
   3. Run 38474.
   4. Then revert the host items (handover §3 one-liner: the sshd drop-in, keys, route) and
      `crypto key destroy userkey manager rsa` on the 4050.

   If Terrence drops the case instead, do only step 4.

### D. Case-text / documentation fixes (for the suite owners; no bench time)

7. **Text corrections to send to the suite owners:**
   - I-8: commands that don't exist or are IPv4-only.
   - I-12: static-mroute downstream syntax.
   - I-14: 38430's ACL wording.
   - I-18: the IE520 WRR scheduler-set syntax; the case's interface command doesn't exist.
   - 13553: CoS set by tag, because port default CoS is ignored (I-17).
   - 38435: steps; today's redraft could become the definition.

   One consolidated list, drafted from the logs, for Terrence to forward.

### E. Repo and tooling

8. **I-10:** ~~fix or retire `bench_topology.py generate`'s stale 09-15 scaffold~~ **DONE
   2026-09-25** by item 11: both old scripts are deleted.
9. **I-11:** the pim6/ospf6/bfd daemons linger until the next stack reboot. The 38435 member
   reloads have since restarted members 3 and 4, but the daemon state was not re-read. Check
   `show running-config | include service` at the next orient.
10. **I-24:** read 4050 `port1.0.2`'s VLAN when next on the 4050 console.
11. **Consolidate the bench-state tooling into one script** (Terrence, 2026-09-25; replaces
    `bench_probe.py`, `bench_topology.py` and `bench_setup.py`, and supersedes item 8).
    **BUILT 2026-09-25, before the DLF test at Terrence's request:** `bench-setup/bench_probe.py`
    (the name is fixed by Test-cases' `ask-ck/functions/test-composer/bench_probe.md` pointer).
    First live run 10:55–10:57 NZST: 1 m 56 s, all six consoles read (x230 at 9600 included —
    the old baud defect is gone), `lldp run` switched on and off on the x230 only, **MATCH**
    against the deployed `.setup`. Static facts seeded in `tb470.static`. Memory:
    `bench-probe-one-tool`. Still open: whether to `apply` the generated (comment-free) `.setup`
    to the box — sections are identical, only the hand-written `###` header would go.

    The pipeline:
    1. **Capture.** A short, fixed list of read-only `show` commands per console: serialnumber,
       `show stack`, interface status, LLDP neighbours, the MAC table and `show running-config`.
       Save the raw output to disk so the parser can be re-run without the hardware.
    2. **Parse.** Offline, from the saved files only.
    3. **Generate.** A bench-state.md in `.setup` format.
    4. **Diff.** Compare it against `tb470.setup`.

    Target: about 10 s per IE520, the same cost as a `show run` config check.

    Decisions (Terrence, 2026-09-25):
    - **Static facts.** PDU outlets, the PDU's IP and anything else no `show` command can
      reveal are a one-time user entry, kept in a hand-declared static section. That loss is
      accepted; don't re-open it.
    - **LLDP.** Switch-to-switch cabling comes from LLDP, so the script first checks whether
      `lldp run` is on for each device. If it's off, the script turns it on for the capture
      and turns it off again at the end. Devices where it was already on are left as found.
    - **Direction.** The tool keeps both functions for now: diff-check, and optionally create
      the `.setup` from the measured file. In future only the diff-check will be used, with
      the `.setup` as the intended template.
    - **Drop the prose.** The generated bench-state.md holds only the measured state, with no
      history, "last test" notes or reasons for a port's state. ART tests don't use that
      information. With run-to-run variance, the last test's notes often conflict with the new
      test's config, so they mislead more than they help.
    - **Where durable bench knowledge goes instead.** Anything that matters beyond one run goes
      where the repo already keeps that kind of fact:
      - platform and tooling mechanics → the orient-dt skill
      - non-obvious cross-session lessons → memories
      - what a session did → its handover
    - **When building it:** sweep the current bench-state.md prose once and move anything
      durable to those homes. Update orient-dt and wrap-dt, which point at its "Current state —
      <date>" section.

**Order of work:** A first, because it is cheap and unblocks D and parts of E; then C if
Terrence is at the box (it is the only case left in the queue); then B when someone is
on site.
