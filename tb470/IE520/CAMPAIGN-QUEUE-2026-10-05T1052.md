# Campaign queue — tb470 IE520, T27887 supplementary re-investigation, from 2026-10-05 10:52 NZDT

Terrence, 2026-10-05, after the 10:31 help probes re-confirmed that the global VLAN-based QinQ
command `vlan-stacking vlan <inner> outer-vlan <outer>` is absent on the IE520 (and, as a new
finding, on the x230 control too):
*"Yes, i think the switchport vlan ones should be tried for sure. is that actually Q-in-Q if it
works"* → *"use 2. and then start test mode"* (2 = observe through the x230, not the SA).

The ask: exercise the two IE520 commands that have never been configured or put under traffic:
- **(A)** `switchport vlan translation vlan <wire> vlan <vid> outer-vlan <outer>`: the combined
  translation + double-tag entry. IE520 help offers both argument orders (`… vlan <vid> outer-vlan
  <outer>` and `… outer-vlan <outer> vlan <vid>`).
- **(B)** `switchport vlan translation default outer-vlan <vid>`: outer VLAN added to tagged frames
  that match no translation entry.

Each forward (customer → provider) and reverse. The question each stage answers: does the customer
tag survive inside the outer tag (true Q-in-Q), or is it dropped (a repeat of O-2 from the 09-30 run)?

**Supplementary evidence only.** T27887's case is VLAN-based QinQ (global mapping, "cannot be
applied per interface", T27895/T27989); these are per-port entries. Terrence's framing: the verdict
stays UNSUPPORTED unless he decides otherwise. Prior run, topology and O-2:
[../../IE520/vlan-2026-09-29/27887-unsupported.log](../../IE520/vlan-2026-09-29/27887-unsupported.log).

Shape: ONE session (orient-dt §10 A, `/test-mode`): this session is the sentinel, `bench-runner`
subagents are the tester.

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-05 10:52 NZDT. These are the Test Engineer's answers, word for word:
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470 (this host's default and the last test bench run, IE520/SESSION-HANDOVER-2026-10-05.md)
Consoles: u0,u2,u4,u5
PDU: No PDU / do not power-cycle
Constraints: Don't power-cycle the SA (u3/outlet 8 is not to be power-cycled; observe via the x230 path (option 2); u1 never touched; sentinel stands down 17:30 today)

Notes from the session (sentinel):
- u1 (AR4050S) is held by the Test Engineer's `minicom --wrap -D /dev/u1 -c off` (PID 527573): never open it.
- u3 (IE520-sa, swi_b) is unresponsive since before 2026-10-05 08:21 (handover 2026-10-05) and is NOT
  in this session's consoles. Its links to the stack (sa3: stack port1.0.13, port4.0.9; SX port4.0.26)
  are down. Do not use the SA path.
- Precheck 2026-10-05 10:30: u0, u2, u3, u4, u5 free; FOUND only the u1 minicom above.
- No PDU this session: nothing is power-cycled, by the tester or the framework.

Decisions 2026-10-05 ~11:15 NZDT (after triage found the bench per the 10:28 handover update, commit
7f0c6ff: old build `tomahawk_ie520-20260825-42` stacked as u5 = ID 1 master, u4 = ID 2; u2 standalone
on `awplus_main-20260923-20`; no stack-to-x230 link; eth3 on stack port1.0.9, eth1 on port1.0.10):
- Path: "Direct at eth3" — no recable; customer = eth1 on stack port1.0.10, provider = eth3 on stack port1.0.9.
  This REPLACES the x230 observation path (option 2), which no longer exists.
- Build: first answer "u2 standalone (new build)"; that conflicts with "Direct at eth3" (no tb470 NIC
  reaches u2). Asked again with the bench changes it would need → **"Fall back: old-build stack"**.
  So the DUT is the old-build stack; O-2 (measured on 20260923-20 on 09-30) is re-measured on this build,
  and a new-build comparison stays open.

## Rules carried with the queue

- Verdicts, the working log, the `RESULT` line, the results list and the final log:
  [logged-output.md](../../logged-output.md). The final log is made ONLY by `/create-logs`, on the
  Test Engineer's request.
- `STANDING-ORDERS.md` applies, tightened by the constraints above (no power cycling at all).
- Nothing is `write`n to startup-config. Teardown is verified by diffing `show running-config`
  against the pre-case copy on every device touched.
- Stop on any `% ` CLI line. Gate each dependent step on proven state.
- Drive consoles through `tools/` (console.py-based) with transcripts at tb470
  `/tmp/<campaign>/console-<uN>.log`, so the sentinel's normal mode sees them.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | T27887 supplementary: (A) combined translation + outer-vlan entry, (B) `default outer-vlan`, forward + reverse each | vlan-2026-10-05T1052 | RUNNING (from ~11:25, tester) | DUT = old-build stack via u5; customer = port1.0.10 (eth1), provider = port1.0.9 (eth3), direct capture; stages S0, S1 control, SA1/SA1p, SA2, SB/SBp (triage hand-back). Triage probe MISMATCH by design (bench deliberately off-template, do NOT apply), bench-state 04f92a7 |

## Group setup and restore — vlan-2026-10-05T1052

Written by the tester (bench-runner), 2026-10-05 ~11:25 NZDT, before the first stage. Option D,
Test Engineer's answer relayed 11:19: DUT = the OLD-build stack (u5 = ID 1 Active Master, u4 = ID 2,
`tomahawk_ie520-20260825-42`), driven from **u5 only**. u0, u2, u1 and u3 are not touched. Nothing is
power-cycled and nothing is written to startup-config. Scratch: tb470 `/tmp/ckvlan1052/` (tools copy,
transcripts `console-u5.log`, pcaps).

