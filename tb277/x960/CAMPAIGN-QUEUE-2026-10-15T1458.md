# Campaign queue — tb277 x960-56YSQ, 6 AWPTCM DHCP cases, from 2026-10-15 14:58 NZDT

The ask (Test Engineer, 2026-10-15): *"Please do the test cases that I give you"*, with a
screenshot of six AWPTCM cases for **x960-56YSQ**. Earlier in the same session: *"Don't worry
about the test cases that you have done — that is done and dusted. Don't worry about the number
that you saw on the screenshot … Some of the test cases will be done manually by me"*, then:
*"the list that I send you are the ones that you would be required to do. I won't send you the
list of test cases that have been manually done."*
⇒ **This campaign is exactly these six. No reconciliation against any earlier list.**

Shape: ONE session (orient-dt §10 A, `/test-mode`): this session is the sentinel, `bench-runner`
subagents are the tester.

**This file is the resume point.** A session that wakes up reads it top to bottom, continues from
the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state changes.

## Session facts

Recorded 2026-10-15 14:58 NZDT. The Test Engineer's answers, confirmed verbatim:
Test Engineer: bidhanc@bidhanc-dl
Testbox: tb277
Consoles: u2 = swi_d (DUT), u3 = swi_b, u5 = swi_a
PDU: 10.36.230.212 outlets u2=1, u3=7; 10.36.230.35 outlet u5=3
Constraints: None

Devices, measured by `bench_probe.py` 2026-10-15T012929Z (`bench-setup/tb277/bench-state.md`):
- **DUT — swi_d, /dev/u2 @115200, AT-x960-56YSQ, S/N `A2WQS700B`**, standalone Active Master,
  software **`sin_x96056-20261012-24`** (Mon Oct 12 2026), bootloader reads `Unknown`,
  **boots from FLASH** (`flash:/x960-tb277.rel`, file exists), flash 166 MB used of 14.3 GB,
  hostname `awplus` — **the DUT is at default config**.
- partner — swi_b, /dev/u3 @9600, AT-x960-28YSQ, S/N A10737A261700021,
  `sin_x96056-20260921-9`, boots `flash:/backup.rel`, hostname `x960-28YSQ`.
- partner — swi_a, /dev/u5 @9600, AT-x950 GEN2-52XSTQm, S/N A10713A262600012,
  `awplus_main-20261008-56`, netboots, boot image **Not set**, hostname `awplus`.

**🔥 The DUT is a DIFFERENT PHYSICAL UNIT from the 2026-10-08 campaign** (`A2WQS700B`, was
`A2WQS7004` = `swi_c`) on a build three weeks newer, and it now boots from flash instead of
netbooting. Confirmed by the Test Engineer: *"The DUT is the same, just a different unit. Boots
from flash now."* `tb277.static` is append-only, so it still carries the stale `swi_c` line.

