# Process review -- ports-2026-10-09T0845 (tb470, x230v2-28GS DUT, T46421 T47208 T47210 T20358 T47209)
Reviewed 2026-10-12 by /create-logs from `agent-a4163fdf23e120522.jsonl` (the bench-runner transcript, run 2 of the
18:00 plan) and the cases' working files. Numbers: `tools/case_tokens.py` split of that transcript (segment = first
tool call into `<id>/` to the case's `RESULT`). Findings cite the segment call number (`#n`, in the order the calls
were made) or the working log. Recommendations are the reviewer's; no verdict is changed here.

## Token usage

| segment | API calls | input | cache write | cache read | output* | tool calls | wall | tool output read | avg context / call |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| overhead (gate, reading, wrap, hand-back) | 29 | 58 | 108,247 | 3,664,830 | 448 | 31 | 424 s | 160,963 chars | 126k |
| T46421 Link flap | 27 | 54 | 51,079 | 4,057,339 | 784 | 29 | 502 s | 36,383 chars | 150k |
| T47208 Copper pluggable speeds | 13 | 26 | 22,571 | 2,464,450 | 109 | 13 | 558 s | 13,318 chars | 190k |
| T47210 MAC/PHY TLV | 11 | 22 | 24,005 | 2,336,485 | 93 | 11 | 635 s | 15,270 chars | 212k |
| T20358 RSTP loopback | 10 | 20 | 21,333 | 2,369,007 | 95 | 10 | 314 s | 6,695 chars | 237k |
| T47209 Fibre pluggable speeds | 10 | 20 | 22,012 | 2,558,937 | 81 | 10 | 352 s | 17,804 chars | 256k |
| **total** | **100** | **200** | **249,247** | **17,451,048** | **1,610** | **104** | **2,785 s** | **250,433 chars** | |

\* Output tokens are as the transcript records them (186 assistant records, 2,293 output tokens in all). They are far
too low for the heredoc working logs written (e.g. T47208 #11, a ~2.4k-char log in one call), so treat the output
column as unreliable; the cache-read column is the one that matters.

**Where the tokens go.** Cache reads are 99% of the volume: every API call re-reads the whole context, which grew
from ~126k tokens during the gate to ~256k per call by T47209. A case's cost is set less by what it does than by
how much is already in context when it starts, so the last cases of the group cost the most per call even though
they were the leanest (10 calls each). The cases themselves were efficient: one ckcon call per step block, outputs
saved to files and grepped back, the working log written once with a heredoc, one commit, one RESULT.

## Overhead findings (the biggest saving)

**Wasted input: 161k chars (~40k tokens) read before the first case, then carried by ~70 later calls.**

| call | size | what | narrower read |
| --- | ---: | --- | --- |
| #7-#8 | 2k + 33k | `cat TESTBOX-ACCESS.md` spilled to a file, then the file Read in full | none allowed: the lab-home CLAUDE.md requires reading it in full before touching a testbox. Only the Test Engineer can relax that (e.g. a "tb470 gate digest" the tools already enforce) |
| #2-#3 | 14k + 12k | the campaign queue, lines 1-260, in full | Session facts (lines 10-32) + the ports Run 2 section (`sed -n '/^### Run 2/,/^### Run 3/p'`) + the ports Results rows: ~6k |
| #9 | 17k | `tools/README.md` lines 20-233 and 348-430 | the entries actually used: `grep -A12 '^### \`ckcon.py\`\|^### \`rcdiff.py\`\|^### \`rc2cfg.py\`\|^### \`qmark.py\`\|^### \`tb\`'` (~5k) |
| #6 | 15k | STANDING-ORDERS.md + logged-output.md §2 | the dispatch already carried the tester's rules; logged-output §2 "The tester's working log" only (~3k) |
| #12 | 11k | six memories in full | the dispatch named their rules; read one only if a case needs it (speed-duplex constraint for T47208/T47209) |
| #14 | 7k | orient-dt SKILL.md sections | bench-runner's own gate list covers the run; orient-dt only if a gate fails |
| #10 | 5k | the platform group's 47226 run1.log (80 lines) to copy the working-log shape | the shape is in logged-output.md §2; or keep a one-page working-log skeleton in `tools/` |
| #26 | 4k | `linerate.py` source, for T20358's planned broadcast | read only after the T20358 gate passed; it failed, so this was never used |

**Misattributed setup.** T46421's segment (#1-#10) holds group work: creating all five `work/` folders, editing and
committing the queue's run row, and extending `tools/ckcon.py` with `@sleep` / `@poll` (reading 13k of ckcon.py and
console.py source). That is ~15k chars and 10 calls of group overhead counted against T46421 (its review says so).

**Gate.** The gate itself was compact: precheck, scratch, peek of six consoles, probe (MATCH), the pre-run captures
of u0/u5/u1 saved to `46421/work/prerun-*` and reused by every case's teardown diff. Good practice: one baseline
capture per group, not per case.

## Cross-case findings (said once here; the case files point here)

