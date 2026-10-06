# Session handover — 2026-10-07, wrap of the x230v2-28GS bootloader 6.2.40 campaign (tb470 u0)

The campaign ran 2026-10-06 in session `device-testing-c7` (one-session `/test-mode`). Terrence
could not return to that session, so session `device-testing-13` ran `/create-logs` and this wrap
on 2026-10-07 07:30–08:00 NZDT at his request. `device-testing-c7` was told not to act; it made no
commits.

## Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470 (this host's default and the last test bench run)
Consoles: u0 only (x230v2-28GS, S/N A10783G262900002, swi_a in this run's setup)
PDU: 10.36.150.14, outlet 1 (u0)
Constraints: "do not interact with any other devices yet" (u0 + its PDU outlet 1 only). Sentinel stands down "When the run ends". Host session: "Stay in VS Code" (risk accepted).

(Copied from the campaign queue, [CAMPAIGN-QUEUE-2026-10-06T1325.md](../../x230v2-28GS/bootloader-6.2.40/CAMPAIGN-QUEUE-2026-10-06T1325.md).)

## TL;DR

- **Campaign done, final logs created** (b60a24c): 5700.2001 PASS, 2002 PARTIAL, 2003 PARTIAL,
  2004 PASS, 2005 FAIL. README: [x230v2-28GS/bootloader-6.2.40/README.md](../../x230v2-28GS/bootloader-6.2.40/README.md).
- **u0 is whole and idle at `login:`**: standalone x230v2-28GS, powered on (outlet 1), software
  `awplus_main-20261006-52`, bootloader 6.2.40, boots `flash:/x230v2_28GS-tb470.rel`, boot config
  `flash:/default.cfg`, Boot Security Level none. **Bootloader default boot source set back to
  9 "Boot from default (determined by main CLI)" at the wrap** (Terrence's choice), proven by a
  plain reload: `Loading flash:x230v2_28GS-tb470.rel...`, no forced-boot banner.
- **Sentinel stood down**: c7 stopped its Monitor and cron at 2026-10-06 21:12. This session had
  no Monitor or cron. No suite, watcher or driver process is left on tb470, and u0 has no holder.
- **bench-state.md was NOT regenerated** (see OPEN 5).

## Bench state and how to verify it

```bash
sock=/run/user/$(id -u)/keyring/ssh
SSH_AUTH_SOCK=$sock ssh -o BatchMode=yes tb470 \
  'cd ~/claude/device-testing/bench-setup && python3 bench_probe.py --box tb470 precheck --consoles u0'
# read-only device row, without overwriting the repo's bench-state.md:
SSH_AUTH_SOCK=$sock ssh -o BatchMode=yes tb470 'mkdir -p /tmp/ckwrap && cd ~/claude/device-testing/bench-setup && \
  python3 bench_probe.py --box tb470 run --consoles u0 --read-only --no-prompt --pdu 10.36.150.14 \
  --outlet u0=1 --out /tmp/ckwrap/bench-state-u0.md; sed -n "/## Devices/,/## Links/p" /tmp/ckwrap/bench-state-u0.md'
# the probe leaves u0 logged in: log out afterwards (exec mode: "exit").
```

Read 2026-10-07 07:35 (read-only probe, capture on tb470 `/tmp/ckwrap/`): `/dev/u0 | 9600 | swi_f |
AT-x230-28GS V2 | A10783G262900002 | awplus | standalone | awplus_main-20261006-52 | 6.2.40 |
flash:/x230v2_28GS-tb470.rel`. The probe's MISMATCH (32 items) is every other device of the
full-bench template that a u0-only probe does not read, so it is expected. NEEDS-CHECK: eth3 carrier up, MAC not learned
(read-only, no pings); eth1/eth2 carrier down.

Host (07:40): eth1 and eth2 carrier down, eth3 up; addresses as TB470-HOST-NETWORKING.md; eth2/eth3
advertise 10/100/1000/2500 (no pinning). `/tftproot` (tmpfs) holds `IE520-tb470.rel`,
`x230v2_28GS-tb470.rel`, the symlink `x230-tb470.rel -> x230v2_28GS-tb470.rel`, and two suite
files `x230-copy-tb470.rel` (17:59) and `x250-tb470.rel` (16:12). All root-owned; left as found.

## What was done

- 2026-10-06 (c7): triage, run 1 (stopped 14:58, see the queue), u0 recovery, run 2 of the whole
  suite 15:18–20:58, u0 restored to the run-2 baseline by 21:07 (running-config identical to the
  pre-run capture), logged out.
- 2026-10-07 (this session):
  - `/create-logs`: five final logs + group README from the run-2 working logs; `work/` folders
    removed (in history at b60a24c^). **Commit b60a24c.**
  - Wrap: precheck CLEAR; read-only u0 probe; u0 logged out; Boot Menu 2 → 9 on u0 + proof
    reload (07:47–07:53, driver `/tmp/x230/blmenu2.py` on tb470, the same one the tester used
    at 13:58 on 10-06); 69 untracked framework `*-tags.log` files deleted (Terrence's choice); a
    memory update; this handover.

## Results

| case | verdict | run label | final log |
| --- | --- | --- | --- |
| 5700.2001 | PASS | clean: 11/11, rc 0 | [5700.2001.log](../../x230v2-28GS/bootloader-6.2.40/5700.2001/5700.2001.log) |
| 5700.2002 | PARTIAL | clean: 18 PASS / 7 UNSUPPORTED (no SD slot) / 2002.110 stopped by the pristine script's NameError (`library_5700.py:227`, `copy` not imported) | [5700.2002-partial.log](../../x230v2-28GS/bootloader-6.2.40/5700.2002/5700.2002-partial.log) |
| 5700.2003 | PARTIAL | confounded at the end: 11 PASS / 2 UNSUPPORTED (NVS, SD); 2003.11's erase passed on the device but framework c1e7679's post-erase boot-config reset FAILed it and skipped 2003.10 | [5700.2003-partial.log](../../x230v2-28GS/bootloader-6.2.40/5700.2003/5700.2003-partial.log) |
| 5700.2004 | PASS | clean: 2/2, rc 0 | [5700.2004.log](../../x230v2-28GS/bootloader-6.2.40/5700.2004/5700.2004.log) |
| 5700.2005 | FAIL | clean to 2005.2: 2005.1 PASS; 2005.2's erase gate expects `Erasing flash`, the device printed `Erasing nand0:` (erase + level-1 reset happened); 2005.3–.8 skipped by c1e7679 | [5700.2005-fail.log](../../x230v2-28GS/bootloader-6.2.40/5700.2005/5700.2005-fail.log) |

Final logs: **created, b60a24c.** No per-device `.cfg` exists for any case: the framework held u0
for the whole run (the queue's adaptation rule). The framework's own logs are committed in the
runner dirs `5700_x230v2-28GS_6.2.40/` (run 1) and `5700_x230v2-28GS_6.2.40_run2/`.

## Findings

Measured:
- Bootloader 6.2.40 on the x230v2-28GS prints `Erasing nand0: [===]` / `Erase complete.
  Restarting...` on the security-level reset (swi_a_2005.log); the Feb x230v2 18GT control
  (6.2.37) printed `Erasing flash:`.
- The suite needs the bootloader default boot source = TFTP; with "determined by main CLI" 2002's
  configure strands the unit (run 1, queue file).
- The framework names the x230v2-28GS family `x230`, so TFTP recovery asks for
  `/tftproot/x230-tb470.rel` (hence the symlink).
- Framework c1e7679 (in a5bb6a1 and 89900a6) skips the rest of a TestSet after a deliberate erase.
- `/home/st-art/framework` moved a5bb6a1 → 89900a6 during the run (queue Issues). Per the queue,
  2001–2003 ran on a5bb6a1 and 2004–2005 on 89900a6. No run log pins the commit itself.
- The framework reports the build name as `x220-awplus_main-20261006-52.rel` on this x230.

Inferred: 2005.2's FAIL is a message-text change, not a functional fault, because every
functional check in it passed. That is the tester's reading; the verdict stands as FAIL (OPEN 1).

## OPEN

1. **5700.2005: FAIL or PARTIAL?** Is `Erasing nand0:` an intended 6.2.40 change (the test's gate
   is out of date) or a product regression? Re-grade with `/create-logs` if you change it.
2. **2003.10** was never run. To run it alone: `./test-5700.2003.py -s default.setup -u -v 10` as
   root in a runner dir with the pristine suite (from the 5700.2003 log's UNBLOCK).
3. **2002.110** needs `import copy` in `library_5700.py`, which means editing the pristine suite.
   Do you want that?
4. **u0 flash no longer holds `x230-2.rel`** (run 1's 2001 configure deleted it, by suite
   design). The USB stick holds a copy. The **ACCESS licence** stays installed (allowed 10-06).
5. **bench-state.md is stale and was not regenerated.** A u0-only probe would rewrite it without
   the IE520 stack, and the 10-06 IE520 handover already records that it is stale (stack on
   `main-calanm`, consoles at 9600). The next session that probes the whole bench regenerates it.
   tb470.static names u0 `swi_f`; this run's setup called it `swi_a`.
6. **tb470 `/tftproot` leftovers** (root's, tmpfs): `x230-tb470.rel` symlink, `x230-copy-tb470.rel`,
   `x250-tb470.rel`. `IE360-tb470.rel` / `IE560-tb470.rel` are gone (accepted collateral 10-06).
7. `x230v2-28GS/bootloader-6.2.40/current_test.log` is a root-owned symlink the framework left in
   the repo tree (to `test-5700.2005.log`). Untracked; delete it or leave it.

## Next steps

1. Decide OPEN 1 and 3.
2. Before any re-run of this suite: re-create the `/tftproot/x230-tb470.rel` symlink if tb470 has
   rebooted, and set u0's bootloader default to TFTP (Boot Menu 2 → 3, prompts in the queue file's
   "Row #1" section), then set it back to 9 afterwards.

## Recipes

- **Bootloader default boot source** (u0, 9600): `reload` → `y`+CR → at `Press <Ctrl+B>` send bare
  Ctrl+B until `Enter selection` → `2` → `9` ("Boot from default (determined by main CLI)") or `3`
  (TFTP: IP version 4, device IP 10.38.215.34, mask 255.255.255.224, gateway 0.0.0.0, server
  10.38.215.33, file x230-tb470.rel) → `Saving settings... Complete` → `9` (Quit and continue
  booting). Prove with a plain `reload`: the flash default prints `Loading flash:<file>...` with no
  `forced to boot from a non-standard location` banner.
- **Restore u0 after the suite**: the queue file's "Run 2 baseline / restore recipe". **Never
  delete the current boot config** (that forces factory defaults and the password dialog).
- Case-own drivers from the run (`step0-tftpboot1.py`, `launch_suite.sh`, `run2-restore2.py`,
  `run2-post2.py`) are in git at `b60a24c^` under `x230v2-28GS/bootloader-6.2.40/5700.200*/work/`.

## Pointers

- Queue / resume record: [CAMPAIGN-QUEUE-2026-10-06T1325.md](../../x230v2-28GS/bootloader-6.2.40/CAMPAIGN-QUEUE-2026-10-06T1325.md)
- Control corpus and the traps above: memory `x230v2-5700-control-corpus` (updated 2026-10-07)
- IE520 bench state at the same time: [IE520/SESSION-HANDOVER-2026-10-06.md](../../IE520/SESSION-HANDOVER-2026-10-06.md)
