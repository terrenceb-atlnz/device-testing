# Bootloader TestSuite (5700) — Technical Detail

> Companion to **Bootloader-Executive-Overview.md**. This is the evidence base: full root-cause
> analysis, verbatim console captures, source references and audit trail.

**Subject:** Root-cause analysis of every non-UNSUPPORTED failure in the 5700 bootloader suite
**Campaign:** tb504 (IE520, bootloader `master-20260717-518`, U-Boot `2025.01-04843-g6eaac4e1fcad`)
**Window:** 2026-08-07 14:07:25 → 2026-08-08 08:31:21 (18 h 24 m)
**Author:** Terrence Beach · **Date:** 2026-08-10

---

## 1. Executive summary

Twenty-four test cases failed across the campaign. **Not one is a confirmed product defect, and
only three are attributable to how long the hardware genuinely takes.** They reduce to **four root
causes**, plus one framework defect that destroys diagnostic evidence.

| # | Root cause | Type | Cases | Cost |
|---|---|---|---|---|
| **A** | `ATBootLoader` sends the file **size** instead of the menu **index** | Framework | 11 | ~5 h |
| **B** | Gate strings the current bootloader no longer emits | Test script | 8 | ~3 h |
| **C** | Diagnostics menu **option 8 does not exist** on this bootloader | Product ↔ test-plan mismatch | 2 | ~10 m |
| **D** | SPI-flash test/erase/reset exceed their time budgets | Budget calibration | 3 | ~1 h 35 m |
| **E** | Crash **inside the error-reporting path** (`log_device_output`) | Framework | *(co-defect in 2005.2)* | — |
| **F** | **2005 removes its own last boot path** — `no boot system` at setup, then a factory restore clears the TFTP override | Test design | *(all of 2005)* | ~1 h reboot loop |
| **G** | **An exception in `main()` skips `tear_down()` entirely** — every case leaks its state mutations | Framework | *cause of the §3 cascade* | ~4 h |
| **H** | **A bare `sys.exit()` in `library_5700.py` kills the process — and exits 0** | Library | 6 of 8 cases in 2005 | run abandoned |
| **I** | **The framework cannot answer a bootloader password prompt** — Security Level 2 locks out 2002/2003/2005 automation | Framework | blocks all re-runs | — |

> **Coverage headline.** The campaign references **47 distinct requirement IDs**. **19** have at
> least one passing verdict; **28** have none. One of the 19 — **AWP2684** — is a provably false
> pass (§9.1). So **at most 18 of 47 requirements (38%) came out of this campaign with a
> trustworthy verdict.**

**Roughly 9 of the 18.4 hours — about half the campaign — was spent inside failures the DUT had
nothing to do with.** Suites 2001 (9/9) and 2004 (2/2) are completely clean. Where the device *was*
the slow part (root cause D) it was behaving normally: erasing and verifying 128 MB of SPI flash
simply takes longer than the budgets allow.

> ### ⚠️ Bench state — read before scheduling the next run
> The 2005 run **never finished**; it stops mid-case at 08:31:21 with no `TESTSET FINISHED` marker.
> The raw console transcript confirms tb504's IE520 was left at **Security Level 2 (Password
> Protected)**, password `789012`, parked in the Security Settings menu.
>
> **This is awkward to undo, and my earlier advice on it was wrong.** Clearing Level 2 needs **no
> password** — but the bootloader warns it "will **DESTROY the entire contents of the FLASH file
> system**" and performs a full SPI-flash erase taking well over 13 minutes. It is a destructive,
> re-image-afterwards operation, not a quick tidy-up. See §7.
>
> The unit is **not** bricked — it booted normally after the interrupted erase. A root `minicom`
> has been attached to its console since 2026-08-10 08:38, so someone may already have acted.

---

## 2. Campaign results at a glance

| Suite | Window | Duration | PASS | FAIL | UNSUP | rc |
|---|---|---|---|---|---|---|
| 2001 — Boot System CLI | 14:07:25 → 14:49:01 | 41 m | **9** | 0 | 0 | 0 |
| 2002 — Default/one-off boot | 14:49:03 → 00:59:40 | **10 h 11 m** | 8 | **14** | 7 | 1 |
| 2003 — Diagnostics menus | 00:59:42 → 05:45:35 | 4 h 46 m | 8 | **8** | 2 | 1 |
| 2004 — (2 cases) | 05:45:36 → 06:06:08 | 21 m | **2** | 0 | 0 | 0 |
| 2005 — Boot security levels | 06:06:10 → *(abandoned)* | 2 h 25 m+ | 1 | **1** + 1 incomplete | 0 | — |

