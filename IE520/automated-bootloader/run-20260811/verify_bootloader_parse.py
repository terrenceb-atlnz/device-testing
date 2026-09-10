#!/usr/bin/env python3
"""
Replay the OLD and NEW ATBootLoader file-selection parse against REAL captured
bootloader output, so the fix is demonstrated rather than asserted.

Capture source: tb504 swi_a_2002.log, 2026-08-07 15:46:35 (bidhanc's campaign).
The menu offered "(1-1, 0 to cancel)" and the framework typed 4101515.
"""

# --- verbatim console capture -------------------------------------------------
REAL_USB = """6

Bus usb@50000: USB EHCI 1.00
scanning bus usb@50000 for devices... 5 USB Device(s) found
       scanning usb for storage devices... 1 Storage Device(s) found
  Reading filesystem...

            System Volume Information/
  1572864   IE520-bootloader-master-20260626-509.bin
 41015155   ---w-z-03-09-a-y---.rel
  1572864   IE520-bootloader-richardl.kwb
  1572864   IE520-bootloader-richardl.bin
  1572864   IE520-bootloader-master-20260717-518.bin
  1572864   IE520-bootloader-master-20260717-518.kwb

6 file(s), 1 dir(s)

Listing of usable files (root directory only)

  1. usb:---w-z-03-09-a-y---.rel

Enter selection (1-1, 0 to cancel) and press enter ==> """

# Same shape, but several usable files so the menu index is not trivially 1.
REAL_FLASH_MULTI = """  41015155   mainrelease.rel
  41015155   backuprelease.rel

2 file(s), 0 dir(s)

Listing of usable files (root directory only)

  1. flash:backuprelease.rel
  2. flash:mainrelease.rel

Enter selection (1-2, 0 to cancel) and press enter ==> """

# Menu never rendered (e.g. media pulled) - must select nothing, not guess.
TRUNCATED = """ 41015155   ---w-z-03-09-a-y---.rel

6 file(s), 1 dir(s)
"""


def old_parse(output, filename):
    """Pre-fix logic, verbatim from ATBootLoader.py:744-757."""
    for line in output.splitlines():
        if filename in line:
            try:
                return line.split()[0][:-1]
            except (ValueError, IndexError):
                pass
    return None


def new_parse(output, filename):
    """Post-fix logic."""
    menuLines = [x.strip() for x in output.splitlines()
                 if x.strip().endswith(':{}'.format(filename))]
    for line in menuLines:
        try:
            return int(line.split()[0].replace('.', ''))
        except (ValueError, IndexError):
            continue
    return None


CASES = [
    ("USB, awkward filename (the real 2026-08-07 failure)",
     REAL_USB, "---w-z-03-09-a-y---.rel", "4101515", 1),
    # Note both releases are 41015155 bytes, so OLD returns the SAME wrong index
    # ('4101515') whichever file was requested - it is not even self-consistent.
    ("flash, 2 usable files - wanted file is menu entry 2",
     REAL_FLASH_MULTI, "mainrelease.rel", "4101515", 2),
    ("flash, 2 usable files - wanted file is menu entry 1",
     REAL_FLASH_MULTI, "backuprelease.rel", "4101515", 1),
    ("NEGATIVE CONTROL: menu never rendered - must select nothing",
     TRUNCATED, "---w-z-03-09-a-y---.rel", "4101515", None),
]

ok = True
for desc, output, filename, expect_old, expect_new in CASES:
    got_old = old_parse(output, filename)
    got_new = new_parse(output, filename)
    old_ok = got_old == expect_old
    new_ok = got_new == expect_new
    ok = ok and old_ok and new_ok
    print(f"\n{desc}")
    print(f"  file wanted : {filename}")
    print(f"  OLD -> {got_old!r:<12} (expected {expect_old!r})  {'ok' if old_ok else 'MISMATCH'}")
    print(f"  NEW -> {got_new!r:<12} (expected {expect_new!r})  {'ok' if new_ok else 'MISMATCH'}")

print("\n" + ("ALL CHECKS PASSED" if ok else "*** CHECKS FAILED ***"))
raise SystemExit(0 if ok else 1)
