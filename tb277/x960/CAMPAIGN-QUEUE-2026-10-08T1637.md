# Campaign queue — tb277 x960-56YSQ, 13 AWPTCM cases, from 2026-10-08 16:37 NZDT

The ask, verbatim (Test Engineer, 2026-10-08): *"Use /orient-dt and /test-mode to run these test
cases"*, with a screenshot of the AWPTCM "Not Executed" list for **x960-56YSQ** (47 cases; the 13
visible ones are this campaign). Then: *"Go ahead."*

**This file is the resume point.** A session that wakes up reads it top to bottom, continues from
the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state changes.

Shape: ONE session (orient-dt §10 A, `/test-mode`): this session is the sentinel, `bench-runner`
subagents are the tester.

## Session facts

Recorded 2026-10-08 16:37 NZDT. The Test Engineer's answers, word for word:

```
Test Engineer: bidhanc@bidhanc-dl
Testbox:       tb277
Consoles:      u2 (swi_c, DUT), u3 (swi_b), u5 (swi_a)
PDU:           10.36.230.212 outlet 1 (u2), outlet 7 (u3); 10.36.230.35 outlet 3 (u5)
Constraints:   none stated
Power cycles:  "Power cycles allowed"
Durability:    "I am not sure, but we can run it in plain terminal" -- NOT tmux/screen.
               If this window closes the tester dies with it; the queue file and the per-case
               commits survive and `/test-mode --resume` loses only the case in flight.
Stand-down:    "stand down the sentinel when I tell you to stop"
```

Devices (measured, `bench-setup/tb277/bench-state.md` generated 2026-10-08T025159Z):
- **DUT — swi_c, /dev/u2, AT-x960-56YSQ, S/N A2WQS7004**, standalone member 1, 115200 baud,
  software `sin_x96056-20260921-9`, bootloader `benb` (a dev build), **netboots**
  (`Current boot image: Not set`; `/tftproot/x960-tb277.rel` present, 2026-09-30).
  **Marvell 98CX8514 (Falcon)** — see `platforms/x960.md` §1.
- partner — swi_b, /dev/u3, AT-x960-28YSQ, S/N A10737A261700021, 9600 baud, same software,
  boots `flash:/backup.rel`. **Marvell 98DX4580M (AlleyCat5P-XL)** — a DIFFERENT switching core.
- partner — swi_a, /dev/u5, AT-x950 GEN2-52XSTQm, S/N A10713A262600012, 9600 baud,
  `awplus_main-20261008-56`, netboots. Rebooted and defaulted this morning when
  `/tftproot/x950GEN2-tb277.rel` was refreshed at 12:21; holds no config across a reboot.