UNSUPPORTED results are excluded by request. For the record they are all `No SD card present` (6)
plus `No NVS` (1) — a bench-provisioning gap, not a defect. Fitting an SD card to tb504 would
convert 7 skipped cases into real coverage.

---

## 3. Root cause A — the bootloader media-select parser (11 cases)

### The defect

`framework/ATDrivers/ATBootLoader.py`, in `__set_swi_boot_from_media_via_bootrom()` (≈ line 744):

```python
for line in output.splitlines():
    if filename in line:                      # matches ANY line mentioning the file
        try:
            number = line.split()[0][:-1]     # assumes "  1. usb:foo.rel"
            __send_bootloader_command(swi, f'{number}\n', ...)
            bootSet = True
        except (ValueError, IndexError):
            pass
        else:
            break                             # first match wins
```

The IE520 bootloader prints the **raw filesystem listing before** the numbered menu, and the
filename appears in both:

```
 41015155   mainreleaseusb.rel        <-- MATCHED FIRST.  line.split()[0] == "41015155"
...
Listing of usable files (root directory only)
  1. usb:mainreleaseusb.rel           <-- the real menu line.  NEVER REACHED
```

`"41015155"[:-1]` → **`4101515`**. The `[:-1]` exists to strip the `.` from `"1."`; on a size field
it just chops a digit. **No exception is raised** — `"41015155"` is an ordinary string — so the
`except (ValueError, IndexError)` guard is dead code and `break` stops the loop ever reaching the
correct line.

Verbatim, from `test-5700.2002.log:1110`:

```
Enter selection (1-2, 0 to cancel) and press enter ==>
2026-08-07 18:06:31: 4101515

Value entered must be between 1 and 2
```

### Why one bad digit costs an hour

1. Six attempts (`retries = 5`), ~28 s apart, all identical → `Problem occurred whilst setting boot environment`.
2. **Nothing sends `0` or `9`.** The DUT is abandoned at the bootloader `Select device:` prompt.
3. `checkShowBoot()` → `dut.mode('#')` polls for a CLI prompt that cannot appear.
4. `AWPConsoleCore.mode()` has `timeOut=1800` → raises `INFINITE LOOP DETECTED` after **exactly** 30 min.
5. `tear_down()` calls `dut.mode(')#')` on the same stranded console → **another 30 min**.

`INFINITE LOOP DETECTED` is a flat wall-clock timeout, not loop detection. The gaps are exact:
16:26:35→16:56:35, 18:06:31→18:36:34, 22:41:29→23:11:32.

### The cascade — how step 5 poisoned the rest of the suite

`TestCase_60` and `TestCase_62` deliberately rename the main release out of the way in `main()`, and
restore it in `tear_down()`:

```python
def tear_down(self):
    dut.mode(')#')
    dut.cmd('no boot system')
    dut.mode('#')
    dut.cmd(f'move {dut.tftpfilename} {self.MAIN_RELEASE}')   # <-- NEVER EXECUTES
```

**`tear_down()` never runs, because an exception in `main()` skips it entirely.** This is a property
of the framework, not of these two cases — `ATTestCase.py:995-1010`:

```python
try:
    self._execute_if_not_aborted(self.main)(self)
    ...
except Exception as e:
    self.__handle_exception_in_test_run(reason='exception in TestCase main, aborting test')
    return                      # <-- RETURNS. The tear_down block below is never reached.

try:
    if self.doTear:
        self._execute_if_not_aborted(self.tear_down)(self)     # <-- unreachable after an exception
```

`__handle_exception_in_test_run()` runs only `self._post_tear_down()` — the **framework's** restore of
the boot *configuration*. It does not call the user's `tear_down()`, and it does not restore
filenames on flash.

The console transcript confirms it. A case that failed *without* raising still tears down; the two
that raised do not:

```
swi_a_2002.log:17405   15:59:14  ========= TestCase 22 Tear Down =========      <- case 22 failed, no exception
swi_a_2002.log:17452   15:59:17  ========= End of TestCase 22 Tear Down =========

swi_a_2002.log:61686   18:00:29  cmd(move mainrelease.rel IE520-tb504.rel)      <- case 60 renames it away in main()
swi_a_2002.log:80141   18:36:34  ========= End of TestCase 60 Tear Down =========
                                  ^ "End of" only - NO start marker. tear_down() never began.
```

