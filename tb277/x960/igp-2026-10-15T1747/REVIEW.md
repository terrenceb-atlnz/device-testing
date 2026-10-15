# igp-2026-10-15T1747 -- process review
Reviewed 2026-10-16 by /create-logs from `agent-a6f1baf6d4e3e024b.jsonl` and the working files.
Per-case reviews are in each case folder as `<id>-review.md`.

## Token usage

| case | calls | cache read | cache write | output | wall | tool output read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T43857 | 52 | 8,688,536 | 90,196 | 443 | 29m | 53,613 |
| T43856 | 44 | 11,381,671 | 75,365 | 383 | 34m | 36,831 |
| **overhead** | 26 | 3,020,842 | 104,956 | 309 | 72m | 145,419 |
| **total** | **122** | **23,091,049** | **270,517** | **1,135** | **2h 17m** | **235,863** |

Campaign-wide: **562 calls, 118,571,145 cache-read**, of which **45% is group overhead** rather than case work.

### This group's own overhead
26 calls and 3.0M cache-read — **the lowest overhead of the campaign by a wide margin**, because
the bench was already built and proven. 145,419 chars of tool output in the overhead segment is
mostly the group's setup/restore write-up.

### Group-specific
- **The service gate was derived twice**, once per case. It belongs in the group's setup section:
  start is asynchronous (gate on the refusal message), stop needs a reload, and
  `show process | include <daemon>` is the only true daemon-state instrument.
- **Put the daemon read in a graded step, not in teardown.** T43857's `show process` line exists
  only in its teardown table, so its final log carries no daemon evidence; T43856's does.
- **A routing protocol's own packets are the only thing that can prove which protocol installed a
  route.** Both cases rest on decoded protocol frames — Router LSAs, and the RIPv1/v2 difference —
  and neither verdict would survive on `show ip route` alone.

## Findings that recur across this campaign (said once here)

1. **Overhead is 46% of everything the testers read.** Across the four groups, case work accounts
   for 64,209,901 cache-read tokens and group overhead — gates, triage, rules, setup reasoning and
   hand-back — for **54,361,244 over 264 calls**. The single largest lever on campaign cost is not
   how a case is measured but how much is re-read around it.
2. **Cost per call rises through a session**, because every call carries the accumulated context.
   Front-load specs, probes and driver-building into the cheap early part of a group; leave the
   long observation limbs for later, where they cost tool time rather than context.
3. **The first case of a group pays for the group.** T33248 reads six times more expensive than the
   five ARP cases after it purely because it absorbed the bench setup and the first build of the
   instrument. Judge a case's cost against its peers *within* a group, never across the first/rest
   boundary.
4. **Tool output read back is 919,837 characters campaign-wide**, and **73% of it sits in the
   overhead segments**, not in cases. Most of that is console batches echoing configuration the
   sending script already knew, and files re-read after being written.
5. **Instruments must be proven before a verdict rests on them.** Two separate instrument faults
   were found and corrected mid-campaign (a capture flag that hid forwarded frames; a flow
   generator that correlated the fields the ECMP hash consumes), and one finding was raised and
   retracted because a capture file was sized before its writer had exited. All three share a
   shape: **a zero is only a measurement once the same instrument has produced a non-zero in the
   same run.** Every counted leg in this campaign carried an instrument control for that reason.
6. **`cfg.py` stops at the first `% ` line.** A benign advisory mid-batch silently abandons the
   rest. It cost a shut port for ~2 minutes in group D. Keep advisory-prone commands out of
   batches that have work after them, and gate on proven state rather than on an exit code —
   `rcdiff.py` prints differences but exits 0.

---
Recommendations are the reviewer's; findings cite the transcript segment or working file they come from. A review never changes a verdict: a doubt about one goes to the Test Engineer.
