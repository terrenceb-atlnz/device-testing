# T44277 process review -- dot1x-2026-10-29T1528
Reviewed 2026-10-30 by /create-logs from agent-a703cc5195e03bfaa.jsonl and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 47 | 96 | 173,288 | 3,541,041 | 32,170 | 46 | 10,071 s (incl. ~2 h 27 min usage-limit cut, 17:02-19:29) | 64,283 chars |

## Process taken
1. Gate: precheck both boxes, read-only probes (tb490 MATCH, tb5 read-only artefacts).
2. Read platforms/x980.md + a 60-line slice of platforms/x960.md, T44274's run1.log (lines 1-150) and the x960 T44277 log's verdict and steps.
3. STEP A: `qmark` help on `auth supplicant-mac`; health before.
4. STEPs 0-5: `arpleg` ICMP legs from tb5 (eth6, fake MACs ff41/ff42) around each `auth supplicant-mac` change; `show auth supplicant brief` after each.
5. STEP 6: filtered `show log`. Health after, restore (rcdiff 0), eth6 re-login, logout.
6. Usage-limit cut at 17:02 before run1.log was written; resumed 19:29, re-checked the DUT read-only, wrote run1.log from the saved outputs.

## Wasted input
- `sed -n '14,73p' platforms/x980.md; sed -n '1600,1660p' platforms/x960.md` (8,615 chars): only x960 §7K.1 (one paragraph) was used. `grep -n -A8 '7K.1' platforms/x960.md` would do.
- T44274's run1.log lines 1-150 (7,078 chars), read for the arpleg/httpq recipe. The group A recipe in the queue (lines 186-229) already names the commands.

## Repetition
- none found within the case. The resume re-read of the DUT (show system, reboot history) was needed after the cut.

## Accuracy risks
- STEP 2's first force-authorized leg got 3 of 4 ICMP (one ARP in the window); the 4 of 4 came from the next leg. The verdict rests on the pair, which the final log quotes.
- "ck.db has no authored steps" came from the x960 run's record because ck.db was unreachable from the dev host this run. Confirm with `tools/tb tool tb490 <run> ckcase --db /home/terrenceb/claude/Test-cases/ask-ck/db/ck.db AWPTCM-T44277`.
- swi_dut.cfg header is not the logged-output.md §2 three-line format (no hostname/S/N on line 1, no `case ..., run 1` line, no `testbox tb490, console u2` line).

## Next run: expected outputs
- bare `auth supplicant-mac <mac>` -> no admission, ICMP 0/4.
- `auth supplicant-mac <mac> port-control force-authorized` -> brief `NONE <mac> ForceAuthorized`, ICMP 4/4 (first leg may be 3/4).
- `... force-unauthorized` on an authenticated MAC -> its session ends at once, ICMP 0/4, a valid web login is ignored.
- a second `auth supplicant-mac <mac> <param>` silently replaces the first (no `%` line).
- `no auth supplicant-mac <mac>` -> `supplicantMac: none`.

## Next run: scripts
- existing: `tools/tb tool tb5 <run> arpleg ...`, `httpq`, `tools/tb health`, `rcdiff.py`, `qmark`.
- proposed: `tools/authleg.py` -- one call per leg: set a per-MAC override on the DUT, send N ICMP from a given MAC via arpleg, read `show auth supplicant brief`, print one table row. Arguments: `--box tb490 --u u2 --port port1.0.81 --mac <mac> --ctl <force-authorized|force-unauthorized|auto|none> --count 4`.

## Next run: references
- platforms/x980.md §1 (auth surface), §1.1 (web-auth DHCP, supplicant-mac).
- queue tb490/x980/CAMPAIGN-QUEUE-2026-10-29T1528.md, Group B recipe (lines 230-256).