`move IE520-tb504.rel mainrelease.rel` appears **nowhere** in the campaign. From 20:15 onward
`mainrelease.rel` does not exist on flash for the remainder of the 10-hour run, and every subsequent
case referencing it fails with `% Source file not found`.

> **This generalises, and it is the single most important structural finding in the report.**
> *Every* test case in this framework that mutates device state in `main()` and relies on
> `tear_down()` to restore it will leak that state permanently if `main()` raises for any reason.
> The bootloader parse bug (§3) is merely what made `main()` raise here; the same leak would follow
> from any exception in any case. Fixing the parser removes this instance. It does not remove the
> hazard.
>
> **Structural fix:** invoke the user `tear_down()` from a `finally`, or call it (guarded, with a
> short timeout) inside `__handle_exception_in_test_run()` before `_post_tear_down()`. Pair it with
> the bootloader escape from §3 so teardown is not attempting to drive a stranded console.

**Direct hits (6):** 2002.22, 42, 60, 62, 100, 102
**Cascade victims (5):** 2002.110, 112, 119, 120, 122 — plus 7 of the 8 assertions in 2002.100

Two cascade failures look like product findings and are **not**:

- `2002.122 — expected error message not displayed when setting Boot System to external storage with a backup set` (expected `% A backup file must be set`). The device actually said
  `% usb:/mainreleaseusb.rel does not exist or is inaccessible`, because the USB copy in step 1 had
  already failed with `% Source file not found`. **The condition under test was never reached.**
- `2002.100 — There is no primary release file set on swi_a` ×2. The device was correct to refuse:
  the primary release genuinely did not exist.

Both must be **re-run**, not filed.

### Fix

A correct implementation already exists in the same file —
`perform_one_off_boot_from_alternate_source_with_output()` (≈ line 1441) anchors on the `:` separator:

```python
line = [x.strip() for x in output.splitlines() if x.strip().endswith(':{}'.format(fileName))][0]
selection = int(line.split()[0].replace('.', ''))
```

`' 41015155   mainreleaseusb.rel'.endswith(':mainreleaseusb.rel')` → `False`
`'1. usb:mainreleaseusb.rel'.endswith(':mainreleaseusb.rel')` → `True`

Recommended patch (no new imports):

```python
### Match ONLY the numbered menu line ("  1. usb:foo.rel").  The raw filesystem
### listing ("  41015155   foo.rel") precedes it and also contains the filename -
### selecting from it sends the file SIZE.
menuLines = []
for line in output.splitlines():
    line = line.strip()
    if not line.endswith(':{}'.format(filename)):
        continue
    token = line.split()[0]                      # expect "1."
    if token.endswith('.') and token[:-1].isdigit():
        menuLines.append(line)

if not menuLines:
    _failureMsg = f'{filename} was not offered in the bootloader file list for {media}'
else:
    number = menuLines[0].split()[0][:-1]
    output, matchedWords = __send_bootloader_command(
        swi, f'{number}\n', strList=keywords,
        nextStrList=[KEYWORD_ENTER_SELECTION], waitTime=60, interval=0.05)
    responses.append(output)
    bootSet = True
```

**And, separately, never strand the DUT.** Before returning `bootSet = False`:

```python
if not bootSet:
    swi.send('0\r\n')   # cancel file selection
    swi.send('0\r\n')   # return to previous menu
    swi.send('9\r\n')   # quit and continue booting
```

This second change alone would have saved ~5 hours *and prevented the entire cascade*, even without
the parser fix. It is arguably the higher-value of the two.

---

## 4. Root cause B — gate-string rot (8 cases)

The suite blocks on literal strings this bootloader build no longer emits. In **every** one of these
cases the device did the right thing; the test simply failed to recognise it.

### B1 — `"Verifying release"` (7 cases)

**This string does not appear in a single line of console output anywhere in the campaign.** Grep
across all five logs returns three hits, all traceback echoes of the source line itself. What the
bootloader actually emits on this build is:

```
Verifying Hash Integrity ... sha1+ OK
Verifying Hash Integrity ... crc32+ OK
Loading file / Mounting / Initializing
```

Six of the seven pass **no `waitTime`**, so they inherit `AWPConsoleCore.send()`'s 1800 s default
and burn 30 minutes apiece:

| Case | Source | Gate | Cost |
|---|---|---|---|
| 2002.70 | `test-5700.2002.py:640` | `dut.send('0', strList=["Verifying release"])` | 30 m |
| 2002.80 | `test-5700.2002.py:662` | `dut.send('0', strList=["Verifying release"])` | 30 m |
| 2002.90 | `test-5700.2002.py:699` | `dut.send('b', strList=["Verifying release"])` | 30 m |
| 2003.1 | `test-5700.2003.py:50` | `dut.send('0', waitTime=120, strList=['Verifying release'])` | 2 m |
| 2003.8 | `test-5700.2003.py:341` | `dut.send('9', strList=[keyWord])` | 30 m |
| 2003.9 | `test-5700.2003.py:378` | `dut.send('0', strList=[keyWord])` | 30 m |
| 2003.15 | `test-5700.2003.py:684` | `dut.send('9', strList=[keyWord])` | 30 m |

2003.1's own failure dump contains the full U-Boot banner, the TFTP transfer and the load progress —
the device booted perfectly. It has a second, independent problem: its 120 s budget is shorter than
a TFTP netboot of a 41 MB release, so it would fail on time even with the right string.

### B2 — `"Restoring default settings... Complete"` (1 case: 2005.2)

The test expects that as one contiguous string. The device (`swi_a.log` ≈ line 8899) emits:

```
  Restoring default settings... Saving Environment to SPIFlash... Erasing SPI flash...Writing to SPI flash...done
OK
Saving Environment to SPIFlash... Erasing SPI flash...Writing to SPI flash...done
OK
Complete
```

Both halves are present — but the bootloader now interleaves four lines of SPI-flash progress
between them, so the substring match fails. **The restore succeeded.** This was the one assertion in
the campaign that looked like it might be a genuine regression; it is not.

*(It took reading the raw console transcript to establish that, because the framework crashed while
trying to print exactly this output — see §6.)*

### Fix

Replace the literals with the framework's own bootup keyword set,
`['Mounting', 'Booting', 'Initializing']`; for B2 match `'Restoring default settings'` and
`'Complete'` independently rather than as one string. Give every `send()` on a boot path an explicit
`waitTime`. Then **grep every hard-coded gate string in the suite against a real console capture
from the current build** — this class of rot is silent, and here it cost three hours.

---

## 5. Root cause C — diagnostics menu option 8 does not exist (2 cases)

`2003.7` (AWP2760, stage 1) and `2003.14` (AWP2766, stage 2) both select **option 8, "Quit to U-Boot
shell"**. Neither menu offers it on this build. Captured verbatim:

```
Bootup Stage 1 Diagnostics Menu:        Bootup Stage 2 Diagnostics Menu:
  0. Restart                              0. Restart
  1. Full RAM test                        2. Test FLASH (Filesystem only)
  2. Quick RAM test                       4. Erase FLASH (Filesystem only)
  ----------------------------------      6. Bootloader ROM checksum test
  7. Bootup stage 2 diagnostics menu      7. USB slot test
  ----------------------------------      ----------------------------------
  9. Quit and continue booting            9. Quit and continue booting
```

Both menus redisplay on an invalid selection, so the test reports
`did not enter u-boot ... expected "Unknown command"`.

**This is the one category that warrants a question back to the bootloader team rather than a script
fix.** If option 8 was **deliberately withdrawn**, AWP2760 and AWP2766 should be retired or rewritten
as negative tests. If it was **not**, this is a genuine regression. Either way the answer is theirs.

**Suite 2004 sharpens the question.** `2004.1 Access U-boot` **passes** — it reaches the U-Boot shell
via **Ctrl-U** at boot, and `2004.2` then drives real U-Boot commands successfully (`date reset`,
setting past/present/future dates, and confirming the DUT syncs to U-Boot time after bootup). So the
U-Boot shell is alive and reachable on this build; only the *diagnostics-menu route* to it is gone.

That makes a wholesale security lockdown of U-Boot the less likely explanation, and a menu
restructure the more likely one — but it is still their call. Worth asking as: *"option 8 has gone
from both diagnostics menus while Ctrl-U still works — intended?"*

---

## 6. Root cause E — the crash that hides the evidence (co-defect in 2005.2)

`library_5700.py:986` calls `log_device_output(output)` where the function needs `(self, output)`:

```
06:44:34: !!FAIL: Did not see expected "Restoring default settings... Complete":
06:44:34: TypeError: log_device_output() missing 1 required positional argument: 'output'
```

**The crash is in the failure-reporting path.** The moment the test found something, the code that
would have shown what the device actually said threw instead — so the run recorded the assertion but
not the evidence. Establishing that §4-B2 was a stale gate string rather than a product regression
required going to the raw console transcript on tb504, because this log line was destroyed.

