# Session handover — 2026-10-09 (~08:20 NZDT): tb470 image update to awplus_main-20261008-57, probe MATCH, applied

Session `50f164f5…` (VS Code), 2026-10-08 15:4x to 2026-10-09 08:2x NZDT.
- It oriented on tb470 and traced why the backup consoles refused logins (the Test Engineer then
  fixed the user).
- At the Test Engineer's direction it updated every unit it could reach to the new builds in
  `/tftproot`, booted them from flash, and ran the full probe and `apply`.
- No test case ran, so no sentinel was armed.

## Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u2,u4,u5 at orient (last test bench run); then u0–u5 for the update (*"update all devices you can"*)
PDU: 10.36.150.14; outlets u0=1, u1=7, u2=6, u3=8, u4=4, u5=5 (tb470.static)
Constraints: "Run now, no power cycles" (carried from the 10-08 queue). No PDU action was taken; every reboot was a CLI reload.

The Test Engineer's direction, verbatim:
- *"I've updated the .rel files on tb470, please update all devices you can with the correct .rel
  files, have them boot those from flash, and THEN run the probe."*
- *"please apply the results when you are complete"*
- Their decisions:
  - **Flash space:** delete `release.rel` on the master.
  - **u3:** "its now 115200".
  - **Old images:** delete all.
  - **AR4050S:** "Skip 4050, probe now".

## TL;DR
- **The bench is whole and idle, not parked.** Wrap probe `2026-10-08T191510Z`: **MATCH** on all six
  consoles at 115200. `apply` ran at `2026-10-08T180908Z`, snapshot `bench-setup/backups/2026-10-08T180908Z.*`.
- **Every IE520 and the x230 run `awplus_main-20261008-57` from flash.** Each one now holds only that one `.rel`.
  The AR4050S is **not updated** (still `awplus_main-20260924-26`): it has no return path to tb470 (OPEN 1).
- **The backup-console login failure is explained.** The stack's running-config had `no username manager`.
  The Test Engineer re-created the user and saved it; u2 and u4 log in again. platforms/IE520.md §3 row rewritten.
- **Incident:** while stopping my own rejected `ckcon` on u5, I also killed the Test Engineer's minicom on u5,
  because we are the same Unix user. Memory `rejected-tool-calls-keep-running-remotely` (incident 6).

## Bench state left (read at this wrap, 08:14–08:15 NZDT 10-09)
Topology, consoles and links: [bench-state.md](../../bench-setup/bench-state.md) (generated `2026-10-08T191510Z`).

| unit | console | build | boot | flash free | notes |
| --- | --- | --- | --- | --- | --- |
| IE520 stack: members 1, 3 (Active Master), 4 | u2, u5, u4 | `awplus_main-20261008-57` (Oct 8 00:00:32 UTC) | bootloader: Flash + `IE520-awplus_main-20261008-57.rel`; `show boot` the same `(file exists)` | 65.1 / 59.7 / 65.1 MB | Normal operation; member 2 still `Provisioned` (absent). The three members have identical uptimes, so they booted together from the same parked file |
| IE520-sa | u3 | `awplus_main-20261008-57` | same file, bootloader + `boot system` | 65.2 MB | standalone |
| x230v2-28GS | u0 | `awplus_main-20261008-57` (Oct 8 00:10:09 UTC) | `boot system flash:/x230v2_28GS-awplus_main-20261008-57.rel (file exists)`, banner `Loading flash:x230v2_28GS-…` | 60.7 MB | boot config `default.cfg` |
| AR4050S | u1 | `awplus_main-20260924-26` (unchanged) | `flash:/AR4050S-tb470.rel` | 3.4 GB | not touched beyond reads |

- **Reboot history:** the only new entries are this session's CLI reloads (03:13–03:15 UTC 10-08 on the
  IE520s, 16:08 local on the x230). There has been no `Unexpected` entry on any unit since 10-05.
- **Running-only state:**
  - The x230 has `lldp run`, set by the probe; its startup `default.cfg` lacks it.
  - The x230's temporary `vlan11` 10.38.215.20/27 is **gone** (cleared by the reload, re-read).
  - Its 10-08 running-only `no lacp global-passive-mode enable` was also cleared by the reload
    (10-08 handover OPEN 4 is now moot).
- **Stack:** `username manager` is in both running and startup.
- **Files changed by this session:**
  - `boot system` on the stack and u3 (stored in boot config, needs no `write`);
  - the bootloader default boot source on all four IE520s (Boot Menu `2` → `1` → file, `Saving settings... Complete`);
  - the x230's `boot system`.
- **tb470:** unchanged. No route or IP was added. `10.10.10.0/27` has no route. eth2 has no carrier. Scratch
  `/tmp/loginprobe/` (tmpfs) holds this session's transcripts.

Verify:
```bash
sock=/run/user/$(id -u)/keyring/ssh
SSH_AUTH_SOCK=$sock ssh -o BatchMode=yes tb470 'cd ~/claude/device-testing/bench-setup && \
  python3 bench_probe.py --box tb470 precheck --consoles 0-5 && \
  python3 bench_probe.py --box tb470 run --consoles 0-5 --baud 115200 --no-prompt \
    --pdu 10.36.150.14 --outlet u0=1,u1=7,u2=6,u3=8,u4=4,u5=5'
```

## What was done
1. **Orient** (15:4x): the precheck was CLEAR, the probe on u2/u4/u5 gave USER-CONFLICT (u2/u4 `Login incorrect`).
2. **Login diagnosis on u5** (the Test Engineer asked):
   - running-config `no username manager` + `aaa authentication login default local`;
   - `flash:/tb470-bench.cfg` still had `username manager privilege 15 …`;
   - the probe captures date the loss to between 10-05 17:12 and 10-07 23:42 UTC;
   - the buffered log has no auth entries.

   The Test Engineer stopped a `show log permanent` read. My cleanup killed their minicom too (incident above).
   They then re-created the user.
