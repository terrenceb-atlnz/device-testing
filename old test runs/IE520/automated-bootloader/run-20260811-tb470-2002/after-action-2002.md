# After-action — 5700 suite 2002 (Default / one-off boot), tb470

**DUT:** IE520, S/N `264A23052`, console `/dev/u4`, PDU `10.36.150.14` outlet 4 ("D")
**Software:** `IE520-tb470.rel`, build `IE520-tomahawk_ie520-continuous`, bootloader 9.1.0
**Setup:** `copilot/tb470-u4.setup` · **Run dir:** `copilot/run-20260811-tb470-2002/`
**Window:** 2026-08-11 15:03:09 → 19:33:16 (**4 h 30 m**), `rc = 1`
**Ran alongside** suite 2003 on the second IE520 (`/dev/u5`), concurrently, on the same testbox.

---

## 1. Headline

| | tb504 (2026-08-07) | **tb470 (this run)** |
|---|---|---|
| Duration | 10 h 11 m | **4 h 30 m** |
| PASS | 8 | **18** |
| FAIL | 14 | **1** |
| UNSUPPORTED | 7 | 7 |

**The single FAIL is a test-tooling defect, not a product defect.** No behaviour of the IE520
bootloader failed in this run. All seven UNSUPPORTED are the same cause — this platform has no
SD card slot — and are permanent, not a provisioning gap.

Case 113 (YMODEM one-off boot) is excluded by `testCaseRunPriority = 10`; the source comments it
`# Will take 12 hours at 9600 baud rate`. 26 of 27 cases therefore executed.

---

## 2. Full results

| Case | Description | Verdict | Asserts | Requirement(s) | tb504 |
|---|---|---|---|---|---|
| 1 | SD Card is present | UNSUPPORTED | 2/1 | – | UNSUP |
| 2 | USB Media is present | **PASS** | 3 | – | – |
| 10 | Skip Default config | **PASS** | 8 | AWP2716 | PASS |
| 20 | Filenames `---w-z…` – Flash | **PASS** | 7 | AWP2750, 2751 | PASS |
| 21 | Filenames `---w-z…` – SD Card | UNSUPPORTED | 2/1 | AWP2750, 2751 | UNSUP |
| 22 | Filenames `---w-z…` – USB media | **PASS** | 8 | AWP2750, 2751 | **FAIL** (parser) |
| 30 | Try release for different platform | **FAIL** | 3/1 | AWP2684 | *false PASS* |
| 41 | Boot default off sdcard | UNSUPPORTED | 2/1 | AWP2707 | UNSUP |
| 42 | Boot default off usb | **PASS** | 9 | AWP2707 | **FAIL** (parser) |
| 50 | Boot fails with no release set | **PASS** | 10 | AWP2640 | PASS |
| 60 | Boot with release, same name as cli | **PASS** | 5 | AWP2682 | **FAIL** (parser, started cascade) |
| 61 | …same name as cli – SD Card | UNSUPPORTED | 2/1 | AWP2682 | UNSUP |
| 62 | …same name as cli – USB Media | **PASS** | 3 | AWP2682 | **FAIL** (parser, started cascade) |
| 70 | Check bootloader version | **PASS** | 4 | AWP2718 | **FAIL** (gate string, 30 m) |
| 80 | Restart from boot menu | **PASS** | 3 | AWP2670 | **FAIL** (gate string, 30 m) |
| 90 | Boot from backup (b) | **PASS** | 6 | AWP2654 | **FAIL** (gate string, 30 m) |
| 100 | Test all options for default boot | **PASS** | **20** | AWP2639 +15 more | **FAIL** (cascade) |
| 101 | …default boot – SD Card | UNSUPPORTED | 2/1 | AWP2639 +15 | UNSUP |
| 102 | …default boot – USB Media | **PASS** | 6 | AWP2639 +15 | **FAIL** (parser) |
| 110 | Test all options for one-off boot | **PASS** | 13 | AWP2641 +10 | **FAIL** (cascade) |
| 111 | …one-off boot – SD Card | UNSUPPORTED | 2/1 | AWP2641 +10 | UNSUP |
| 112 | …one-off boot – USB Media | **PASS** | 9 | AWP2641 +10 | **FAIL** (cascade) |
| 113 | …one-off boot – YMODEM | *excluded* | – | AWP2641 +10 | excluded |
| 119 | One-off boot can read all of flash | **PASS** | 3 | CR-82742 | **FAIL** (cascade) |
| 120 | One-off boot can boot from all of flash | **PASS** | 7 | CR-86835 | **FAIL** (cascade) |
| 121 | Boot System to SD Card without backup | UNSUPPORTED | 2/1 | – | UNSUP |
| 122 | Boot System to USB Media without backup | **PASS** | 5 | – | **FAIL** (cascade) |

