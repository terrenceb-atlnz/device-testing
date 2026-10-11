# Process review -- l2l3-2026-10-09T0845 (tb470, x230v2-28GS swi_f, T15255 T38294 T38295 T18570 T18571)
Reviewed 2026-10-12 by /create-logs from `agent-a416990ee48b8b1f0.jsonl` (the bench-runner
transcript, run 3 of the 18:00 plan, 19:27:52-20:04:55 NZDT) and the cases' working files.
Findings cite the transcript call (segment #n) or the working log. Recommendations are the
reviewer's. T30403 was not attempted (NOT TESTED); its 19:35 read-only re-check sits inside
T15255's segment.

## How the segments were cut

`tools/case_tokens.py --cases 15255,38294,38295,18570,18571` starts a case at its first tool call
whose input names `<group>/<id>/`. Here the tester often wrote `D=tb470/.../l2l3-2026-10-09T0845/38295;`
(no trailing slash), so seven case calls (T38294 #1, T38295 #1-#3, T18570 #1-#2, T18571 #1) were
counted as overhead and T38295 shows 4 calls instead of 7. The table below therefore cuts each
case from the previous case's RESULT line to its own RESULT line (the first case from its first
call into `15255/`); the tool's own figures follow for comparison. Totals agree exactly.

## Token usage

| segment | API calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| overhead before T15255 (gates, reading, tool building) | 25 | 50 | 103,463 | 2,236,794 | 6,033 | 26 | 263 s | 133,473 chars |
| T15255 SNMP Walk | 24 | 48 | 47,714 | 3,621,781 | 10,876 | 25 | 472 s | 31,073 chars |
| T38294 static route IPv4 | 9 | 18 | 15,314 | 1,636,130 | 5,290 | 9 | 254 s | 6,955 chars |
| T38295 static route IPv6 | 7 | 14 | 11,107 | 1,372,221 | 4,804 | 7 | 194 s | 4,881 chars |
| T18570 trunk over static aggregator | 13 | 26 | 22,244 | 2,753,518 | 6,793 | 13 | 458 s | 8,973 chars |
| T18571 trunk over LACP aggregator | 10 | 20 | 16,842 | 2,316,438 | 6,439 | 10 | 387 s | 6,901 chars |
| overhead after T18571 (final probe, queue, hand-back) | 6 | 12 | 5,912 | 1,466,412 | 56 | 6 | 116 s | 3,014 chars |
| **total** | **94** | **188** | **222,596** | **15,403,294** | **40,291** | **96** | **2,144 s** | **195,270 chars** |

`case_tokens.py` as run (first-call-into-folder cut): T15255 24 calls / 3,621,781 cache read;
T38294 8 / 1,459,192; T38295 4 / 793,405; T18570 11 / 2,346,479; T18571 9 / 2,090,835;
overhead 38 / 5,091,602.

**Where the tokens go.** Cache reads are 98% of the volume. The average context per call grew
from ~89k tokens during the gates to ~151k (T15255), ~182k (T38294), ~196k (T38295), ~212k
(T18570), ~232k (T18571) and ~244k at hand-back. The ~133k chars (~33k tokens) read before the
first case are carried by every one of the ~69 calls after it: about 2.3M cache-read tokens,
15% of the group. The cases themselves were lean: one ckcon call per phase, outputs to files,
the working log written once.

## Overhead findings

**Wasted input: 133k chars read before the first case.**

| call | size | what | narrower read |
| --- | ---: | --- | --- |
| #8 | 33,214 | `TESTBOX-ACCESS.md`, Read in full | none: the lab-home CLAUDE.md requires reading it in full before touching a testbox; only the Test Engineer can relax that |
| #2-#3 | 17,995 + 15,047 | the queue file, lines 10-400 | Session facts (10-32) plus this group's Run section and restore recipe: `sed -n '/<row 4 heading>/,/^## /p'` |
| #6 | 15,705 | `tools/README.md` 20-135, 217-236, 352-460 (and 134-200 again in T15255 #7) | `grep -A12` of the entries used: `tb`, `ckcon.py`, `qmark.py`, `rc2cfg.py`, `rcdiff.py`, `linerate.py` (~6k) |
| #5 | 7,625 | `logged-output.md` §2 | none: the tester's own rules |
| #21 | 7,395 | `cat linerate.py` | needed: the tester extended it in #25-#26 and in T18570 #1 |
| #16-#17 | 2,022 + 5,829 | another group's working log (ports 46421) for NIC and clock facts | #22 `tools/tb nics tb470` (2,588) gave the NIC facts anyway; clocks are three `show clock` lines |
| #12-#13 | 4,911 + 4,154 | `TB470-HOST-NETWORKING.md`, `tools/tb --help` | the `tb` README entry already lists the subcommands |

**Tool building in the overhead.** `tools/snmpwalk.py` (written and unit-tested, #23-#24) and the
linerate `--rx-mac/--rx-len/--ipv6/--src-macs` extension (#25-#26) were done before the first case.
That is legitimate case work for T15255 and T38294; it is counted here only because it happened
before the first call into a case folder.

**Group work inside T15255.** The pre-run captures of u0, u5 and u1 (#1, #4), their read-back
(#2-#3, #5-#6, ~12.5k chars), the qmark re-check for T30403 (#8) and the queue status edits
(#10-#12) belong to the group. Counting them as group overhead would put T15255 near 14 calls.

## Findings that recur across cases (said once here)

1. **`ckcon.py @poll` README wording caused T18570's wasted poll.** The entry says `@poll <s>
   <regex> <cmd>` "(no spaces; use `\s`)". The tester applied that to the command as well and
   sent `show\sinterface\sbrief` literally for 30 s (T18570 #4), leaving eight `user.err`
   lines in the x230 log. Reword the entry: "the regex may not contain spaces (write `\s`); `<cmd>`
   is the rest of the line, with ordinary spaces". T18571 #3 used it correctly.
2. **Counter arithmetic by hand.** Every traffic case read `show interface` before, between and
   after runs, then grepped and subtracted (T18570 #8, the working logs' tables). A helper would
   do it and add what the hand version missed: the bytes per frame, which on the x230 shows the
   802.1Q tag directly (1518.000 B/frame on the access port, 1521.99-1522.00 on the trunk
   members; T18570/T18571 reviews).
3. **The one-frame shortfall.** 11 of 13 linerate runs counted exactly what was sent. Two came up
   one short at 1500 bytes: T38294's bridged baseline (822500/822501) and T38295's IPv6 run
   (822000/822001), where the x230's counters show every frame in and out. That points at the
   host capture ending a moment early, not at the DUT. To close it: have linerate wait ~1 s after
   tcpreplay ends before stopping tcpdump, and print tcpdump's "received by filter / dropped by
   kernel" line.
4. **TTL / hop limit is not checked.** The routed cases count frames by source MAC and length;
   "TTL-decremented" in T38294's working log has no printed source and was left out of the final log.
5. **Setup and teardown lists typed in full per case.** T18570 and T18571 differ in two lines
   (`static-channel-group 2` vs `channel-group 12 mode active`) but each typed ~45 config lines
   on two consoles plus a loop-safe teardown. A plan file would make them data.
6. **Partner .cfg for an unchanged partner** (T38294, T38295 stk_a.cfg) was copied from the 19:33
   group pre-run capture (T38295's via T38294's with the header edited by `sed`). The content is
   right for a stack the case never touched, but nothing re-read the stack. A fresh `show
   running-config` plus `rcdiff.py` against the pre-run copy costs one call.
7. **Evidence kept outside `work/`.** T15255's walk-diff output went to the session scratchpad,
   so the final log can quote only the working log's prose about it. Small diffs belong in `work/`.

## Next run: scripts

| need | today | recommended |
| --- | --- | --- |
| counter deltas | grep + mental subtraction per case | **`tools/ifdelta.py`** (proposed): `ifdelta.py <before.out> <after.out> [--ports port1.0.2,port1.0.3,port1.0.5]` parses ckcon captures of `show interface`, prints per-port input/output packet and byte deltas, drops, and bytes per frame |
| setup/teardown as data | ~45 typed config lines per case per console | `ckcon.py --file <plan.txt>` (proposed option): one command or `@` directive per line, so a case's setup, step and teardown are files in `work/` and T18570/T18571 share one with a parameter |
| host-side capture tail | one frame missed twice | `linerate.py --settle 1` (proposed) and print tcpdump's own counters |
| TTL / hop limit | not checked | `linerate.py --rx-ttl N` (proposed): count only frames arriving with that TTL/hop limit |
| per-case token split | misses `D=.../<id>;` | `case_tokens.py`: match `<group>/<id>` followed by `/`, `;`, a quote, space or end of string, or cut on RESULT lines as here |
| SNMP walk compare | diff by hand in the scratchpad | `snmpwalk.py --compare <other-outfile>` (proposed) |

Existing tools that fit as they are: `linerate.py` (with this group's options), `snmpwalk.py`,
`qmark.py`, `rc2cfg.py`, `rcdiff.py`. Build none of the proposals without the Test Engineer's go;
they go in `tools/` with README entries.

## Next run: references (read these instead of re-deriving)

- **Group facts** for this bench (NICs, MACs, clocks, stack membership, x230 standing state): the
  TOPOLOGY blocks of the five final logs in this folder. tb470 eth1 `00:f0:4d:00:77:16`, eth3
  `00:f0:4d:00:77:18`; the x230 clock is NZ local labelled UTC (~3 s behind tb470), the stack's is
  true UTC (~48 s ahead).
- **x230 CLI on this build** (qmark, 19:35): `ip multicast`, `ip mroute`, `ipv6 multicast` are
  "% Unrecognized command" (no multicast routing, hence T30403 UNSUPPORTED at triage); `ip route`,
  `ipv6 route`, `ipv6 forwarding`, `static-channel-group <1-248>`, `channel-group <n> mode
  active|passive` exist; `show interface status <port>` is refused (use it without a port).
- **Each case's expected outputs** in its review file.

## Suggested shape of the next L2/L3 run

1. Gate (precheck, probe, `tools/tb nics`, three `show clock`) and pre-run captures read with greps: ~8 calls, under 10k chars.
2. Read the queue's group section, the six `tools/README.md` entries, and these review files' expected outputs: 2-3 calls, under 15k chars.
3. Per case: plan file through ckcon, linerate runs, `ifdelta.py`, working log + commit + RESULT: 4-6 calls.

That removes ~25k tokens of carried context (roughly 10-15% of every later call's cache read),
the hand arithmetic, and about a third of the per-case calls.
