# T33403 process review -- oper-2026-10-22T1122
Reviewed 2026-10-22 by /create-logs from agent-a39e912de26a7c9d1.jsonl and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 35 | 70 | 52,879 | 11,811,170 | 353 | 34 | 20 min (1,214 s) | 22,154 chars |

Boundaries: from the previous case's `RESULT` (01:03:30 UTC) to this case's `RESULT`
(01:23:45 UTC). That span includes the group's own closing work: the console teardown and
the campaign queue edits. See REVIEW.md.

## Process taken
1. Baseline reads: `show clock`, uptime, `show trigger`, the two ports, `dir flash:`
   (call 1).
2. The CLI surface with `qmark`, in three calls: `activate`, then the trigger sub-mode
   `type` list, then `type log` and `script` (calls 2-4).
3. `show system`, the rest of the baseline and `swi_d.cfg` (call 5).
4. STEP 2: wrote both `.scp` files on the DUT with `awshell` and read them back (call 6),
   then listed them from the CLI (call 7).
5. STEP 3 and STEP 4: `activate`, the trigger configuration, the near-miss control and the
   matching string, each with its own read (calls 7-10).
6. STEP 5: `write`, `ckreload`, the reads after the boot, clearing the artefact and
   re-running the stimulus pair (calls 11-13).
7. STEP 6: removal with `cfg`, the two `delete force` commands through `ckyn`, and the
   proof by re-sending the stimulus (calls 14-15).
8. Health after, the raw sample copied off the box, the post-case probe, the working log in
   three parts, the case commit (calls 16-22).
9. Group close-out: `hostinfo`, console teardown, four reads and two edits of the campaign
   queue, two commits, the RESULT (calls 23-34).

## Wasted input
- Calls 25-33 are the campaign queue being edited, read back, repaired and committed twice:
  nine calls and about 7 KB, after the case itself was finished. The first edit put three
  results rows in the wrong table and the second removed them. One read of the table shape
  before the first edit would have avoided both the mistake and the repair.
- Call 7 included `dir flash: | include scp`, which the platform rejects. The cost was
  small and the rejection is now recorded as an expected output.
- Nothing large was pulled into the context in the measurement part of this case. 22 KB of
  tool output for six steps is the best ratio of the three cases.

## Repetition
- The stimulus pair (near-miss, then matching string) was sent twice: once before the
  reload and once after. That repetition is the point of STEP 5 and should be kept.
- `show trigger 1` was read five times. Each read follows a different event, so none is
  redundant.
- `show running-config interface port1.0.21` was read seven times. The same is true: each
  read is the state after a different action.

## Accuracy risks
- In the working log, the STEP 4 `show trigger 1` block carries the post-reload value
  `Last activation ... Thu Oct 22 01:12:30 2026` with a note in brackets that the first run
  read `01:09:23`. The two runs' output was merged in that one block. The final log
  therefore quotes only `Number of activations ....... 1` for the first firing and takes the
  time from the `TRIGGER[4679]` log line, which is unambiguous.
- The `show system` quoted in the working log has a masked digit, `Thu Oct 22 01:06:4x
  2026`, and the `swi_d.cfg` header has `captured 2026-10-22 14:0x NZDT`. The final log
  carries the `show system` block as the working log wrote it.
- The script files were created in a root shell on the DUT. That is recorded plainly in the
  log, together with the statement that nothing else was written there and that both files
  were deleted and proved gone.
- The trigger regular expression was chosen so that it cannot match its own configuration
  line. Without that choice the trigger would fire when it is configured, and every later
  result would be ambiguous. This is the most reusable idea in the case.

## Next run: expected outputs
| step | what this bench gave |
| --- | --- |
| `show script` | `^` and `% Invalid input detected at '^' marker.` -- no such command |
| `activate ?` | `SCRIPT  Script to activate` / `background  Activate script in background` |
| trigger types | atmf cpu env-sensor interface linkmon-probe log main-pse memory periodic ping-poll pse-port reboot stack time usb |
| `script ?` in the trigger sub-mode | `<1-5>  The list position of the script` |
| `activate flash:/<f>.scp` | prints a CLI banner, then every line of the file in order, then `exit` |
| a trigger firing | `TRIGGER[<pid>]: Trigger 1 activated` and `IMISH[<pid>]: [SCRIPT]<command>` |
| `show trigger` with none | `% No triggers currently defined` -- a `% ` line from a successful show |
| `show running-config | include trigger` | only `trigger 1`; the sub-mode lines do not contain the word |
| after a reload | the trigger persists; `Number of activations` resets to 0 |
| `dir flash: | include <x>` | `% Invalid input detected at '^' marker.` -- `dir` takes no pipe filter |

## Next run: scripts
- No new tool was needed. The useful call shapes were:
  `CKSHTO=60 CKTO=300 tools/tb awshell <TB> <scratch> <uN> <baud> "printf '...' > /flash/<f>.scp"`
  to place a script, and
  `CKTO=240 tools/tb ckyn <TB> <scratch> <uN> <baud> 'YN?:delete force flash:/<f>.scp'`
  to delete it.
- Every `show` in this case went through `ckcon`, never `cfg`, because `show trigger`
  prints a `% ` line when it succeeds and a stop-on-error driver treats that as a failure.

## Next run: references
- `platforms/x960.md` §7F.6 (the `% ` line from `show trigger`, and `show trigger <n>` as
  the read that matters) and §7F.8, whose open item this run closed.
- The final log of this case, STEP 1 -- what scripting is on this platform, so it need not
  be established again.
- memory `never-send-cli-help-through-a-cr-driver` -- why the help was read with `qmark`.
- memory `bench-scripts-stop-on-cli-errors` -- a `% ` line and what a driver does with it.
