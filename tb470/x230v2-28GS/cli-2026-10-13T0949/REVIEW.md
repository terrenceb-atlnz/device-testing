# Process review -- cli-2026-10-13T0949 (tb470, x230v2-28GS DUT, T30403 / T45543 / T20358 / T47228)
Reviewed 2026-10-13 by /create-logs from `agent-a3ab1e57621c1d438.jsonl` (the bench-runner transcript) and the
cases' working files. Numbers: `tools/case_tokens.py --cases 30403,45543,20358,47228` on that transcript.
Findings cite the transcript call (segment #n, in the per-segment call order) or the working log.
Recommendations are the reviewer's.

## Token usage

Measured (`case_tokens.py`: a case runs from its first call naming `/<id>/` to its `RESULT` line):

| segment | API calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| overhead (gates, reading, hand-back) | 30 | 60 | 111,623 | 2,811,493 | 3,634 | 31 | 175 s | 121,121 chars |
| T30403 | 16 | 32 | 27,332 | 2,004,507 | 3,641 | 17 | 228 s | 17,450 chars |
| T45543 | 2 | 4 | 3,342 | 276,498 | 40 | 3 | 7 s | 328 chars |
| T20358 | 10 | 20 | 22,406 | 1,489,333 | 86 | 11 | 250 s | 18,472 chars |
| T47228 | 41 | 82 | 72,018 | 8,192,742 | 7,474 | 44 | 773 s | 58,648 chars |
| **total** | **99** | **198** | **236,721** | **14,774,573** | **14,875** | **106** | **1,433 s** | **216,019 chars** |

Apportioned by what each call did (per-call usage from the transcript; output not re-split):

| segment | API calls | cache write | cache read | tool calls | wall | tool output read | moved |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| overhead | 34 | 114,820 | 3,744,335 | 35 | ~220 s | 122,929 chars | + T47228 #41-#44 (after-run probe, bench-state checkout, queue DONE) |
| T30403 | 11 | 21,672 | 1,380,246 | 12 | ~170 s | 9,138 chars | - T45543's device run (#11-#13), - T20358 prep reads (#3-#4) |
| T45543 | 5 | 6,521 | 667,237 | 6 | ~35 s | 3,130 chars | + its device run from the T30403 segment |
| T20358 | 12 | 24,887 | 1,722,855 | 13 | ~275 s | 23,982 chars | + LACP memory and linerate README reads |
| T47228 | 37 | 68,821 | 7,259,900 | 40 | ~730 s | 56,840 chars | - group after-run checks |

**Why the measured split is off.** The tester writes each working log at the end of its case, so a case's
first call naming `/<id>/` can come late (T45543's whole device run sat in T30403's segment) and the last
case's segment swallows the group's after-run checks. Either the tester writes the working-log header
first (logged-output.md §2 already says "as it goes"), or `case_tokens.py` gets a proposed
`--split-at-result` mode that starts each case right after the previous `RESULT` line.

**Where the tokens go.** Cache reads are 98% of the volume. The context was ~116k tokens per call at the
first case and ~200-233k per call during T47228; T47228's 37 calls carry half the group's cache reads.
What is read up front, and what a long case pulls in, is paid again on every later call.

## Overhead findings

**Wasted input -- 121k chars (~30k tokens) read before the first case, then carried by ~70 calls.**

| call | size | what | narrower read |
| --- | ---: | --- | --- |
| #7-#8 | 2k + 34k | `cat TESTBOX-ACCESS.md` (spilled), then the whole file Read | the lab CLAUDE.md requires reading it in full; the `cat` first was a wasted call. Only the Test Engineer can relax the rule |
| #9 | 15k | memory `awplus-restconf-api-reference` + `tools/README.md` lines 20-200 | the memory is right for T47228; for the README, `sed -n '/^### \`ckcon.py\`/,/^### /p'` per tool used (tb, ckcon, qmark, rcdiff, rc2cfg, linerate) |
| #5 | 12k | `platforms/x230v2-28GS.md` + STANDING-ORDERS 21-110 | the platform file is the right read; STANDING-ORDERS §1/§6 only |
| #6 | 8k | logged-output.md 47-188 | §2 "The tester's working log" and "Reporting" only |
| #12, #29 | 10k + 3.5k | the 2026-10-09 T20358 review + group REVIEW, then the old `20358-partial.log` head | those reviews' "Next run" sections only; the old final log is not needed (each run stands alone) |
| #3 | 7.6k | the whole queue file, after #2 had printed its outline | the outline + `sed -n '/^## Run, group 1/,/^## Run, group 2/p'` and Session facts |
| #19 | 4k | `tools/tb --help` | fine once per session |

**Gates were lean and correct:** precheck CLEAR, peek both consoles, `/nfsHome` mounted, probe with the Test
Engineer's facts (`--baud 115200`, outlets u0=1 u1=7), diff checked against the known set, one gate
report to the sentinel (#20-#28, ~8k chars).

## Cross-case findings (said once here)

1. **Group facts once, then pointed to.** T30403's working log holds the devices, builds, MACs, NICs and clocks;
   the other three point to it. Keep this: it removed ~3 repeated captures.
2. **Working logs written at the end of each case**, in one Write, not "as it goes" (logged-output.md §2).
   Harmless here (no session died), but it is the resume point, and it skewed the token split above.
3. **Clock offsets recorded once** (x230 NZ wall time labelled UTC, ~9 s behind tb470; 4050 NZDT ~12 s behind):
   every final log could state its device-clock line from the working logs. Keep.
4. **Teardown by running-config diff after every case** (`rcdiff.py` against `prerun-u0/u1.out`): empty each
   time; the office-hours constraint (no write, no reload) was kept throughout.
5. **No claim had to be left out of the final logs for lack of a source**; the wording limits are listed in
   each case's Accuracy risks (T20358 LLDP attribution, T47228 far-end enable proof).

## Next run: scripts (group)

| need | today | recommended |
| --- | --- | --- |
| per-case split of tokens | segments shifted by late working logs | `case_tokens.py --split-at-result` (proposed), or the tester writes `work/run1.log`'s header first |
| `show spanning-tree interface` under `--stop-on-error` | ckcon stops on its `% `-prefixed lines (T20358) | `ckcon.py --error-regex` (proposed); note the trap in its README entry |
| counter deltas | computed by hand (T20358) | `tools/ifdelta.py BEFORE AFTER --ports ...` (proposed) |
| RESTCONF request matrices | one bash `try()` loop per phase (T47228) | `restconf.py --plan FILE` (proposed), the expected table in 47228-review.md as its first plan |

Build none of these without the Test Engineer's go; they go in `tools/` with README entries.

## Suggested shape of the next run of these four cases

1. Gate as here (~8 calls), then read: `platforms/x230v2-28GS.md` §2 (it now holds all four outcomes), the
   queue's group recipe, and the case reviews' expected-output tables -- under 15k chars.
2. T30403 and T45543: one device call each (the refusals + `show license`; the two TPM shows), graded
   against the expected tables.
3. T20358: one setup call, one closure+traffic call (no `show spanning-tree interface` under
   `--stop-on-error`), one teardown call.
4. T47228: setup, one plan run per phase with both consoles read after each change, teardown -- ~6 calls
   instead of 37.