3. **Image update**: each `/tftproot` image's sha256 matched its `.sha256sum`; every copy landed +0 bytes.
   - **Stack:**
     - deleted `release.rel` (24.2 MB, master only) and `IE520-awplus_main-20261002-47.rel` on all three members;
     - TFTP from 10.38.215.1 to the master took 323 s;
     - `boot system flash:/IE520-awplus_main-20261008-57.rel` synced members 1 and 4 in **72 s**;
     - parked member 1 (`reload stack-member 1`), member 4, then the master (`reload`), each Boot Menu
       `2` → `1` → file 1 → `Saving settings... Complete`.
   - **IE520-sa:** TFTP from **10.38.215.65** (eth3 ↔ its port1.0.2, vlan1 .69), parked the same way.
   - **Release:** a bare `9` on all four together (`tools/bootmenu_escape.py`); all reached `login:` and the
     stack re-formed.
   - **x230:**
     - temporary `interface vlan11` / `ip address 10.38.215.20/27`, running only (its port1.0.2 lands untagged in
       the stack's VLAN 1 = tb470 eth1's segment);
     - TFTP took about 40 s;
     - `boot system`, then `reload`; `login:` came after 164 s.
   - **Old images deleted** (Test Engineer: "Delete all old"): the calanm `IE520-tb470.rel` on all three
     members, `IE520-awplus_main-20261002-47.rel` on u3, and `x230v2_28GS-tb470.rel` on u0.
     (`IE520-sa` needed `boot system` to the new file first: AW+ will not delete the boot-image file.)
4. **Probe** `2026-10-08T180837Z`: MISMATCH, i.e. the recabling since the last apply, plus one NEEDS-CHECK
   (eth2 no carrier, which the template dropped). **`apply`** went in at the Test Engineer's request.
   **Wrap probe** `2026-10-08T191510Z`: MATCH.

## Results
No test cases ran. **Final logs: none to create.**

## Findings
**Measured:**
- The backup-console login failure (u2/u4) coincided with `no username manager` in the stack's running-config,
  and cleared when the user was restored. The user then survived a reload onto `20261008-57`.
- A stack `boot system` sync of 40.3 MB to two members took 72 s (195 s on 10-06).
- On bootloader 9.2.0, a park from `reload` to `Ctrl+B` took 5–14 s.

**Inferred, not proven:**
- The master's own console still accepted `manager` through a local-console fallback.
- What removed the user between 10-05 and 10-07 is unknown. The stack was reloaded many times by
  several sessions in that window.

## OPEN
1. **AR4050S update:** skipped. It needs `sudo ip route add 10.10.10.0/27 via 10.38.215.10` on tb470 (yours).
   Then `ip route 10.38.215.0/27 10.10.10.1` on the 4050 (running only), `copy tftp://10.38.215.1/AR4050S-tb470.rel
   flash:/AR4050S-awplus_main-20261008-57.rel` (67,692,655 B), `boot system`, `reload`, delete the old
   `AR4050S-tb470.rel`. Do it now, or wait for the next build?
2. **Make the park scripts repo tools?** The IE520 image update has now run three times (10-05, 10-06, 10-08).
   Recipe below. Add `park.py` (and the reload-then-park wrapper) to `tools/`?
3. **Image names:** units now boot dated files (`IE520-awplus_main-20261008-57.rel`), not the conventional
   `<PLATFORM>-tb470.rel`. Fine as is, or rename at the next update?
4. **Member 2 still provisioned:** `no switch 2 provision`? T22650 keeps failing on 0x0049 while it stays.
   Carried from 10-08.
5. tb470 `/tftproot` cleanup still owed (from 10-08, root): `x250-tb470.rel`, `x230-copy-tb470.rel`, the
   `x230-tb470.rel` symlink.

## Next steps
1. Push (`git push origin main`; this commit is local).
2. Decide OPEN 1–3.

## Recipes
**Park an IE520 on Flash + a file (scripted, 2026-10-08).**
- Open the port with `stty -F <tty> -hupcl` first, at 115200.
- Read until `Ctrl+B` appears.
- Then send `\x02` every 0.25 s until `Enter selection` appears. Confirm `9. Quit and continue booting` is on screen.
- Send a bare `2`. Wait for `Enter selection`, find `(\d)\.\s*Flash`, and send that digit bare.
- Wait for `to cancel)`. Find `(\d+)\.\s+flash:<file>\s` in `Listing of usable files`, and send the number + `\r`.
- Wait for `Saving settings... Complete`, then `Enter selection`. Leave it there.
- Stop and send nothing more on anything unexpected.

Who sends the `reload`:
- **A stack member:** start the watcher on its console, then send `reload stack-member N` on the master and
  answer `y\r`.
- **The master or a standalone:** log in on that same port, send `reload`, answer `y\r` (answer `n\r` to any
  save question), close, then start the watcher.

Release all the parked units together with `tools/bootmenu_escape.py <tty>` (it sends a bare `9`).

**`boot system` with a sync wait:** `configure terminal` → `boot system flash:/<file>`. Read the console until
`File synchronization with stack member N successfully completed` appears for every member, then `end`.

## Pointers
- Procedure memory: `ie520-image-update-procedure` (updated with Step 0, 2026-10-08 timings, x230/AR4050S paths).
- Platform row: [platforms/IE520.md](../../platforms/IE520.md) §3, backup-console logins.
- Previous handover: [SESSION-HANDOVER-2026-10-08.md](SESSION-HANDOVER-2026-10-08.md).
- Sentinel: none was armed (no test cases); nothing to stand down.
