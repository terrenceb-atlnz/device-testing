# dhcp-client-2026-10-15T1458 process review
Reviewed 2026-10-15 by /create-logs from agent-a355179677143f86e.jsonl and the working
files. This group ran T35370 (DHCP Extended ID) and T43854 (DNS Relay). Per-case detail is in each case's
`<id>-review.md`.

## Token usage -- the whole campaign

One `bench-runner` tester ran all three groups in one subagent session, so the overhead row is
**session-wide**, not this group's alone. It is repeated in each group's REVIEW.md so no group
file is read in isolation.

| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T43851 | 30 | 60 | 55,136 | 5,478,463 | 22,914 | 30 | 926 s | 18,583 |
| T43853 | 17 | 34 | 28,341 | 3,952,821 | 7,242 | 17 | 623 s | 10,705 |
| T43852 | 40 | 80 | 50,778 | 11,671,664 | 7,177 | 40 | 1,958 s | 13,834 |
| T43850 | 20 | 40 | 36,996 | 6,941,355 | 8,990 | 20 | 1,268 s | 20,671 |
| T35370 | 16 | 32 | 27,863 | 6,226,109 | 7,408 | 16 | 964 s | 8,293 |
| T43854 | 16 | 32 | 35,080 | 6,891,647 | 8,993 | 16 | 1,362 s | 9,942 |
| **overhead** (session-wide) | 50 | 100 | 159,307 | 7,154,891 | 8,682 | 58 | 1,104 s | 147,128 |
| **total** | **189** | **378** | **393,501** | **48,316,950** | **71,406** | **197** | — | **229,156** |

## The two numbers that matter

**1. Cost per call climbs 2.4x across a campaign.** Cache read divided by calls, in run order:

| case | cache read per call |
| --- | --- |
| T43851 | 183 k |
| T43853 | 232 k |
| T43852 | 292 k |
| T43850 | 347 k |
| T35370 | 389 k |
| T43854 | 431 k |

Every call carries the whole accumulated context, so the same tool call made in the last case
costs 2.4x what it costs in the first. The lever is not "fewer calls" in general -- it is
**fewer calls late**, and front-loading anything that can be done once (reading specs, building
drivers, probing the bench) into the cheap early part of the session.

**2. The overhead segment read 64% of all tool output** -- 147,128 of 229,156 chars -- on 26% of
the calls. Its largest reads:

| chars | what |
| --- | --- |
| 22,757 | reading the tester's OWN tool-results file back off disk |
| 10,557 | an ssh grep over the cached spec headings |
| 10,129 | `cat` of the full DHCP ARP Probe TFS |
| 8,878 | `cat` of the whole campaign queue file |
| 8,506 | a second range of the same tool-results file |

**31 kB -- 14% of everything the tester read all day -- was the tester re-reading its own tool
output off disk.** That is the single largest avoidable cost in the campaign. Whatever a result
is needed for later, extract it when it first arrives.

## Overhead findings

- The campaign queue file was `cat` whole (8,878 chars). A dispatch that carries the group's rows
  and the setup recipe inline removes the read.
- The specs were cached on the box under `/tmp/<campaign>/` -- good -- but then read whole, more
  than once. Read a TFS once per GROUP, by section.
- The no-console precheck and `bench_probe.py run` ran both in overhead and again inside
  individual cases. Once per group is enough unless the bench changed.

## Findings that recur across every group

1. **Every case hand-built its own leg driver by heredoc.** `runleg.sh`, `runleg82.sh`,
   `legC.sh` / `runlegC.sh`, `dnsmain.sh` / `dnsctl.sh` / `dnsctl2.sh` / `dnsorder.sh` /
   `nsorder.sh` / `dnscache.sh` / `dnssetup.sh` / `persistC.sh` / `postrebootC.sh` -- twelve
   scripts, each a variation on apply-config, capture, send, count, save. Script text is charged
   as input every time it is sent.
   **Proposed `tools/leg.py`**: `--leg NAME --nics eth3,eth4 --config F --client '<args>' --out DIR`,
   which applies the config, captures on both NICs, runs the client, stops, emits per-NIC counts
   beside the tool's own count, and **fails loudly when the two disagree**. This is the single
   highest-value item in this review.
2. **`<dev>.cfg` was captured AFTER the legs in at least four of six cases**, not "after setup,
   before step 1" as logged-output.md §2 requires. Every header says so honestly, so nothing is
   misrepresented -- but the deliverable is then not the config the case was run under. Save it
   immediately after setup.
3. **No working log states its run span.** Every final log's `Run:` line had to be derived from
   timestamps inside the working files. One line at the start and end of a case closes it.
4. **A group-shared reboot check must write its per-case result into each case's own working
   log.** It did not here: T43851's persistence evidence had to be fetched out of a sibling
   case's files, and T35370 ended with no persistence evidence at all because the shared reload
   happened after its removal step.
5. **Two independent counters, always.** This campaign's value came from running tcpdump beside
   every scapy tool. It caught a brand-new tool being trustworthy (T43854) and surfaced an
   unexplained one-frame gap (T43852). Keep it, and make the disagreement an error rather than a
   note.
6. **A `%` line is not uniformly an error on this platform.** `% DHCP Relay is already globally
   enabled` is an advisory and the state holds; `% DHCP client is already running on this
   interface.` is a genuine rejection with exit 2 and unchanged state; and
   `% Can not configure ... remote-id unless agent option is set` is the EXPECTED result of a
   negative step. A gate that fails on any `%` would have failed a passing case.

Recommendations here are the reviewer's. Findings cite the transcript call or working-file line
they come from. No verdict was changed by this review.
