# Process review -- modbus-2026-10-08T1131 (tb470, IE520 stack, T22650-T22655)
Reviewed 2026-10-08 by /create-logs from `agent-a819940a509fabe68.jsonl` (the bench-runner transcript)
and the cases' working files. Numbers: `tools/case_tokens.py --find ~/.claude/projects/<slug>
--cases 22650,22651,22652,22653,22654,22655`. Findings cite the transcript call (segment #n, as listed
by the tool's per-segment call order) or the working log. Recommendations are the reviewer's.

## Token usage

| segment | API calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| overhead (gates, reading, hand-back) | 45 | 90 | 197,506 | 7,262,988 | 2,174 | 45 | 484 s | 299,199 chars |
| T22650 | 10 | 20 | 27,397 | 2,047,760 | 6,152 | 10 | 172 s | 33,688 chars |
| T22651 | 5 | 10 | 11,784 | 1,127,864 | 3,667 | 5 | 103 s | 9,797 chars |
| T22652 | 6 | 12 | 11,805 | 1,420,968 | 3,703 | 6 | 113 s | 10,430 chars |
| T22653 | 6 | 12 | 12,443 | 1,492,871 | 4,360 | 6 | 139 s | 8,486 chars |
| T22654 | 9 | 18 | 29,455 | 2,426,928 | 6,264 | 9 | 298 s | 31,726 chars |
| T22655 | 6 | 12 | 20,126 | 1,766,795 | 4,866 | 6 | 285 s | 17,650 chars |
| **total** | **87** | **174** | **310,516** | **17,546,174** | **31,186** | **87** | **1,596 s** | **410,976 chars** |

**Where the tokens go.** Cache reads are 98% of the volume: every API call re-reads the whole
context. The context was already ~160k tokens on average during the gates and grew to ~205k
(T22650) and ~294k (T22655) per call. **The size of what is read up front is multiplied by every
later call.** The cases themselves were lean: 5-10 calls each, one driver script per case, results
copied to files, the working log written once.

## Overhead findings (the biggest saving)

**Wasted input -- 299k chars (~75k tokens) read before the first case, then carried by ~80 calls.**

| call | size | what | narrower read |
| --- | ---: | --- | --- |
| #2-#4 | 2k + 55k + 24k | `cat platforms/IE520.md; sed -n 1,400p orient-dt/SKILL.md` spilled to a file, then the whole file Read; then orient-dt 400-700 + STANDING-ORDERS | bench-runner's own gate list covers orient-dt for a run; read orient-dt §1/§3 only if a gate fails. platforms/IE520.md: the Modbus and console sections only |
| #5-#6 | 2k + 45k | `cat logged-output.md; cat tools/README.md`, spilled, Read in full | logged-output.md §2 only (the tester's part); tools/README.md: `grep -A8 '### \`mb.py\`\|### \`ckcon.py\`\|### \`rcdiff.py\`'` |
| #8-#11 | 5k + 8k + 11k + 27k | the previous modbus group's README and **all six of its final logs** | that README's register-map lines only (or platforms/IE520.md once it holds the map, below) |
| #12-#13 | 2k + 33k | TESTBOX-ACCESS.md, spilled, Read in full | none: the lab-home CLAUDE.md requires reading it in full before touching a testbox. Only the Test Engineer can relax that rule |
| #7 | 13k | the session handover + bench-state head | the handover's OPEN list (`sed -n '/OPEN/,/^## /p'`) |
| #15 | 11k | three memories in full | the dispatch already carried their rules |
| #19 | 9k | `cat mb.py` + ckcon.py head | `mb.py --help` |

**Repetition / detours.**
- #24-#28: five calls reading `bench_probe.py` source to work out whether it would fall back to
  9600 baud on u4 (the dispatch had warned about that). A `--baud 115200` (no fallback) option on
  the probe would replace the source reading with one flag. Proposed below.
- #29, #32: peeking at and trying a login on u2, two minutes, to characterise the backup-console
  drop. It is now recorded as a known behaviour (handover / NEEDS TEST ENGINEER 13:15). Next time:
  skip it unless the case needs u2.
- #16-#18: the case texts pulled from ck.db into the session scratchpad, which dies with the
  session. They were not carried into every working log (T22650 and T22651 have only item names),
  and the final-log writers had to fetch them again.

**Accuracy (group-wide).**
- **Exception codes are inferred, not printed.** `mb.py` prints `ExceptionResponse(... status=1)`
  and pymodbus prints `Exception response 131 / 0`, never the Modbus exception code. Every
  "illegal data address" / "slave device failure" in these logs was derived from the server's
  `show scada modbus tcp server` counters before and after. Fix: have `mb.py` print
  `exception_code` (2 = illegal data address, 3 = illegal data value, 4 = slave device failure).
- **tb470 eth1's MAC address** is in no working log, so no final log's TOPOLOGY could carry it.
  Add `ip -br link show eth1` to the gate capture.
- **The DUT clock is UTC and ~50 s ahead of tb470** (T22654 working log). Times in the DUT log
  and on the host differ by that much. Record the offset once per group.

## Next run: scripts

| need | today | recommended |
| --- | --- | --- |
| per-case driver | a new `work/<id>.sh` per case, two of them cloned from T22651's by `sed` and patched (T22652 #1-#2) | **`tools/mbplan.py`** (proposed): runs a plan file of lines `unit addr count type expect [cli-regex]` against `--host`, prints one PASS/FAIL row per line with the TX bytes and the decoded value, and writes the trace. The six plans become data files (the expected outputs below), and grading is a diff, not a reading |
| setup / teardown per case | identical blocks in each `.sh`: enable server, `rc2cfg.py`, disable, `rcdiff.py` against the group baseline | one shared `case_wrap` function (or `mbplan.py --setup/--teardown`) instead of six copies |
| exception type | inferred from server counters | `mb.py` prints the exception code (above) |
| probe without 9600 fallback | five calls into `bench_probe.py` source | `bench_probe.py run --baud 115200` (proposed flag) |

Build none of these without the Test Engineer's go; they go in `tools/` with README entries.

## Next run: references (read these instead of re-deriving)

- **Mapping Version 5 register map.** `platforms/IE520.md` §3 already has the Modbus row (MV5,
  unit id = member, 6-word alarms, LED = 0x8000, no PoE, the 0x0049 provisioned-member count,
  exception 4 on an aggregator member) and points to `IE520/modbus-2026-09-29/README.md` for the
  map. The tester read that README **and all six final logs** (#8-#11, 51k chars); the platform
  row plus the README's map would have done. Worth adding to that row, as measured on this build:
  per-member summary 0x0120 `[1, 28, 0, 5, 31]`, identity 0x0200/0x0202/0x0222/0x0242, sensors at
  0x1000 (5 words each, 5 per member), ports at 0x5000 (13 words each; port N of a member at
  0x5000 + 13*(N-1)), unit 0 also answering 0x5000 on main-calanm.
- **The case texts' addresses are the older version-1 layout** for T22650 and T22652, and the
  T22654 "bit 0 = LED" is the MSB (0x8000). Grade at the MV5 address from the start.
- **Bench facts the cases depend on:** port1.0.1 on every member is an empty SFP cage; port1.0.2
  is the x230 link and is in `static-channel-group 2`; port3.0.13 is the client link (tb470
  eth1). The stack has a provisioned, absent member 2.

## Suggested shape of the next modbus run

1. Gate (precheck, probe `--baud 115200`, eth1 MAC + DUT clock offset) -- about 8 calls.
2. Read platforms/IE520.md §Modbus and this file's expected outputs -- 1-2 calls, under 10k chars.
3. Per case: `mbplan.py <id>.plan` + CLI reference + working log + commit + RESULT -- 3-4 calls.

That removes ~75k tokens of carried context (about 40-50% of every later call's cache read) and
roughly half the per-case calls.
