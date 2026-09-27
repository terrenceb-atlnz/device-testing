# T5437 IP-OPTIONS INVESTIGATION — CLOSED 2026-09-28

**RESOLVED: FAIL (candidate product defect).** Re-run 2026-09-28 with a valid unicast source MAC,
on BOTH the bridged and a genuinely routed path (scratch vlan90 SVI, dst = stack router MAC),
RR and LSRR options wire-verified, ~3200 pps: `dos ipoptions` armed but counted 0 and never shut
the port. The 'needs L3 routed path' theory below is DISPROVEN. Arming works on a master-member
port (the old port1.0.1 'Cannot update hardware filter' was member-1-specific). Full result and
method: ../5437.log. CONTROL 2026-09-28: eth3 recabled to the x230 (a platform that HAS the
feature) — it detected the same stimulus (Attacks detected 1, err-disable); the AR4050S build has
no `dos` feature at all. Confirmed IE520-specific defect. The notes below are the historical
investigation, kept for provenance.

---

# T5437 IP-OPTIONS INVESTIGATION — BOOKMARKED 2026-09-04 (paused, not finished)

Status: **PAUSED mid-investigation.** One earlier conclusion was CORRECTED; the core
question is still open and currently blocked. Read this before resuming.

## The question
Does `dos ipoptions` (AWPTCM T5437) actually detect/err-disable on the tb470 IE520, and if
option packets are dropped, WHERE and is it an AW+ issue?

## ⚠️ CORRECTION — an earlier finding here was WRONG
An initial conclusion ("the IE520 unconditionally drops ALL IP-options packets; it's AW+-wide")
was an **artifact of the test harness**, not device behaviour. Every crafted packet used source
MAC `01:00:01:00:00:01` — the multicast bit (0x01 first octet) makes it an ILLEGAL source MAC
that both devices drop regardless of L3 content. Inherited from `dos_campaign.py`'s attack
builders (`b_ipoptions`, `b_pod` use it). **Any future DoS crafting must use a valid unicast
source MAC** (tb470 eth3 = `00:f0:4d:00:77:18`, eth2 = `00:f0:4d:00:77:17`).

## What is TRUE (valid source MAC — see valid-mac-retest.log)
- Both the **IE520 (switch)** and the **AR4050S (router)** PROCESS most IP options — they reply
  to router-alert / timestamp / record-route / nop-padding option pings to their own SVI.
- Both DROP only **LSRR (source-route)** — the standard, expected security default (`no ip
  source-route` equivalent). This is NORMAL, shared across the two AW+ platforms, NOT a defect
  and NOT IE520-specific.
- The IE520 FORWARDS (routes) router-alert / record-route / nop-padding option packets to the
  x230; drops timestamp and lsrr on the forwarding path (corrected-t5437.log — but note arming
  had failed in that run, see below).

## STILL OPEN + BLOCKED
Does `dos ipoptions` itself COUNT / err-disable a forwardable option packet? NOT ANSWERED.
Blocker: arming `dos ipoptions` on **port1.0.1 now fails**:
  `% Failed to attach DoS settings to port1.0.1. Cannot update hardware filter` (arm-verify.log)
- NOT global exhaustion: classifier table `0/1536` used (hwfilter-diag.log).
- `dos ipoptions` ARMS FINE on port2.0.2 (member 2). Failure is **port1.0.1 / member 1-specific**
  — member 1 (S/N 264A23066) is the flagged SUSPECT-HARDWARE unit.
- It armed successfully on port1.0.1 on the FIRST run today (5437-routed.log), so this state
  DEVELOPED since — possibly the traffic floods, possibly the member. Likely clears on an IE520
  reboot (NOT done — see hazard).

## BENCH STATE LEFT IN PLACE (all running-config only; a reload reverts; NO reboots done)
- IE520: `vlan10`(10.0.10.1/24)+`vlan20`(10.0.20.1/24) SVIs; `port1.0.1`→access vlan10;
  `port2.0.9`→access vlan20. Router MAC (both SVIs) = `0000.cd37.0d6f`.
- AR4050S: `vlan30`(10.0.30.1/24) SVI; `port1.0.1`→access vlan30. SVI MAC `0000.cd40.0394`.
- x230: still on baseline vlan1 10.38.215.71/27 (never re-addressed in this phase).
- tb470: eth3 += 10.0.10.2/24 (+route 10.0.20.0/24 via 10.0.10.1); eth2 += 10.0.30.2/24.
- 🔴 **eth2 IS UNPLUGGED FROM THE IE520 TFTP-BOOT PATH** (moved to AR4050S port1.0.1).
  **DO NOT REBOOT/POWER-CYCLE THE IE520 until eth2 is back on the TFTP cable** — a member that
  reboots cannot netboot and will drop offline. Unexpected reboots happen here unprompted.

## RESTORE POINTS (exact baselines captured)
baseline-ie520.json / baseline-4050.json / baseline-x230.json — all were pure default
(vlan1 only; IE520 .66, 4050 .70, x230 .71; target ports plain access/vlan1).
Revert = put moved ports back to `switchport access vlan 1`, delete vlan10/20/30 SVIs+vlans,
`ip addr del` the two host secondaries + the host route. Running-config only, no reboot.

## TO RESUME
1. Move eth2 back to the IE520 TFTP-boot connection FIRST.
2. Then an IE520 reboot is safe and would likely clear the port1.0.1 hw-filter attach failure.
3. To close the open question: arm `dos ipoptions` on a WORKING ingress port, fire forwardable
   option packets (router-alert/RR/nop) with a VALID source MAC as TRANSIT traffic, read
   `show dos interface <port>` Attacks-detected + port state.
4. DOS-METHOD.md + the `ie520-dos-test-method` memory still say "ipoptions needs L3 routed path"
   — that is DISPROVEN but NOT yet corrected (picture still incomplete). Correct once closed.

## Evidence files (this dir)
baseline-*.json, apply.log, apply-4050.log, routed-path-proof.txt, 5437-routed.log,
wire-*.txt, discover.log, cli-help.log, optiontypes.log, 4050-optiontest.log,
valid-mac-retest.log, corrected-t5437.log, counter-check.log, arm-verify.log, hwfilter-diag.log
