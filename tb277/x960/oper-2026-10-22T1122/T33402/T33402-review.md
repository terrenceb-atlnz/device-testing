# T33402 process review -- oper-2026-10-22T1122
Reviewed 2026-10-22 by /create-logs from agent-a39e912de26a7c9d1.jsonl and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 32 | 64 | 336,864 | 8,447,838 | 326 | 32 | 30 min (1,802 s) | 23,992 chars |

Boundaries: from the previous case's `RESULT` (00:33:28 UTC) to this case's `RESULT`
(01:03:30 UTC). `tools/case_tokens.py` on its own put almost all of this work in
"overhead", because its segment starts at the first tool call that names the case folder
and this tester wrote its working log at the end of the case. See REVIEW.md.

## Process taken
1. Checked the PDU outlet was reachable and read its status (call 1).
2. Setup reads and the health-before sample, `show system`, `show boot`, the `log` lines of
   both configurations, and `swi_d.cfg` (calls 2-3).
3. STEP 1: the notice marker, the rejected `show log buffered`, then the same marker read
   from `show log` and from `show log permanent` (calls 4-6).
4. Waited for the console to be free after a command that did not return a prompt (call 7).
5. STEP 2: raised the filter with `cfg`, then the three markers around `write` (calls 8-9),
   and confirmed all five entries were stored before the restart (call 10).
6. STEP 3: `awshell` to read `mount`, `ls -l /flash/log/` and the match counts (call 11).
7. STEP 4: the last marker (call 12), the power-cut attempt and the poll that followed it
   (call 13), the reads that showed the unit had not restarted (call 14), one
   `NEEDS TEST ENGINEER:` message (call 15), then `ckreload` (call 16).
8. STEP 5: the reads after the restart (call 17) and three `awshell` calls that counted the
   markers on flash and in RAM and checked the one result that could have been read the
   wrong way (calls 18-20).
9. STEP 6 and STEP 7: removal (call 21), the fresh notice (call 22), a second wait for the
   console (call 23), and the counts that proved it was not stored (call 24).
10. Health after, the raw sample copied off the box, the post-case probe, the working log in
    three parts, the commit and the RESULT (calls 25-32).

## Wasted input
- Call 22 cost 10 minutes of wall time for no data: `show log permanent | include
  CKT33402-AFTER-RESTORE` matched nothing, printed nothing and returned no prompt, so the
  driver waited out `CKTO=600` and the DUT then logged the console out. Call 23 was a pure
  recovery wait. Together they are a third of this case's wall time. The method note in
  the final log says what to do instead.
- Call 10 had the same shape at `CKTO=180` (3 minutes lost) earlier in the case. The
  second occurrence should not have happened: the first had already shown the behaviour.
- Nothing else of size was pulled into the context. This case read 24 KB of tool output in
  total, the least of the three.

## Repetition
- The absence of a marker was proved three times in three different ways (`show log
  permanent | include`, then `grep -c` on `/flash/log/*`, then `grep -c` again after the
  restore). The `grep -c` form is the one that works; the first form should not be used
  again.
- `mount | grep -E " /flash | /var/log "` was run twice, before and after the restart. That
  repetition is deliberate and worth keeping: it shows the media did not change.

## Accuracy risks
- The abrupt power interruption was attempted and could not be achieved on this bench. The
  case is graded on a `reload`. The final log says so in `CAVEAT:` and in STEP 4. The
  reason is a bench matter and is recorded in the campaign queue, not in the log.
- "`show reboot history` gained no entry" after the power-cut attempt is prose in the
  working log. The command's output was not quoted there. The health-after sample does
  show only one new reboot entry, which is the `reload`, so the claim is supported, but
  indirectly.
- The `swi_d.cfg` header line reads `captured 2026-10-22 13:3x NZDT`, with the last digit
  masked.
- `/var/log/messages.1` held two matches and could have been read as RAM keeping
  pre-restart content. The tester checked the first and last line of that file and showed
  both matches were made after the restart. Without that check the case would have carried
  a wrong conclusion.

## Next run: expected outputs
| step | what this bench gave |
| --- | --- |
| baseline | `Permanent log: Status enabled, Maximum size 50kb, Filters *1 Level warnings` |
| volatile side | `Buffered log: enabled, 50kb, Filters *1 Level notices` |
| `show log buffered` | `% Invalid input detected at '^' marker.` -- the command does not exist |
| `log permanent level informational` | adds filter `2 Level informational`; `*1 Level warnings` stays |
| media | `/var/log` is `tmpfs ... size=10240k`; `/flash` is `/dev/mmcblk0p1 ... ext3` |
| permanent log files | `/flash/log/messages` plus `messages.1`, `.2`, `.3`, rotated at each boot |
| after a `reload` | the five pre-restart entries are in `/flash/log/messages.2` and in none of the tmpfs files |
| `show log permanent | include <no match>` | no output and no prompt; the driver waits out its timeout |
| removal | `no log permanent level informational` leaves exactly the default `*1 Level warnings` |

## Next run: scripts
- No new tool was needed. `tools/awshell.py` through
  `CKSHTO=60 CKTO=300 tools/tb awshell <TB> <scratch> <uN> <baud> '<read-only shell command>'`
  did everything the CLI could not.
- Proposed `tools/tb` option: a `--no-prompt-ok` or short per-command timeout for `ckcon`,
  for commands that may print nothing. It would have saved 13 minutes here.

## Next run: references
- The final log of this case, STEP 3 -- the media names, so they need not be found again.
- `logged-output.md` §2 "Check the DUT's health, every case".
- memory `cli-surface-is-not-the-device-surface` -- `start-shell` reaches what no `show`
  command reports.
- memory `console-driver-retries-are-lockout-generators` -- why the driver refused to type
  at the login prompt after the console timed out, which was correct behaviour.
