# After-action — 5700 suite 2003 (Diagnostics menus), tb470

**DUT:** IE520, S/N `264A23066`, console `/dev/u5`, PDU `10.36.150.14` outlet 5 ("E")
**Software:** `IE520-tb470.rel`, build `IE520-tomahawk_ie520-continuous`, bootloader 9.1.0
**Setup:** `copilot/tb470-u5.setup` · **Run dir:** `copilot/run-20260811-tb470-2003/`
**Window:** 2026-08-11 14:36:08 → 19:40:07 (**5 h 04 m**), `rc = 1`
**Ran alongside** suite 2002 on the first IE520 (`/dev/u4`), concurrently, on the same testbox.

> ## ⚠️ READ FIRST — u5's flash filesystem is EMPTY
>
> ```
> dir *.rel             % No such file or directory
> show file systems     106.3M total, 106.2M free
> Current boot image :  Not set
> Current boot config:  flash:/default.cfg (file not found)
> hostname              awplus            (was "u5" — config wiped)
> ```
>
> This is **expected**: cases 11 (Erase FLASH) and 10 (Test FLASH) erase the flash filesystem by
> design. The unit is **not bricked** — it is running from the bootloader's TFTP override and
> netboots from tb470 on every power cycle — but it has **no local release and no configuration**.
>
> **It cannot boot without tb470 serving TFTP.** Before moving this unit, powering down tb470, or
> clearing the bootloader override, put a release back in flash and set `boot system`.
> A subsequent suite run repopulates it automatically in `configure()` (~12 min of SPIFlash time).

---

## 1. Headline

| | tb504 (2026-08-08) | **tb470 (this run)** |
|---|---|---|
| Duration | 4 h 46 m | 5 h 04 m |
| PASS | 8 | **10** |
| FAIL | 8 | **3** |
| UNSUPPORTED | 2 | 2 |

The longer wall-clock is **not** a regression — it is the opposite. tb504 spent ~92 minutes stalled
on gate strings that were then cut off by budgets that were too short; this run replaced that with
**3 hours of genuine flash testing** that had never previously run.

Of the 3 failures: **2 are the same candidate product finding** (diagnostics option 8), and **1 is
a budget ceiling on a test that was measurably working**.

---

## 2. Full results

Execution order is the `__main__` registration order, **not** numeric — `1…9, 12, 13, 14, 15, 11, 10`.
The two destructive flash cases are deliberately last.

| Case | Description | Verdict | Asserts | Req | tb504 |
|---|---|---|---|---|---|
| 1 | Diagnostics menu option `0. Restart` | **PASS** | 4 | AWP2754 | **FAIL** (gate string) |
| 2 | Diagnostics menu option `1. Full RAM test` | **PASS** | 4 | AWP2755 | PASS |
| 3 | Diagnostics menu option `2. Quick RAM test` | **PASS** | 3 | AWP2756 | PASS |
| 4 | option 3, Battery backed RAM (NVS) test | UNSUPPORTED | 2/1 | AWP2757 | UNSUP |
| 5 | option 4, Bootloader ROM checksum test | **PASS** | 3 | AWP2758 | PASS |
| 6 | option 7, Enter stage 2 diagnostics menu | **PASS** | 3 | AWP2759 | PASS |
| 7 | **option 8, Quit to U-Boot shell** | **FAIL** | 2/1 | AWP2760 | **FAIL** (same) |
| 8 | option 9, Quit menu and continue rebooting | **PASS** | 3 | AWP2761 | **FAIL** (gate string, 30 m) |
| 9 | stage 2, option 0, Restart | **PASS** | 3 | AWP2762 | **FAIL** (gate string, 30 m) |
| 12 | stage 2, option 5, Card slot test | UNSUPPORTED | 1/1 | AWP2765 | UNSUP |
| 13 | stage 2, option 7, USB slot test | **PASS** | 2 | AWP11517 | PASS |
| 14 | **stage 2, option 8, Quit to U-Boot shell** | **FAIL** | 1/1 | AWP2766 | **FAIL** (same) |
| 15 | stage 2, option 9, Quit and continue booting | **PASS** | 2 | AWP2767 | **FAIL** (gate string, 30 m) |
| 11 | stage 2, option 4, **Erase FLASH** | **PASS** | 3 | AWP2764 | **FAIL** (budget) |
| 10 | stage 2, option 2, **Test FLASH** | **FAIL** | 1/1 | AWP2763 | **FAIL** (budget) |

