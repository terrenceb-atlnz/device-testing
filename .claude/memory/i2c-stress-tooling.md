---
name: i2c-stress-tooling
description: tools/i2c_stress.py + tools/i2c_stress_fw.py = two validated IE520 i2c stress scripts (standalone pyserial + thin framework wrapper), moved to repo-root tools/ 2026-10-02; smoke-tested clean on tb470 2026-08-26; 'show platform port' on a stacked pair = ~36 s / 344 KB, so 300 pairs ≈ 3.1 h, NOT the campaign's 2 s/iter figure
metadata:
  type: project
  verified: 2026-10-02
---

The re-created i2c stress tooling from the 2026-08-19/20 lockup campaign lives in the repo-root
**`tools/`** (moved from `IE520/i2c-stress/` on 2026-10-02; entries in `tools/README.md`).
`~/i2c_evidence.log` is the full campaign record; [[tb470-topology-and-setup]] has the bench.

- `tools/i2c_stress.py`: standalone. It needs pyserial only, no framework and no `.setup`, and
  takes `--baud/--user/--password`.
- `tools/i2c_stress_fw.py`: a thin wrapper over `ATSwitch.Switch(devicePath)`. It needs
  `PYTHONPATH=/home/st-art`, no `.setup` and no sudo.
- Both interleave `show platform port` + `show system pluggable diagnostics` N times each
  (default 300). Both stop at the first lock and recover hands-off: the IE520 watchdog
  self-resets about 42 s after a lock.
- Logs go to CWD. **Run from a fresh dated directory on the box's `/tmp`, never inside the
  repo** (logged-output.md §2). Commit what the case needs into its case folder.

**Both smoke-tested clean on tb470 2026-08-26.** The evidence stayed at
`IE520/i2c-stress/runs/2026-08-26-tb470-smoke/`. The run used u4+u5 stacked with 19
pluggables; the faulty AT-SPTXc …006 was quarantined, so it was absent from the inventory.

**Why:** the boss wants i2c stress runs on other IE520 units to trigger fails, and these are
the portable reproducer harness.
- The proven single-command reproducer is `show platform port`: a +2.6 s lock with …006 fitted.
- The DDM Vcc census in the baseline doubles as the field screen: the faulty module read
  Vcc 3.4167 V, above the 3.4000 V High threshold.

**How to apply:**
- **Budget the time from the stacked-pair figure.** `show platform port` covers 56 ports, so
  it returns 344 KB, about 36 s at 115200; serial transfer dominates. 300 pairs therefore take
  **about 3.1 h per console**. Never budget from the campaign's ~2 s per-unit figure.
- The framework variant drops an extra `swi_noname_4.log` at `Switch()` construction, despite
  the per-run log names. This is cosmetic.
- A full 300-iteration campaign was proposed but NOT yet run as of 2026-08-26. It is
  Terrence's call.
