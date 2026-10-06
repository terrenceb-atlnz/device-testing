# Campaign queue — tb470 x230v2-28GS, AWPTCM 5700 bootloader suite on bootloader 6.2.40, from 2026-10-06 13:25 NZDT

Terrence, 2026-10-06: *"we want to run the base script (unedited, not IE520 specific), because the
output should be nominal. It will be for the 6.2.40 bootloader testing, for the x230v2-28GS. i have
put a directory in root for you to use."* → *"go"* (13:2x).

The ask: run the **pristine** 5700 suite (`test-5700.2001`–`2005`, `library_5700.py`,
`runTestSuite.py`, byte-identical to `claude/raw-data/test_scripts/5700_bootloader/`, md5-checked)
against the x230v2-28GS on u0 with **bootloader 6.2.40**. The control is the Feb 2026 x230v2 run in
that raw-data directory (AT-x230-18GT V2, bootloader 6.2.37, build awplus_main-20260218-1237).
History: memories `bootloader-media-parse-bug`, `x230v2-5700-control-corpus`,
`run-attribution-5700-campaign`; the IE520 adaptation is `IE520/automated-bootloader/` (edited, NOT
used here).

Shape: ONE session (orient-dt §10 A, `/test-mode`): this session is the sentinel, `bench-runner`
subagents are the tester.

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-06 13:25 NZDT. These are the Test Engineer's answers, word for word where given:
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470 (this host's default and the last test bench run)
Consoles: u0 only (x230v2-28GS, S/N A10783G262900002, swi_a in this run's setup)
PDU: 10.36.150.14, outlet 1 (u0)
Constraints: "do not interact with any other devices yet" (u0 + its PDU outlet 1 only). Sentinel stands down "When the run ends". Host session: "Stay in VS Code" (risk accepted).

Answers given 2026-10-06 ~12:55–13:20 NZDT:
1. Console baud: *"its now 9600"* (bootloader and AW+).
2. Framework: *"can you update my framework to match the box's?"* → the run uses tb470's
   `/home/st-art/framework` (a5bb6a1, 2026-10-05) via the run dir's `framework` symlink; the
   DeviceSkrips clone was fast-forwarded to the same commit.
3. Release under test: *"the 28GS boots way faster than the IE520, shouldnt be an issue. accept the
   swap."* The suite TFTPs `/tftpboot/x230v2_28GS-tb470.rel`, which the nightly replaces ~08:49
   (it held `awplus_main-20261006-51` at launch).
4. 2002.30's random foreign release may delete/replace `/tftpboot/IE360-tb470.rel` or
   `IE560-tb470.rel`: *"i accept the collateral, those are gone now anyway"*.
5. Run dir: *"please change it how you need to."* → `x230v2-28GS/bootloader-6.2.40/` (was
   `bootloader 6.2.40`), runner dir `5700_x230v2-28GS_6.2.40/` inside it.
6. Media: *"SD card is unsupported, we dont have an SD card slot. as before, we have one USB location
   so we are using a hub to have both the tftp eth and the usb stick."* Hub USB-eth adapter on
   **tb470 eth2** (bootloader TFTP); *"eth3 is on port1.0.1 now"* (post-boot CLI transfers);
   USB stick in the hub (holds `x230-2.rel` + both `.kwb`).
7. *"it doesnt fit 3 .rels on flash."* *"ive finished the .kwb swaps, dont worry about that."*

Notes from the session (sentinel), measured:
- u0 13:03–13:15: `AT-x230-28GS V2` board 706, bootloader **6.2.40**, software `awplus_main-20261006-51`
  (`x230v2_28GS-tb470.rel`), 9600 baud; flash 95.6 MB (27.3 MB free; `x230-2.rel` +
  `x230v2_28GS-tb470.rel`); `usb:` 28.8 GB; `nvs:` present (91 KB — Feb's NVS case was UNSUPPORTED).
- eth3 carrier up, its MAC `00f0.4d00.7718` learned on u0 port1.0.1 (1000/full). eth2 carrier down
  between boots (dongle).
- tb470 rebooted 2026-10-06 12:43 (uptime): `/tmp` wiped, runtime routes gone; `/nfsHome`, `/tftproot` fine.
- Other users on tb470 at 13:00: calanm (minicom on u2 and u4), maxj. Not ours; never touch.

Triage 2026-10-06 13:28–13:55 (bench-runner; sentinel-verified where marked):
- **Release prefix:** the box framework maps board `AT-x230-28GS V2` → family `x230` (no table entry;
  `ATSwitch.get_family_name_from_board_name`, the generic rule; no `x230v2_28GS` anywhere in the framework).
  So every bootloader TFTP boot/recovery asks for `/tftpboot/x230-tb470.rel` (absent); configure's flash
  download uses `x230v2_28GS-tb470.rel` (present). OPEN — Test Engineer's decision.
- **`/tftproot` is tmpfs** (sentinel `df`, 14:0x): the 12:43 reboot wiped it; it now holds only
  IE520-tb470.rel + x230v2_28GS-tb470.rel (12:46/12:49; .info says -52).
- **6.2.40 TFTP prompt** (menu 1 → Select device 3, read 13:50): `Note: TFTP downloads will be performed via
  the USB Ethernet adapter.` → `Enter IP version [4|6]`. No port/interface prompt → the hub/eth0 setup
  as written is right. Cancelled (Ctrl-C, 0, 9); nothing saved deliberately.
- **Forced-boot banner** on that boot: `Warning: System has been forced to boot from a non-standard
  location` … `Reading flash:x230v2_28GS-tb470.rel`. Pre-existing or not is unknown. OPEN — a saved
  Flash+file default ignores `boot system`, which 2001's configure relies on.
- **Licence:** run will `license ACCESS` (unit has Base only): *"Yes, allow ACCESS"* (Test Engineer, ~14:00).

## Expected, not 6.2.40 findings (decided before launch)

- **SD card cases** (Feb 2002 .1/.21 + card: cases): no slot → UNSUPPORTED.
- **2002.110**: pristine `NameError: name 'copy'` (`library_5700.py:227`, `copy` never imported). Failed in Feb too. Script bug.
- **Third `.rel` on flash** (`library_5700.py:1406` copies MAIN_RELEASE to a new name): does not fit
  95.6 MB flash with two 36.5 MB releases. A FAIL there is flash capacity.
- **2003.11 Erase FLASH / 2005 security-level reset** erase flash: expected and accepted.
- Framework drift: the scripts are Jan 2026; the framework is 294 commits newer than the Feb run's
  (`d4c21f7`). A harness break is compared against `d4c21f7` before it is called a 6.2.40 result.

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  The final log is made ONLY by `/create-logs`, on the Test Engineer's request.
- **Adaptation for a framework suite:** a "case" here is a **TestSet** (5700.2001 … 5700.2005); the
  per-TestCase verdicts are in the framework's own `test-5700.<set>.log`. The framework holds u0 for
  the whole run, so no tester-captured `.cfg` mid-run; the device config is the framework's
  `default.cfg` + what each case logs in `swi_a_<set>.log`.
- Launch exactly as Feb (minus publish): from the runner dir, as root,
  `./runTestSuite.py -s default.setup -u -v`. **No `-p`.** The scripts are not edited.
- `STANDING-ORDERS.md` applies; §6: the framework's post-failure power cycle (outlet 1) is accepted.
  Stop a run whose failures are systematic (e.g. every case failing at `configure()`).
- Root-owned output on the NFS share is chowned back to terrenceb before commit.
- Framework logs stay where the runner writes them (the runner dir); never re-run in the same dir
  without moving the previous run's logs aside first (the framework overwrites).

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | 5700.2001–2005 (65 TestCases, one `runTestSuite.py` process) | x230v2-28GS/bootloader-6.2.40/5700_x230v2-28GS_6.2.40 | TRIAGE | ~19 h by the Feb timings (2001 31 m, 2002 5 h 24 m, 2003 2 h 45 m, 2004 25 m, 2005 10 h 20 m) |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

