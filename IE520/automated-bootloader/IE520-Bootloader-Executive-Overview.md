# Bootloader TestSuite (5700) — Executive Overview

**Campaign:** tb504 · IE520 · bootloader `master-20260717-518` · 2026-08-07 → 2026-08-08 (18 h 24 m)
**Author:** Terrence Beach · **Date:** 2026-08-10
**Evidence base:** `Bootloader-Technical-Detail.md`

---

## Bottom line

Twenty-four test cases failed. **None is a confirmed product defect.** They reduce to four causes in
our own test framework and scripts, plus three structural faults that turned small failures into
large ones. About **half the 18-hour campaign was spent inside failures the device had nothing to do
with**, and the final suite died without finishing.

The device itself came through clean: no flash damage, no crashes, no memory faults.

The problem is not the IE520. The problem is that **we cannot currently trust most of what the
campaign reported** — and one requirement is recorded as passing when it was never actually tested.

---

## By the numbers

| | |
|---|---|
| Test cases failed | **24** |
| Confirmed product defects | **0** |
| Campaign time lost to our own tooling | **~9 h of 18 h 24 m** |
| Requirement IDs referenced | **47** |
| …with a trustworthy passing verdict | **≤18 (38%)** |
| Security suite (2005) cases that produced a result | **2 of 8** |

Suites 2001 (9/9) and 2004 (2/2) are entirely clean.

---

## What went wrong

| Cause | Cases | Cost |
|---|---|---|
| **Bootloader menu parser reads the file *size* as the menu *index*** — sends `4101515` instead of `1` | 11 | ~5 h |
| **Gate strings the current bootloader no longer emits** — e.g. the suite waits for `"Verifying release"`, which appears nowhere in 18 hours of console output | 8 | ~3 h |
| **Flash test / erase / security-reset budgets are shorter than the operations take** — cut off mid-progress-bar | 3 | ~1.5 h |
| **A diagnostics menu option the test plan expects no longer exists** on this build | 2 | ~10 m |

Three structural faults amplified all of the above:

- **An exception in `main()` skips `tear_down()` entirely.** Any case that changes device state and
  relies on teardown to restore it leaks that state permanently. This is what turned one parser bug
  into five further failures across the following ten hours.
- **A bare `sys.exit()` in `library_5700.py` kills the whole run — and exits with code 0.** It is why
  6 of 8 security cases never executed, and why an abandoned run looks like a successful one to
  anything reading the exit code.
- **The framework cannot answer a bootloader password prompt.** The device was left password-
  protected, which now blocks re-running 2002, 2003 *and* 2005.

**Two failure modes cost 30 minutes each, every time they fire**, because the suite inherits a
1800-second default timeout instead of setting a realistic one.

---

## What to do first

Four items unblock everything else. Three are one-line changes in files we now own locally.

1. **Clear Security Level 2 on tb504.** Mandatory — nothing can re-run until it is done. It wipes
   the flash filesystem, so it needs a re-image plan and about 20 minutes of bench time.
2. **Replace the bare `sys.exit()`** (`library_5700.py:663`) with a scoped test-case abort.
3. **Move state restoration into a `finally:` block** inside each `main()`, so it survives an
   exception.
4. **Fix the inverted assertion** at `test-5700.2002.py:320` that produces the false pass.

After those, the substantive fixes are the menu parser, the stale gate strings, and realistic
timeouts. Expected result: the campaign shortens by roughly **8 hours** and the remaining failures
become worth reading.

Full ordered list — 15 items — in the technical detail.

---

## What is *not* wrong

Checked rather than assumed, because these will be asked:

- **No flash damage.** `bad PEBs: 0` and `corrupted PEBs: 0` in all 711 reports, including after an
  interrupted erase and a 678-cycle reboot loop.
- **No device crashes.** 42 exception-log checks, all clean.
- **No memory faults.** Every DRAM test reports zero errors.
- **Alarming-looking log noise is benign** — 81 rejected CLI commands are shell probes issued before
  a licence is installed; the framework retries and succeeds.

One item may be a genuine product question: a diagnostics-menu option for U-Boot access has gone
from this build while the `Ctrl-U` route still works. That is a question for the bootloader team,
not a defect claim.

---

## What we cannot yet claim

Being direct about this, because it is the thing most likely to be over-read:

- **Security Level 3 has no coverage at all.** That test case never ran.
- **The most security-relevant test — whether levels 2 and 3 block shell access — never ran.**
- **AWP2684 is recorded as verified and is not.** The test reached a pass verdict in 33 seconds for
  an operation that takes minutes; it never performed the check.
- 28 of 47 requirement IDs ended the campaign with no passing verdict.

We have a credible plan to make the campaign run to completion. We do **not** yet have evidence that
the bootloader security feature works as specified.

---

## Confidence and caveats

Findings are grounded in the campaign's own console transcripts — quoted output is verbatim device
capture, not inference. Three earlier conclusions were corrected during analysis as better evidence
emerged; those corrections are recorded in the detail document.

Two limits worth stating: the framework version analysed differs by a few lines from the one that
ran, so line numbers should be confirmed before patching; and the bench state is as of 2026-08-08,
since a console session has been open on the device since then without logging.
