# Group process review -- dot1x-2026-10-23T1304 (tb277, swi_d, x960-56YSQ)
Reviewed 2026-10-28 by /create-logs from two tester transcripts and the working files.

Four cases, four PASS. Three of them ran on 2026-10-23 in one tester
(`agent-a6601a35454174322.jsonl`); T9032 ran on 2026-10-28 in its own tester
(`agent-a8a5628ecbb2b564a.jsonl`).

## Two things to know before reading the table

1. **`--find` picks the wrong transcript and returns empty rows for this campaign.** The tester
   wrote its boundary lines as `RESULT AWPTCM-T44270 ...`, and `tools/case_tokens.py` matches
   `^RESULT T?<id> `. The numbers below came from a copy of the transcript with
   `RESULT AWPTCM-T` rewritten to `RESULT T`. **Fix:** let `result_re()` accept an optional
   `AWPTCM-` prefix. It is one regex and it would have saved this review a manual step.
2. **The per-case rows for T44270, T33360 and T33354 cover the write-up, not the measurement.**
   `case_tokens.py` starts a case at its first tool call into the case's own folder. That tester
   drove the bench from its scratchpad and only touched the case folders when writing up, so
   almost all of its real work is in the `overhead` row. **Do not read those three small rows as
   efficiency.** T9032's row is complete, because that tester worked in its case folder
   throughout, and it is the right number to plan the next case from.

## Token usage

Session 1, 2026-10-23, three cases:

| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T44270 | 22 | 44 | 52 076 | 4 586 769 | 214 | 22 | 748 s | 13 630 |
| T33360 | 6 | 12 | 15 578 | 1 754 537 | 104 | 6 | 202 s | 1 860 |
| T33354 | 16 | 32 | 27 467 | 7 068 484 | 197 | 16 | 389 s | 10 864 |
| overhead | 173 | 346 | 576 578 | 43 640 925 | 33 997 | 183 | 5 208 s | 214 110 |
| **total** | **217** | **434** | **671 699** | **57 050 715** | **34 512** | **227** | **6 547 s** | **240 464** |

Session 2, 2026-10-28, one case:

| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T9032 | 62 | 124 | 147 912 | 8 236 973 | 10 988 | 72 | 1 628 s | 143 716 |
| overhead | 3 | 6 | 50 743 | 403 282 | 93 | 4 | 40 s | 11 993 |
| **total** | **65** | **130** | **198 655** | **8 640 255** | **11 081** | **76** | **1 668 s** | **155 709** |

Group total: **282 API calls, 870 354 cache-write and 65 690 970 cache-read tokens, 303 tool
calls, 8 215 s (2 h 17 m) of wall time, 396 173 characters of tool output read back.**

## The overhead's own findings (session 1)

The `overhead` row holds 80 per cent of session 1's wall time and 76 per cent of its cache
reads. Three things are in it.

1. **Three tools were written and debugged inside the measurement window.** `tools/eapol.py` was
   new and was fixed twice; `tools/wpasup.py` was new and was edited twice; `tools/tb` itself
   was edited three times, because `killmine` could not stop a root tool it had launched itself.
   The repeated-command list shows exactly that: `Edit tools/tb` three times, `Edit
   tools/eapol.py` three times, `Edit tools/wpasup.py` twice. This is the single largest cost in
   the group.
2. **Large reference reads at the start.** `cat tb277/x960/CAMPAIGN-QUEUE-2026-10-23T1304.md`
   pulled 24 318 characters in one call; `sed -n '1005,1140p' platforms/x960.md` 8 690; a
   combined heading listing of `STANDING-ORDERS.md`, `logged-output.md` and `platforms/x960.md`
   6 298; `sed -n '20,110p' tools/README.md` 6 163. That is roughly 45 KB before the first
   console command, and the queue was then read again in part during T33354.
3. **The gate.** The occupancy check, the probe, the pings that disproved its two `CHECK_CABLE`
   lines and the restore of `bench-setup/tb277/bench-state.md`. This is necessary work and it is
   correctly once per group, not once per case.

Session 2's overhead is only 4 tool calls, because that dispatch was for a single case.

## Findings that recur across the cases

