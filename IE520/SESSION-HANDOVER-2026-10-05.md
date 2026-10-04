# Session handover — 2026-10-05 (stack restored from the rollback; the SA is unresponsive)

## Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u2,u3,u4,u5 (stack + SA); u0 read by the probe; **u1 NOT touched** (held by the Test
Engineer's `minicom --wrap -D /dev/u1`, PID 527573, all session)
PDU: 10.36.150.14; outlets per bench-setup/tb470.static
Constraints: none stated

Continues [SESSION-HANDOVER-2026-10-02.md](SESSION-HANDOVER-2026-10-02.md): the rollback to
`tomahawk_ie520-20260825-42` and the split it caused.

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
