# Group process review -- oper-2026-10-22T1122 (tb277, x960, three Management_Operation cases)
Reviewed 2026-10-22 by /create-logs from agent-a39e912de26a7c9d1.jsonl and the working files.

## Token usage

| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T33401 | 100 | 200 | 140,847 | 17,601,467 | 1,147 | 111 | 41 min | 81,730 |
| T33402 | 32 | 64 | 336,864 | 8,447,838 | 326 | 32 | 30 min | 23,992 |
| T33403 | 35 | 70 | 52,879 | 11,811,170 | 353 | 34 | 20 min | 22,154 |
| overhead | 10 | 20 | 75,290 | 1,298,278 | 95 | 14 | 2 min | 103,416 |
| **total** | **177** | **354** | **605,880** | **39,158,753** | **1,921** | **191** | **93 min** | **231,292** |

### How these numbers were produced, and one defect in the measurement
`tools/case_tokens.py --find ... --cases T33401,T33402,T33403` returned zeros for all three
cases and put everything in overhead. Two things caused it:

1. **The `RESULT` regular expression.** `result_re()` builds `^RESULT T?<id> `. This tester
   wrote `RESULT AWPTCM-T33401 PASS -- ...`, so no boundary was found. Widening the pattern
   to `^RESULT (?:AWPTCM-)?T?<id> ` finds all three at once. **Recommended fix:** make that
   the tool's own pattern, since `AWPTCM-T<id>` is the form the case database uses.
2. **The segment start.** Even with the boundaries found, the tool starts a case at the
   first tool call whose input names `/<id>/`. This tester wrote each working log at the end
   of the case, so T33402 was credited 5 calls and T33403 16, while 80 calls of real
   measurement fell into overhead. The table above instead runs each case from the previous
   `RESULT` to its own, which matches what the tester actually did.
   **Recommended fix:** when a case's folder is first touched after the previous `RESULT`,
   fall back to the previous `RESULT` as the start, rather than to the end of the segment.

With the tool's own defaults the same transcript reports: T33401 101 calls / 41 min,
T33402 5 calls / 3 min, T33403 16 calls / 8 min, overhead 55 calls / 39 min. Those three
case rows understate the work and should not be quoted.

### What the shape of the numbers says
- **Cache read dominates everything**: 39.2 M cache-read tokens against 354 input tokens
  and 605 K cache writes. The cost of this group is the cost of carrying its own context
  forward, not of reading new material.
- **The first case paid for the group.** T33401 is 56% of the calls and 45% of the cache
  reads. It also wrote the group's new tool, established the stimulus that the other two
  cases reused, and did the bench gating.
- **Overhead is small and well spent**: 10 API calls, but 103 KB of tool output, which is
  45% of all the output read in the group. That is the queue, STANDING-ORDERS,
  logged-output.md, `tools/README.md`, `platforms/x960.md` and the previous group's files,
  all read once at the start. Reading them once per group rather than once per case is
  exactly right.

## Overhead: its own findings
- The campaign queue was pulled in whole with `Read` (27,604 chars), the largest single
  tool result of the group. The tester needed its group-B row and the session facts. A
  `sed -n` on the group's own section would have cost about a tenth.
- `tools/README.md` was read in three slices at the start (18,217 chars) and twice more
  inside T33401 (4,457 and about 1,000 chars). A single index of the entries, or one read
  of the whole file kept in context, would avoid the later returns.
- The gate work itself (precheck, template, scratch, peek) was four calls and is the
  cheapest part of the group. Nothing to change.
- The group closed with nine calls of campaign-queue editing, including one repair commit
  for three rows written into the wrong table. That is bookkeeping charged to T33403.

## What recurs across all three cases
1. **No authored case text.** All three cases have `has_objective = 0` and one placeholder
   step in ck.db. Every objective and every step was designed before the run from the
   title, the x960 TPS row and the DUT's own CLI help. The final logs say so in `Case:`.
   For the next campaign in this folder, assume the same and budget design time per case.
2. **One stimulus served all three cases.** The DUT writes a log message for every CLI
   command it is given. A command carrying a unique string is therefore a log message on
   demand, with known text, known facility and known severity, and no traffic generator,
   no cable and no port flap. T33401 established it, T33402 and T33403 reused it. Put this
   in the next tester's briefing.
3. **Every `log ... <criterion>` sub-command on this platform is a filter builder, not a
   property setter.** `log host <ip> facility <f>` adds a filter (T33401 STEP 3) and
   `log permanent level <lvl>` adds a filter beside the default one (T33402 STEP 2). Read
   `show log config` under `Filters:` before assuming a setting was replaced.
4. **A `% ` line is not always an error.** `show trigger` with no triggers prints
   `% No triggers currently defined` from a successful show. Every `show` in these cases
   went through `ckcon`, and only configuration went through `cfg`, which stops on `% `.
5. **An absence needs an instrument that is proved alive.** T33401 put a 4-packet ping in
   the same capture file as the silence it was measuring. T33402 proved an absence with
   `grep -c` on the device's own files, because the CLI's `include` form returns nothing and
   no prompt. Both are better than reading an empty result.
6. **The health tool reported DIRTY after every case and the tester adjudicated CLEAN every
   time.** The cause is the same in all three: the §8 filter matches the literal word
   `kernel`, and every ordinary `kern.*` start-up line of a permitted reload contains it.
   Each case's new reboot entry was matched to its own `reload` to the second, using the
   13-hour difference between the DUT's UTC clock and the box's NZDT display.
   **Recommendation for `tools/health.py`:** when the only flagged lines are `kern.*` lines
   whose timestamps fall inside 60 s of a new `Expected CLI(user request)` reboot entry,
   report them as expected boot text instead of flagging them. That would remove three
   manual adjudications per group.
7. **`show cpu` on this platform never prints an idle percentage.** It prints busy averages
   over 1 s, 20 s and 60 s. All six samples read `1 second: 0%, 20 seconds: 0%, 60 seconds:
   0%`. The `HEALTH:` block of each log records what the command actually printed.
8. **The DUT came back to the same configuration after every case.** The three `swi_d.cfg`
   files are identical below their three header lines, across two reloads and three
   teardowns. That is the strongest available evidence that the teardowns were complete.
9. **Waiting was hand-written everywhere.** Across the group the tester wrote the "wait
   until tcpdump exited" loop 12 times and the "wait until the console is free" loop 7
   times. One `tools/tb capwait <scratch> <timeout>` action and one `tools/tb freewait
   <uN> <timeout>` action would replace all 19 and remove the risk of a short count.

## Recommended for the next run, in priority order
1. Fix `tools/case_tokens.py` as above (the `AWPTCM-` prefix and the segment start). Without
   it, every review of a bench-runner campaign has to be measured by hand.
2. Add `tools/tb capwait` and let `tools/tb capture` take more than one NIC.
3. Teach `tools/health.py` the expected-boot-text rule of finding 6.
4. Give `ckcon` a way to accept "this command may print nothing", so a non-matching
   `include` does not cost a full timeout (13 minutes were lost to this in T33402).
5. Brief the next tester with findings 2, 3, 4 and 7 before the first case. They are the
   four facts this group spent the most time discovering.