Links (measured, richer than the 10-08 campaign's):
```
tb eth3 ──── swi_d port1.0.10        swi_a 1.0.1  ── 1.0.1  swi_b
tb eth4 ──── swi_d port1.0.48        swi_a 1.0.11 ── 1.0.11 swi_b
tb eth2 ──── (carrier up, unlearned) swi_a 1.0.4  ── 1.0.4  swi_d
                                     swi_a 1.0.14 ── 1.0.14 swi_d
                                     swi_b 1.0.2  ── 1.0.2  swi_d
                                     swi_b 1.0.16 ── 1.0.16 swi_d
```
Two host NICs reach DUT **switch ports**, so inject-and-observe across the DUT is available
without recabling.

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list and the final log template:
  **`logged-output.md`**. Final logs are made only by `/create-logs`, on request.
- `STANDING-ORDERS.md` applies in full. Constraints are "None", so the tester has full authority
  within the tests, including power-cycling the three units.
- **🔥 STANDING-ORDERS §7 (Test Engineer, 2026-10-15): traffic tests use scapy, not ping.** Craft
  the exact frame the rule matches, send a known count, count arrivals, and send a **control**
  flow in the same run that must NOT match. These six are DHCP cases — DISCOVER/OFFER/REQUEST/ACK,
  Option 82 insertion and stripping, relay rewriting, ARP probing — none of which a ping can
  express. Use `tools/` first; anything new is generic and lands in `tools/` with its README entry.
- **Satisfactory level of testing** (Test Engineer, 2026-10-08): the step text is the FLOOR —
  also prove removal (gone from running-config) and persistence across reboot; baseline OFF first.
- Nothing is written to startup-config unless a case requires it.
- Teardown verified by diffing `show running-config` against the pre-case copy.
- Gate each dependent step on proven state, never on an exit code alone; a benign `% ` advisory
  reads as failure to a stop-on-error driver (`platforms/x960.md` §5).

## 🔴 Case steps: NOT in ck.db — ground them in the feature docs

`ck.db` does **not** contain these six. Proven three ways on 2026-10-15: no title anywhere in
`testlink_cases` contains `IPv4_`; `atp_tests` has no `IPv4_DHCP` rows (its DHCP suites are
IxANVL, a different thing); and the AWPTCM-T numbering is absent from the database entirely.
Title `LIKE` searches return many plausible-but-different cases (five "ARP Probe", six
"Option 82"), so **no ck.db case may be mapped to one of these six** — that would be fabricating
a source. See memory `ckdb-case-lookup-by-title`.

⇒ Per the Test Engineer's 2026-10-08 rule (memory `review-feature-docs-before-testing`), steps
are grounded in, and cite, these three — NOT reconstructed from the title alone:
1. **Software TPS** — `https://wiki.atlnz.lc/awpwiki/index.php?title=X960_platform_support_TPS&action=raw`
   (confirmed reachable from tb277, 200, 70,440 B). Quote the DHCP support row per case. A row
   saying **No** is UNSUPPORTED with the TPS as evidence; a row saying **Yes** whose command is
   absent on the DUT is a **finding**, not a limit.
2. **Feature Overview and Configuration Guide** — the public guide for each feature.
3. **Test Strategy** for the x960-56YSQ.
Fetch on the box with `curl -sk` (`lab-wiki-reachable-from-a-testbox`); the dev host cannot reach
the wiki and neither can WebFetch.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| A | T43851 ARP Probe · T43853 120-day lease | dhcp-server-2026-10-15T1458 | **DONE** 15:42 — 2 PASS | DUT = DHCP server, VLAN 10, host eth3 as client + ARP responder |
| B | T43852 DHCP Relay · T43850 Option 82 | dhcp-relay-2026-10-15T1458 | RUNNING (dispatched 15:44) | DUT = relay; eth3 client side, eth4 scapy DHCP server. Option 82 is a RELAY feature (TFS S1566.100), not a server one |
| C | T35370 Extended ID · T43854 DNS Relay | dhcp-client-2026-10-15T1458 | RUNNABLE — awaiting dispatch | DUT = DHCP client on VLAN 48; eth4 scapy server, eth3 the querying host for DNS |

**Triage 2026-10-15 15:10 — 6 runnable, 0 blocked by topology, 0 blocked otherwise.** No
recabling, no partner switch, no licence. swi_b and swi_a are not needed by any of the six, which
sidesteps OPEN-1. Re-cut from 2 groups to 3 because the DUT cannot be server, relay and client at
once and STANDING-ORDERS §6 sets bench setup once per TestSet.

**TPS rows, verbatim — all six priority 1 / Yes**, so none may be graded UNSUPPORTED without DUT
evidence, and a Yes whose command is absent on the DUT is a FINDING:
row 25 DHCP 120-day lease → T43853 · row 26 Option 82 → T43850 · row 27 DHCP ARP Probe → T43851 ·
row 28 DHCP Relay → T43852 · row 29 DNS Relay → T43854 · row 30 Extended ID → T35370.

**Steps are grounded in functional specs**, not reconstructed: `DHCP ARP Probe TFS` (S1566.1.x),
`DHCP Option 82 Remote ID TFS` (S1566.100.x), `DNS Relay TFS` (S1570.1.x), the `DHCP` feature page
and the AW+ CLI command pages. Cached on the box at `/tmp/dhcp-2026-10-15T1458/`.
Feature Overview Guides (PDF) are at the repo root in `Feature Overview Guides/`.

Common setup for all three groups: `tb eth3 → swi_d port1.0.10` = VLAN 10, SVI 192.168.10.1/24;
`tb eth4 → swi_d port1.0.48` = VLAN 48, SVI 192.168.48.1/24. Both links measured present.
**Restore both ports to untagged VLAN 1** or the post-run probe will not MATCH — its host-MAC
discovery depends on exactly those ports.

## Group A bench setup and restore recipe (written before the first case, 2026-10-15)

**If this tester dies mid-group, a fresh tester restores the DUT with the RESTORE block below.**
Only swi_d (/dev/u2 @115200) is touched by Group A. swi_b and swi_a are not used at all.

Scratch on the box: `/tmp/dhcp-2026-10-15T1458/` (tools copy + console transcripts + captures).

### Pre-existing baseline (what "restored" means)
DUT swi_d at **default config plus `lldp run`** (the probe added `lldp run` by design on
2026-10-15T0129; it is in the baseline, not drift). Boot config default, boots
`flash:/x960-tb277.rel`. Byte-exact pre-case copy:
`tb277/x960/dhcp-server-2026-10-15T1458/T43851/work/rc-before.log`.

### SETUP (applied once for the whole group, STANDING-ORDERS §6)
```
clock set <HH:MM:SS> <DD> <MON> <YYYY>          # exec-only; DUT RTC reads year 2000. Pre-change
                                                # value recorded in the working log first.
configure terminal
 vlan database
  vlan 10 name ckdhcp-client
  exit
 interface port1.0.10
  switchport access vlan 10
  exit
 interface vlan10
  ip address 192.168.10.1/24
  exit
 service dhcp-server
 ip dhcp pool CKPOOL
  network 192.168.10.0/24
  range 192.168.10.100 192.168.10.110
  lease 1 0 0
  probe enable
  probe type arp
  probe timeout 1000
  probe packets 3
  exit
 exit
```
Host side: `tb eth3` (→ swi_d port1.0.10) is the scapy client and ARP responder. No host IP,
route or mount change is made — every flow is crafted at layer 2, so `sudo` is needed only for
raw sockets.

### RESTORE (run this to put the bench back)
**Boot pointer FIRST** — added 2026-10-15 15:38, after T43853's persistence check set
`boot config-file flash:/ckdhcp.cfg`. A tester that dies mid-group and is restored only by the
config block below would otherwise leave the DUT booting a TEST config (/orient-dt §7).
The pre-existing baseline is `flash:/default.cfg`.
```
configure terminal
 boot config-file flash:/default.cfg
 end
show boot                 # must read: Current boot config: flash:/default.cfg (file exists)
delete flash:/ckdhcp.cfg  # decided: DELETE it (it is a copy of a test config, not a baseline,
                          # so unlike the 2026-10-12 OPEN-6 precampaign.cfg it is worth nothing)
```
A direct copy back onto `default.cfg` may be refused with
`% Cannot overwrite flash:/default.cfg as it is the default config file` (seen on the previous
DUT, handover OPEN-6). That is expected, not a failure: `default.cfg` is never written here, only
re-pointed to, so the refusal should not arise at all.

```
configure terminal
 no ip dhcp pool CKPOOL
 no service dhcp-server
 interface vlan10
  no ip address
  exit
 no interface vlan10
 interface port1.0.10
  switchport access vlan 1
  exit
 vlan database
  no vlan 10
  exit
 exit
```
Then verify: `show running-config` must diff clean against `rc-before.log` (tools/rcdiff.py),
`show ip dhcp pool` must be empty, and **port1.0.10 must be back in untagged VLAN 1** or the
post-run `bench_probe.py` will not exit 0 MATCH — its host-MAC discovery uses that exact port.
Nothing is written to startup-config at any point, so a power-cycle of outlet 1 on
10.36.230.212 is also a valid last-resort restore.

## Group B bench setup and restore recipe (written before the first case, 2026-10-15)

**If this tester dies mid-group, a fresh tester restores the DUT with the RESTORE block below.**
Only swi_d (/dev/u2 @115200) is touched. swi_b and swi_a are not used.
Scratch on the box: `/tmp/dhcp-2026-10-15T1458/`.

### Pre-existing baseline (what "restored" means)
Identical to Group A's: DUT at default config **plus `lldp run`** (bench_probe's by-design
addition — baseline, not drift). Boot config `flash:/default.cfg`, boots
`flash:/x960-tb277.rel`. Group A's teardown was verified CLEAN against it and the post-run probe
exited 0. Byte-exact copy: `dhcp-server-2026-10-15T1458/T43851/work/rc-before.log` (still the
reference for this group — the baseline has not moved).