Total assertions passed: **160**.

---

## 3. The one failure — case 30, AWP2684 (ACTION REQUIRED)

**Verdict: test-tooling defect. The device behaved correctly. AWP2684 still has no trustworthy
verdict — on either bench.**

The case performs a one-off boot of a release built for a different platform (`x540-5.5.3-2.1.rel`
on an IE520) and expects an error. Verbatim device output:

```
Booting image 04000000#IE520-28GSX ...
## Loading kernel from FIT Image at 04000000 ...
Could not find configuration node
ERROR -2: can't get kernel image!
Restarting system in ...  5
```

**The IE520 correctly rejected the foreign release** — it looked for its own `IE520-28GSX`
configuration node in the FIT image, did not find one, and refused to boot. That is exactly the
behaviour AWP2684 exists to verify.

The test could not see it, for two compounding reasons in the gate:

```python
send('1\n', 360, ['Error', 'Verifying release... OK', 'Mounting',
                  'Booting', 'Allied Telesis Inc.', 'Initializing'])
                                    ^ matched "Booting"
```

1. **`'Booting'` matched `Booting image 04000000#IE520-28GSX ...`** — an *attempt* marker printed
   before the load fails, not evidence of success. `send()` returns on first match, so it stopped
   reading immediately before the error arrived.
2. **`'Error'` never matched `ERROR -2:`** — the keyword list is case-sensitive and the bootloader
   emits upper case.

`booting=True` was therefore set by "we started trying". The corrected assertion (RCA fix #4,
present in this tree) then faithfully reported a failure from a wrong input.

**History of this requirement:**

- tb504 2026-08-07: **false PASS** in 33 s — the inverted `if not booting: self.passed(...)`
- tb470 2026-08-11: **false FAIL** — assertion fixed, detection still broken

**Fix:** gate on the *outcome*, not the attempt.

- Match `Could not find configuration node` and `can't get kernel image` **case-insensitively**
- Do not treat `Booting image` as success; require a post-load marker (`Mounting` / `Initializing`)
  before concluding the device booted
- Suggest `re.IGNORECASE` matching, or lower-casing output before the keyword scan, since
  `'Error'` vs `ERROR` will bite anywhere else the same list is used

---

## 4. The seven UNSUPPORTED — permanent, not a bench gap

Cases 1, 21, 41, 61, 101, 111, 121 all report `No SD card present` / `DUT does not support SD Card`.

**The IE520 has no SD card slot** (confirmed by Terrence, 2026-08-11). These can never produce a
verdict on this platform.

> **This contradicts RCA recommendation #14** — *"Fit an SD card to tb504 — converts 6 UNSUPPORTED
> into real coverage."* That is not achievable on IE520 hardware. The recommendation should be
> withdrawn, and the SD-card cases either retired for this platform or marked with a
> `testCaseExcl` entry so they are reported as excluded rather than as failures.

Note each currently logs `!!FAIL: No SD card present` *and* an UNSUPPORTED verdict — the
`numFailed: 1` in the table above. That inflates the raw FAIL line count in the log (8 `!!FAIL`
lines for 1 failing case) and is worth tidying.

---

## 5. What this run proves

Every RCA root cause that was fixed is now validated on hardware.

**Root cause A — bootloader media-select parser (`ATBootLoader.py`).** The RCA lists six direct
hits on tb504: cases **22, 42, 60, 62, 100, 102**. **All six PASS here.** The fix anchors on the
numbered menu line (`endswith(':<filename>')`) instead of matching the raw filesystem listing and
sending the file *size* as a menu index.

**Root cause B — stale gate strings.** Cases **70, 80, 90** each burned 30 minutes on tb504 waiting
for `"Verifying release"`, a string this bootloader never emits. All three PASS, in minutes.

**Root cause G — teardown skipped after an exception.** This is the structural one. tb504:

```
18:00:29  cmd(move mainrelease.rel IE520-tb504.rel)     <- renamed away in main()
18:36:34  ========= End of TestCase 60 Tear Down =========
          ^ "End of" only — no start marker; tear_down() never began
```

`move IE520-tb504.rel mainrelease.rel` appears **nowhere** in that campaign, so the file was absent
for the following ten hours. tb470, same case:

```
17:05:39  cmd(move mainrelease.rel IE520-tb470.rel)     <- renamed away
17:11:58  ========= TestCase 60 Tear Down =========     <- START marker present
17:12:01  cmd(move IE520-tb470.rel mainrelease.rel)     <- RESTORED
17:17:33  ========= End of TestCase 60 Tear Down =========
```

