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
- 14:14 u0 logged `AT-SPTX removed from port1.0.3/port1.0.4`: *"I pulled those"* (Test Engineer, 14:15). Not used by the suite.
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
- **Decisions ~14:05 (Test Engineer):** forced-boot banner → *"Restore default (2 → 9)"*; x230-tb470.rel → *"Symlink, I approve"* (`sudo ln -s x230v2_28GS-tb470.rel /tftproot/x230-tb470.rel`, proven with a tftp get; tmpfs, re-create after any tb470 reboot).
- **Re-triage 14:06 (bench-runner):** RUNNABLE 1/1. Bootloader default restored (menu 2 → 9 "Boot from
  default (determined by main CLI)", `Saving settings... Complete`; plain-reload proof: no forced banner,
  `Loading flash:x230v2_28GS-tb470.rel`). Symlink `/tftproot/x230-tb470.rel -> x230v2_28GS-tb470.rel`
  (root, relative), proven by curl tftp: 36,553,967 B, sha256 a22982fc…0b1bbd = source. **Re-create it after any tb470 reboot.**
- **Launch decision ~14:10 (Test Engineer):** *"Prove TFTP, then launch"* — one one-off TFTP boot via the USB
  adapter first (Boot Menu 1 → 3, saves nothing); launch only if it reaches login.
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

## Row #1 — bench setup and restore recipe (bench-runner, 2026-10-06 14:19, before launch)

**Step 0 PASSED (14:12–14:18):** one-off TFTP boot on u0 (Boot Menu 1 → 3; prompts verbatim:
`Enter IP version [4|6].................. [4]:` → 4; `Enter IP address for this device........ [10.38.215.40]:`
→ 10.38.215.34; `Enter subnet mask....................... [255.255.255.224]:` → same; `Enter gateway IP........................ [0.0.0.0]:`
→ 0.0.0.0; `Enter TFTP server IP.................... [10.38.215.33]:` → same; `Enter filename.......................... [x230v2_28GS-tb470.rel]:`
→ x230-tb470.rel) → `Loading tftp://10.38.215.33/x230-tb470.rel via USB Ethernet adapter...` → `Verifying release... OK`
→ login, `Current software : x230-tb470.rel`, `awplus_main-20261006-52`. eth2 carrier 14:12:53–14:13:12, tx 37.7 MB.
Plain reload → `Loading flash:x230v2_28GS-tb470.rel...`, no forced banner, -51. Logged out. Evidence: `5700.2001/work/step0-*`.

**Bench setup for the group (set once, by the Test Engineer/triage; nothing changed by the tester):**
u0 x230v2-28GS S/N A10783G262900002, 9600, PDU 10.36.150.14 outlet 1; tb470 eth3 ↔ port1.0.1; tb470 eth2 ↔ USB
Ethernet adapter on the hub (USB stick on the same hub); `/tftproot/x230-tb470.rel -> x230v2_28GS-tb470.rel` (root, tmpfs).
Pre-run baseline (`5700.2001/work/u0-prerun-*`): boot image `flash:/x230v2_28GS-tb470.rel`, boot config
`flash:/default.cfg` (near-factory running-config), bootloader default boot source = 9 "Boot from default (determined
by main CLI)", Boot Security Level none, licence Base only; flash holds `x230-2.rel` + `x230v2_28GS-tb470.rel`.

**Launch:** `sudo -n setsid nohup /tmp/x230/launch_suite.sh` → in the runner dir, as root,
`./runTestSuite.py -s default.setup -u -v > runTestSuite.stdout 2>&1 < /dev/null`; start/end/rc in
`/tmp/x230/run1/suite.{start,rc}`, done-marker `/tmp/x230/run1/suite.done` (tb470 tmpfs).

**Restore recipe (if the tester dies mid-group; u0 and outlet 1 only):**
1. Let any in-flight runTestSuite / PDU cycle finish, or stop it by PID (`ps -o user,lstart,cmd -p <pid>`; it is root).
   Outlet 1 must end ON.
2. u0 console (9600): if parked in the Boot Menu, back out (submenu `0`, main `9`); if the bootloader security level was
   raised (2005), Boot Menu `S` back to level none, as the suite's own tear_down does.
3. Bootloader: Boot Menu `2` → `9` ("Boot from default (determined by main CLI)") if a saved default source shows the
   forced-boot banner.