It is a one-line fix, and it has been blinding every failure on that path since it was written.

Its consequential damage was larger than the failure it hid: the exception aborted `main()` before
**step 19 — reset security level to 1** — which is why the bench was left at Level 2 (§7).

---

## 7. Root cause D — under-budgeted SPI-flash operations (3 cases)

**This is the only category where the device really is the slow part** — and even here it is
behaving normally, not badly. All three are 128 MB SPI-flash operations cut off mid-progress-bar.

| Case | Operation | Budget | Cut off at |
|---|---|---|---|
| 2003.10 | Test FLASH (Filesystem only), 2 passes | 3600 s | mid `Reading test data`, **pass 1 of 2** |
| 2003.11 | Erase FLASH (Filesystem only) | ~1230 s | 36 of 50 blocks |
| **2005.3** | **Reset Security Level 2 → 1** | **780 s** | **23 of 50 blocks** |

The suite's own message concedes the problem —
`Did not see expected succeesful completion, but flash test may have succeed` *(sic)*.

### 2005.3 in detail — and a correction to my earlier reading

I previously suggested this was a password problem or a possible product defect. **It is neither.**
The raw console transcript shows what actually happens:

```
Select '1. Set security Level to 1 (None)'

  WARNING: This option will reset the security level to One.
  which will DESTROY the entire contents of the FLASH file system
  Press Y to proceed, or any other key to return to the previous menu ==>

08:16:37  send(y)
          Probing SPI flash... Complete
          Erasing SPI flash...  [=======================        ]   <- 23 of 50
08:29:37  send(y, 780, [...]) wait time reached
08:30:48  Power off swi_a is complete: Success                      <- power-cycled MID-ERASE
```

**No password is requested at any point.** Clearing Level 2 is not an authentication operation — it
is a full flash-filesystem wipe. The framework allowed 780 s, the erase needed longer, and the
framework then power-cycled the switch part-way through it. The level therefore stayed at 2, and
`2005.3` correctly refused to continue against an unknown state.

The unit booted normally afterwards (U-Boot banner and boot menu both reachable at 08:31), so the
interrupted erase did no lasting harm.

### Fix

Measure one full FLASH test, one full erase and one full security-level reset on an idle IE520, then
set each budget from the measurement with headroom. All three are inherently long on 128 MB SPI
flash; a 780 s cap for a full filesystem wipe is not a realistic figure. Until then these results are
neither pass nor fail — they are **unmeasured**.

**Design note worth raising:** a test that clears a security level destroys the flash filesystem as a
side effect. Any suite that sets Level 2 or 3 needs a re-image step built into its teardown, not just
a menu selection.

---

## 8. The 2005 boot-path gap — the suite removes its own last boot path

Worth separating from the four root causes because it is neither a framework bug nor a gate-string
bug: it is a **test-design gap inside 2005**, and it put the DUT into an hour-long reboot loop.

`2005`'s `TestSet.configure()` does two things:

```python
dut.cmd('no boot system')                 # clears the primary boot pointer
dut.cmd('no boot system backup')          # clears the backup boot pointer
...
createFlashBootImages(self, dut, filenames=[self.MAIN_RELEASE, self.BACKUP_RELEASE])
```

So the release files **exist in flash**, but nothing points at them. The only remaining boot path is
the bootloader's TFTP override — the "System has been forced to boot from a non-standard location"
state that `restore_boot_from_tftp()` leaves behind.

`2005.2` step 17 then selects `7. Restore Bootloader factory settings`, whose entire purpose is to
clear bootloader-menu settings — **including that override.** With the override gone and both boot
pointers unset, the device has nowhere to go:

```
Loading file '.release' ... Error: There is no primary release file set
Loading file '.backup'  ... Error: There is no backup release file set
ERROR: Boot failed. Please recover the system using the Boot Menu
Restarting system in ...  5
```

**678 boot-failure cycles**, 06:44 → 07:45 — roughly an hour and ~37,000 lines of console transcript.

**The device is not at fault.** It correctly reported that no boot image was configured and named its
own recovery path. The suite simply removed the last thing holding it up.

**Fix:** before any step that restores bootloader factory settings, set `boot system` to a real
release in flash so the DUT has a valid fallback. Treat `restore_boot_from_tftp()` as a diagnostic
prop, not a boot configuration.

### A related observation, lower impact

