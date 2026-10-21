# lacp-2026-10-21T1222 process review (tb101, IE520 4-stack)
Reviewed 2026-10-21 by /create-logs from agent-aca2a1875cb17111e.jsonl (TRIAGE) and agent-aa263e65e1ba965a5.jsonl
(RUN), measured with `tools/case_tokens.py` (RUN) and a usage sum of the TRIAGE transcript.
The sentinel session's own tokens are not measured here.

## Token usage
| segment | calls | input | cache write | cache read | output | tool calls | wall |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T17584 (RUN, case segment) | 71 | 1,772 | 492,481 | 17,387,599 | 1,166 | 174 | 5,440 s |
| RUN overhead (gate reading, hand-back) | 5 | 130 | 106,708 | 554,806 | 44 | 16 | 89 s |
| TRIAGE agent (whole transcript) | 19 | 578 | 167,974 | 2,074,805 | 200 | 36 | 590 s |
| **total** | **95** | **2,480** | **767,163** | **20,017,210** | **1,410** | **226** | **6,119 s** |

The case segment is 87% of all tokens. Inside it, the hand-built event sequence (17584-review.md,
"Repetition") is the main cost: about 120 tool calls across 6 events, made while the context grew.

## Overhead findings
- **The two agents read the same rules twice.** TRIAGE read STANDING-ORDERS §3/§7, logged-output §1/§2,
  platforms/IE520.md §1/§3, the bench-map and LACP memories, tools/README.md and TESTBOX-ACCESS.md
  (calls 2-11, about 110 KB). RUN read the same set again (calls 2-13, 127 KB). That is about 30 k tokens
  read twice, then carried as cache read in every later call of each agent.
  Fix: the TRIAGE agent writes a short "rules that apply to this group" block into the queue (it already
  wrote the plan there), and the RUN dispatch tells the tester to read that block plus only the sections
  it names.
- **TRIAGE read TESTBOX-ACCESS.md from a persisted tool-result file of the sentinel session** (calls
  10-11, 32 KB), because `../Test-cases/TESTBOX-ACCESS.md` is only a 2 KB pointer. Fix: point the dispatch
  at the repo-root `TESTBOX-ACCESS.md` and the sections needed (§0 SSH, §2 election, §3 flags).
- **RUN printed the whole queue file (23 KB, call 2).** About 14 KB of it was the triage section, which the
  run did need. The 9 KB queue header and bench snapshot were already in the dispatch prompt.
- **Gate reads were cheap and correct** (precheck, peeks, probe: under 2 KB total).

## Findings that recur across the group
Only one case ran, so the per-case findings are in [17584/17584-review.md](17584/17584-review.md).
Two of them apply to any future traffic-plus-event case on tb101:
- Save every console read of an event into `work/` at the time it is taken, so the final log can quote it.
- Build one event-window script instead of 15-20 calls per event. **Built 2026-10-21: `tools/eventwin.py`**, with
  `l2flows.py --per-link` and the `rcdiff.py` fix (Test Engineer: "yes, all").

## Process facts worth keeping (from the hand-back)
- `ckyn` stopped with "no prompt within 60 s" on the first `boot config-file` because the stack file sync
  took longer. It was not a CLI error. Use `CKTO=300`.
- `tools/tb` now accepts `bond*` NIC names for `capture` and `ping`, and has `bondctl` in `SUDO_TOOLS`.
  **The Test Engineer should decide whether `bondctl` stays there**: it makes a root change (host
  bonding and addresses) reachable through `tools/tb sudotool`. The 2026-10-21 permission covered this
  case only.
