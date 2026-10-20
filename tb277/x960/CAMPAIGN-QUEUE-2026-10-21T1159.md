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

## 🔴 Thirteen of fourteen cases have ONE authored step; one has NONE

From `ck.db` (`tools/ckcase.py`, run on the box) at 2026-10-21 11:5x:

| case | title | authored steps |
| --- | --- | --- |
| T33379 | (230) Management - Telnet Client (IPv4) | 1 |
| T33380 | (231) Management - SSH Server (IPv4) | 1 |
| T33381 | (232) Management - SSH Client (IPv4) | 1 |
| T33384 | (235) EnhancedOperationManagement - Auto boot from external media | 1 |
| T33386 | (237) EnhancedOperationManagement - Management ACL | 1 |
| T33387 | (238) EnhancedOperationManagement - Management Stacking | 1 |
| T33388 | (239) EnhancedOperationManagement - Hardware Watchdog | 1 |
| T33389 | (240) EnhancedOperationManagement - Software Watchdog | 1 |
| T47192 | (243) Config_File - A dynamic configuration while operating (Change, Delete) | 1 |
| T44296 | (259) LLDP - LLDP | **0** |
| T33398 | (260) LLDP - LLDP-Med | 1 |
| T33399 | (262) NTP - IPv4 NTP Server | 1 |
| T33400 | (263) NTP - IPv4 NTP Client | 1 |
| T44298 | (264) NTP - IPv6 NTP Server | 1 |

As in the 2026-10-20 campaign, each test is **designed from the TFS, the TPS row and the DUT's
own CLI surface**, and each log says plainly that no authored step text beyond the single line
exists. A case id that resolves to nothing is widened to the measurable surface, and the log
says no authority exists.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| A | T33379 Telnet Client; T33380 SSH Server; T33381 SSH Client | `access-2026-10-21T1159` | PENDING | Remote access, IPv4. The DUT is both server and client, so swi_b is the far end. Telnet is disabled on the DUT (`no service telnet` is in its baseline) — enabling it is part of T33379's own setup |
| B | T33386 Management ACL; T47192 dynamic config change/delete | `mgmt-2026-10-21T1159` | PENDING | No reboot expected. T33386 must prove the ACL BLOCKS as well as permits — a permit-only result is the absence-of-evidence trap |
| C | T44296 LLDP; T33398 LLDP-Med | `lldp-2026-10-21T1159` | PENDING | 🔴 Needs the STP question (above) settled first: LLDP is a counted traffic case. The probe switches `lldp run` on itself, so record the pre-case state before touching it |
| D | T33399 IPv4 NTP Server; T33400 IPv4 NTP Client; T44298 IPv6 NTP Server | `ntp-2026-10-21T1159` | PENDING | DUT as server with a partner as client, and the reverse. IPv6 server needs IPv6 addressing on the transit VLAN |
| E | T33384 Auto boot from external media; T33387 Management Stacking; T33388 Hardware Watchdog; T33389 Software Watchdog | `eom-2026-10-21T1159` | PENDING | 🔴 **Reboot-heavy — run LAST.** All four may reset a unit. **swi_a is off-limits for reboots** (above), so any limb needing a swi_a reset is BLOCKED, not attempted. T33384 needs external media (USB/SD) — if the DUT has none, that is UNSUPPORTED with the proof, not a bench request |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

