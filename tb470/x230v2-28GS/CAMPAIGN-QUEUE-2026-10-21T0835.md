# Campaign queue — tb470, x230v2-28GS as the DUT, 2 AWPTCM ATMF cases (4050 = AMF master), from 2026-10-21 08:35 NZDT

The ask, Test Engineer 2026-10-21 08:3x (after `/orient-dt`):
*"today we will be running two ATMF tests, with the 4050 being the ATMF master."* Screenshot: AWPTCM-T28218 (1.0)
ATMF provisioning, AWPTCM-T46810 (1.0) ATMF Backup. *"The parallel session will remain on tb101, that is out of our
scope. we will be on tb470 today running those x230v2 tests."*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-21 08:35 NZDT (Test Engineer's answers to the setup questions):
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u0,u1 (u0 = AR4050S swi_e, the AMF master; u1 = x230v2-28GS swi_f, the DUT). No other console exists on tb470 today (u2-u9 absent).
PDU: 10.36.150.14, u0=3, u1=4 (per tb470.static, applied by the Test Engineer 2026-10-21 08:3x)
Constraints: "Reloads allowed now" (option text: "The two cases may reload / power-cycle the x230 and the 4050 as their steps need, during office hours."). Sentinel stand-down: "When the run ends". Host: "Stay in VS Code" (risk accepted). The 4050 is the ATMF master (Test Engineer). The parallel session on tb101 is out of scope.

Test Engineer's rulings carried into this campaign (2026-10-21):
- The `Unexpected System reboot` entries on the x230 dated 2026-10-19/20 are his unplugging ("i unplugged it a few times"). *"if there are any more, notify me."*

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  The final log is made ONLY by `/create-logs`, on the Test Engineer's request.
- `STANDING-ORDERS.md` applies. Reloads and PDU cycles of u0/u1 are allowed within a test; a systematic failure stops the run.
- **Only u0 and u1 are touched.** Nothing else is on tb470's consoles today.
- Case texts: Ask-CK `ck.db` table `zephyr_cases` (read-only: `sqlite3 'file:<path>/ck.db?mode=ro'`), key `AWPTCM-T<n>`.
  T28218 has 5 steps (provision node "future_node", create its directory on the backup media, copy + set the release
  file, copy + set the config file, `show atmf provision nodes`). **T46810 has NO steps and no objective in ck.db**
  (one empty step; folder "/5.5.5-2/Gomboc/Project:ER-7243 ..."): triage reports it as blocked otherwise unless the
  Test Engineer defines what to run.
- MANUAL-ONLY.md (repo root) is read at triage.
- Platform traps: [platforms/x230v2-28GS.md](../../platforms/x230v2-28GS.md). AMF memories: `ie520-master-ignores-remote-backup-server`
  (the AR4050S's FULL licence carries AMF-MASTER; `atmf master` took on it 2026-09-23; the x230-10GP could not be master),
  `atmf-recovery-residue-and-reboots`. Prior ATMF evidence on tb470: `IE520/atmf-2026-09-21/` (README, TOPOLOGY, 38479 =
  provisioning capture) and `IE520/atmf-2026-09-23/`.

## Bench at queue creation (2026-10-21 08:27-08:33, probe `2026-10-20T192716Z`, MATCH after the Test Engineer's apply)

- u0 AR4050S swi_e S/N A10401G214000005, awplus_main-20261008-57, bootloader 5.2.8, boots `flash:/AR4050S-awplus_main-20261008-57.rel`
  + `flash:/tb470-bench.cfg`; flash 3.4 GB free; **a USB stick is mounted (`usb:` 28.9G, Avail Y)** = candidate AMF backup media; uptime 5 d 17 h.
- u1 x230v2-28GS swi_f S/N A10783G262900002, awplus_main-20261019-75, bootloader 6.2.40, boots `flash:/x230v2_28GS-awplus_main-20261019-75.rel`
  + `flash:/tb470-bench.cfg` (saved 10-19 22:31 on its clock); flash 60.5 MB free (one 36.7 MB .rel); no USB; uptime 20 h 58 m.
- Link swi_e port1.0.2 <-> swi_f port1.0.1 (LLDP both ends). tb470 eth1/eth2/eth3 all carrier DOWN. Lock files `LCK..u0`/`LCK..u1`
  on tb470 are stale (PIDs dead, 2026-10-20 08:44); fuser shows no holder.
- Clocks: the x230 reads 13 h behind the 4050 (UTC-like); its `show reboot history` is in that clock.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | ATMF: T28218 (provisioning), T46810 (backup) | tb470/x230v2-28GS/atmf-2026-10-21T0835/ | QUEUED | manual CLI; 4050 (u0) = AMF master, x230 (u1) = AMF member/DUT; backup media on the 4050 (USB present) unless triage says otherwise; T46810 needs a definition from the Test Engineer (no steps in ck.db) |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

