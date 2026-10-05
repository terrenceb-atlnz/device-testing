# Session handover — 2026-10-05 (old build stacked as 2 members; u2 standalone; the SA is unresponsive)

## Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u2,u3,u4,u5 (stack + SA); u0 read by the probe; **u1 NOT touched** (held by the Test
Engineer's `minicom --wrap -D /dev/u1`, PID 527573, all session)
PDU: 10.36.150.14; outlets per bench-setup/tb470.static
Constraints: none stated

Continues [SESSION-HANDOVER-2026-10-02.md](SESSION-HANDOVER-2026-10-02.md): the rollback to
`tomahawk_ie520-20260825-42` and the split it caused.

## UPDATE ~14:45 NZDT — bench swaps, GUI updates, the pending stack reload

- **u1 is no longer the AR4050S.** It was an IE560 (5.5.6-1.2), and is now an **IE360**
  (5.5.6-1.2, `IE360-5.5.6-1.2.rel`), on `default.cfg`, with port1.0.1 cabled to tb470 eth2.
  At boot the IE360 logged `Voltage: Input 1: Alarm asserted. Reading:0.000` (one PSU input unfed?).
- **u0 is now an x230-28GS v2** (the Test Engineer's swap; they are updating it under minicom). Not
  read by this session.
- **GUI updated on both the IE560 and the IE360** to `awplus-gui-20261005_1020.gui`, saved as
  `awplus-gui_556_99.gui`; `show http` → `GUI file in use : awplus-gui_556_99.gui`. Old GUIs
  (`_555_38` and `_554_34`), the script and the temporary IP/route were removed afterwards. Recipe:
  memory `awplus-gui-load-script`.
- **Stack update to `awplus_main-20261002-47` (tb470 `/tftproot/IE520-tb470.rel`, dropped 10:54
  today) is HALF DONE. Do not assume it is finished:**
  - On both members the `20260923-20` copy of `IE520-tb470.rel` was deleted to make room.
  - `flash:/IE520-awplus_main-20261002-47.rel` (40,121,127 bytes) was TFTPed to the master (u4).
  - `boot system flash:/IE520-awplus_main-20261002-47.rel` was sent on the master at ~14:11 (the
    tool call was rejected but ran remotely) and started the stack file sync to member 1 (u5).
    Neither its completion nor member 1's copy has been verified.
  - **No reload yet.** The stack runs the old build. The Test Engineer wants it run after they
    finish the x230 v2.
  - Next: verify `dir IE520-stk-1/flash:/IE520-awplus_main-20261002-47.rel` = 40,121,127, and
    `show boot`. Then reload and check that the bootloader banner reads
    `releasefile=IE520-awplus_main-20261002-47.rel`.
- **u2** is still on `20260923-20`. `coro-…` was deleted, so 65 MB is free. The new image could not
  be fetched (`% Network is unreachable`): u2 has no IP, and its only links go to the x230. It needs
  a network path first.

## UPDATE ~10:30 NZDT — READ THIS FIRST: the OLD build is now stacked (2 members); u2 is out

The ~08:20 restore below (the stack back on the new build) was **not what the Test Engineer
wanted**: *"i wanted them on the old build, but i wanted the old build stacked"*. The old build
takes member IDs 1–2 only, so on their answers ("u5 + u4", "Disable stacking on it", "Translated
copy", "Default config" for u2):

| console | unit | now | build | boot config |
| --- | --- | --- | --- | --- |
| u5 | S/N 264A23066, MAC …0740 | **stack ID 1, Active Master** (was 3) | `tomahawk_ie520-20260825-42` | `flash:/tb470-oldstack.cfg` |
| u4 | S/N 264A23052, MAC …09c0 | **stack ID 2, Backup Member** (was 4) | `tomahawk_ie520-20260825-42` | `flash:/tb470-oldstack.cfg` |
| u2 | S/N 264A23061, MAC …0ac0 | **standalone, stacking disabled** (`no stack 1 enable`), hostname `IE520-u2` | `awplus_main-20260923-20` | `flash:/u2-standalone.cfg` |
| u3 | SA | still unresponsive (below) | | |

- `tb470-oldstack.cfg` is `tb470-bench.cfg` translated: port3.0.x→port1.0.x and port4.0.x→port2.0.x,
  u2's port1.0.x blocks dropped, `switch 3/4 provision` dropped, `interface sa2-3` → `sa3`.
  `sa2` (the x230) had all its legs on u2, so **the stack has no link to the x230 now**. u2's
  ports 1.0.2/1.0.9 still face the x230's sa2, in VLAN 1 under u2's default STP.
- `u2-standalone.cfg` holds only: hostname `IE520-u2`, `no stack 1 enable`, `lldp run`, console
  exec-timeout. It has no IP addresses and no aggregators.
- The configs were delivered with `copy http://10.38.215.1:8080/<file>` from a user-space
  `python3 -m http.server` in tb470 `/tmp/ckflash/http` (stopped afterwards). No root write.
- Verified on the new build first (renumber reload 10:15–10:19), then on the old build (10:26):
  - IDs 1 and 2 Ready, with no `member-ID … invalid`;
  - no "forced" warning in the bootloader banner (`releasefile=coro-IE520-tb470.rel`);
  - `remote-diff` identical;
  - `sa1` (to the AR4050S, LLDP on 1.0.2/2.0.2) and the host links port1.0.9/1.0.10 running;
  - vlan1 `10.38.215.10` and vlan10 `10.10.10.1` up.
- Expected noise: `Not all stack ports are up`, plus VCS `Neighbor discovery has timed out on
  link port1.0.28 / port2.0.27`. Those stack ports face u2, which now has stacking disabled.
- **Do not `bench_probe.py apply`**: the bench is deliberately off-template.

**Way back to the 1/3/4 stack on the new build** (untested; check the bootloader banner each time):
1. On the old-build stack: `boot system flash:/IE520-tb470.rel`, then reload.
   - Earlier today the old build's `boot system` did not reach a FORCED bootloader. The forced
     setting is cleared now (Boot Menu 2→9), so it should be followed. If the banner still reads
     `coro-…`, use Boot Menu 2→9 (platforms/IE520.md §2).
2. On the new build: `stack 1 renumber 3`, `stack 2 renumber 4`,
   `boot config-file flash:/tb470-bench.cfg`.
3. On u2: `stack 1 enable` (remove the `no` form), `boot config-file flash:/tb470-bench.cfg`.
4. Reload all three, then `show stack` → 1/3/4 Ready, and re-probe → MATCH.

## TL;DR — read first

- **The stack is whole again on `awplus_main-20260923-20`.** IDs 1, 3 and 4 are Ready, member 3
  (u5) is Active Master, `Normal operation`, virtual MAC `0000.cd37.0d6f`, `remote-diff` running
  configs identical, `show boot` = `flash:/IE520-tb470.rel (file exists)`. All three read
  `Software version : awplus_main-20260923-20` (08:23 NZDT).
- **The SA (swi_b, u3, S/N 264A23068, PDU outlet 8) is unresponsive. OPEN.**
  - Its console is silent at 115200 and at 9600 and prints nothing when listened to.
  - Its three links to the stack (port1.0.13, port4.0.9, port4.0.26, so `sa3`) are down, and it
    is not an LLDP neighbour.
  - tb470 eth2, cabled to its port1.0.2, still has carrier, so it has power.
  - It was last seen healthy 2026-10-02 ~10:25 NZDT, left at exec. This session sent it nothing
    before finding it like this.
  - Likely wedged; the cause is not established. Recovery is a power cycle on outlet 8, which is
    the Test Engineer's call.
- **Probe `2026-10-04T192131Z` (08:21 NZDT, consoles u0,u2–u5): MISMATCH, all from swi_b**
  (`CONSOLE_DOWN` on swi_b and its links, `CHECK_CABLE` on eth2). Do not `apply`.
- `coro-IE520-tb470.rel` (the old build, 41,104,007 bytes) is still in flash on members 1, 3 and
  4. That leaves about 24 MB free. Delete it once the rollback work is finished.

## What was done

1. **Corosync / CMSG log check:** recorded in the 2026-10-02 handover (commit `0cf258d`). No
   corosync anywhere; two `CMSG … Receive took 60 s` lines on u2, from before the rollback.
2. **`boot system flash:/IE520-tb470.rel` on each standalone unit (old build), then reload:** all
   three booted the OLD build again. The bootloader was **forced** to boot from a non-standard
   location, saving `coro-IE520-tb470.rel`, and the old build's `boot system` does not clear that.
   Mechanics: `platforms/IE520.md` §2.
3. **Boot Menu `2` → `9` on each unit:**
   - u5 08:09, then u2 and u4 08:15. Each printed `Saving settings… Complete`, then
     `bootmenu_escape.py` sent `9` and the unit booted to `login:`.
   - u5 came up first as `Disabled Master` (failover mode) while the others were still old-build
     masters.
   - When u2 and u4 booted, the stack re-formed at about 08:20, and members were Ready by 08:21.
   - Driver: the session scratchpad's `boot_default.py`, copied to tb470 `/tmp/ckflash/` (tmpfs).
     The recipe is in the platform file.

## Next steps

1. Decide on the SA (u3): power-cycle outlet 8, or inspect it first. Then re-probe → expect MATCH.
2. When the rollback verification is finished, `delete flash:/coro-IE520-tb470.rel` on members
   1, 3 and 4.
3. Note: tb470 `/tftproot/IE520-tb470.rel` still holds the OLD build (`.info` =
   `IE520-tomahawk_ie520-20260825-42.rel`, dropped 2026-10-02 09:24). A netbooting unit would load
   it.