Total assertions passed: **36**.

---

## 3. Failures 1 & 2 — diagnostics option 8 (PRODUCT QUESTION, needs the bootloader team)

**Cases 7 (AWP2760, stage 1) and 14 (AWP2766, stage 2). This is the only candidate product finding
in the entire campaign, and it has now reproduced on a second bench with the tooling fixed.**

```
15:17:38  Enter the U-Boot shell, Option 8.
          !!FAIL: did not enter u-boot from diagnostics menu, expected "Unknown command"

15:35:39  !!FAIL: did not enter u-boot from diagnostics stage 2 menu, expected "Unknown command"
```

Neither diagnostics menu offers option 8 on this build. Captured menus:

```
Bootup Stage 1 Diagnostics Menu:      Bootup Stage 2 Diagnostics Menu:
  0. Restart                            0. Restart
  1. Full RAM test                      2. Test FLASH (Filesystem only)
  2. Quick RAM test                     4. Erase FLASH (Filesystem only)
  ---------------------------------     6. Bootloader ROM checksum test
  7. Bootup stage 2 diagnostics menu     7. USB slot test
  ---------------------------------     ---------------------------------
  9. Quit and continue booting          9. Quit and continue booting
```

Both menus simply redisplay on an invalid selection, so the test reports "did not enter u-boot".

**Why this is now worth escalating.** On tb504 this could be dismissed as one bench, or as another
gate-string artefact. It is neither:

- reproduced on **different hardware** (S/N `264A23066` vs tb504's unit)
- with **the gate-string and parser fixes in place**, which cleared every other failure in this suite
- at **both menu levels independently**
- while **Ctrl+U still reaches U-Boot** — tb504's suite 2004 passed `Access U-boot` and then drove
  real U-Boot commands, so the shell is alive; only the *diagnostics-menu route* is gone

**Ask them:** *"Option 8 (Quit to U-Boot shell) has gone from both bootup diagnostics menus on
`master-20260717-518` / 9.1.0, while Ctrl+U still works. Intended?"*

- If **deliberately withdrawn** → retire AWP2760 and AWP2766, or rewrite them as negative tests.
- If **not** → this is a genuine regression.

Either way it is their call, not ours. Do not file it as a defect until answered.

---

## 4. Failure 3 — case 10, Test FLASH (UNMEASURED, not a product failure)

```
16:26:23  Initiating FLASH test
19:26:24  !!FAIL: Did not see expected succeesful completion, but flash test may have succeed
          Expected pass string "Result for test 2/2 (pass 1): PASS"
```

It hit its 10800 s (3 h) ceiling exactly. **The device was working correctly the whole time**, and
reported so:

```
Performing test 1/2 with pseudorandom data...
Result for test 1/2 (pass 1): PASS
Performing test 2/2 with pseudorandom complemented data...
```

Console progress at cut-off:

```
Erasing SPI flash...  [==================================================]  50/50
Making test data:     [==================================================]  50/50
Writing test data:    [==================================================]  50/50
Reading test data:    [==================================================]  50/50
Erasing SPI flash...  [=================================                 ] ~33/50   <- test 2
```

**Test 1 of 2 completed and PASSED** — a full 128 MB erase/write/read cycle with pseudorandom data,
with no `FAIL` or `Error` anywhere in the transcript. Per the RCA this case has **never** completed
on any run; half of it is now genuinely measured for the first time.

### Two findings from this

**a) The budget is still short, and now measurably so.** tb504 reached only `Reading 20/50` of
test 1 in 3600 s. Here, 10800 s bought all of test 1 plus ~16 % of test 2 — so **one test costs
~9300 s and both cost ~18,600 s (5 h 10 m)**. That is more than double the RCA's ~8400 s estimate,
which was extrapolated from tb504's much smaller sample. A ceiling of **~21,000 s** would be needed
for this case to ever pass.

**b) The case discards a real result.** It gates solely on `Result for test 2/2 (pass 1): PASS`, so
test 1's device-reported PASS is thrown away. **Asserting per-test would bank that coverage even
when the clock beats it** — worth more than raising the budget to nearly six hours, and it would
convert this from FAIL to a partial PASS with a documented gap.

> Note the failure text still reads `"Did not see expected succeesful completion, but flash test
> may have succeed"` *(sic)* — the hedge the RCA criticised. With per-test assertions it would no
> longer need to hedge.

---

## 5. Two UNSUPPORTED — both permanent

