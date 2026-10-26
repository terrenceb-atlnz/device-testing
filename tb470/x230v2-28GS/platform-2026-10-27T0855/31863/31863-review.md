# T31863 process review -- platform-2026-10-27T0855
Reviewed 2026-10-27 by /create-logs from agent-a512b95ab36fe7ece.jsonl (group 1 tester) and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 32 | 64 | 37,863 | 3,408,363 | 21,894 | 32 | 871 s | 24,842 chars |

## Process taken
1. Queue row, group recipe and the 2026-10-09 run's review read (group overhead, see ../REVIEW.md).
2. Reload 1 (`tools/tb ckreload ... 400`), 169 s.
3. Two `tools/tb grep` passes over the console transcript for the boot start jobs (the first used grep flags the wrapper does not take and returned 32 chars; the second returned 3.9 KB).
4. `exec-timeout 0` set (ckcon), `exit`, fresh login via `tools/tb health --label before`.
5. Setup reads (show clock/system/boot/platform bist/running-config) in one ckcon; `rc2cfg.py` wrote swi_f.cfg.
6. `ckyn "YN?:platform bist instance all"`, then a ckcon for `instance 0`, `instance all full`, `show platform bist`, `show exception log`, `show license brief`; one qmark for the parser help.
7. Health after; then two `tools/tb grep` + awk passes to count the EXFX devGroup 99 lines per second (3 KB, then 57 chars).
8. Reload 2, 168 s; post reads; rcdiff against the pre-run copy.
9. Five calls (88-95) to find whether the poefw / TPM2 start jobs predate the licence, in the 2026-10-06 framework log.
10. RESULT to the sentinel.

## Wasted input
- Call 47: `tools/tb grep tb470 -n -a -i -E ...` returned 32 chars (an error): the wrapper already runs `grep -a -E`, so flags in front of the pattern are taken as the pattern. The narrower read is the second call, with the pattern first.
- Calls 49/51: the full start-job grep (3.9 KB) was read into context, then re-extracted into reload1-startjobs.txt. Writing straight to a file and reading only `head`/`tail` per job would have cost ~1 KB.

## Repetition
- The start-job extraction ran once per reload with a hand-built pipeline each time (calls 49-52 and 85-87). One helper would do both.
- See ../REVIEW.md for the group-level reads (queue, logged-output.md, tools/README.md) done before this case.

## Accuracy risks
- The devGroup 99 count (96 per `show platform bist`) comes from an awk count over a per-second key; the final log quotes the per-second counts, not 96 raw lines. A developer who wants the raw lines needs the box's `/tmp/plat-1027/health-u1-20261027T093016.out` (tmpfs, lost at the next tb470 reboot).
- The "not new since the licence" conclusion about poefw/TPM2 rests on one 2026-10-06 framework log; it is an observation, not graded, and it is not in the final log.

## Next run: expected outputs
- 1a reload -> login after 165-170 s; poefw ~55-58 s (no limit), TPM2 Access Broker to ~1 min 20 s of ~2 min 45 s.
- 1b `exec-timeout 0` -> "% The new exec-timeout settings will apply to new sessions only" (information only).
- 1d `platform bist instance all|0|all full` -> `% BIST test not supported.` (no y/n).
- 1e `show platform bist` -> "Switch Instance 0 ......... Not run", plus ~96 `local7.err EXFX ... illegal devGroup 99` lines in the log per call.

## Next run: scripts
- Proposed `tools/startjobs.py <console-log> [--from-line N]`: strip ANSI, print first/last sighting of each "A start job is running for ..." line and the login time. Replaces calls 47-52 and 85-87.
- Existing: `tools/tb health` (one call per sample), `tools/tb ckyn` for the BIST command.

## Next run: references
- platforms/x230v2-28GS.md §2 (BIST row) for the expected refusal.
- This case's final log for the exact command forms and outputs.
