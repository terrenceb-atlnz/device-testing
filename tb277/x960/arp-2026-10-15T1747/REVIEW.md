# arp-2026-10-15T1747 -- process review
Reviewed 2026-10-16 by /create-logs from `agent-abaa4bf7d49aa5cc5.jsonl` and the working files.
Per-case reviews are in each case folder as `<id>-review.md`.

## Token usage

| case | calls | cache read | cache write | output | wall | tool output read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T33248 | 21 | 3,108,319 | 50,499 | 12,889 | 14m | 16,543 |
| T33247 | 4 | 804,104 | 18,276 | 9,700 | 2m | 316 |
| T33249 | 3 | 686,795 | 10,537 | 8,032 | 0m | 275 |
| T43848 | 3 | 754,303 | 12,975 | 10,297 | 0m | 273 |
| T43849 | 3 | 916,706 | 17,009 | 14,404 | 0m | 279 |
| T33246 | 6 | 2,246,661 | 21,535 | 14,406 | 5m | 6,164 |
| **overhead** | 108 | 24,836,035 | 198,970 | 10,673 | 117m | 157,443 |
| **total** | **148** | **33,352,923** | **329,801** | **80,401** | **2h 21m** | **181,293** |

Campaign-wide: **562 calls, 118,571,145 cache-read**, of which **45% is group overhead** rather than case work.

### This group's own overhead
108 calls and 24.8M cache-read — **the largest overhead of the campaign, and correctly so**: this
group carried the triage for all thirteen cases, the occupancy and probe gates, the reading of
STANDING-ORDERS, logged-output.md and the platform file, and the first build of the ARP
instrument. Charging it to group A makes group A look expensive; it funded the whole campaign.

### Group-specific
- **The five cases after T33248 cost 3-6 calls each.** Once the bench and the instrument were
  proven, an ARP case is genuinely cheap. That is the shape to aim for: one expensive setup case,
  then a run of cheap ones.
- **Save each `.cfg` as the first action after setup.** T33246 missed the capture point and its
  `.cfg` had to be reproduced by re-applying the command set; the file is honest about it but the
  RADIUS key hash cannot match. The capture is cheap and unrecoverable afterwards.
- **Five of the six cases had no authored step text.** Each was designed from the TFS, the TPS row
  and the DUT's own `?` surface, and each log says so rather than inventing a quotation. Budget
  for that: it is the normal case on this suite, not the exception.

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
