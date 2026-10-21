# longrun-2026-10-21T1824 process review -- tb101, IE520 4-stack, 1 case
Reviewed 2026-10-22 by /create-logs. Per-case detail: [17509/17509-review.md](17509/17509-review.md).

## Token usage
| segment | calls | input | cache write | cache read | output | tool calls | wall |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T17509 triage + Phase A (tester a8b6dc9d) | 88 | 178 | 207,732 | 12,065,920 | 19,397 | 89 | 1740 s |
| T17509 Phase C (tester a5c2c189) | 61 | 122 | 308,844 | 7,396,240 | 826 | 63 | 1337 s |
| sentinel session (this /test-mode session, whole campaign incl. /create-logs so far) | 546 | 1,800 | 625,967 | 125,516,091 | 154,068 | 154 | about 13.6 h |
| **total** | **695** | **2,100** | **1,142,543** | **144,978,251** | **174,291** | **306** | |

The sentinel's own session is **87 % of all cache reads**. The two testers together are 13 %.

## Overhead findings
- **Phase B cost almost everything, and did almost nothing.** For 12 h the sentinel ran a Monitor
  whose `IDLE <n>m` alarm fired every 5 min, re-armed it every 30 min, and ran the 15-min cron
  check. Each wake-up re-read the whole conversation from cache. Only 13 of those wake-ups (the
  hourly samples) had anything new to read. Fix, for a detached long run: once the row is
  `RUNNING-DETACHED`, stop the Monitor and rely on one cron per sample (for example `57 * * * *`,
  just after each sample is written) plus the one-shot Phase C cron. That keeps every health
  check the plan asks for and removes about 120 empty wake-ups.
- **Each tester read the whole queue file** (17-22 k chars), most of `tools/README.md` (about
  11 k chars) and long parts of `logged-output.md`. For a 3-phase case, give the Phase C
  dispatch a short brief (the Phase A record lines, the restore recipe, the grading block) so it
  does not re-read the plan.
- **Tool defects found during the run** (four, all fixed in `tools/` now; see the case review).
  They cost calls in Phase A and Phase C, not in Phase B.

## Cross-case findings
One case only, so none.

## The three biggest savings
1. Phase B: no Monitor while a detached sampler runs; one cron per sample instead (removes most of
   the 125 M cache reads).
2. A short Phase C brief in the dispatch instead of "read the queue top to bottom" (about 40 k
   chars of reading per tester).
3. `tools/longrun.py --report` and `tools/ixtcl.py pair` (proposed; arguments in the case review)
   so grading tables and control pairs are one call each.
