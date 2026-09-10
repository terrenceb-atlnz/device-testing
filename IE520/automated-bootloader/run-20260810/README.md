# run-20260810 — first fix-and-validate pass (2026-08-10)

Ours, not bidhanc's. The inherited baseline campaign (2026-08-07/08) is his and lives in
`/home/bidhanc/5700_bootloader_x220/` — do not write there.

## What is in here

| Suite | Result | Runtime |
|---|---|---|
| 2001 | 9 PASS / 0 FAIL (rc=0) | 48 m |
| 2002 | 11 PASS / 8 FAIL / 7 UNSUPPORTED | 5 h 31 m |
| 2003 | 9 PASS / 4 FAIL / 2 UNSUPPORTED | 3 h 04 m |
| 2004 | 2 PASS / 0 FAIL (rc=0) | 17 m |
| 2005 (cases 1-3) | 2 PASS / 1 FAIL | 3 h 40 m |

`2005-run1-cases123/` holds the 2005 artefacts from THIS date. They were moved into that
subdirectory on 2026-08-11 because the 2026-08-11 re-run of 2005 executes in this same directory
and the framework renames `swi_a.log` -> `swi_a_2005.log` at the end of every TestSet, which would
have overwritten them. `test-5700.2005.log` in that folder was restored from a copy taken before
the 2026-08-11 run started (the framework had already overwritten the original in place, since it
opens the TestSet log without `-a`).

**Lesson: the framework overwrites its logs. A second run of the same suite in the same directory
destroys the first run's evidence.** Hence the dated run directories.

## Framework

`framework/` is a copy of the tree the baseline campaign actually ran
(`/home/bidhanc/5700_bootloader_x220/framework`), patched by us. Pristine originals are kept
alongside as `*.orig`:

- `ATDrivers/ATBootLoader.py.orig` md5 `6f539baed1183274757f31a7f0944707`
- `ATTestCase.py.orig` md5 `3485e8590fb27ea0fa809fab1daad8e5`

`/home/st-art/framework` is read-only and a DIFFERENT version — never point a run at it.

Runs must be started as root (`launch.sh` does this) or `eth1` reads as missing. See
`../Bootloader-Technical-Detail.md` and the session memory for why.