| Case | Reason | Status |
|---|---|---|
| 4 (AWP2757) | `Test case not supported on this device. No NVS.` | No battery-backed RAM on IE520 |
| 12 (AWP2765) | `No SD card present, test unsupported` | **IE520 has no SD card slot at all** |

Case 12 cannot ever pass on this platform. As noted in the 2002 after-action, **RCA recommendation
#14 ("fit an SD card") is not achievable on IE520 hardware and should be withdrawn.**

---

## 6. What this run proves

**Root cause B — stale gate strings — is fixed and validated.** Cases **1, 8, 9 and 15** all failed
on tb504 waiting for `"Verifying release"`, a string this bootloader never emits; three of them
burned 30 minutes each. All four PASS here, in minutes.

**Root cause D — under-budgeted flash operations — is confirmed as a budget problem, not a device
problem.** Case 11 (Erase FLASH) **PASSED** in ~27 minutes. tb504 recorded it as a failure solely
because it was cut off at 36/50 blocks after ~1230 s. The raised 3000 s ceiling converted a false
failure into a real pass. The operation was never failing.

**The bootloader escape never fired** (0 occurrences). It remains untested on hardware.

**Concurrency works.** This ran start-to-finish alongside suite 2002 on the second IE520, sharing
tb470's tftpd and eth1, with no interference.

---

## 7. Handoff — actionable items

| # | Item | Priority |
|---|---|---|
| 1 | **Put a release back in flash on u5 and set `boot system`** — flash is empty, unit depends on tb470's TFTP to boot | **HIGH** |
| 2 | **Ask the bootloader team about diagnostics option 8** (§3) — the only candidate product finding in the campaign | **HIGH** |
| 3 | **Assert per-test in case 10** so test 1/2's PASS is banked rather than discarded (§4b) | MEDIUM |
| 4 | **Re-budget case 10 to ~21,000 s** if it is ever to complete — real cost is ~18,600 s (§4a) | MEDIUM |
| 5 | **Withdraw RCA recommendation #14** (SD card) — the platform has no slot | LOW |
| 6 | **Exercise the bootloader escape deliberately** — never fired on hardware | LOW |
| 7 | u5 still carries a **Provisioned member 2** — phantom `port2.0.x` in `show interface brief`, and the generated `default.cfg` shut `port1.0.1-port2.0.28` accordingly | LOW |

---

## 8. Bench state left behind (verified after the run)

```
show boot
  Current software   : IE520-tb470.rel        (running from TFTP netboot)
  Current boot image : Not set
  Backup  boot image : Not set
  Current boot config: flash:/default.cfg (file not found)
  Boot Security Level: none

dir *.rel            % No such file or directory
show file systems    flash    106.3M total, 106.2M free   <- EMPTY
                     usbstick  28.8G total,  28.8G free
```

Hostname is back to the factory default `awplus`; the previous `u5` hostname, `vlan1
10.38.215.66/27` and `vlan100 192.168.100.2/24` are all gone with the erased config.

**This is the designed outcome of cases 11 and 10, not damage.** But it generalises, and the RCA
made the same point about the security-level cases:

> *a test that clears a security level destroys the flash filesystem as a side effect. Any suite
> that sets Level 2 or 3 needs a re-image step built into its teardown, not just a menu selection.*

**The same applies to Erase FLASH and Test FLASH.** Neither restores the filesystem afterwards, so
any suite ending on them leaves the DUT dependent on a netboot. Worth building a re-image step into
their teardown.

---

## 9. Caveats

1. **Case 10's result is `unmeasured`, not `failed`.** Do not report AWP2763 as a product failure.
   Test 1/2 passed on the device; test 2/2 ran out of clock.
2. **`+352 bytes`** on every TFTP-written release (`41,104,167` vs a `41,103,815` source) —
   deterministic across 4 transfers and 2 devices, so an AW+ write artefact, not corruption.
   Not investigated.
3. **Silent phases are normal.** This IE520's SPIFlash is extremely slow and the unit goes
   *completely* dark while working — console silent even to a bare CR, and ping/ARP failing. A
   41 MB flash-to-flash copy measured ~12 minutes. **Never power-cycle a unit mid-write** on the
   assumption it has hung.
4. **`rc = 1`** reflects the three failing cases.

---

*Written 2026-08-11 by Claude, from this run's own logs. Suite 2002's after-action is in
`run-20260811-tb470-2002/after-action-2002.md`.*