**Baseline (pre-group capture, u5):** `show running-config`, `show boot` (boot config
`flash:/tb470-oldstack.cfg`), `show stack`, `show reboot history`, `show interface port1.0.9,port1.0.10
status` → `27887/work/pre-group-u5.out`.

**Setup (u5, `ckcon.py --stop-on-error`):**
```
configure terminal
vlan database
 vlan 3995 name ck-svlan
 vlan 3997 name ck-internal
interface port1.0.9-1.0.10
 shutdown
 switchport mode trunk
 switchport trunk allowed vlan add 3995,3997
 no shutdown
end
```
Native VLAN 1 stays on both ports, so eth1/eth3 keep the lab VLAN 1. Loop risk is nil, because only
host NICs are on these ports. Each stage adds its own lines (customer-edge-port / provider-port /
translation entries) and removes them before the next stage.

**Restore (u5, `ckcon.py --stop-on-error`), the exact recipe:**
```
configure terminal
interface port1.0.9-1.0.10
 shutdown
 no switchport vlan translation all
 no switchport vlan translation default
 no switchport vlan-stacking
 switchport mode trunk                           (only if a stage left a port in access mode)
 switchport trunk allowed vlan remove 3995,3997
 switchport mode access
 no shutdown
vlan database
 no vlan 3995
 no vlan 3997
end
```
If a `no` form is refused because nothing is configured, skip that line; never skip the rest.
**Verify:** `show running-config` on u5 rcdiffs EMPTY against the pre-group capture.
`remote-diff all show running-config` shows the members identical. `show boot` still names
`flash:/tb470-oldstack.cfg`. port1.0.9/1.0.10 are connected in VLAN 1. A re-probe shows the same
MISMATCH set as 10:56 (off-template by design; do NOT apply).
**If the tester dies mid-group:** run the restore block above on u5 as written, then verify.

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

- I-1 (carried): SA u3 unresponsive, OPEN since the 2026-10-05 handover. Not this campaign's to fix.
- I-2: tb470 eth2 (to SA port1.0.2) had carrier at 08:21 and has NONE at 10:56: the SA's state changed. Not investigated (u3 not this session's).
- I-3: dispatch facts were stale (sentinel read the handover before its 10:28 update); triage caught it.