4. AW+: `boot system flash:/x230v2_28GS-tb470.rel` (copy it back from `tftp://10.38.215.65/x230v2_28GS-tb470.rel`
   over port1.0.1 if 2003.11/2005 erased it), `no boot system backup`, delete the suite's leftover `*.rel`/`*.cfg`
   (mainrelease/backuprelease/copy*, `swi_a_5700_*.cfg`, `TestCase_*.cfg`) but keep `x230-2.rel` on flash, write the
   pre-run running-config (`5700.2001/work/u0-prerun-running-config.txt`) back as `flash:/default.cfg` (the
   framework regenerates default.cfg with hostname `swi_a_5700_<set>` + every port shut), `boot config-file flash:/default.cfg`, reload.
5. Prove: `show boot` = the baseline above, no forced banner, then `exit`. The ACCESS licence stays (Test Engineer allowed it).

## Row #1 run 1 STOPPED (14:58) — and run 2 (bench-runner, 15:20)

**Run 1 stopped at 14:58:43 (rc 143, SIGTERM to runTestSuite 8327 then test-5700.2002 11334, by PID; no power cycle in flight).**
2001 PASS (11/11). 2002 failed systematically at a setup assumption: the pristine suite expects u0's **bootloader default
boot source = TFTP** (Feb's bench: every Feb 2001 boot was `Loading tftp://10.37.101.1/x230v2-tb101.rel via switchport 2...`
with the forced-boot banner, so `Current software` stayed the TFTP file name). With the 14:05 "Restore default (2 → 9)"
u0 booted flash, ended 2001 on `backuprelease.rel`, and 2002's configure (createFlashBootImages → framework
download_file_from_tftp, remote name = swi.software) asked for `tftp://10.38.215.65/backuprelease.rel` → `% Source file not
found` ×2 after deleting flash's releases → no release on flash → 2002.10 `!!FAIL: There is no primary release file set`,
unit restart-looping (`ERROR: Boot failed`), framework stuck in mode('#'). The suite's `recovery()` (2→3) is never called.
2002.1 UNSUPPORTED (no SD), 2002.2 PASS before it. Run 1 logs stay in `5700_x230v2-28GS_6.2.40/`; 2002's are unrenamed
(`swi_a.log`, `test-5700.2002.log`) because the TestSet was killed.

**Recovery (within the test, 15:00–15:11):** one-off TFTP boot (Boot Menu 1 → 3, x230-tb470.rel) → CLI: temporary
`ip address 10.38.215.74/27` on vlan1 (running only), `copy tftp://10.38.215.65/x230v2_28GS-tb470.rel flash:/x230v2_28GS-tb470.rel`
(Successful), `boot system flash:/x230v2_28GS-tb470.rel`, `no boot system backup`, leftover `swi_a_5700_*`/`TestCase_*`
cfgs deleted. **Tester error:** the cleanup also deleted `flash:/default.cfg` while it was the boot config → 15:06 flash
boot loaded factory defaults → forced `% Default password needs to be changed.` (the sentinel caught it). The dialog refuses
`friend` (`% password matches the default password`), so it was passed with the framework-list password `P@ssw0rd`, then
`username manager privilege 15 password friend` restored manager/friend explicitly and `copy running-config
flash:/default.cfg` recreated the boot config. A fresh manager/friend login reached `#` with no dialog. running-config now
= the pre-run capture (only the hash salt differs). Flash: `default.cfg` + `x230v2_28GS-tb470.rel` (36,553,967 B = build
-52 from /tftproot, was -51 pre-run). **`x230-2.rel` is no longer on flash** (run 1's 2001 configure `delete force *.rel`,
suite design); the USB stick holds a copy (session facts).

**Test Engineer, relayed ~15:03:** (1) *"Yes, TFTP default (Recommended)"* — **reverses the 14:05 "Restore default (2 → 9)"**.
Done 15:11: Boot Menu 2 → 3, prompts verbatim `Enter IP version [4|6].................. [4]:` → 4; `Enter IP address for this
device........ [10.38.215.40]:` → 10.38.215.34; `Enter subnet mask....................... [255.255.255.224]:` → same;
`Enter gateway IP........................ [0.0.0.0]:` → 0.0.0.0; `Enter TFTP server IP.................... [10.38.215.33]:` → same;
`Enter filename.......................... [x230v2_28GS-tb470.rel]:` → x230-tb470.rel → `Saving settings... Complete`. Plain-reload
proof 15:14–15:16: `Warning: System has been forced to boot from a non-standard location` → `Loading tftp://10.38.215.33/x230-tb470.rel
via USB Ethernet adapter...` → `Verifying release... OK` → login, `Current software : x230-tb470.rel` (-52); u0 logged out.
(2) *"Whole suite (Recommended)"* in a fresh run dir: `5700_x230v2-28GS_6.2.40_run2/` — pristine copies md5-verified
against raw-data, same `default.setup`, `framework` symlink. Working logs `5700.<set>/work/run2.log`.

