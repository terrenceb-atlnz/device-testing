# run-20260811 — second validation pass (2026-08-11)

Ours. Evidence kept separate from `../run-20260810/` on purpose: the framework overwrites its own
logs, so re-running a suite in the directory that already holds that suite's results destroys them.
One dated directory per run day.

## Framework

`framework/` is carried over from `../run-20260810/framework`, i.e. the tree the inherited
2026-08-07/08 baseline actually ran, plus our patches. Pristine originals kept as `*.orig`:

- `ATDrivers/ATBootLoader.py.orig` md5 `6f539baed1183274757f31a7f0944707`
- `ATTestCase.py.orig` md5 `3485e8590fb27ea0fa809fab1daad8e5`

Patches present in this copy:

- **F7** — `__set_swi_boot_from_media_via_bootrom()` selected the file SIZE as the menu index
  (`41015155`[:-1] -> `4101515`). Now anchors on `endswith(':<filename>')`.
- **A2** — `KEYWORD_SAVING_SETTINGS = 'Saving settings... Complete'` never matches; the bootloader
  interleaves SPI progress between the halves. Now a split match. This bug was MASKED by F7.
- **F13** — `_post_tear_down()` ran its config compare even for TestCases built `confCheck=False`,
  manufacturing two extra failures on the abort path. Restore kept, compare skipped.

## Running

    ./launch.sh <suite> [case ...]        e.g.  ./launch.sh 2005 3 4 5 6 7 8

`launch.sh` re-syncs `library_5700.py`, `test-5700.<suite>.py` and `default.setup` from `../`
(the staging copies) on every launch, runs as root — required, or `ATTestBox.Eth` cannot read the
0600 NetworkManager file and `eth1` is reported as missing — and detaches with `setsid nohup` so
the run survives an SSH drop.

No `.atpylib_publisher.json` here, so `ATPublisher` stays disabled and nothing reaches the shared
results DB.
