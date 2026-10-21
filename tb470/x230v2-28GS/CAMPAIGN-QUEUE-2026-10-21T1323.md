# Campaign queue — tb470, x230v2-28GS as the DUT, 6 AWPTCM platform/port cases (AR4050S = link partner), from 2026-10-21 13:23 NZDT

The ask, Test Engineer 2026-10-21 13:1x (after `/orient-dt tb470` and the question *"how many of these can we execute
without further topology changes"* over a Zephyr screenshot of 18 Not-Executed x230v2 cases): *"yes, please execute
those six"* — the six the triage answer named as runnable on today's bench: AWPTCM-T47226 check for sh version,
AWPTCM-T47227 check for sh license, AWPTCM-T47215 sh sys environment, AWPTCM-T46421 Link flap, AWPTCM-T47208 Copper
pluggable with supported speeds, AWPTCM-T47210 MAC/Phy TLV with combination of user defined speed, duplex.

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-21 13:23 NZDT (Test Engineer's answers to the setup questions):
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u0,u1 (u0 = AR4050S swi_e, the link partner; u1 = x230v2-28GS swi_f, the DUT). No other console exists on tb470 today (u2-u9 absent).
PDU: "No PDU / do not power-cycle" (Test Engineer, 13:2x). tb470.static's outlets (u0=3, u1=4) are not disputed, they are simply not to be used: the probe runs without `--pdu`/`--outlet`, and no case power-cycles anything.
Constraints: "None: reloads allowed now" (option text: office hours; none of the six cases needs a reload or PDU cycle). Sentinel stand-down: when the run ends (hard stop 17:30). Host: VS Code (risk accepted). The parallel session on tb101 is out of scope.

Test Engineer's rulings carried into this campaign (2026-10-21):
- The `Unexpected System reboot` entries on the x230 dated 2026-10-19/20 are his unplugging. *"if there are any more, notify me."* (from the 08:35 campaign; still stands)
- Earlier verdicts for these cases exist in the repo (10-09/10-13 campaigns) but Zephyr shows them Not Executed; this run is a fresh execution on the current build (x230 awplus_main-20261019-75), not a re-grade.

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  The final log is made ONLY by `/create-logs`, on the Test Engineer's request.
- `STANDING-ORDERS.md` applies, §8 health reads included. No PDU use this session (session fact above).
- **Only u0 and u1 are touched.** Nothing else is on tb470's consoles today.
- Case texts: Ask-CK `ck.db` table `zephyr_cases` (read-only: `sqlite3 'file:<path>/ck.db?mode=ro'`), key `AWPTCM-T<n>`.
  T46421 "Link flap": precondition "conduct link flap at supported speed and check status", no objective. T47208 and T47210: no
  objective/precondition text in ck.db; read their steps. T47226/T47227/T47215 are show-command checks.
- MANUAL-ONLY.md (repo root) is read at triage. None of the six is listed there.
- Platform traps: [platforms/x230v2-28GS.md](../../platforms/x230v2-28GS.md) (all 28 ports SFP cages; `show cpu` prints busy %;
  SPTXa vs the 4050 drives 10/100/1000; `duplex half` refused at 1000).
- Prior evidence on tb470: `tb470/x230v2-28GS/ports-2026-10-09T0845/` (T46421, T47208, T47210 PASS) and
  `tb470/x230v2-28GS/platform-2026-10-09T0845/` (T47226, T47227, T47215 PASS) — read for method, never for the verdict.

## Bench at queue creation (2026-10-21 12:25–13:20, probe `2026-10-20T232516Z`, MATCH, no advisories)

- u0 AR4050S swi_e S/N A10401G214000005, awplus_main-20261008-57, bootloader 5.2.8, boots `flash:/AR4050S-awplus_main-20261008-57.rel`
  + `flash:/tb470-bench.cfg`; flash 3.4 GB free; USB stick mounted; AMF enabled, network name Not Set, 1 node.
- u1 x230v2-28GS swi_f S/N A10783G262900002, awplus_main-20261019-75, bootloader 6.2.40, boots `flash:/x230v2_28GS-awplus_main-20261019-75.rel`
  + `flash:/tb470-bench.cfg`; flash 60.6 MB free; port1.0.7 admin down (saved). Newest Unexpected System reboot 2026-10-19 22:30:23 (its UTC clock).
- **The only link: swi_e port1.0.2 (copper, access VLAN 10) <-> swi_f port1.0.1 (AT-SPTXa 1000BASE-T copper SFP; trunk, `switchport atmf-link`), LLDP both ends.**
  `show system pluggable` on the x230 lists ONLY port1.0.1: every other cage is empty. The 4050 lists no pluggable.
- tb470 eth1/eth2/eth3 carrier DOWN: no host NIC reaches either unit. No scapy traffic possible this campaign; none of the six needs it.
- Lock files LCK..u0/LCK..u1 removed 13:0x (Test Engineer); precheck CLEAR at 13:23.
- Clocks: the x230 reads 13 h behind the 4050 (UTC-like); its `show reboot history` is in that clock.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | platform + ports: T47226 (sh version), T47227 (sh license), T47215 (sh sys environment), T46421 (link flap), T47208 (copper pluggable speeds), T47210 (MAC/PHY TLV vs speed/duplex) | tb470/x230v2-28GS/platform-ports-2026-10-21T1323/ | RUNNING (from 2026-10-21 13:4x, bench-runner) | manual CLI on u1 (DUT) with u0 as the link partner / LLDP decoder; the three show cases first (read-only), then the three port cases on the one link port1.0.1 <-> 4050 port1.0.2; no PDU, no reload expected; restore the link to auto/1000-full and LLDP after each port case |

### Group setup and exact restore recipe (written at triage 2026-10-21 13:3x by bench-runner, before any device change)

Pre-run baseline, measured (probe `2026-10-21T002632Z` MATCH; capture `bench-setup/captures/2026-10-21T002632Z/`):
- u1 x230 `port1.0.1`: `connected trunk a-full a-1000 1000BASE-T`; running-config stanza = `switchport` / `switchport mode trunk` /
  `snmp trap link-status` / 2 `rmon collection history` lines / `switchport atmf-link`; NO `speed`, NO `duplex`, NO `lldp tlv-select` lines.
  `lldp run` global. `show system pluggable` lists ONLY 1.0.1 (ATI AT-SPTXa A04906R191400072, 1000BASE-T). `port1.0.7 shutdown` is saved baseline: leave it.
- u0 4050 `port1.0.2`: `connected 10 a-full a-1000 1000BASE-T`; stanza = `switchport` / `switchport mode access` / `switchport access vlan 10`;
  NO `speed`/`duplex`/`lldp tlv-select` lines. `lldp run` global.
- Both: `show boot` -> `Current boot config: flash:/tb470-bench.cfg (file exists)`. Nothing in this group changes it; no `write` at any point.

Setup the port cases add (running-config only, never saved):
- T47210 only: `lldp tlv-select mac-phy-config` on u1 `interface port1.0.1` AND on u0 `interface port1.0.2` (so each end's 802.3 MAC/PHY TLV is readable
  at the other with `show lldp neighbors detail`).
- T47208 / T47210: `speed …` / `duplex …` under u1 `interface port1.0.1`, and for the fixed-speed combos the matching `speed`/`duplex` under u0
  `interface port1.0.2`. T46421: `shutdown` / `no shutdown` on u1 `port1.0.1` (local flaps) and on u0 `port1.0.2` (remote flaps). The three
  show cases change nothing.

Restore, after EACH port case (the next case starts from the baseline above), all on the console, then verified:
```
u1 (x230):  configure terminal / interface port1.0.1 / no speed / no duplex / no lldp tlv-select mac-phy-config / no shutdown / end
u0 (4050):  configure terminal / interface port1.0.2 / no speed / no duplex / no lldp tlv-select mac-phy-config / no shutdown / end
both:       terminal no monitor (exec, after `end`)
```
- `no speed` returns the port to `speed auto` (all rates advertised) and `no duplex` to `duplex auto`; status must read `connected ... a-full a-1000`
  on both ends within ~5 s, and `show lldp neighbors` must list the peer again on both ends (LLDP re-learns inside one Tx interval, 30 s max).
- Proof: `show running-config` on each unit diffed against the pre-run capture (`tools/rcdiff.py`, or the probe's capture file) must be
  byte-identical apart from the header's time stamp. `show boot` still `flash:/tb470-bench.cfg` on both. The final probe (same facts) must read MATCH.
- Never: `write`, `boot config-file`, `reload`, a PDU command, any `/dev/uN` other than u0/u1, any change to `switchport atmf-link` or VLANs.
- If a session dies mid-case: run the two restore blocks above as written, then the proof; a port left `shutdown` or at a forced speed is the
  only state this group can leave behind.

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| T47226 | check for sh version | platform-ports-2026-10-21T1323 | PASS | show version answers in full (AlliedWare Plus 0.0.0 10/19/26, Build name x220-awplus_main-20261019-75.rel, expected x220 target name); health clean | platform-ports-2026-10-21T1323/47226/work/run1.log | tester |
| T47227 | check for sh license | platform-ports-2026-10-21T1323 | PASS | show license lists Base License (Full, 11 features) and ACCESS (Full), no error line; health clean | platform-ports-2026-10-21T1323/47227/work/run1.log | tester |
| T47215 | sh sys environment | platform-ports-2026-10-21T1323 | PASS | show system environment Overall Status Normal, fan + 5 voltages + 3 temperatures all Ok within limits; health clean | platform-ports-2026-10-21T1323/47215/work/run1.log | tester |

## Issues