Cabling (measured 2026-10-08T025159Z, after the Test Engineer's recable):
```
tb eth3 (10.38.22.33/27) ──── swi_c port1.0.10    [NEW copper SFP + cable, fitted today]
tb eth4 (10.38.22.65/27) ──── swi_c port1.0.48
tb eth2 (10.38.22.1/27)  ──── (carrier up, far end not proven; recorded 10-07 as swi_c eth0 mgmt)
swi_a port1.0.1  ──── port1.0.1  swi_b
swi_a port1.0.11 ──── port1.0.11 swi_b           [NEW today]
swi_a port1.0.4  ──── port1.0.4  swi_c   (in swi_c sa1)
swi_a port1.0.14 ──── port1.0.14 swi_c           [NEW today]
swi_b port1.0.2  ──── port1.0.2  swi_c   (in swi_c sa1 and swi_b sa1)
swi_b port1.0.16 ──── port1.0.16 swi_c           [NEW today]
swi_c port1.0.8, port1.0.40 ──── OFF-BENCH, far ends unidentified
swi_b port1.0.8             ──── OFF-BENCH
```
The Test Engineer added the three second links *"so you would be able to form a channel"*.

**Only 5 of the DUT's 48 cages hold a copper SFP** (1.0.2, 1.0.4, 1.0.8, 1.0.40, 1.0.48) plus the
new one in 1.0.10. Every other port cannot link.

STP at probe time (measured on the DUT): root is **swi_b** (`0000cd423029`); `sa1` is the root
port and Forwarding; `port1.0.10` and `port1.0.48` Designated/Forwarding; **`port1.0.14` and
`port1.0.16` both Alternate/Discarding**.

## Grounding — what these cases are graded against

Per [[review-feature-docs-before-testing]] and [[corpus-sources-are-not-authoritative]], in
order of authority: the standard → the TPS and Feature Overview guide → the DUT → the corpus.

- **ck.db**: all 13 resolved by title (the AWPTCM-T numbers do not exist in it). Three needed
  fuzzy matching: T44986 = `AWP-13990` *"deny/permit statements for standard access list"*,
  T44987 = `AWP-8612` (double space in the stored title), T44992 = `AWP-8659`.
- **Software TPS** (`X960_platform_support_TPS`): ACLs, ACL table utilisation, sequence numbers,
  `send-to-vlan-port`, per-VLAN ACLs, SNMPv3-group ACLs, port mirroring and RSPAN are **all
  supported, priority 1**. Nothing in this campaign may be graded UNSUPPORTED without DUT
  evidence.
- **Test Strategy** (`Test:3331_Test_Strategy_-_x960-56YSQ`): hardware ACLs get *"full testing as
  they are TCAM-backed"*; coverage includes *"TCAM utilisation and contention with QoS"*; the
  named risk is *"TCAM consumption against the chosen 2.5K rule budget on Falcon"*. And:
  *"Results from the x960-28YSQ demonstrate nothing about this board's dataplane"*.
- **Feature Overview guides** (ACL, Mirroring): the action definitions, the QoS-vs-ACL ordering
  rule and the mirroring restrictions are all in `platforms/x960.md` §5. Read that section before
  drafting or grading any step here.

### Three traps that would produce false results — carried into every group

1. **Interface ACLs are matched BEFORE QoS on the same port**, and a permit in the interface ACL
   bypasses every subsequent QoS rule (ACL guide p24). ⇒ for any case that says *"apply the same
   ACL via service policy and repeat"*, the `access-group` must be **removed and proven gone**
   before the `service-policy` form is applied. Otherwise the QoS half silently passes without
   being exercised. This is also where the ACL suite's CR history is densest.
2. **`send-to-cpu` can drop control traffic** — the guide warns of EPSR healthchecks, and
   T44989's own precondition cites **CR30477** for STP interference. **RSTP is running on all
   three units.** Capture `show spanning-tree brief` on the DUT before and after every
   send-to-cpu step and record any change.
3. **Never enable `access-list hardware-deny-log` while a `copy-to-cpu`/`send-to-cpu` ACL
   exists** — matching packets are then dropped (ACL guide p14).

### Depth required of every case ([[satisfactory-level-of-testing]])

The case's step text is the floor. Unless a row says otherwise, every case also proves:

- **D0 baseline** — the behaviour with the feature OFF, so the later steps are readable;
- **D1 positive proof** — something only visible if the feature works (absence of an error is
  never proof), plus the inverse where the case allows;
- **D2 removal** — the `no` form is accepted AND the line is gone from `show running-config`,
  diffed against the pre-case copy. Residue is a finding;
- **D3 persistence** — `copy running-config startup-config`, reload, confirm the config is still
  present and still working, then restore. Power cycles are allowed this session. **The DUT
  netboots**: before any reload, confirm `show boot` reads `Current boot config: ... (file
  exists)` and that `/tftproot/x960-tb277.rel` is present, and watch u2 through the boot;
- **D4 non-matching / non-IP traffic** — an IP ACL must not affect ARP.

D3 is run **once per group**, on that group's representative case, not once per case — a reload
costs several minutes and the mechanism is shared. The group's row says which case carries it.

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list and the final log template:
  **`logged-output.md`**. Final logs are made only by `/create-logs`, on request.
- **Every final log's `TOPOLOGY AS TESTED` opens with an ASCII diagram** of that case's
  environment (Test Engineer, 2026-10-08; rules in `logged-output.md` §4).
- `STANDING-ORDERS.md` applies in full. No constraints were stated, so the tester has full
  authority within the tests, including power-cycling the three units.
- Startup-config is written only where D3 requires it, and restored afterwards.
- Teardown verified by diffing `show running-config` against the pre-case copy.
- Stop on any `% ` CLI line *except* the known mirror-port advisory (`platforms/x960.md` §5);
  gate each dependent step on proven state ([[bench-scripts-stop-on-cli-errors]]).
- `mls qos enable` prompts (y/n) and has aborted config and logged sessions out
  ([[awplus-config-prompts-abort-and-logout]]). Send `y\r`.

## Campaign setup and restore (set ONCE before group 1, restored ONCE at the end)

Goal: one deterministic path through the DUT, one mirror destination, one far-side observer.

```
  tb eth4 10.38.22.65/27            tb eth3 10.38.22.33/27
     SOURCE (scapy/ping)              CAPTURE (tcpdump) - mirror dest
          |                                   ^
          v                                   |
     port1.0.48                          port1.0.10
   +=====================================================+
   |      swi_c   AT-x960-56YSQ   DUT   (Falcon)         |
   +=====================================================+
                        | sa1 = port1.0.2 + port1.0.16
                        v
              swi_b  AT-x960-28YSQ   vlan100 10.38.22.70/27
              FAR SIDE - "was it forwarded?"

   swi_a: isolated for this campaign (DUT 1.0.4 and 1.0.14 shut)
```

Setup, in order. The tester records the pre-state of every line it changes:

1. **DUT**: `interface port1.0.4` → `no static-channel-group`; `interface port1.0.16` →
   `switchport access vlan 100`, `static-channel-group 1`.
   **swi_b**: `interface port1.0.4` → `no static-channel-group`; `interface port1.0.16` →
   `switchport access vlan 100`, `static-channel-group 1`.
   ⇒ `sa1` becomes a real 2-member LAG, both members to the same switch. Confirm with
   `show static-channel-group` on both, and that both members read `Forwarding`.
2. **DUT**: `interface port1.0.48` → `switchport access vlan 100`. ⇒ host eth4 is now L2-adjacent
   to swi_b across the DUT. The DUT needs **no IP address**: it is a pure L2 switch in this path.
3. **swi_b**: `interface vlan100` → `ip address 10.38.22.70/27`. Confirm `ping 10.38.22.65` from
   swi_b reaches the host, and `ping 10.38.22.70` from the host reaches swi_b — **that round trip
   is the proof the path transits the DUT**, and it is the control every ACL case is read against.
4. **DUT**: `interface port1.0.4` and `interface port1.0.14` → `shutdown`. ⇒ swi_a is isolated, so
   no swi_a↔swi_b path can carry test traffic around the DUT and no STP reconvergence can move
   the path mid-case. Record that swi_a is deliberately isolated.
5. Re-read `show spanning-tree brief` on the DUT and record the post-setup state. `port1.0.10`,
   `port1.0.48` and `sa1` must all be Forwarding before the first case.
6. Capture `show running-config` on all three units as the campaign baseline, and
   `show platform classifier statistics utilization brief` on the DUT as the TCAM baseline.

Restore at the end: reverse 1–4 exactly, un-shut 1.0.4 / 1.0.14, remove swi_b's vlan100 address,
return port1.0.48 and port1.0.10 to vlan 1 and clear any mirror, then diff all three
running-configs against the campaign baseline and re-probe.

### Setup AMENDMENTS from triage (2026-10-08 ~17:10) — apply these before group 1

The tester found four things in the recipe above that would have produced unreadable or false
results, and two gaps in the restore. All are within its own authority; none needs the Test
Engineer at the bench.

- **(a) 🔥 VLAN 100 is not a closed domain.** **DUT `port1.0.8` and swi_b `port1.0.8` are both
  connected, both already in VLAN 100, both STP Forwarding, both far ends unidentified.** The
  setup moves test traffic INTO vlan 100, so anything live behind either port floods into the
  test VLAN, reaches `sa1` and `port1.0.48`, **and is mirrored into every group-1 capture** —
  destroying the "eth3 captures only the expected frames" proof, and able to answer ARP for
  10.38.22.70. ⇒ **`shutdown` DUT port1.0.8 and swi_b port1.0.8 in setup; un-shut in restore.**
  Same family, lower priority: DUT `port1.0.40` (connected, vlan 1, Forwarding, far end unknown)
  is an STP participant that can inject topology changes — shut it too or record it explicitly.
- **(b) swi_a↔swi_b stays live, and swi_b is the observer.** Shutting DUT 1.0.4/1.0.14 isolates
  swi_a from the DUT, but swi_a 1.0.1/1.0.11 ↔ swi_b 1.0.1/1.0.11 remain up — two parallel vlan-1
  links with RSTP blocking one and loop-protection fast-block armed. A flap there sends a TCN
  into **swi_b**, flushing the MAC table that every ACL case's forwarding check depends on.
  ⇒ **also `shutdown` swi_b port1.0.1 and port1.0.11.** One STP domain in the path, swi_a fully
  out.
- **(c) Shut 1.0.16 before reworking the LAG.** `loop-protection` is enabled on every port,
  action `vlan-dis`, fast-block, 7 s timeout. Changing VLAN and channel-group membership on
  1.0.16 at two ends leaves a window where the ends disagree; a transient loop there silently
  disables VLAN 100 on a port for 7 s mid-setup. ⇒ **`shutdown` DUT 1.0.16 and swi_b 1.0.16 →
  make every change at both ends → `no shutdown` both.** Then confirm
  `show static-channel-group` reads `port1.0.2, port1.0.16` on both units with both members
  Forwarding, and check `show log` for loop-protection actions before case 1.
- **(d) DUT port1.0.4 keeps `switchport access vlan 100`** after `no static-channel-group`. It is
  shut so it is harmless, but set it to vlan 1 or record it deliberately.
- **(d2) Mirror oversubscription.** `port1.0.10` links at **1 Gbps** and so does the monitored
  `port1.0.48`. `direction both` at line rate exceeds the destination and drops frames, which
  reads as a mirror failure. **Keep group-1 traffic at ping/scapy rates — not `tcpreplay` line
  rate.**
- **(e1) Back up `flash:/default.cfg` first.** D3 does `copy running-config startup-config`,
  which overwrites the DUT's 1703-byte saved baseline. The restore only reverses running-config.
  ⇒ **copy `flash:/default.cfg` to `flash:/precampaign.cfg` before group 1** and restore it at
  the end. Note the running-config carries `lldp run` that startup-config does not, so a D3 save
  would persist that too.
- **(e2) Set the clocks.** The DUT logs in **UTC** while the box is NZDT (**+13 h**), and swi_b's
  clock is ~12 h off the DUT's. Group 1's method correlates DUT behaviour against host `tcpdump`
  stamps and swi_b receipt. `clock set` is exec-only with no running-config footprint, so fixing
  it on the DUT and swi_b at campaign start costs nothing and needs no restore. **Do it.**

Boot baseline confirmed safe for D3 (triage): DUT `Current boot config: flash:/default.cfg (file
exists)`; `/tftproot/x960-tb277.rel` present, 57,496,435 B, `.info` =
`x960-sin_x96056-20260921-9.rel`, **matching the running build**. swi_a reads
`flash:/default.cfg (file not found)` — it netboots and defaults, as I-3 records.

**`port1.0.10` becomes the mirror destination in group 1 and stays one for group 3.** A mirror
destination leaves every VLAN and stops normal switching, and **only one mirror destination is
supported per switch** — so host eth3 sees mirrored frames only, and no case may configure a
second destination.

## Group 4 bench setup AS APPLIED, and its exact restore recipe (2026-10-08T1637)

Written BEFORE the group's first case so a fresh tester can restore the bench if this
session dies mid-group (bench-runner RUN obligation). **T44992's stack clauses were
withdrawn by the Test Engineer 2026-10-08:** *"AWPTCM-T44992 (1.0) ACL: Named Hardware on
static LAG - IP does not need a stack, so please perform the test on a current setup."*
The case is therefore graded in full on a standalone DUT, and its row is no longer PARTIAL.

Pre-change baselines (full `show running-config`, `show static-channel-group`,
`show spanning-tree brief`, `show access-list`, `show mirror`, `show boot`) are captured at
`/tmp/ck-t44992-2026-10-08/pre-u2.txt` and `pre-u3.txt` on tb277, and copied into
`tb277/x960/acl-lag-2026-10-08T1637/T44992/work/`. **The repo copies are authoritative** —
tb277's `/tmp` does not survive a box reboot.

This adopts triage recommendations (a), (c) and (e): the two off-bench VLAN-100 ports are
shut, the LAG rework is done shut-first, and `flash:/default.cfg` is backed up.

### Setup, in the order applied

```
S0  DUT    copy flash:/default.cfg flash:/precampaign.cfg        [done 17:13]
S1  swi_b  interface port1.0.16 ; shutdown                        [done 17:13]
S2  DUT    interface port1.0.16 ; shutdown                        [done 17:13]
S3  swi_b  interface port1.0.4  ; no static-channel-group
           interface port1.0.16 ; switchport access vlan 100 ; static-channel-group 1
           interface port1.0.8  ; shutdown        (off-bench, was in vlan 100)
           interface port1.0.1  ; shutdown        (isolates swi_a)
           interface port1.0.11 ; shutdown        (isolates swi_a)
           interface vlan100    ; ip address 10.38.22.70/27
S4  DUT    interface port1.0.4  ; no static-channel-group ; switchport access vlan 1 ; shutdown
           interface port1.0.14 ; shutdown        (isolates swi_a)
           interface port1.0.8  ; shutdown        (off-bench, was in vlan 100)
           interface port1.0.16 ; switchport access vlan 100 ; static-channel-group 1
           interface port1.0.48 ; switchport access vlan 100
S5  swi_b  interface port1.0.16 ; no shutdown
    DUT    interface port1.0.16 ; no shutdown
```

Gate before case 1: `show static-channel-group` must read `port1.0.2` + `port1.0.16` on BOTH
units, both members Forwarding; `show log` must show no loop-protection action; and the
control ping 10.38.22.65 (host eth4) <-> 10.38.22.70 (swi_b vlan100) must pass BOTH ways.
That round trip transits the DUT and is what every ACL step is read against.

### Restore — exact reverse, run it whole

```
R1  DUT    interface port1.0.16 ; shutdown
    swi_b  interface port1.0.16 ; shutdown
R2  DUT    interface port1.0.48 ; switchport access vlan 1
           interface port1.0.16 ; no static-channel-group ; switchport access vlan 1
           interface port1.0.8  ; no shutdown
           interface port1.0.14 ; no shutdown
           interface port1.0.4  ; no shutdown ; switchport access vlan 100 ; static-channel-group 1
R3  swi_b  interface vlan100    ; no ip address
           interface port1.0.11 ; no shutdown
           interface port1.0.1  ; no shutdown
           interface port1.0.8  ; no shutdown
           interface port1.0.16 ; no static-channel-group ; switchport access vlan 1
           interface port1.0.4  ; static-channel-group 1      (it kept vlan 100)
R4  swi_b  interface port1.0.16 ; no shutdown
    DUT    interface port1.0.16 ; no shutdown
R5  DUT    delete flash:/precampaign.cfg      (only after any D3 save has been undone)
R6  diff both running-configs against the pre-change baselines; re-run bench_probe.
```

**If D3 wrote startup-config on the DUT**, restore it before R5:
`copy flash:/precampaign.cfg flash:/default.cfg`, then confirm `show boot` still reads
`Current boot config: flash:/default.cfg (file exists)`.

Nothing in S0-S5 was saved to startup-config on either unit, so a reload of either clears
S1-S5 by itself. S0 leaves only an inert extra file in the DUT's flash.

## Group 1 bench setup and its exact restore recipe (mirror-2026-10-08T1637)

Written BEFORE the group's first case (bench-runner RUN obligation) so a fresh tester can
restore the bench if this session dies mid-group. Group 4 (T44992) ran first and was fully
restored; this setup starts from the restored baseline, NOT from group 4's state.

Pre-change baselines are captured to the group's first case folder as
`work/pre-u2.txt` / `work/pre-u3.txt`. The repo copies are authoritative — tb277's `/tmp`
does not survive a box reboot.

Adopts the triage amendments: (a) the two live off-bench VLAN-100 ports are shut, (b) swi_a
is isolated on BOTH sides, (c) the LAG rework is done shut-first against loop-protection
fast-block, (g) both device clocks are set so console logs correlate with host tcpdump.

### Setup, in order

```
G0  both   clock set <HH:MM:SS> <DD MMM YYYY>        exec-only, NO running-config footprint,
                                                     so it needs no restore. The DUT logs in
                                                     UTC (+13h from the box) and swi_b's clock
                                                     was ~12h off the DUT's; without this the
                                                     mirror evidence cannot be lined up with
                                                     the host capture.
G1  swi_b  interface port1.0.16 ; shutdown
    DUT    interface port1.0.16 ; shutdown
G2  swi_b  interface port1.0.4  ; no static-channel-group
           interface port1.0.16 ; switchport access vlan 100 ; static-channel-group 1
           interface port1.0.8  ; shutdown        (off-bench, was live in vlan 100)
           interface port1.0.1  ; shutdown        (isolates swi_a)
           interface port1.0.11 ; shutdown        (isolates swi_a)
           interface vlan100    ; ip address 10.38.22.70/27
G3  DUT    interface port1.0.4  ; no static-channel-group ; switchport access vlan 1 ; shutdown
           interface port1.0.14 ; shutdown        (isolates swi_a)
           interface port1.0.8  ; shutdown        (off-bench, was live in vlan 100)
           interface port1.0.16 ; switchport access vlan 100 ; static-channel-group 1
           interface port1.0.48 ; switchport access vlan 100     MONITORED (source) port
G4  swi_b  interface port1.0.16 ; no shutdown
    DUT    interface port1.0.16 ; no shutdown
```

`port1.0.10` is left a plain VLAN-1 access port by the setup. **Each case makes it the mirror
destination itself** — that is the case's own content, not bench setup. Only ONE mirror
destination is supported per switch, so no case may configure a second.

Gate before case 1 — all must pass:
- `show static-channel-group` reads `port1.0.2` + `port1.0.16` on BOTH units, both Forwarding
- `show spanning-tree brief` on the DUT: `sa1` Forwarding, `port1.0.48` and `port1.0.10`
  Forwarding, `port1.0.4`/`1.0.8`/`1.0.14` Discarding (shut)
- `show log` shows no loop-protection action
- `show mirror` is EMPTY on the DUT
- CONTROL PING host eth4 10.38.22.65 <-> swi_b 10.38.22.70 passes BOTH ways. That round trip
  transits the DUT on port1.0.48 and sa1, and it is the traffic every mirroring case captures.

### Restore — exact reverse, run it whole

```
R0  DUT    clear any mirror: interface port1.0.10 ; no mirror interface <src>|none
           `show mirror` must be EMPTY before going on
R1  DUT    interface port1.0.16 ; shutdown
    swi_b  interface port1.0.16 ; shutdown
R2  DUT    interface port1.0.48 ; switchport access vlan 1
           interface port1.0.16 ; no static-channel-group ; switchport access vlan 1
           interface port1.0.8  ; no shutdown
           interface port1.0.14 ; no shutdown
           interface port1.0.4  ; no shutdown ; switchport access vlan 100 ; static-channel-group 1
R3  swi_b  interface vlan100    ; no ip address
           interface port1.0.11 ; no shutdown
           interface port1.0.1  ; no shutdown
           interface port1.0.8  ; no shutdown
           interface port1.0.16 ; no static-channel-group ; switchport access vlan 1
           interface port1.0.4  ; static-channel-group 1      (it kept vlan 100)
R4  swi_b  interface port1.0.16 ; no shutdown
    DUT    interface port1.0.16 ; no shutdown
R5  host   ip addr del <any secondary> dev eth4 ; stop any tcpdump by PID
R6  diff both running-configs against the pre-change baselines; re-run bench_probe
```

**D3 for this group is carried by T44969.** Before its reload: re-read `/tftproot/x960-tb277.rel`
(the DUT netboots) and confirm `show boot` reads `Current boot config: flash:/default.cfg
(file exists)`. `flash:/precampaign.cfg` is ALREADY on the DUT from group 4 and is the
byte-exact pre-campaign startup config — do NOT delete it, and after any D3 save restore the
startup config by re-saving the torn-down running-config (a direct
`copy flash:/precampaign.cfg flash:/default.cfg` is REFUSED: "% Cannot overwrite
flash:/default.cfg as it is the default config file").

Nothing in G0-G4 is saved to startup-config, so a reload of either unit clears G1-G4 by itself.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| T44967 | PASS | `direction transmit` accepted on the destination port, reported by `show mirror` and `show mirror interface <src>`, and copies ONLY egress frames (6 replies, 0 requests); `no` form removes it from config and dataplane. | bench-runner 2026-10-09 | mirror-2026-10-08T1637/T44967/work/run1.log |
| T44968 | PASS | `direction receive` copies ONLY ingress frames (6 requests, 0 replies), the exact inverse of T44967 on identical cabling. Found defects M1 (re-applied mirror needs a destination-port bounce) and M2 (in-place direction change silently ignored, `show mirror` keeps the stale value). | bench-runner 2026-10-09 | mirror-2026-10-08T1637/T44968/work/run1.log |
| T44969 | **FAIL** | `mirror interface port1.0.48 direction both` is accepted, reported correctly by every CLI status command and survives a save+reload, but copies **NO frames** to the destination. `transmit` and `receive` both work on the same boot, cabling and traffic, so the platform's mirroring and the method are sound and the fault is specific to `both`. Reproduced 5 times incl. on a pristine boot with no reconfiguration history (eliminating M1 as the cause). Capture sizes: all five `both` runs 1 B; tx 535/541 B; rx 547 B. **Defect M3.** Config-persistence half of D3 PASSES | tester | mirror-2026-10-08T1637/T44969/work/run1.log |
| T44969 | FAIL | `direction both` is accepted, reported correctly by every CLI status command and survives a reload, but copies NO frames. transmit and receive both work on the SAME boot/cabling/flow, so the fault is specific to `both`. Reproduced 5x incl. on a pristine boot. D3 config persistence passed. | bench-runner 2026-10-09 | mirror-2026-10-08T1637/T44969/work/run1.log |
| T44973 | PASS | bare `no mirror interface` correctly rejected with `% Incomplete command.` leaving the mirror intact; `no mirror interface <src>` removes it from config AND dataplane, and the destination port returns to normal switching (LLDP/broadcast reappear on eth3 -- proof `show interface status` cannot give). | bench-runner 2026-10-09 | mirror-2026-10-08T1637/T44973/work/run1.log |
| T44974 | PASS | crash regression CR56263 did NOT reproduce. `mirror interface none` gives an ACL-driven destination (`none (via ACL)`); across apply and remove NSM stayed pid 795/12 threads, uptime monotonic 10:12->12:09, log clean, dataplane and CLI serving. | bench-runner 2026-10-09 | mirror-2026-10-08T1637/T44974/work/run1.log |
| 0 | — | — | TRIAGE DONE | campaign setup above; then triage confirms every drafted command on the DUT |
| 1 | T44967 T44968 T44969 T44973 T44974 | mirror-2026-10-08T1637 | DONE | port mirroring. Now with **real frames**: 1.0.48 is the monitored port, 1.0.10 the destination, host eth3 captures. D3 carried by T44969 |
| 2 | T44987 T44988 T44986 | acl-num-2026-10-08T1637 | TODO | numbered ACLs: IP 3000 range, MAC 4000 range, standard 1–99. D3 carried by T44987 |
| 3 | T44979 T44991 T44989 T44990 | acl-named-2026-10-08T1637 | TODO | named hardware ACLs on a port: proto, copy-to-cpu, send-to-cpu, copy-to-mirror. Run copy-to-cpu and send-to-cpu back to back and contrast. D3 carried by T44979 |
| 4 | T44992 | acl-lag-2026-10-08T1637 | DONE | named hardware ACL on `sa1`. Stack clauses WITHDRAWN by the Test Engineer 2026-10-08 — graded in full, no longer PARTIAL. Setup + restore recipe above |

## Drafted case steps — to be syntax-confirmed on the DUT at triage

Confirm each command family with `?` sent **without** a trailing CR (`tools/qmark.py`;
[[never-send-cli-help-through-a-cr-driver]]). Where the DUT's form differs, the tester records
the DUT's actual syntax in the working log and uses it.

### Group 1 — port mirroring

Monitored (source) port = **port1.0.48** (carries the host↔swi_b traffic). Mirror destination =
**port1.0.10** (host eth3 captures). The `mirror interface` command is entered on the
**destination** port and names the **source**.

- **T44967 / AWP-5316 — CLI show mirror interface direction set to transmit.**
  `interface port1.0.10` → `mirror interface port1.0.48 direction transmit`. Verify
  `show mirror interface port1.0.48` reports direction `transmit` with the right source and
  destination. **Frame-level proof:** ping host→swi_b, confirm eth3 captures only the DUT's
  **egress** frames on 1.0.48 (the replies), not the ingress ones. D2, D4.
- **T44968 / AWP-5317 — ... set to receive.** As above with `direction receive`; eth3 must
  capture only the **ingress** frames (the requests). The transmit/receive pair is each other's
  control — run them back to back.
- **T44969 / AWP-5318 — ... set to both.** `direction both`; eth3 captures both directions.
  **This case carries D3** for group 1: save, reload the DUT, confirm the mirror is still
  configured and still mirroring, then restore.
- **T44973 / AWP-6299 — CLI Remove mirror interface.** Remove with
  `no mirror interface port1.0.48`; `show mirror` empty, port1.0.10 back to a plain port, removal
  diff CLEAN. **The bare `no mirror interface` is INVALID on the x960** (`% Incomplete command.`,
  measured 2026-10-07) — record the rejection as evidence and grade the corrected form.
  Frame-level: eth3 captures nothing after removal.
- **T44974 / AWP-25167 — Mirror set to interface none.** ⚠ **This is NOT a feature test.** Its
  ck.db summary names **CR56263** and says *"Make sure system is stable (was NSM crash)"* — it is
  a **crash regression**. Grade it on NSM staying up, not on "the mirror turned off".
  `mirror interface none` makes port1.0.10 an **ACL-driven** destination (`show mirror` reports
  `none (via ACL)`), which is the mechanism T44990 needs. Steps: apply it, confirm `show mirror`,
  then check `show process` / `show log` for an NSM restart, confirm the CLI and the dataplane
  still work, and remove it with `no mirror interface none`.

### Group 2 — numbered hardware ACLs

- **T44987 / AWP-8612 — Hardware IP 3000 range, applied to ports.** Steps call for both `deny`
  and `permit` across `icmp|ip|proto|tcp|udp`, each attached to a port, matching and non-matching
  traffic including non-IP, `show plat count sdma` for CPU traffic, and a mirror port to check
  copy-to-mirror. Apply on **port1.0.48** with `access-group <3000-3699>`; the host↔swi_b ping is
  the control. Verify with `show access-list counters` (5.5.1-2.1+) and by whether swi_b still
  answers. **Carries D3** for group 2. Also record
  `show platform classifier statistics utilization brief` before and after, against the TPS's
  2.5K Falcon rule budget.
- **T44988 / AWP-8616 — Hardware MAC 4000 range, applied to ports.** The stored steps give
  worked examples using `copy-to-cpu`, `send-to-cpu` and `copy-to-mirror` on 4000-range MAC ACLs
  and a trunk port with vlan 600. Source frames from the host with a known MAC (scapy). Keep the
  CPU actions here consistent with group 3's findings and contrast them.
- **T44986 / AWP-13990 — deny/permit statements for standard access list.** Five numbered steps:
  permit works, deny works, implicit deny works, wildcard masks select correctly, and rules are
  evaluated top to bottom with first match winning. ⚠ **A standard (1–99) list cannot be bound to
  an interface on this platform** (measured 2026-10-07) — `access-group` takes 3000–3699,
  4000–4699 or a named hardware list. Standard lists **do** bind to `vty access-class`
  (ACL guide p16), so exercise the five behaviours there, where they are observable, and state
  the binding limit in the log. ⚠ **Hardware ACLs implicitly PERMIT; software/standard ACLs
  implicitly DENY** — step 3 is about the software default and must not be graded against the
  hardware one.

### Group 3 — named hardware ACLs on a port

All four use `access-list hardware <name>` with the entry forms under `(config-ip-hw-acl)`, and
all four say *"apply the same ACL via service policy and repeat"* — run that as a **separate
pass with the `access-group` removed and proven gone** (trap 1 above). QoS path:
`mls qos enable` → `class-map` `match access-group <name>` → `policy-map` `class` →
`interface port1.0.48` `service-policy input <pmap>`.

- **T44979 / AWP-8646 — Named Hardware on port - Proto.** Match an IP protocol number
  (e.g. `deny proto 1 any any` for ICMP). Matching traffic denied, non-matching passes, non-IP
  traffic unaffected, first-match applies; repeat with `permit` for the inverse. **Carries D3**
  for group 3.
- **T44991 / AWP-8655 — copy-to-cpu IP.** Guide definition: **copy to the CPU AND still
  forwarded.** Prove both halves: CPU counters rise (`show platform count sdma`) **and** swi_b
  still receives. Run immediately before T44989 so the pair contrast is on identical setup.
- **T44989 / AWP-8654 — send-to-cpu IP.** Guide definition: **to the CPU and NOT forwarded.**
  Prove CPU counters rise **and** swi_b stops receiving. ⚠ Precondition cites CR30477 — capture
  `show spanning-tree brief` before and after and record any change (trap 2).
- **T44990 / AWP-8657 — copy-to-mirror IP.** Needs the ACL-driven mirror destination from T44974:
  `interface port1.0.10` → `mirror interface none`, then
  `access-list hardware <name>` → `copy-to-mirror ip <src> <dst>`, then `access-group` on
  port1.0.48. Prove **both**: eth3 captures the mirrored copies **and** swi_b still receives the
  originals. ⚠ `copy-to-mirror` **terminates ACL processing at the first match** — a later
  permit/deny in the same list will not be evaluated. Test that explicitly; it is the documented
  reason `mirror interface <src> vlan <vid>` was added.

### Group 4 — named hardware ACL on a static LAG

- **T44992 / AWP-8659 — Named Hardware on static LAG - IP.** Apply a named hardware ACL to the
  aggregator **`sa1` itself**, not its members (ACL guide: static channel group → the group;
  LACP → every member port). With the campaign setup `sa1` is a genuine 2-member LAG to swi_b, so
  "effective on its members" is testable for the first time on this bench. Specify src/dest host
  and network addresses, with and without vlan; matching denied, non-matching permitted, non-IP
  and **ARP unaffected**; first-match applies; repeat via service policy.
  ⚠ **Expected PARTIAL.** The stored steps also require *"LAG should straddle stack members"* and
  *"Test after stack failover, rejoin, reboot"*. **The DUT is a standalone unit, not a stack** —
  those clauses cannot run here at any cabling. State them as NOT RUN with the reason, and
  UNBLOCK = a second x960-56YSQ stacked with the DUT.

## Results

| case | verdict | reason | graded by | working log |
| --- | --- | --- | --- | --- |
| T44992 | PASS | named hw IP ACL on static LAG sa1 enforces on BOTH members; host+network forms, vlan qualifier both ways, first-match, ARP unaffected, via access-group AND service-policy, survives reload, removes with no config or TCAM residue. Stack clauses withdrawn by the Test Engineer, NOT run. | bench-runner 2026-10-08 | acl-lag-2026-10-08T1637/T44992/work/run1.log |
| T44967 | PASS | `mirror interface port1.0.48 direction transmit` accepted on the destination port, reported by both `show mirror` and `show mirror interface`, and copies ONLY egress frames of the monitored port (6 replies, 0 requests); forwarding undisturbed; the `no` form removes it cleanly from config and dataplane | tester | mirror-2026-10-08T1637/T44967/work/run1.log |
| T44968 | PASS | `mirror interface port1.0.48 direction receive` accepted and reported correctly, copies ONLY ingress frames (6 requests, 0 replies) — the exact inverse of T44967 on identical cabling, so the two are each other's control. Defects **M1** (a re-applied mirror needs a destination-port bounce) and **M2** (an in-place `direction` change is silently ignored) were found while proving it; both are recorded as measured observations in this log, with the seven-capture table and the host-side causes ruled out first | tester | mirror-2026-10-08T1637/T44968/work/run1.log |

## Issues

Status: OPEN (waiting on the Test Engineer), CHOSEN (a blocker; recommendation applied for
review), NOTED (no decision needed now), CLOSED (decided or answered).

- **I-1 (CLOSED, 2026-10-08) The 2026-10-07 "VLAN ACLs absent" finding was wrong.** That session
  recorded *"`access-group` exists on ports and aggregators but not on VLAN interfaces"* and the
  inference drawn was that per-VLAN ACLs were missing while the TPS marks them supported. The ACL
  guide p17 settles it: per-VLAN ACLs use `vlan access-map` + `match access-group` +
  `vlan filter <map> vlan-list <list> input`, **not** `access-group` under `interface vlanN`. The
  observation was right, the inference wrong. Nothing to report as a defect.
- **I-2 (NOTED) `sa1` spanned two different switches until today.** `static-channel-group 1` on
  the DUT held port1.0.2 (→ swi_b) and port1.0.4 (→ swi_a). The campaign setup fixes it to
  1.0.2 + 1.0.16, both to swi_b. Recorded because any result from before this change that
  depended on `sa1` hashing is suspect.
- **I-3 (NOTED) swi_a holds no config across a reboot.** It netboots with empty flash and
  defaulted this morning. It is deliberately isolated for this campaign (setup step 4), so this
  costs nothing here, but a later campaign that needs swi_a must reconfigure it after any reload.
- **I-4 (NOTED) The DUT netboots, and `/tftproot` is a tmpfs.** `x960-tb277.rel` is present
  (2026-09-30), and tb277's uptime is 27 days. A reboot of **tb277 itself** would empty
  `/tftproot` and the DUT could not then boot. Re-read `/tftproot` immediately before any D3
  reload.
- **I-6 SHARPENED 2026-10-08 17:43, during T44992 — the consumption rate is now MEASURED.**
  With exactly one hardware ACL rule applied (`deny ip … vlan …` on `sa1`), the DUT reports
  `ACL 1` and `Total 3 / 1024`, against a clean baseline of `Total 2 / 1024` (the 2 being Loop
  Detection). ⇒ **one hardware ACL rule = one classifier entry**, so the ceiling on this build is
  about **1022 ACL rules with nothing else configured** — and the same 1024 pool is shared with
  Global ACL, VACL, QoS, Loop Detection, EPSR, CFM, G8032, DoS, RA Guard, BFD/BEFD, AMFAPPS,
  IPFIX (Flow and Sample), OpenFlow (Hybrid/Flow/Default) and MLAG, each separately counted.
  The project budget is **2.5K 60-byte rules**. This is not a margin question: the pool is
  roughly **2.5x smaller than the budget assumes**. Egress is a separate `0 / 6144`.
  **This is the strongest evidence yet for raising it as its own CR** — it is measured on the
  DUT, reproducible in one command, and lands exactly on the Test Strategy's headline risk.
- **I-6 (OPEN — Test Engineer) The ingress classifier pool reads 1024 entries, not ~2.5K.**
  Measured at triage on a clean DUT: `show platform classifier statistics utilization brief` →
  `[Instance 0] [port1.0.1-port1.0.77]`, ingress `Total 2 / 1024` (the 2 = Loop Detection),
  egress `0 / 6144`. The TPS's Falcon arithmetic implies ~3K 60-byte ACL rules and the project
  works to a **2.5K budget**; the Test Strategy's named risk is *"TCAM consumption against the
  chosen 2.5K rule budget on Falcon"*. On this build that risk looks already realised, by roughly
  2.5x. Only **one** instance is reported although the TPS describes two control pipes.
  **Blocks none of the 13 cases** (each uses a handful of rules), and the separate
  `Global ACL` / `ACL` / `VACL` / `QoS` counters in that one pool make group 3's ACL-vs-QoS
  contention directly measurable. **Asked 2026-10-08, unanswered:** is 1024 expected on
  `sin_x96056-20260921-9`, or is this the budget risk materialising? May deserve its own case or
  CR, independent of these 13.
- **I-7 (OPEN — Test Engineer) Four consoles on tb277 are outside this session's list** — `u0`,
  `u1`, `u4`, `u6`. None was opened. If one fronts a second **x960-56YSQ**, T44992's stack
  clauses could be revisited; that is both a console outside the session list and a topology
  change, so it is the Test Engineer's call, not the tester's.
- **I-8 (NOTED, for group 3) The `access-list hardware <name>` sub-mode actions are unconfirmed.**
  Entering that sub-mode creates the list — a config change the read-only triage correctly
  refused. The numbered forms prove every action the four group-3 cases use. **Confirm the
  sub-mode's action list in the first minute of group 3**, where creating a named hardware ACL is
  the case's own step. Related: `send-to-mirror` and `deny-and-not-cpu` are **absent** from the
  numbered forms on this build (`platforms/x960.md` §5, corrected 2026-10-08).
- **I-5 (NOTED) Case steps are drafted, not authoritative.** They come from ck.db's `steps_text`
  and `summary`, re-grounded against the Feature Overview guides, the TPS and the Test Strategy.
  Where the standard or the guide contradicts a step, the tester tests the correct behaviour and
  records the discrepancy ([[corpus-sources-are-not-authoritative]]).