`2003.11 Erase FLASH (Filesystem only)` did re-create the UBI volume — `image sequence number`
changes from `58377922` (2002) to `1417222377` (2005), and `max/mean erase counter` resets from `9/5`
to `2/0`. This is **not** the cause of the 2005 failures: every TestSet re-populates flash in
`configure()` via `createFlashBootImages()`, and `2004`'s own setup confirms it —
`dir *.rel` at 05:59:24 lists both `mainrelease.rel` and `backuprelease.rel` present and correct.
Noted only so the UBI counters are not misread as corruption.

### What the security suite did and did not establish

**Established (18 passing assertions in 2005.2):** Security Settings menu access; Level 2 set, abort
and password-mismatch detection; password change; and the full enforcement matrix — password
required on boot-menu options 1, 2, 3 and 5 with incorrect passwords rejected, and not required on
4, 6 and 7.

**Established by evidence, though never asserted:** step 18's requirement — that a bootloader factory
restore does *not* clear the security setting. The last `set the security level to two` is at
06:27; the factory restore ran at 06:44:27; at 08:16:36 the menu still read
`currently set to 2 (Password Protected)`. **The setting survived both the restore and 678 reboot
cycles.**

**Unevaluated — not failed:**

- step 18's own assertion (the test aborted at exactly that point — §6)
- step 19 — reset to Level 1
- **the whole of Security Level 3 (Locked Down)**, `2005.3`, which never passed its precondition

Level 3 is the more restrictive setting and has no coverage at all from this campaign.

---

## 9. Second-pass audit — findings, and things ruled out

A second sweep looked specifically for what the first pass had *not* examined: passing cases,
never-executed paths, device-side output nobody asserted on, and requirement traceability.

### 9.1 AWP2684 is a false PASS — `2002.30` never performed the test *(HIGH)*

```
16:10:26  Perform a one-off boot using a release intended for a different platform, should fail
16:10:47  Turning swi on from thread, swi_a
16:10:59  PASS: correct error loading an invalid release        <- 33 seconds, start to finish
```

A TFTP one-off boot of a 41 MB release takes minutes; this never attempted one. The assertion at
`test-5700.2002.py:320` is inverted:

```python
booting, output = perform_one_off_boot_from_alternate_source_with_output(self, dut, fileName=dut.incorrectfilename)
if not booting:
    self.passed("correct error loading an invalid release")
```

`booting=False` is returned for **any** failure — file not offered in the menu, bootloader not
entered, parse failure, timeout. The test cannot distinguish *"the device correctly rejected a
foreign release"* from *"the automation never got as far as trying"*. Given the same function was
returning `False` for menu-parse reasons in cases 110/112/120, the latter is far more likely.

**AWP2684 is recorded as verified and is not.** Fix: assert on the *reason* — require the expected
error text in `output`, not merely `not booting`.

This is the **only** inverted-boolean pass in the entire codebase — a static sweep of every
`self.passed()` call site across all five scripts plus `library_5700.py` found no other instance.

### 9.2 Two assertions that pass on silence *(MEDIUM)*

`library_5700.py:1096`, in `selectBootMenuOptionCorrectPW()`:

```python
output = dut.send("\n", strList=[strconf], waitTime=20)
if 'Incorrect password' not in output:
    self.passed("Correct password detected")
```

Absence of an error is treated as proof of success. A 20 s timeout returning empty or partial
output passes. At 9600 baud, with the console truncation this campaign shows repeatedly, that is a
live risk rather than a theoretical one. It ran four times in `2005.2` (options 1, 2, 3, 5) — four
of that case's 18 passing assertions.

`library_5700.py:1211`, in `selectBootMenuOptionPWTimeout()`:

```python
output = dut.cmd("show boot")
if "Boot Security Level:" in output:
    self.passed("Device has rebooted")
```

That matches the *field label*, which appears in every `show boot` output regardless of value or of
whether the device rebooted. The correct pattern is used elsewhere in the same suite —
`test-5700.2005.py:792` checks `"Boot Security Level: none"`, and `:830` checks the expected level
by name.

### 9.3 Five non-fatal USB filesystem read errors, unasserted *(LOW)*

```
Bus usb@50000: USB EHCI 1.00
scanning bus usb@50000 for devices...
 ** fs_devread read error - block
5 USB Device(s) found
Loading tftp://10.38.249.33/IE520-tb504.rel ...
```