### Roles
DUT swi_d = **DHCP relay**. tb eth3 (00:0d:b9:55:77:0e) → port1.0.10 = the **client** side.
tb eth4 (00:0d:b9:55:77:0f) → port1.0.48 = the **server** side, running `tools/dhcp4.py server`.
Both host NICs are driven at layer 2 only; no host IP, route or mount change is made.

### SETUP (applied once for the whole group, STANDING-ORDERS §6)
```
configure terminal
 vlan database
  vlan 10 name CKCLIENT
  vlan 48 name CKSERVER
  exit
 interface port1.0.10
  switchport access vlan 10
  exit
 interface port1.0.48
  switchport access vlan 48
  exit
 interface vlan10
  ip address 192.168.10.1/24
  ip dhcp-relay server-address 192.168.48.2
  exit
 interface vlan48
  ip address 192.168.48.1/24
  exit
 service dhcp-relay          # enabled by default; stated so the control can turn it OFF
 end
```
`ip dhcp-relay agent-option` is **disabled by default**, so T43850's baseline-OFF control is
free and must be measured BEFORE anything is enabled.
The scapy server answers ARP for 192.168.48.2 itself (`dhcp4.py server --arp-for`), so no static
`arp` entry is configured on the DUT. If the relay ever fails to resolve the server, add
`arp 192.168.48.2 000d.b955.770f port1.0.48` on the DUT and record it.

