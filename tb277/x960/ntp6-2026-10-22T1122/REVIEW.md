# Group process review -- ntp6-2026-10-22T1122
Reviewed 2026-10-22 by /create-logs from `agent-aeb5642c4fb54bf61.jsonl` and the working files.
tb277, DUT swi_d (AT-x960-56YSQ), one case.

## Token usage

`tools/case_tokens.py --find ~/.claude/projects/-media-bidhanc-mnt-testbox-home-claude-device-testing --cases T44299`
found the transcript and printed `no RESULT line found for: T44299`. The tester reported its
RESULT to the sentinel with `SendMessage`, which the splitter does not read, so it could not
separate the case from the group overhead and put every call in the overhead row. This group
held exactly one case, so the overhead row is the case plus its overhead. The split is shown
below from a hand count of the transcript's tool calls.

| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T44299 | not split | — | — | — | — | — | — | — |
| overhead (= the whole run) | 242 | 484 | 238,327 | 42,248,268 | 3,519 | 241 | 2,876 s | 144,707 chars |
| **total** | **242** | **484** | **238,327** | **42,248,268** | **3,519** | **241** | **2,876 s** | **144,707 chars** |

Hand split of the 241 tool calls:

| what | calls | share |
| --- | --- | --- |
| pure waiting (`sleep N; echo ...`, `echo idle`) | 116 | 48% |
| gates, rules and prior logs read before any measurement (calls 1-13) | 13 | 5% |
| real measurement, configuration and writing | 112 | 46% |

Cache read averaged about 174,580 tokens per API call, so the 116 waiting calls cost roughly
20.3 million cache-read tokens on their own -- about half of everything this group spent.

## Overhead findings

1. **The first five calls read rules and tool documentation: the campaign queue in full
   (21,760 chars), the STANDING-ORDERS and logged-output.md headings, STANDING-ORDERS 7-8,
   platforms/x960.md 7H.5, logged-output.md lines 112-270, and three tools/README.md ranges.**
   For a one-case group that is reasonable, but reading the WHOLE queue to find one group is
   not. Read the group's own section.
2. **Calls 6-10 read the previous NTP group's folder, both of its review files and 195 lines
   of one of its final logs.** The review files are written exactly so the final log does not
   have to be re-read. Reading both is doing the same work twice.
3. **The probe had to run twice** (calls 16 and 17) because the first used `--outlet 1
   --name swi_d` instead of `--outlet u2=1 --name u2=swi_d`. The correct spelling was in the
   `tb` README entry read at call 5.
4. **The single-console probe regenerates `bench-state.md` as a one-unit record**, which then
   has to be reverted to the committed multi-unit version by hand. That happened twice in this
   group (calls 20 and 232). A `--no-write` or `--keep-state` flag on the probe would remove
   both calls and the risk of forgetting one.

## Findings that recur across cases

This group held one case, so there is no cross-case pattern inside it. Three findings are
general enough to carry to the next group:

1. **Idle polling is the dominant cost of any case with long captures.** Five time-bounded
   captures (80 s, 300 s, 480 s, 170 s, 780 s) total 1,810 s of unavoidable waiting out of
   2,876 s of wall time. Waiting is not the problem; waiting one `sleep 5` tool call at a time
   is. Every such call re-reads the whole context cache. Use `Monitor` with an until-loop on
   the result file, or `run_in_background` with a single wake-up. The tester did use `Monitor`
   three times and it worked, then went back to `sleep 5; echo .` for 104 calls.
2. **A case with no authored text costs a design pass before it costs a measurement.** T44299
   had no objective and no step text in the database. The tester designed 8 steps from the
   title, the TPS row and the DUT's CLI surface, wrote them down first, and then ran them.
   That is the right order and it should stay the standard. Budget for it at triage.
3. **Capture first, change second, always as two separate calls.** All five captures in this
   group were started as their own call before the DUT was touched. No measurement was lost to
   a watcher that started beside a change instead of before it.

## Tools

No tool was left inside the case folder. `tools/ntpwire.py`, `tools/ntpc.py`, `tools/tb`,
`tools/health.py` and `tools/case_tokens.py` are all in `tools/` with README entries.

Two improvements are proposed in `T44299/T44299-review.md`: `tb waitjob` (a single blocking
wait on a background capture or result file) and a probe flag that does not rewrite
`bench-state.md` for a single-console probe.

Note for the repo, not for this campaign: `tools/README.md` carries TWO `### health.py`
sections, at lines 240 and 317. They describe the same tool with slightly different wording.
One of them should go.
