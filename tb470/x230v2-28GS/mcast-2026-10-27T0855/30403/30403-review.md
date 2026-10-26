# T30403 process review -- mcast-2026-10-27T0855
Reviewed 2026-10-27 by /create-logs from agent-a4a7a65c22a5db4d1.jsonl (group 2 tester) and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 66 | 132 | 98,997 | 7,217,480 | 41,470 | 67 | 932 s | 108,126 chars |

## Process taken
1. Rules and catalogue reads: tools/README.md (6.6 KB index + 8.8 KB sections), logged-output.md (6.8 KB), group 1's run1.log head (5.2 KB), the 2026-10-13 review's "Next run" section.
2. Looked for the Feature Overview Guides (absent), then the memory, then the CLI wiki on the share (3 calls, ~11 KB) and ck.db's command tables (4 calls, after `sqlite3` was not found).
3. Gate: precheck, scratch, peek, probe; queue row RUNNING.
4. Setup reads + licence in one ckcon (pre.out); health before; swi_f.cfg.
5. Three qmark help passes (exec, config, interface); read back 2.2 KB + 5.5 KB.
6. Step 1 commands with CR in one ckcon; caret columns read from the box transcript (2 greps, the first returned 112 chars).
7. Lab wiki: opensearch, then the X230v2 Features / X220 / X230 TPS pages via `tools/tb tool httpq`, read back in five slices (~11 KB).
8. Health after (DIRTY on the boot-time HTTP line); greps to show it pre-existed.
9. Post reads, rcdiff, logout; several awk slices of pre.out/step1.out to write run1.log.
10. RESULT to the sentinel.

## Wasted input
- Calls 36-38: the CLI wiki on the share (~11 KB) documents the ORIGINAL x230, not the x230v2, so it could not decide the verdict. The TPS and the build-target page did. Skip the CLI wiki for a support question; go to the TPS first.
- Calls 32-35: `sqlite3` is not installed on the dev host; four calls to reach ck.db's `cli_command_products` by Python. That table has no x230 entry and did not change the verdict.
- Calls 106-113: eight awk/sed slices of pre.out and step1.out (~6 KB) to copy text into run1.log. Writing run1.log sections as each step ran would avoid re-reading the saved outputs.

## Repetition
- tools/README.md and logged-output.md were read again although group 1 had just read them in the same campaign (see ../REVIEW.md).
- The DIRTY-flag check by hand repeats group 1's T31866 (health.py defect, below).

## Accuracy risks
- The caret column in each `% Invalid input` line is not in the saved step1.out (ckcon strips leading spaces). The working log took the columns from the box transcript `/tmp/mc-1027/console-u1.log`, which is lost at the next tb470 reboot. The final log quotes them from the working log.
- `tools/health.py` false DIRTY on a boot-time line already in the before sample. The Test Engineer confirmed "clean".

## Next run: expected outputs
- `show license brief` lists PIM, PIM-100, PIM-1024, PIM6, L3-MC-ROUTE (FULL licence).
- `show ip ?`, config `ip ?`, interface `ip ?`: no mroute / multicast-routing / pim / multicast entries.
- Every step 1 form -> `% Invalid input detected at '^' marker.` and a `user.err ... Command [...] failed` log line.
- X220 Software TPS rows (22)-(24) Multicast Routing = NO; X230v2 Features `mcast-ip-cmd = no`.

## Next run: scripts
- Proposed: ckcon option to keep leading spaces (or a raw mode) so caret columns survive into the saved output.
- Fix `tools/health.py` as in ../../platform-2026-10-27T0855/31866/31866-review.md.
- Existing: `tools/tb tool <box> <run> httpq "<wiki raw URL>"` fetched the TPS pages in one call each.

## Next run: references
- This case's final log (TPS and build-target evidence quoted).
- Lab wiki pages "X220 Software TPS" and "X230v2 Features" (action=raw, from a testbox).