U-Boot fails to read a block from the USB stick during boot-time enumeration, then proceeds
normally. Five occurrences, **all in suite 2003** (`swi_a_2003.log` lines 25611, 29947, 30145,
32538, 32734), none in the other four suites. No test asserts on it. Worth an `fsck` on that stick
before the next campaign — 2002 writes and deletes 41 MB files on it, including one with a
deliberately awkward name.

### 9.4 Traceability gaps *(INFORMATIONAL)*

- **9 cases carry no requirement reference at all** (`testCaseRef = "None"` or empty) — test effort
  not traceable to any requirement.
- **`2002.113`** (YMODEM one-off boot, AWP2641 among others) is excluded by
  `testCaseRunPriority = 10`, commented `# Will take 12 hours at 9600 baud rate`. A deliberate
  exclusion, but invisible unless you read the source.

### 9.5 Ruled out — things that look alarming and are not

Stated because they will be asked about, and because each was checked rather than assumed.

| Concern | Verdict |
|---|---|
| Flash damage from the interrupted erase / 678-cycle reboot loop | **None.** `bad PEBs: 0` and `corrupted PEBs: 0` in all 711 UBI attach reports across the campaign |
| Device crashes or exceptions | **None.** 42 exception-log checks, all clean; the check genuinely parses for `.tgz`/`kernel-*.txt` artefacts |
| RAM faults | **None.** Every DRAM test reports `0 error` |
| `dut.version = dut.bootVer[0]` looked like a character-index bug | **Not a bug.** `bootVer` is a list (`ATSwitch.py:108`), so `[0]` is the first element. *(Latent: would `IndexError` on an empty list.)* |
| 17 × `oops` in the transcripts | **False positive** — the substring in `loops` |
| 81 × `% Invalid input detected` | **Benign.** Shell commands (`uname -m`, `df`, `echo … > default.cfg`) hitting the AW+ CLI because `start-shell` is licence-gated. The framework installs ACCESS and retries; `default.cfg` then builds correctly |
| Raising the console to 115200 to shorten runs | **Not viable** — see §9.6 |

### 9.6 Why the console cannot simply be moved to 115200

Three findings, the third decisive:

1. `AWPConsoleCore._connect_serial(tty, baudRate)` opens the port once at the `[baudrates]` rate and
   never renegotiates — one rate serves both the bootloader and the AW+ CLI.
2. The generated `default.cfg` contains no console `speed` line (`ATSwitch.py:1151`), and that file
   is in the read-only framework, so nothing in the test flow pins the AW+ rate.
3. **`2005.2` deliberately restores bootloader factory settings** — `WARNING: This option erases any
   settings that may have been configured by this menu` (`swi_a.log:8792`) — and console baud is
   option 4 on that same menu. Mid-suite, the device would revert to its default rate while the
   framework kept transmitting at 115200, with no second management path to recover through.

The only gain would be making `2002.113` (YMODEM) feasible — 12 h down to about 1 h. Worth doing as
a **standalone run** with its own setup file, outside the campaign, where no factory restore can
pull the rate out from under it.

---

## 10. Recommendations, in priority order

| # | Action | Why |
|---|---|---|
| 1 | **Clear tb504's Security Level 2** — mandatory, not optional (§9/I): the framework has *no* bootloader-password handling, so Level 2 locks out 2002, 2003 and 2005 alike. Clearing it wipes flash and needs a re-image plan | Nothing can be re-run until this is done |
| 2 | **`library_5700.py:663` — replace the bare `sys.exit()`** with `self.failed(..., forceAbort=True)` | It kills the process mid-run *and exits 0*; it is why 6 of 8 cases in 2005 never ran |
| 3 | **Restore state in a `finally:` inside `main()`**, not in `tear_down()` (§3/G) | `tear_down()` never runs when `main()` raises — this is what caused the cascade, and it applies to every case |
| 4 | **Fix the inverted assertion at `test-5700.2002.py:320`** — require the expected error text, not `not booting` (§9.1) | AWP2684 is currently recorded as verified and is not |
| 5 | **Add the `0`/`0`/`9` bootloader escape** to every failure path in `__set_swi_boot_from_media_via_bootrom()` | Prevents the cascade; ~5 h saved; smaller and safer than the parser change |
| 6 | **Fix the file-selection parse** — reuse the `endswith(':<filename>')` predicate already proven in the same file | Root cause A |
| 7 | **Fix `log_device_output()`** at `library_5700.py:986` | One line; currently blinds every failure on that path |
| 8 | **Replace the stale gate strings** and give every boot-path `send()` an explicit `waitTime` | Root cause B; ~3 h saved |
| 9 | **Ask the bootloader team about diagnostics option 8** (§5) | Only possible genuine product finding in the campaign |
| 10 | **Re-measure and re-budget** the FLASH test, erase, and security-level reset | Root cause D; results are currently unmeasured, not failed |
| 11 | **Cap `mode()`/`send()` defaults** — pass a task-appropriate `timeOut` rather than inheriting 1800 s | Two half-hour stalls per failed case is an unreasonable price for a device that is not coming back |
| 12 | **Give 2005 a valid boot fallback** before its factory-restore step (§8) | ~1 h of 2005 was the DUT in a reboot loop with nowhere to boot |
| 13 | **Get coverage on Security Level 3** — it has none from this campaign (§8) | The more restrictive setting is entirely untested |
| 14 | **Fit an SD card to tb504** | Converts 6 UNSUPPORTED into real coverage |
| 15 | **Re-run 2002 and 2005 end-to-end after 2-5** — do not triage any cascade failure until then | 5 of 14 failures in 2002 are downstream artefacts |

