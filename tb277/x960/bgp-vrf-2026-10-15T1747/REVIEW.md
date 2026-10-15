# bgp-vrf-2026-10-15T1747 -- process review
Reviewed 2026-10-16 by /create-logs from `agent-ab60d6243d8eb4d8a.jsonl` and the working files.
Per-case reviews are in each case folder as `<id>-review.md`.

## Token usage

| case | calls | cache read | cache write | output | wall | tool output read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T43858 | 62 | 11,551,543 | 103,053 | 828 | 34m | 46,773 |
| T43859 | 30 | 8,331,568 | 60,326 | 250 | 20m | 29,024 |
| **overhead** | 65 | 15,751,771 | 176,680 | 1,278 | 78m | 215,510 |
| **total** | **157** | **35,634,882** | **340,059** | **2,356** | **2h 13m** | **291,307** |

Campaign-wide: **562 calls, 118,571,145 cache-read**, of which **45% is group overhead** rather than case work.

### This group's own overhead
65 calls and 15.8M cache-read, with 215,510 chars of tool output — the highest overhead read-back
of the campaign. It includes the end-of-campaign restore, the single remedial reload and the
post-run probe, all of which are genuine closing work rather than waste.

### Group-specific
- **Reach for the DUT's own `tcpdump` first.** AW+ exposes `tcpdump` at privileged exec. For a
  unicast control-plane protocol like BGP, which never reaches a host NIC on another segment, it is
  the correct instrument — and about a third of T43858's cost went on a port-mirror limb that was
  reached for first and carried no verdict in the end.
- **A capture file's size is not a measurement until its writer has exited.** This produced the one
  retracted finding of the campaign. Confirm the process is gone, or read tcpdump's own
  `N packets captured` line.
- **Check the gate's shape before assuming it.** BGP is not service-gated on this build, unlike
  OSPF and RIP; the dispatch said otherwise and following it literally would have aborted the
  whole BGP batch on a `%` line.

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