1. **ckcon `@poll` made the cases lean.** Added in T46421, it replaced fixed sleeps with "re-run until it matches"
   and records the time taken. Two slips with it, both cost a full timeout: `@poll ... do show ...` at exec mode
   ("% Invalid input", T47210 C1, 61 s) and a regex expecting `a-half` when the x230 prints a configured duplex as
   `half` (T47210 C3, 41 s; T47209 `duplex full` poll, 21 s). A `@poll` whose command errors should stop at once
   rather than wait out the timeout (proposed below).
2. **The x230 status column distinguishes configured from negotiated** (`a-full a-100` vs `full 100` vs
   `half a-100`). Regexes should use `\S*full` / `\S*half` unless the case is about autonegotiation.
3. **`.cfg` timing.** The rule is "after setup, before step 1". T47210 skipped it and re-applied its setup after the
   teardown to capture the files (#7-#8, 2 extra calls, and swi_e.cfg then shows port1.0.2 `shutdown`, unlike the case).
   T20358's swi_f.cfg and T47209's stk_a.cfg were taken at the end of the attempt. Each header says when; none is
   wrong, but capturing in the setup call is cheaper and matches the rule.
4. **Case texts were empty for four of five cases** (T46421, T47208, T47210, T47209: one step, no text, no expected
   result). The tester wrote a method per case; the final logs quote that method. The case owner should add steps.
5. **Cross-file verbatim quoting.** ckcon output carries `HH:MM:SS >>> <cmd>` lines and no device prompt; the final
   logs quote those lines as they are and name the prompt in the step text. If prompts matter for Zephyr, ckcon
   could echo the prompt it matched.
6. **Output read back.** The largest per-case reads were greps of `show log` (T47209 #6, 5.8k) and of pluggable
   detail (T47208 #2, 3k; T47209 #2, 2.1k). `show system pluggable` (the table) and a log grep limited to
   `IMISH.*\](speed|duplex)|EXFX|NSM.*port<p>` give the same facts at a third of the size.

## Next run: scripts

| need | today | recommended |
| --- | --- | --- |
| speed / duplex matrix on a port (T47208, T47209, T47210) | bash arrays built per case, three shapes (`for sp in 100 10 1000`), and T47210's `combo()` shell function pasted twice (#3, #4, 2.5k each) | **`tools/portmatrix.py`** (proposed): `--box tb470 --scratch <dir> --dut u0:port1.0.1 [--partner u1:port1.0.2] --combo "auto 100/auto" --combo "100 full/100 full" ...`; per combo it sets the partner first for forced modes, polls the DUT status, reads `show interface` current/configured lines, optionally the partner's LLDP MAC/PHY TLV, and prints one row per combo (status, current speed/duplex, TLV autoneg/advertised/MAU, % lines). The three cases become three argument lists |
| flap N times and count log events (T46421) | a 3-cycle ckcon block per port + grep counts | `tools/portmatrix.py --flap 3` or a small `tools/flapcount.py <stdout> <ports>` that counts `Port down/up notification` per port from the `show log` in a ckcon stdout |
| `@poll` that errors | waits out the full timeout on "% Invalid input" | ckcon: stop a `@poll` immediately when its command returns a `% ` line |
| BPDU path check before closing a loop (T20358) | a 20 s `@poll` for Backup/Discarding, then manual reading of `show spanning-tree interface` | keep the gate; add `Received` (`Received None` / `Received RSTP`) to the poll so the reason prints directly |

Build none of these without the Test Engineer's go; they go in `tools/` with README entries.

## Next run: references (read these instead of re-deriving)

- **`platforms/x230v2-28GS.md` §2 (Platform-facts table)** already holds this group's product findings: the SX
  module accepting `speed 100` (T47209), fixed `speed 1000` advertising autoneg Disabled (T47210), SPTX at 10 Mb/s
  not measurable against the IE520 (T47208), and the STP-off stack not forwarding BPDUs (T20358). Read that table
  first; it is 20 lines.
- **Bench links for the x230 as DUT** (not yet in the platform file; worth a row or a short section there) (from these logs): port1.0.1 AT-SPTXa <-> AR4050S port1.0.2 (fixed copper,
  10/100/1000 half/full: the only 10 Mb/s / half-duplex partner; shut down on the 4050 by default, so put x230
  port1.0.1 alone in a VLAN before `no shutdown`); port1.0.2 AT-SPTX <-> stack port1.0.2 (in sa2: the stack refuses
  speed changes there, "% port1.0.2: Cannot configure aggregator member."); port1.0.3 AT-SPTX <-> stack port1.0.17
  (IE520 AT-SPTXa refuses 10 Mb/s); port1.0.4 AT-SPSX <-> stack port1.0.3 (1000BASE-SX, no DDM); port1.0.5 AT-SPTXc
  <-> tb470 eth3 (host NIC; flapping it needs root).
- **The x230 clock** runs `no clock timezone` with NZ wall time labelled UTC, so its log times read as NZDT, ~2 s
  behind tb470; the stack is true UTC. Record once per group (T46421's working log has it).
- **RSTP loop cases** need the recable in T20358's UNBLOCK (x230 port1.0.6 <-> 1.0.7 fibre loop) or a hub; the
  stack has no BPDU-tunnel option (`l2 ?` unrecognised).
- **`show log tail` does not exist on the x230** (T46421 attempt 1 stopped on it): use `show log` and grep.