**Expected outcome of 2-5:** 2002 should go from 5 PASS / 14 FAIL to a genuine result, the campaign
should shorten by roughly 8 hours, and the remaining failures will be worth reading.

---

## 11. Evidence, provenance and caveats

**All findings are grounded in the campaign's own console transcripts.** Every quoted bootloader and
CLI string is verbatim framework capture from the IE520 on tb504 — none is reconstructed or inferred.

Key references:

- `copilot/test-5700.2002.log` — lines 380-420 (case 22), 621-894 (case 42), 952-1300 (case 60),
  2320-2379 (case 102), 2470-2530 (case 110), 3060-3110 (case 122)
- `copilot/test-5700.2003.log` — cases 1, 7, 8, 9, 10, 11, 14, 15
- `copilot/test-5700.2005.log` — case 2 (step 18 onward) and the abandoned case 3
- **`tb504:/home/bidhanc/5700_bootloader/swi_a.log`** — the raw console transcript of the aborted 2005
  run (1.3 MB, last written 2026-08-08 08:31, never renamed because the run did not finish). §4-B2 and
  §7 rest on this file; it is world-readable and is the only surviving record of what the device
  actually said.
- Source: `~/DeviceSkrips/framework/ATDrivers/ATBootLoader.py`, `AWPConsoleCore.py`;
  `test-5700.2002.py`, `test-5700.2003.py`, `test-5700.2005.py`

### Caveats — please read before acting

> **1. Framework version.** The campaign ran against `/home/bidhanc/5700_bootloader/framework`, which
> was not readable from the analysis host; the copy inspected was `~/DeviceSkrips/framework`. Line
> numbers differ by ~5 (the `raise Exception('INFINITE LOOP DETECTED')` is at 976 in the traceback,
> 971 in the copy read), so these are near-identical revisions but **not confirmed byte-identical**.
> Check line numbers against bidhanc's tree before patching. The diagnosis does not depend on it: the
> buggy path reproduces the observed `4101515` exactly, and no other path in either file produces it.
>
> **2. `library_5700.py` was not read.** `checkShowBoot`, `runRestoreFactorySettings` and
> `resetBootSecurityLevel` were not available. §4-B2 and §7 were resolved from the device's own
> console output instead, which is stronger evidence than the source would have been — but the exact
> call sites in that library are unverified.
>
> **3. §5 (diagnostics option 8) is the only finding that may be a product issue,** and it is stated
> as a question, not a conclusion. Everything else is a framework, script, budget or bench-state issue.
>
> **4. Bench state is as of 2026-08-08 08:31.** A root `minicom` has held tb504's console
> (`/dev/u0 → ttyUSB0`, lock `LCK..ttyUSB0`, PID 17934) since 2026-08-10 08:38, and anything done in
> that session is not captured in any log. The console was deliberately **not** driven during this
> analysis — two processes on one serial port interleave in both directions. Confirm the live level
> with `show boot` (it reports `Boot Security Level:`) before acting on §8 item 1.
>
> **5. tb504 has exactly one console** for one DUT. There is no second path to the switch: the IE520
> answers on 80/443 but has no SSH or telnet.

### One latent defect, not yet biting

`ATBootLoader.py` ≈ line 964, in `__send_bootloader_command()`:

```python
if nextStrList:
    matchWords += strList[:]      # should be nextStrList[:]
```

`nextStrList` matches can therefore never be reported in the returned `keyWords`. Masked today only
because every current caller passes the same list to both parameters.
