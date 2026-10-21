# platform-ports-2026-10-21T1323 process review -- tb470, x230v2-28GS

Reviewed 2026-10-21 by /create-logs from `agent-ad7157fdc1eed0717.jsonl` (the bench-runner tester's transcript, one
subagent for TRIAGE and RUN) and the six working logs. This file is for the next tester and the Test Engineer, not for Zephyr.

## How the numbers were taken

`tools/case_tokens.py` could not split this run. It assumes each case starts with its own tool call into `<id>/` and ends
at its own RESULT line. Here the three show cases ran in one console login and were reported in one message, so the tool put
about 95% of the run in "overhead". The table below is cut instead at the RUN dispatch and at each RESULT message (a
scratchpad script). Two side effects:
- The three show cases are one segment. Their per-case reviews share it.
- Each port case's segment also holds the NEXT case's setup reads (the tester read them before sending the RESULT line).

| segment | API calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| triage (gates, reading, probe) | 15 | 450 | 96,819 | 1,391,868 | 128 | 30 | 1,222 s ¹ | 125,918 chars |
| T47226 + T47227 + T47215 (one login) | 6 | 164 | 133,677 | 737,072 | 39 | 10 | 343 s | 29,634 chars |
| T46421 | 9 | 288 | 33,477 | 1,513,259 | 56 | 14 | 600 s | 11,254 chars |
| T47208 | 14 | 448 | 196,261 | 2,572,595 | 650 | 18 | 1,115 s | 8,599 chars |
| T47210 | 15 | 450 | 35,697 | 3,342,648 | 1,237 | 17 | 600 s | 8,596 chars |
| closing (restore proof, hand-back) | 3 | 96 | 13,290 | 716,968 | 23 | 3 | 59 s | 5,710 chars |
| **total** | **62** | **1,896** | **509,221** | **10,274,410** | **2,133** | **92** | **3,939 s** | **189,711 chars** |

¹ About 14 minutes of the triage wall time is the wait between the triage hand-back (13:31) and the Test Engineer's go (13:45).

**Cache reads are almost all of the cost.** The context read back on each API call grew through the run:

| segment | cache read per API call |
| --- | --- |
| triage | about 93,000 tokens |
| show cases | about 123,000 |
| T46421 | about 168,000 |
| T47208 | about 184,000 |
| T47210 | about 223,000 |

Every later call re-reads the triage reading. So the triage reading is paid for about 47 more times.

## Overhead findings (triage and closing)

1. **126,000 characters of reference text read in triage** (30 tool calls). The largest reads:
   - `TESTBOX-ACCESS.md` in full, in two reads: 20,085 + 11,961 chars. `tools/tb` already wraps the ssh agent and
     the box paths, so a bench-runner driving only through `tools/tb` needs only its "framework run flags" section.
   - orient-dt §0, the tools index, the bench-state header and the handover OPEN list in one call: 16,537 chars.
   - logged-output.md §2: 12,100 chars.
   - The three 2026-10-09 ports reviews (12,584 chars) and three platform reviews (6,869 chars), read in full. Only
     their "Next run: expected outputs" sections were used.
   - Narrower read: `grep -n -A20 '^## Next run: expected outputs'` on the old reviews; the tools index by `grep -n '^### '`.
2. **A run `.setup` round trip cost 4 calls.** The tester wrote the run `.setup` without its `[power]` lines because the
   session said "no PDU". The probe then read MISMATCH on exactly those 4 lines. It read the `tb probe` and
   `bench_probe.py --template` code, then put the lines back. No framework run binds that file in a manual-CLI campaign.
   - Fix: "no PDU" means "no power cycle". It does not mean "edit `[power]`". A manual-CLI group needs no run `.setup`.
3. **Good: the closing proof was cheap.** One probe and one diff (2 calls, 5,567 chars) proved the restore.

## Findings that recur across the cases

1. **The six health commands were rebuilt by hand in every case** (the `H=(...)` array in 3 of the cases' commands), and
   each sample was then summarised by a separate call (7,779 chars in the show-case segment alone). A helper would make
   this one call that returns one summary line per sample. Proposed below.
2. **Three port cases did not capture `show system` in their own setup reads.** The final logs needed a ruling from the
   Test Engineer to quote the group capture from 13:46:45. Fix: put `show system` in every case's setup reads.
3. **Good: output went to files on the box, and only summary lines were read back.** Each port case read back only
   8,600 to 11,300 characters of tool output across 14 to 18 calls. Keep this pattern.
4. **Good: a background watcher on the partner.** In T47210 one background `ckcon` on the 4050 caught the TLV for four
   rows in one call. T47208 did not do this and lost about 4 minutes (see `47208/47208-review.md`).

## Accuracy risks found while writing the final logs

1. **The port cases' working logs carry the wrong case text.** Lines 9-14 of the T46421, T47208 and T47210 working logs
   hold T47226's "Case text" block, copied from the first case's log. The final logs took each case's own text from the
   test-case database instead. Fix: the working-log generator must read each case's own record.
2. **T46421: one LLDP read listed 0 neighbours.** After the change to `speed auto 10`, the DUT's LLDP table was read once,
   2 s after link-up, and listed no neighbour. It was not read again until the end of the case. The 4050 listed the DUT
   21 s later. The tester's reason says "LLDP re-learned"; the final log keeps PASS and states the gap in CAVEAT.
   Next run: poll the DUT's LLDP table until the neighbour appears, after every flap group.
3. **T47208: the 4050 was not read during three rows.** For `speed auto 1000`, `speed 1000` and `speed auto`, the
   working log filled the 4050 column from other reads. The final log writes "not read" and says so in CAVEAT. The
   tester's reason ("DUT and partner status agree") is wider than what was measured for those rows.
4. **T47210: the 4050's status at C1 was not read in this case.** The final log writes "not read".
5. **Labelled edits to copied output.** The writers removed the terminal-size escape before `show log` output and the
   CRLF endings in the `?` help capture, dropped the help's typed-line echoes, wrote `@poll` and `@sleep` as plain
   notes, and cut repeated log reads as labelled ranges (checked by diff to be identical to an earlier read).

## Proposed scripts

**Built the same afternoon on the Test Engineer's instruction:** `tools/health.py` (`tools/tb health`) and
`tools/speedrow.py` (`tools/tb speedrow`), both verified on tb470 u0/u1; the reading budget and the
background-watcher rule went into `.claude/agents/bench-runner.agent.md`. The proposals as written at review time:


- **`tools/health.py <dev> <baud> <transcript> [--before FILE]`**, wrapped as `tools/tb health <scratch> <uN> <baud>`.
  It runs the six STANDING-ORDERS §8 reads (adds `show log tail 150` when `--before` is given), saves the raw output,
  and prints one line: newest reboot entry, exception log None or not, count of filtered log lines, `show cpu` busy
  1 s / 20 s / 60 s, `show memory` free. With `--before` it prints the difference and flags a new reboot entry.
- **`tools/tb speedrow <scratch> <dut uN> <dut port> <partner uN> <partner port> <setting...>`**: set one speed/duplex
  row on the DUT, match the partner when the row is forced, and poll both ends' `show interface ... status` plus the
  partner's `show lldp neighbors detail` in one call. T46421, T47208 and T47210 all repeat this shape.