**Run 2 gates (15:17):** precheck u0 free (FOUND = calanm u2/u4 + a terrenceb minicom on u3, none ours); read-only probe
MISMATCH = the same swi_a/swi_f naming + hub lines only; `/tftproot/x230-tb470.rel -> x230v2_28GS-tb470.rel` resolves;
tb470 up 2:34 (no reboot), /nfsHome mounted.

**Run 2 baseline / restore recipe** (replaces steps 3–5 above for run 2): bootloader default boot source = **TFTP
x230-tb470.rel** (forced banner expected; keep it unless the Test Engineer says otherwise); flash `x230v2_28GS-tb470.rel`
as `boot system`, `default.cfg` (manager/friend explicit, near-factory) as boot config; Boot Security Level none; ACCESS
licence stays. If the suite leaves u0 without a release or config: one-off/default TFTP boot, copy the release back over
port1.0.1 (vlan1 10.38.215.74/27 temporary), `boot system`, **keep `default.cfg`** (never delete the current boot config),
reload, prove, `exit`.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | 5700.2001–2005 (65 TestCases, one `runTestSuite.py` process) | x230v2-28GS/bootloader-6.2.40/5700_x230v2-28GS_6.2.40 | DONE 20:58 (run 2: suite rc 1; u0 restored to the run-2 baseline 21:07, logged out; RESULT lines sent for 2001–2005) | ~19 h by the Feb timings (2001 31 m, 2002 5 h 24 m, 2003 2 h 45 m, 2004 25 m, 2005 10 h 20 m) |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| 5700.2001 | Boot System CLI rules (11 TestCases) | bootloader-6.2.40 | PASS | run 2 (TFTP default boot, Feb conditions): 11/11 PASS, rc=0, 20 m, identical to the Feb x230v2 control; run 1 (flash default) also 11/11 PASS | 5700.2001/work/run2.log | tester |
| 5700.2002 | default/one-off boot, filenames, foreign release, bootloader version (26 TestCases) | bootloader-6.2.40 | PARTIAL | run 2: 18 PASS / 7 UNSUPPORTED (SD, no slot) / 1 FAIL = 2002.110 pristine NameError (library_5700.py:227, same in Feb, pre-registered); USB variants (unsupported in Feb) all PASS; 2002.120 booted 2 of 3 releases (third .rel doesn't fit flash, pre-registered); no 6.2.40 divergence from Feb. Run 1 PARTIAL (stopped, flash default) superseded | 5700.2002/work/run2.log | tester |
| 5700.2003 | stage-1/2 diagnostics menus (15 TestCases) | bootloader-6.2.40 | PARTIAL | run 2: 11 PASS / 2 UNSUPPORTED (NVS, SD); 2003.11 Erase FLASH PASSED on the device but the framework FAILed the case at its post-erase boot-config reset (`% flash:/swi_a_5700_2003.cfg does not exist`) and ATTestSet skipped 2003.10 — framework commit c1e7679 (2026-09-17, absent from Feb's d4c21f7) moved that reset under doTear; not 6.2.40 | 5700.2003/work/run2.log | tester |
| 5700.2004 | U-Boot access; date reset/set (2 TestCases) | bootloader-6.2.40 | PASS | run 2: 2/2 PASS, rc=0, 17 m (framework 89900a6); assertion counts identical to the Feb control | 5700.2004/work/run2.log | tester |
| 5700.2005 | security levels 2/3, passwords, factory restore (8 TestCases) | bootloader-6.2.40 | PARTIAL | 2005.1 PASS; 2005.2 PASS per the Test Engineer (its device FAIL was only the `Erasing flash` vs `Erasing nand0:` wording; the second FAIL is framework c1e7679's post-erase boot-config reset); 2005.3-.8 NOT RUN (skipped by the framework after 2005.2). Follow-up run: tb470/x230v2-28GS/CAMPAIGN-QUEUE-2026-10-07T0817.md. Final log 5700.2005-fail.log (b60a24c) predates this re-grade | 5700.2005/work/run2.log | Test Engineer, re-graded from FAIL on 2026-10-07 |

## Issues

- **Framework moved mid-run** (tester, ~19:40): `/home/st-art/framework` HEAD went a5bb6a1 → 89900a6 (2026-10-06 17:40) during run 2. Each TestSet is a new python process, so 2004/2005 run on 89900a6 while 2001–2003 ran on a5bb6a1.
- **2003.11 harness FAIL**: framework c1e7679 runs the TestSet boot-config reset under doTear before tear_down; after a deliberate erase it fails and skips 2003.10. Framework behaviour, not 6.2.40.

