# static-2026-10-15T1747 -- process review
Reviewed 2026-10-16 by /create-logs from `agent-aeb89f5d96391104b.jsonl` and the working files.
Per-case reviews are in each case folder as `<id>-review.md`.

## Token usage

| case | calls | cache read | cache write | output | wall | tool output read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T43855 | 33 | 6,065,980 | 48,470 | 377 | 17m | 17,774 |
| T43861 | 21 | 5,080,430 | 45,249 | 176 | 23m | 22,333 |
| T43862 | 16 | 4,593,285 | 30,284 | 123 | 12m | 14,051 |
| **overhead** | 65 | 10,752,596 | 165,295 | 6,481 | 79m | 157,216 |
| **total** | **135** | **26,492,291** | **289,298** | **7,157** | **2h 12m** | **211,374** |

Campaign-wide: **562 calls, 118,571,145 cache-read**, of which **45% is group overhead** rather than case work.

### This group's own overhead
65 calls and 10.8M cache-read, including the build of the shared B/C/D L3 underlay — which groups
C and D then inherited for free. The underlay is the single best cost decision in the campaign.

### Group-specific
- **Build the underlay once and leave it up.** Groups C and D ran with zero bench-setup cost
  because this group left the SVIs, addressing and STP shape in place.
- **The triage's topology recommendation was wrong and the tester measured it rather than
  following it.** RSTP here is single-instance, so two parallel links between the same bridge pair
  cannot both forward; the ECMP paths had to be one link to each partner. Re-surface topology
  assumptions at the moment of use, not only at triage.
- **Per-port counter reads are the repetition hot spot.** Two box-side shell helpers were used that
  are not in the repo. A `tools/` helper snapshotting all counters in one call would pay for itself
  in the first ECMP case.

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