- **The health baseline for this unit is already dirty, and every case diffed against it.** The
  snmpd core of 2026 Oct 22 23:49:18 and two unexpected reboots at 23:55:56 and 23:53:17 pre-date
  the campaign. All four cases recorded them and all four diffs came back CLEAN. Every final log
  states that the exception entry was present before the case and unchanged by it. The next
  tester on swi_d should expect this and not report it as new.
- **`auth host-mode multi-supplicant` silently rewrites `dot1x control-direction both` to `in`,
  and `no auth host-mode` does not put it back.** Found in T33360 and reproduced independently in
  T33354, hours after `both` had been restored and verified. Both final logs carry it. It is the
  same shape as the known behaviour where a `spanning-tree mode` change silently drops
  `no spanning-tree <mode> enable`.
- **The local RADIUS server's counters are cumulative for the whole group** and include tool
  validation runs. Nothing in any final log rests on them. Two counter movements have no sourced
  reading and are therefore left out of the final logs: `Invalid packet from NAS` 0 to 2 in
  T44270, and `Unknown EAP auth type` 0 to 4 plus `Invalid packet from NAS` 2 to 4 in T33360.
- **`wpasup.py`'s JSON file disagreed with its own printed RESULT once**, in T44270. The leg was
  re-run and the second run's agreeing output was graded. T9032 then compared JSON against
  printed RESULT for all five of its legs, and they agreed. Keep doing that until the tool is
  changed to make a disagreement impossible.
- **The capture filter `ether proto 0x888e` is mandatory on tb277.** Loop protection sends one
  frame per second on 57 instances, and an unfiltered capture is drowned by them. Every leg in
  every case used it.
- **`dot1x initialize interface port1.0.48` before every leg** is this group's method. Without
  it, the first attempt of a session can be refused by the authenticator before the RADIUS
  server is ever asked.
- **The authored case records are nearly empty.** Three of the four hold no objective and no
  steps, and the fourth's 15 steps are Internet Explorer clicks on a Windows PC that this bench
  does not have. Every step in this group was designed for the bench. T33354 also shows why the
  authored text cannot be trusted on its own: its objective says `Not Support` and the measured
  answer is the opposite.
- **Every case folder's `swi_d.cfg` is the configuration the measured legs ran under**, captured
  after the last leg and before teardown, with a header that says so. For cases whose STEP 0 is
  the feature-off baseline, a capture before STEP 1 would not contain the feature at all.

## The three biggest savings for the next run

1. **Write and prove the traffic tools before the measurement window opens.** Three tools were
   built or repaired during session 1, and that work dominates its overhead row: 5 208 s of
   wall time and 43.6 M cache-read tokens. `tools/wpasup.py`, `tools/eapol.py`,
   `tools/radeap.py` and `tools/p12split.py` all now exist, are in `tools/README.md` and are
   verified on this hardware, so the next 802.1X campaign starts with them. When a new tool is
   still needed, build it and run one smoke leg against a known-good credential first, outside
   the case.
2. **Put the exact reads and the working command forms in the dispatch.** Session 1 read about
   45 KB of rules, platform notes and the campaign queue before its first console command, and
   session 2 read about 35 KB and then spent three probe runs, each with a 420 s timeout,
   getting the probe's argument form right (`--outlet u2=1` not `--outlet 1`, `--name u2=swi_d`
   not `--name swi_d`, an absolute `--template` path). The working probe line was already
   written in the campaign queue's gate record. A dispatch that names the file and line range
   for each rule, and quotes the probe line verbatim, removes both costs.
3. **Give the working-log assembly a `tools/` helper.** All four cases built their working log
   the same way: cut console fragments into a scratchpad directory with `sed` ranges, write a
   template, substitute. The script was reused; the fragment extraction was hand-written four
   times (`frag`, `frag2`, `frag3`, `frag4`). A `tools/mklog.py <case-dir> --template T
   --fragments D` that cuts named ranges out of a captured console file and substitutes them
   would make it one call per case.

Smaller, and worth doing at the same time: fix `case_tokens.py` to accept the `AWPTCM-` prefix,
and add `--tls-max` to `wpasup.py` so the next tester does not need to know the OpenSSL
configuration format.