**All five cascade victims (110, 112, 119, 120, 122) now PASS.** The RCA insisted these be re-run
rather than triaged; they have been, and they are clean.

**The bootloader escape never fired** (0 occurrences). Nothing stranded the DUT. It remains
**untested on hardware** — insurance, not a dependency.

---

## 6. Handoff — actionable items

| # | Item | Why |
|---|---|---|
| 1 | **Fix the AWP2684 detection** (§3) | The only failure in the run; the requirement is still unverified on any bench |
| 2 | **Withdraw RCA recommendation #14** and mark the SD cases excluded for IE520 (§4) | It asks for hardware the platform cannot accept |
| 3 | **Port the `createFlashBootImages` fix out of this staging copy** | See below — it exists only in `copilot/library_5700.py` |
| 4 | **Clear the USB leftover** `---w-z-03-09-a-y---.rel` before the next run | §7 |
| 5 | **Case 113 (YMODEM) remains unexercised** | Excluded at 9600 baud; needs a standalone 115200 run per RCA §9.6 |
| 6 | **Exercise the bootloader escape deliberately** | Never fired; correctness on hardware is unproven |

### `createFlashBootImages` — fixed here, not yet anywhere else

The existence check could never match, so **every** `configure()` re-downloaded both releases —
82 MB and 12+ minutes of SPIFlash time per suite, per run:

```python
existing_files = [line.split()[-1] for line in output.splitlines() if line.split()]
# -> ['*.rel', '\x1b[32mflash:/mainrelease.rel\x1b[0m', ..., 'swi_a#']
```

`dir *.rel` prefixes names with `flash:/` (a bare `dir` does not) and the names carry ANSI colour
escapes; the echoed command and prompt are swept in as "files".

Replaced with a per-file predicate plus a per-run freshness rule, on Terrence's instruction —
*"regardless of whats there, the first should be a fresh download. that way, we can trust what IS
there, because we got it."* First use of a file in a run always downloads; later uses check
presence. Verified offline against five scenarios with mutation testing, and all three branches
were observed firing on hardware during this run.

**This lives only in `copilot/library_5700.py`.** It is not in `ck.db` and not in any framework
tree.

---

## 7. Bench state left behind (verified after the run)

```
show boot
  Current software   : IE520-tb470.rel
  Current boot image : flash:/mainrelease.rel   (file exists)
  Backup  boot image : flash:/backuprelease.rel (file exists)
  Boot Security Level: none

dir *.rel        41104167  mainrelease.rel
                 41104167  backuprelease.rel      (26.1 MB free of 106.3 MB)

dir usb:         41104167  ---w-z-03-09-a-y---.rel   <- LEFTOVER from case 22
                 41103815  IE520-tb470.rel
                  1572864  IE520-bootloader-9.1.0.kwb
```

**Healthy and re-runnable** — boot pointers set to files that exist, security level `none`. This is
a much better state than tb504 was left in (Level 2, password `789012`, blocking all re-runs).

**One item to clear:** the USB stick carries `---w-z-03-09-a-y---.rel`, left by case 22 — the same
class of leftover that filled u4's flash before this campaign and caused a silent failure. 29 GB
free so it is not urgent, but clear it before a run that fills the stick.

---

## 8. Caveats

1. **`+352 bytes`.** Every release written to flash by TFTP is `41,104,167` bytes against a source
   of `41,103,815`. Deterministic across 4 transfers and 2 devices, so it is something AW+ adds on
   write, not corruption — the images boot. Not investigated further.
2. **u4's USB stick dropped off the bus once**, between the smoke run and the first full attempt,
   with nobody touching it (enumeration 5 → 4 devices). That aborted run is archived in
   `partial-1436-usb-missing/`. The dongle and the stick share one rear port through a hub. If a
   USB case fails oddly in future, suspect the hub before the product — the RCA also recorded five
   unasserted `fs_devread` errors on tb504's stick.
3. **Concurrency.** This ran alongside suite 2003 on the second IE520, sharing tb470's tftpd and
   eth1. No interference was observed. Both DUTs' addresses derive from their tty number
   (`ipOffset = ttyNumber + 2`), so they cannot collide.
4. **`rc = 1`** reflects the single failing case. Note the RCA's warning that a bare `sys.exit()`
   used to make an abandoned run exit 0 — that path is fixed in this tree, so the exit code is
   meaningful here.

---

*Written 2026-08-11 by Claude, from this run's own logs. Suite 2003's after-action is in
`run-20260811-tb470-2003/after-action-2003.md`.*