### RESTORE (run this to put the bench back) — boot pointer FIRST
A persistence reload, if one is done, is staged on a SEPARATE boot file exactly as Group A did;
`flash:/default.cfg` is never written to. Restore the pointer before removing any config:
```
configure terminal
 boot config-file flash:/default.cfg
 end
show boot                  # must read: Current boot config: flash:/default.cfg (file exists)
delete flash:/ckrelay.cfg  # only if the persistence reload was staged; it is a test config,
                           # worth nothing, so it is deleted rather than left undocumented
```
Then the config:
```
configure terminal
 interface vlan10
  no ip dhcp-relay server-address 192.168.48.2
  no ip dhcp-relay agent-option checking
  no ip dhcp-relay agent-option remote-id
  no ip dhcp-relay agent-option
  no ip address
  exit
 interface vlan48
  no ip address
  exit
 interface port1.0.10
  switchport access vlan 1
  exit
 interface port1.0.48
  switchport access vlan 1
  exit
 vlan database
  no vlan 10
  no vlan 48
  exit
 end
```
**Do NOT use `no interface vlan10` / `no interface vlan48`** — AW+ refuses it
(`% Removal of interface not allowed`, measured in Group A). A VLAN interface disappears when
the VLAN is deleted from the vlan database, which the block above does. A stop-on-error driver
that hits the refusal **skips every command after it** and leaves the bench half-restored.

Verify: `show running-config` must diff CLEAN against the baseline (tools/rcdiff.py), and
**BOTH port1.0.10 and port1.0.48 must be back in untagged VLAN 1** — the post-run
`bench_probe.py` discovers `tb eth3 → swi_d port1.0.10` and `tb eth4 → swi_d port1.0.48` by
host-MAC learning on exactly those two ports, so it cannot exit 0 otherwise.
Nothing is written to startup-config, so a power-cycle of outlet 1 on 10.36.230.212 is also a
valid last-resort restore.

## Known bench notes

- **The DUT is at default config**, so every group builds its own setup from scratch.
- **swi_a holds no config across a reboot** (`show boot` → `default.cfg (file not found)`, empty
  flash, netboots). Carried from the 2026-10-12 handover as OPEN-1. Any case using swi_a must
  reconfigure it after any reload.
- **The DUT's clock reads year 2000** (`Sat Mar 25 2000` at probe). Same RTC fault the previous
  unit had, so it looks like a model trait. Repair it with `clock set` (exec-only, no
  running-config footprint) before the first case and record the pre-change value.
- **`tools/tb` does not work on tb277**: it invokes the box's `python3` (3.6) and
  `bench_probe.py` dies with `TypeError: __init__() got an unexpected keyword argument
  'capture_output'`. Use `python3.8` explicitly for every tool on this box. Logged as I-1.
- Occupancy 2026-10-15 14:58: u2, u3, u5 all **free**; the only FOUND item is the box-wide
  `ser2net` (pid 744), which maps only `ttyS0`/`ttyS1` and holds no USB console — cleared by the
  Test Engineer on 2026-10-07 and run over by 13 cases since.

## Results

| case | verdict | reason | graded by | working log |
| --- | --- | --- | --- | --- |
| T43851 | PASS | ARP probing honoured on the wire: 3 probes at the configured 1000 ms spacing; **0** probes when disabled and when `probe packets 0`; an answered probe withholds the address and records a conflict binding (empty ClientId); `no` forms restore the TFS defaults. Frame-level evidence in 7 pcaps, not a `show` read-back. Two TFS-wording observations (O-1, O-2), neither a functional failure | tester | dhcp-server-2026-10-15T1458/T43851/work/run1.log |
| T43853 | PASS | opt51 = **10,368,000 s** in both OFFER and ACK; binding expiry exactly 120 days out (15 Oct 2026 → 12 Feb 2027); parser **accepts 120, refuses 121 and 999** — that boundary IS the 30→120 day feature; 1-day (86,400) and 1-hour (3,600) controls measured in the same run as in-place overwrites; `no lease` restores the 1-day default; settings survive a reboot, re-proven on the wire (3-probe ARP burst at 0.995/1.001 s). **No M2-shaped silent discard for `lease`** — the pool read agreed with the wire at every point | tester | dhcp-server-2026-10-15T1458/T43853/work/run1.log |

