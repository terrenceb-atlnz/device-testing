---
name: x230v2-5700-control-corpus
description: "raw-data/test_scripts/5700_bootloader/ is a FULL x230v2 run of the same 5700 suite (Feb 2026, near all-pass) — the control that separates IE520 output DIVERGENCE from universal test rot; grep needs -a or these logs read as binary and return NOTHING"
metadata:
  node_type: memory
  type: reference
---

`raw-data/test_scripts/5700_bootloader/` holds a **complete 5700 bootloader campaign run on x230v2**
— 2026-02-19, build `awplus_main-20260218-1237`, same suite, `framework -> /home/st-art/framework`.
It has the pristine `test-5700.200x.py` + `library_5700.py` **and** full console captures
(`swi_a_2001..2005.log`). Read-only reference — never write here.

**Why it matters:** it is the only way to answer "does the IE520 say something different, or does
NO platform say this any more?" Baseline results — 2003 **13 PASS / 0 FAIL**, 2005 **8 PASS / 0
FAIL**, 2002 16 PASS / 3 FAIL / 7 UNSUP. Effectively all-pass, so any IE520 failure on a gate string
that passes here is a **product output question, not test rot.**

> **`grep` READS THESE LOGS AS BINARY.** Both the x230v2 and IE520 `swi_a_*.log` contain control
> bytes, so plain `grep` prints nothing and `grep -c` returns 0 — indistinguishable from a real
> absence. **Always `grep -a`.** This produced a false "0 occurrences on both platforms" mid-session
> until caught. Combine with the device-output-only filter (drop lines matching
> `^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d: `) or you match the framework's own logged strList as if it were
> device output.

**The 2026-08-12 comparison, for reuse.** Of 26 edits made to run the IE520, **12 (5 defects)
accommodate IE520 verbiage** and should be product questions; 14 are genuine cross-platform test
bugs. Divergences:

| # | x230v2 emits | IE520 emits |
|---|---|---|
| D1 | `Verifying release... OK` + `Booting...` (215 device lines) | raw U-Boot/FIT: `Probing SPI flash... Complete`, `Booting image 04000000#IE520-28GSX ...`, `Verifying Hash Integrity ... sha1+ OK` (0 `Verifying release`) |
| D2 | `Reading filesystem...` → straight to `Listing of usable files` | dumps the raw filesystem listing (sizes) in between — which is WHY the size-as-menu-index parse bit here and not there |
| D3 | `Saving settings... Complete` contiguous | split by `Saving Environment to SPIFlash...` (0 on x230v2, 36 on IE520) |
| D4 | `Restoring default settings... Complete` contiguous | same SPIFlash interleave |
| D5 | `Verifying release... Error: This release file is not intended for this device.` | no such stage; `Could not find configuration node` / `ERROR -2: can't get kernel image!` (upper case, so `'Error'` misses) |

**D1 and D5 are one question:** does the IE520 implement the AT release-verification stage at all?
If it should, several "fixed" cases are passing against the wrong output.

> ## UPDATE 2026-08-12 — A0 CONFIRMED AND FIXED; D1/D5 STILL BROKEN
>
> A second bootloader (`IE520-bootloader-pauld.kwb`, a developer `-dirty` build, still U-Boot
> 2025.01 underneath) was tested live on tb470 u4. **The A0 inference was right and the leak is
> a suppression problem:** all 11 leaked strings now measure 0 (`U-Boot 2025.01` 995→0,
> `Verifying Hash Integrity` 495→0, `Saving Environment to SPIFlash` 142→0), and the AT banner
> form is restored (`Bootloader pauld loaded`, matching x230v2's `Bootloader 6.2.37 loaded`).
> **D2, D3, D4 all FIXED.**
>
> **But suppression alone was not the fix.** Removing the U-Boot noise did not restore the AT
> messages the tests gate on. **D1 and D5 are now SILENT rather than wrong** — and D5 is *worse*:
> a foreign release is correctly refused with no output at all, then the normal reboot prints
> `Allied Telesis Inc.` / `Mounting` / `Initializing`, all in case 30's **good** keyword list, so
> the test concludes the foreign release **booted**.
>
> Also: **`BOOT_MARKERS` is broken on that build** — 3 of 4 markers dead, only `login:` survives
> (the last line of a completed boot). Use `Mounting` / `Initializing`.
>
> The ask is now singular: restore `Verifying release... OK` and `Error: This release file is not
> intended for this device.` Full detail + captures:
> `device-testing/IE520/automated-bootloader/ie520-5700-edit-inventory-2026-08-12.txt` and
> `new-bootloader-pauld-20260812/`.

**Ruled OUT as divergence — genuine universal test rot, correct to fix:**
`'Password Successfully updated'` (0 device lines on x230v2 too; the gate logs `wait time reached`
there as well, so x230v2 passed by accident-of-timeout identically), and the `dir *.rel` existence
parse (output format is **byte-identical** in shape on both: `flash:/mainrelease.rel`).

Corrects the "gate-string rot" framing in [[bootloader-media-parse-bug]]. Design principle:
**never reclassify a failing gate as "rot" from one platform's logs alone** — check a passing
platform first, or you convert a product finding into a test change.

> ## UPDATE 2026-10-06/07 — the pristine suite on x230v2-28GS, bootloader 6.2.40 (tb470 u0)
>
> Campaign `x230v2-28GS/bootloader-6.2.40/` (final logs b60a24c): 2001 PASS, 2002 PARTIAL, 2003
> PARTIAL, 2004 PASS, 2005 FAIL. What a re-run of this suite needs to know (all measured):
> - **The suite assumes the bootloader default boot source = TFTP** (every Feb boot was a forced
>   TFTP boot). With the default at 9 "determined by main CLI", 2002's configure asks TFTP for
>   `backuprelease.rel`, deletes flash's releases and leaves the unit with nothing to boot. Set
>   Boot Menu 2 → 3 before launch; set 2 → 9 back afterwards.
> - **The framework maps `AT-x230-28GS V2` to family `x230`**, so bootloader TFTP boots ask for
>   `/tftproot/x230-<tb>.rel`; a root symlink to the real file was needed (tmpfs, lost on reboot).
> - **Framework c1e7679 (2026-09-17)** runs the boot-config reset before tear_down even when a case
>   sets `doConfCheck = False`, so after a deliberate erase (2003.11, 2005.2) the case FAILs and
>   ATTestSet skips the rest of the TestSet. Feb's d4c21f7 did not. Harness, not product.
> - **6.2.40 on the 28GS prints `Erasing nand0:`** where Feb's 6.2.37 printed `Erasing flash:`;
>   2005.2's erase gate misses it although the erase happens. **Test Engineer 2026-10-07: wording
>   only, PASS for that TestCase**; the follow-up run's `library_5700.py` patch adds `'Erasing nand0'`
>   to the gate and `import copy` (2002.110's NameError). Diff: `5700_x230v2-28GS_6.2.40_run3/library_5700.diff`.
> - **2026-10-07 follow-up, one TestCase per invocation** (`test-5700.<set>.py -s default.setup -u -v <n>`):
>   the TestSet preamble still runs (~7.5 min); the baseline `.rel` must be OFF flash first or
>   configure runs out of space for `backuprelease.rel`. The framework console log is `swi_a.log`
>   (+ `swi_a-5700.<id>-tags.log`), so a sentinel CLI_GLOB needs `swi_a*.log`, not `swi_a_*.log`.
> - After factory defaults the framework answers the forced new-password dialog with `P@ssw0rd`
>   (friend is refused as default), so manager/friend logins fail until it is set back.
