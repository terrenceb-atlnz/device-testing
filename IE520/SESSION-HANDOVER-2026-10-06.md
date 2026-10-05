# Session handover — 2026-10-06 (wrapped ~06:20 NZDT)

## Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u0,u1,u2,u3,u4,u5 (u6 absent)
PDU: 10.36.150.14; outlets per bench-setup/tb470.static (u0's new unit added as swi_f, outlet 1)
Constraints: none stated

Continues [SESSION-HANDOVER-2026-10-05.md](SESSION-HANDOVER-2026-10-05.md); its "old build stacked"
and "half done" sections are superseded by this file.

## TL;DR — read first

- **The bench is the template again, and the template was re-applied.** Probe
  `2026-10-05T171256Z` → **MATCH**. `apply` snapshotted the old files to
  `bench-setup/backups/2026-10-05T171214Z.*`.
  - The new template records u0's new unit as **swi_f**: board reads `AT-x220-28GS`, S/N
    `A10783G262900002`, runs `x230v2_28GS`; the Test Engineer calls it the x230-28GS v2; outlet 1.
  - **tb470 eth2 now goes to swi_f port1.0.1** (it used to go to the SA's port1.0.2).
- **All four IE520s run `awplus_main-20261002-47`** (build Fri Oct 2 03:05:01 UTC). The stack is
  1/3/4, all Ready, member 3 (u5) Active Master, `Normal operation`, and `remote-diff` reads
  identical. The SA (u3) is standalone.
- **🔥 OPEN — someone else's work on the stack is in progress. Read this before any reload.**
  - On 2026-10-05 at 16:24 NZDT a new developer build, `IE520-main-calanm.rel` (tb470
    `/tftproot/IE520-tb470.rel`, 40,122,919 bytes), was put on the stack master as
    `flash:/IE520-tb470.rel`, and the master's `show boot` now names it.
  - Members 1 and 4 have an `IE520-tb470.rel` of **40,121,127** bytes, the size of `20261002-47`,
    not of the calanm build. **The same name holds different files on master and members.**
  - The stack log shows 6 `User Request` reloads, 3 `SW version auto synchronization` reboots and
    one `Unexpected System reboot` on all three at ~04:40 UTC (17:40 NZDT 10-05). None of these
    were this session's.
  - They still RUN `20261002-47`. Their bootloaders are set to **Flash +
    `IE520-awplus_main-20261002-47.rel`** (below), which overrides `boot system`; that is probably
    why, but it is not confirmed.
  - Before loading the calanm build, put the identical file on every member: TFTP to the master,
    then the master's `boot system` sync. Then follow the update procedure.

## What was done (2026-10-05 15:00 → 2026-10-06 06:15 NZDT)

1. **Back to the full bench on the current build** (Test Engineer: "make the 3 stack again with the
   sa device"):
   - u5 rebooted unexpectedly at 14:59 NZDT and came up on `20261002-47`; u4 was reloaded onto it.
   - Renumbered 1→3 and 2→4. Boot config `tb470-bench.cfg`.
   - u2: `stack enable` (the `stack 1 enable` form is rejected), boot config `tb470-bench.cfg`.
   - Reloaded together. The master auto-synced `20261002-47` to u2 ("Software incompatibility
     detected for Member 1" → "SW version auto synchronization successfully completed"), and the
     stack re-formed 1/3/4.
2. **The SA (u3) was wedged** (silent console; its links to the stack down). It was **power-cycled
   on PDU outlet 8** at 15:26:59–15:27:09 NZDT and came back.
   - It got the new image over a temporary unsaved secondary `10.38.215.30/27` (VLAN 1 via `sa3` and
     the stack to tb470 eth1), dropped at its next reload.
3. **The Test Engineer's image-update procedure** (memory `ie520-image-update-procedure`), run on all
   four units:
   - Each unit was parked at the Boot Menu with `2` → `1` (Flash) →
     `IE520-awplus_main-20261002-47.rel` (`Saving settings... Complete`): members first, then the
     master and the SA.
   - Then `9` on all four. Every banner read `forced to boot from a non-standard location` (expected)
     and `Reading flash:IE520-awplus_main-20261002-47.rel`.
   - The old `.rel` files were deleted: `coro-IE520-tb470.rel` on u5/u4, `IE520-tb470.rel`
     (`20260923-20`) on u2 and the SA.
   - Before the procedure was given, `2 → 9` (follow the CLI) had been used on all four; that is
     now superseded.
4. **u1:** the IE560 and then the IE360 got their GUI updated to `awplus-gui-20261005_1020.gui`
   (memory `awplus-gui-load-script`). The AR4050S (swi_e) is back on u1.
5. **tb470 `/tftpboot`** (a symlink to `/tftproot`): `bl-6.2.40-x220-0B26-F527.kwb` was copied there
   at the Test Engineer's request. sha256 `fa036126…387a2` matches `~/Downloads`. u0's unit now runs
   bootloader 6.2.40.
6. **Probe and apply:**
   - The first probe found u0's unit unlisted (named `swi_g` for the run) and eth2 with no carrier.
   - eth2 then came up on u0 port1.0.1, and `tb470.static` got `A10783G262900002 = swi_f, 1`
     (Test Engineer, 2026-10-06). The old x230 line (`G26ZE80EN`) was commented out as removed.
   - Re-probe → MISMATCH only for the eth2 move → `apply` → MATCH.
   - One probe straight after `apply` read a transient 4-item MISMATCH. Its detail was not
     captured; the next two read MATCH.

## Findings

- **Measured:**
  - The old build's (`tomahawk_ie520-20260825-42`) `boot system` DOES reach a non-forced
    bootloader: u5's unexpected reboot loaded the new file.
  - A Flash + file bootloader setting ignores `boot system` entirely.
  - `PduPower` `OSError(40)` is a self-symlink when the CWD equals `logFilePath` (orient-dt §4).
- **Measured:** silent reboots continue on `20261002-47` too.
  - u5 at 14:59 NZDT 10-05, unexpected, while the stack was mixed-build.
  - The SA wedged sometime before 08:21 NZDT 10-05 (silent console, links down); power cycle needed.
- **Inferred:** the 17:40 NZDT "Unexpected System reboot" on all three stack members at once
  suggests a common cause (a power event, or the calanm work), not a per-unit fault. Not established.

## OPEN — for the Test Engineer

1. **The calanm build on the stack (above):** finish or roll back. Either way, make
   `IE520-tb470.rel` identical on all members first.
2. **Leftover config files from the 2026-10-05 rollback work:**
   - `tb470-oldstack.cfg` on u5 and u4;
   - `u2-standalone.cfg` on u5, u4 and u2.

   They are not in use (boot config is `tb470-bench.cfg`). Delete them?
3. **u0's board identity:** it reads `AT-x220-28GS` (board ID 508) but runs the `x230v2_28GS`
   release. Expected for this unit?

## Verify the bench

```bash
sock=/run/user/$(id -u)/keyring/ssh
SSH_AUTH_SOCK=$sock ssh -o BatchMode=yes tb470 \
  'cd ~/claude/device-testing/bench-setup && python3 bench_probe.py --box tb470 precheck --consoles u0-u5 \
   && python3 bench_probe.py --box tb470 run --consoles u0-u5 --no-prompt'
# then on u5: show boot ; dir ; dir IE520-stk-1/flash: ; dir IE520-stk-4/flash:   (the IE520-tb470.rel sizes)
```

## Recipes (scratch, not repo tools — recreate from here)

- **Park a unit on Flash + a file:** reload, tick Ctrl+B only until `Enter selection` appears,
  bare `2`, bare `1`, then the file's listed number + Enter. Wait for `Saving settings...
  Complete`, then leave it at the main menu. Release with a bare `9` once all are set.
- **Power-cycle an outlet:** from an empty directory on tb470,
  `PYTHONPATH=/home/st-art python3 -c "from framework.ATDrivers.ATPower import PduPower as P; p=P('10.36.150.14', socketNum=8); p.off(); import time; time.sleep(10); p.on()"`.
- **Deliver a small file to a unit without root:** `python3 -m http.server 8080 --bind <tb470 NIC IP>`
  in a `/tmp` directory, then `copy http://<ip>:8080/<file> flash:/<file>` on the unit. Stop the
  server afterwards.

## Pointers

- Bench: [../bench-setup/bench-state.md](../bench-setup/bench-state.md) (Generated `2026-10-05T171256Z`, MATCH).
- Static facts: [../bench-setup/tb470.static](../bench-setup/tb470.static).
- Platform mechanics: [../platforms/IE520.md](../platforms/IE520.md) §2 (Boot Menu, Flash + file).
- Previous handovers: [SESSION-HANDOVER-2026-10-05.md](SESSION-HANDOVER-2026-10-05.md),
  [SESSION-HANDOVER-2026-10-02.md](SESSION-HANDOVER-2026-10-02.md).