## Issues

Status: OPEN (waiting on the Test Engineer), CHOSEN (a blocker; recommendation applied for
review), NOTED (no decision needed now), CLOSED (decided or answered).

- **I-1 `tools/tb` is broken on tb277** — runs the box's python3.6. NOTED; use `python3.8`.
  Worth fixing in the wrapper so the next session does not rediscover it.
- **I-2 Case steps are not available from AWPTCM or ck.db.** Grounded in the TPS, the Feature
  Overview guide and the Test Strategy instead (above). Every verdict must say so, and cite the
  TPS row it rests on. NOTED.
- **I-3 The sentinel watches every testbox, not just this one.** `sentinel.sh` reads the
  framework's per-device logs under `/home/st-art/pytest-create/*/*/`, which is on the SHARED
  lab home (`10.36.250.11:/home`), so a watch on tb277 also replays tb470's runs. On the first
  arm (2026-10-15 15:00) that dumped ~11 MB of 2026-10-08→13 backlog — stale tb470 IE520 and
  x230v2 framework logs and week-old tb277 console transcripts — straight into the sentinel's
  context before a single case had run, and the harness suppressed events for rate. Fixed for
  this session by stopping the watch, letting the pass baseline 415 remote offsets at EOF, and
  re-arming. **The kit should scope the remote glob to this box's own runs, or baseline silently
  on a first arm.** NOTED — worth fixing in `.claude/skills/orient-dt/sentinel/sentinel.sh`.
- **O-1 (T43851) Conflict recovery is per-DISCOVER, not automatic.** S1566.1.04 says the server
  "will repeat this whole process for the next available address" after a probe conflict.
  Measured: it abandons the address (binding with an EMPTY ClientId), sends nothing further for
  that DISCOVER, and serves the next address only when the client re-DISCOVERs. Stock ISC
  behaviour, harmless with any RFC 2131 client. **Candidate spec clarification, not a defect** —
  the Test Engineer's call.
- **O-2 (T43851) `probe type ping` ARPs first and escalates.** S1566.1.01 says the server waits
  for a response "to the ARP Request or ICMP Echo Request". Measured under `probe type ping`: an
  ARP response alone did NOT stop the offer — the DUT escalated to ICMP, got no echo reply, and
  offered the address. Only the ICMP echo reply withheld it. **Consequence for any future
  campaign: "ping probing produces no ARP" is NOT a valid discriminator between the two probe
  types.** The real pair is ARP-answered + ICMP-unanswered (offered) vs ICMP-answered (withheld).
  Belongs in `platforms/x960.md` at wrap. Candidate spec clarification, not a defect.
- **I-4 Root-owned capture files in case folders.** tcpdump under `sudo` wrote T43851's pcaps as
  `root:root` inside `work/`. `/create-logs` finishes by `git rm -r`-ing `work/`, and memory
  `unattended-session-stalls-on-permission-prompt` records this repo losing 11 hours to exactly
  that `rm`. Tester asked to chown existing captures and to use `tcpdump -Z $(whoami)` from here
  on. NOTED — worth making a standing rule if it recurs.

## Carried from Group A into Groups B and C (measured 2026-10-15)

- **🔥 `no interface vlan10` is REFUSED on AW+** — `% Removal of interface not allowed`. In Group A
  this stopped `cfg.py` mid-batch and left the bench **half-restored** until the remainder was
  re-sent. A VLAN interface goes when the VLAN is deleted from the vlan database, not by removing
  the interface. **Fix this in Groups B and C restore recipes BEFORE they run.**
- **Reload is fast on this x960: login after ~60 s**, against `ckreload.py`'s IE520-derived 720 s
  default. Budget accordingly rather than waiting out the default.
- **The DUT clock survives a reload** — the year-2000 reading at probe time was stale RTC state,
  not a per-boot reset. No need to re-repair after each reboot.
- **For T35370 "Extended ID" (Group C):** the DUT's default config already carries
  `interface vlan1 / ip address dhcp` with **`ip dhcp-client vendor-identifying-class`** and
  **`ip dhcp-client request vendor-identifying-specific`** — DHCP **options 124/125**. That is a
  stronger candidate for what "Extended ID" means than the triage reading of
  `client-id <interface>`, and it is already on the box to probe.
- **Root-owned files were 15, not just the pcaps** — `dhcp4.py --json` also ran under sudo. All
  chowned, scratch swept, zero remain. Keep using `tcpdump -Z $(whoami)` and chown after any
  sudo-run tool (I-4).
