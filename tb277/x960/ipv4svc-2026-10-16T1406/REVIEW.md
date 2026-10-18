# Group process review -- ipv4svc-2026-10-16T1406
Reviewed 2026-10-19 by /create-logs from `agent-a716404dd1611bc0d.jsonl` and the working files.

Group B of the tb277 x960-56YSQ campaign: T44181 Ping Polling, T44378 UDP Broadcast Helper,
T44182 Directed Broadcast Forwarding. 3 attempted, 3 PASS. One tester (bench-runner subagent),
one DUT (swi_d on u2), 152 tool calls.

This file carries everything true of all three cases. The per-case `-review.md` files point
here instead of repeating it.

## Token usage

| segment | calls | input | cache write | cache read | output | tool calls | wall s | tool output read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| T44181 | 79 | 158 | 115,048 | 13,922,735 | 890 | 80 | 2475 | 63,461 |
| T44378 | 20 | 40 | 31,548 | 5,227,485 | 216 | 20 | 716 | 13,554 |
| T44182 | 21 | 42 | 30,664 | 6,240,989 | 207 | 21 | 727 | 9,670 |
| **overhead** | 25 | 50 | 99,655 | 3,391,079 | 287 | 31 | 287 | **144,150** |
| **total** | 145 | 290 | 276,915 | 28,782,288 | 1,600 | 152 | 4,205 | 230,835 |

Measured with `python3 -I tools/case_tokens.py --transcript <the tester's .output> --cases
T44181,T44378,T44182`.

### How to read it

- **The group cost 28.8 M cache-read of a 126.0 M campaign** (10 cases, 599 calls) -- 23% of
  the campaign for 30% of its cases. Overhead across the whole campaign was **9%**; the
  2026-10-15 campaign on this same bench ran **46%**, so the campaign-wide number is a large
  improvement and the structure that produced it (one dispatch brief carrying the session
  block, the gate run once per group rather than once per case) should be kept.
- **This group's own overhead is the outlier: 11.8% of its cache-read, and 144 kB of tool
  output -- more than any single case read, more than all three cases combined (86.7 kB).**
  Every byte of it was read before the first command reached the DUT. That is where the next
  group's saving is, not in the measurement.
- **T44181 dominates the cases**: 13.9 M cache-read, 80 tool calls, 41 minutes of wall. It read
  back 63,461 chars of tool output, **2.7x T44378 and T44182 combined** (23,224), and 1.21x
  their combined cache-read (13.9 M vs 11.5 M). Three things made it expensive and only one of
  them was the case: 11 authored steps (unavoidable), a new tool written from scratch
  mid-case (`hostsim.py`, ~12 calls), and three framework-level defects found and fixed while
  it ran (~8 calls). The two later cases, running on the underlay and tooling T44181 had
  already built, cost ~20 calls each. **Build the instruments before the first case, not
  inside it.**

## Overhead findings -- the gate, the rules and the prior reading

The overhead segment is tool calls **1-25** (orientation, rules, guides, the gate, the shared
underlay and the queue edit), **106-109** (the `arpleg.py --udp` / `--l2-dst` extension, built
in the gap between T44181 and T44378) and **144-152** (post-group probe, partner-config check,
the queue results rows, the final `git status`, the hand-back). Its findings:

1. **The campaign queue was read nearly end to end, in four overlapping slices, for one
   group's rows.** Calls #3 `sed -n '1,250p'` (20,445 chars -- the largest single read of the
   whole group), #5 `sed -n '245,640p'` (2,227), #6 `sed -n '300,470p'` (11,629) and #7
   `sed -n '470,640p'` (17,122), plus #1's headings (1,627): **~53 kB, 37% of all overhead
   tool output**, to find the Group B rows, the session block and the triage note.
   *The narrower read:* the dispatch brief already carried the session block (box, consoles,
   PDU, names). The tester needed only its own group's rows and the campaign-wide constraints.
   `awk '/^### Group B/,/^### Group C/' <queue>` plus `sed -n '/^## Constraints/,/^## /p`
   would have cost under 6 kB. **Recommendation: the dispatch brief should name the queue's
   line range for that group, or the group's rows should be extractable by a `--group`
   flag (see "scripts" below).**
2. **`tools/README.md` was read twice at the top, overlapping, then four more times in the
   cases.** #8 `sed -n '20,200p'` (11,217) and #11 `sed -n '357,400p;414,560p'` (12,824) =
   24 kB up front; then #38 (3,245), #48 (801), #49 (255), #81 (1,452) while cases ran.
   *The narrower read:* the up-front pass should be the index only (the `### \`name\`` lines,
   ~1 kB) and each tool's own section read when that tool is first used -- which is what the
   in-case reads already did correctly. The 24 kB up front bought almost nothing the later
   targeted reads did not re-fetch anyway.
3. **The rules were read correctly and should not be trimmed.** #4 read STANDING-ORDERS
   97-200 plus logged-output 47-195 in one call (11,759 chars). That is the right shape: one
   call, bounded ranges, the sections that govern a run. Keep it.
4. **The platform file paid for itself.** #9 headings + #10 `sed -n '389,512p' platforms/x960.md`
   (7,762) gave the reload window, the console facts and the §6/§7 material the three cases
   leaned on. Keep.
5. **The Feature Overview Guide pass was efficient and is the model for a no-step-text case.**
   #23 converted the IP guide with `pdftotext -layout` to the scratchpad (21 chars back), #24
   grepped it (2,965) and #25 read only the two relevant pages (5,484). Both step-text-less
   cases were authored from that. **Never `cat` a converted guide; convert, grep, read the
   page.**
6. **The gate itself was cheap and complete**: #15 `tools/tb precheck`, #16 scratch + template,
   #17 peek on all three consoles, #18 NICs, #29 `tools/tb probe`, #30 the capture clocks.
   Six calls, ~4.5 kB. Nothing to cut.
7. **`tools/tb --help` (#19, 4,118) and `arpleg.py --help` (#13, 3,290) were read before the
   tools were used.** Correct, and cheaper than a failed invocation -- but both are stable
   surfaces that belong in the dispatch brief or in a one-page cheatsheet rather than being
   re-derived per group.

## Findings that recur across all three cases

### A1. The working logs do not name every tool and its arguments (logged-output.md §2)

`ckreload.py` and `rc2cfg.py` were used in all three cases and are named in **none** of the
three working logs. `ckcon.py`, `ckyn.py` and `cfg.py` are named in T44181's log only (and
`ckcon` there just once, bare); T44378's and T44182's logs name only `arpleg`, `qmark`,
`rcdiff`, `ckcase` and `sudotool`. Because `/create-logs` may use nothing but the working log,
the final logs' tool lines were written without them.

*Why it matters:* the tool line is how the next tester reproduces the run. A reader of
`T44378.log` cannot tell how the reload was driven or how the `.cfg` was made.

*Fix:* the working log's "tools used" block must be written from the commands actually sent,
with their exact arguments -- including the ones invoked indirectly through `tools/tb`
(`tb cfg` -> `cfg.py`, `tb ckcon` -> `ckcon.py`, `tb ckyn` -> `ckyn.py`, `tb ckreload` ->
`ckreload.py`, `tb sudotool X` -> `X.py`) and the ones invoked as plain `python3 tools/*.py`
(`rc2cfg.py`, `rcdiff.py`). A `tools/` helper could emit this block (see S3).

### A2. `arpleg.py` mis-marked its own frames on well-known UDP ports -- a false counter disagreement

Found in T44378 (call #114), fixed in the same case (#115, #117). `arpleg.py` identified its
own frames by looking for the `CKARPLEG` payload marker in `pkt[Raw].load`. **scapy dissects
well-known UDP ports into their own layer -- 69 becomes TFTP, 67/68 BOOTP, 53 DNS -- so for
those ports there is no `Raw` layer at all.** The `:69` burst therefore reported **0 of its
own 5 frames** as `[ours]`, and the leg exited 7 with
`COUNTER DISAGREEMENT: sent 20 marked frame(s), capture on eth3 holds 15`.

The measurement was not wrong -- the frames were on the wire and the pcap held them -- but
**the instrument's self-check was**, which is worse than a wrong number because it is the
check that is supposed to catch a wrong number. Both `classify()` and `report()` now scan
`bytes(pkt)`, the whole frame. The baseline leg was re-run after the fix: all four flows
`[ours]`, exit 0. Same family as the already-documented `dhcp4.py` BOOTP trap.

**What it means for reading older results:** any `arpleg.py` leg run **before 2026-10-16** that
used a well-known UDP port (69, 67, 68, 53, and any other port scapy binds to a layer) will
have under-counted its own frames and may have exited 7 with a COUNTER DISAGREEMENT that was
not real. A leg on an arbitrary high port (7777, 9) is unaffected. If an old result rests on an
`[ours]` count or on a clean exit from such a leg, re-read its pcap rather than its summary --
and treat a historic COUNTER DISAGREEMENT on a well-known port as unproven, not as a finding.

### A3. The shared underlay was built once and inherited -- keep doing this

T44181 built the VLAN 10 / VLAN 48 L3 underlay (calls #36-37) and recorded it in the queue with
its exact restore recipe **before any configuration**, so T44378 and T44182 started from a
proven L3 path and groups C and D inherited it. Their `rcdiff` against T44181's pre-group
capture showed only the 31 underlay lines. This is a large part of why cases 2 and 3 cost ~20
calls each. The cost lands entirely on case 1, which is the right place for it; a reviewer
comparing per-case numbers should not read T44181's size as waste.

### A4. The box's copy of `tools/` goes stale after every local edit

`tools/tb scratch tb277 ckt1406b` was re-run at #16, #43, #51, #65, #110 and #114 -- six times.
At #64 a leg produced stale results and #65 had to diagnose and re-push before continuing.
Six generic tool edits were made during the group (`hostsim.py` created; `tools/tb` SUDO_TOOLS
allowlist; `arpleg.py` four times; `console.py` ADVISORY). Each needed a push nobody tracked.

*Fix:* either push unconditionally as the first action of every `sudotool`/`tool` invocation,
or make `tools/tb` compare a checksum and refuse to run a stale copy. Until then: **after any
edit under `tools/`, the next command is `tools/tb scratch`.** A silent stale copy is an
accuracy risk, not just a delay -- #64's leg looked like a measurement.

### A5. Every case used the same six-leg skeleton, and it worked

Baseline OFF -> feature ON -> the discriminator isolated -> persistence across a reload ->
removal proven in the dataplane -> teardown diff. Every positive claim had an in-leg control
flow that must *not* change, and every claim was read off the wire, not off
`show running-config`. All three cases are CLEAN with an empty teardown diff. **This skeleton
is the group's most reusable output; it should be the default shape of an IPv4-services case.**

### A6. Two of three cases had no authored step text

T44378 and T44182 were designed from the **IP Feature Overview Guide C613-22007-00 REV I**
(p.16 IP Helper, p.17 IP Directed Broadcast) plus the DUT's own CLI surface read with
`qmark.py`. Both logs cite the guide page per claim, which is what makes the verdict
re-gradable. **For a case with no step text, the guide page is the step text** -- cite it in
the step heading, not just in the preamble.

## Next run: scripts (shared)

Existing `tools/` entries that already fit and should not be rebuilt:

- **`tools/arpleg.py`** -- now the group's workhorse. Gained in this group:
  `--udp DST[:PORT][@SRC][,...]` (chosen UDP destination port and per-spec source),
  `--l2-dst MAC` (send to a chosen L2 destination, e.g. `ff:ff:ff:ff:ff:ff`), the whole-frame
  marker scan (A2), and a `chown` of its `--out` directory back to `SUDO_UID`.
- **`tools/hostsim.py`** -- new here. A fake IPv4 host on one NIC: answers ARP who-has and ICMP
  echo for given addresses, with `--mute-ip IP --mute-at S --unmute-at S` and
  `--log-echo FILE` (a per-echo TSV). Already in `tools/README.md`.
- **`tools/qmark.py`** (via `tools/tb qmark`) -- the read-only CLI-surface probe, no trailing
  CR. Used in all three cases to prove a command exists before relying on it.
- **`tools/poll.py`** (via `tools/tb poll`) -- the periodic `show` sampler with a donefile.
- **`tools/rc2cfg.py`** / **`tools/rcdiff.py`** -- the `.cfg` writer and the teardown diff.
- **`tools/tb capture`** -- host-side pcap alongside a leg.

Proposed (not built -- listed with the arguments they would take):

- **S1 `tools/queue_group.py --queue <queue.md> --group B [--rows-only]`** -- print one group's
  rows, its triage note and the campaign-wide constraints block, nothing else. Would have
  replaced ~53 kB of queue reading with under 6 kB (finding 1).
- **S2 `tools/tb cheatsheet`** -- the one-page `tools/tb` subcommand index plus the `###` index
  of `tools/README.md`, so the up-front read is ~1 kB instead of 24 kB (finding 2).
- **S3 `tools/toolsused.py --transcript <.jsonl> --since <marker>`** -- emit the working log's
  "tools used" block from the commands actually sent, expanding `tools/tb <sub>` to the
  underlying `tools/*.py` and its arguments. Closes A1 mechanically rather than by discipline.
- **S4 `tools/tb scratch --if-stale`** -- checksum the box copy of `tools/` and push only when
  it differs; have `sudotool`/`tool` call it automatically. Closes A4.
- **S5 `tools/leg.py --tag T --spec <legs.yaml>`** -- run the A5 skeleton's N legs (stimulus +
  control + watch interface + expected disposition) and print one table per leg with a verdict
  column, instead of each case assembling `arpleg` invocations by hand.

## Next run: references (shared)

Read these instead of working the fact out again:

- `platforms/x960.md` **§6** (DHCP relay semantics, for the contrast in O-18) and **§7**
  (IPv4 services; **§7.9** is the 60-68 s reload window both reload legs matched).
- `tb277/x960/ipv4svc-2026-10-16T1406/T44181/T44181.log` **TOPOLOGY AS TESTED** -- the VLAN 10 /
  VLAN 48 underlay, both host NIC MACs and addresses, and the DUT clock offset. T44378 and
  T44182 point at it rather than re-capturing; groups C and D inherit it.
- The campaign queue's **"Group B/C/D shared underlay"** block -- the exact configuration and
  its restore recipe.
- **IP Feature Overview Guide C613-22007-00 REV I**, p.16 (IP Helper) and p.17 (IP Directed
  Broadcast), under `Feature Overview Guides/`. Convert with `pdftotext -layout` into the
  scratchpad, grep, then read the page.
- `logged-output.md` **§2** for what the working log must hold (A1), **§5** for this file.
- `STANDING-ORDERS.md` **§4** -- no root-level write on the box in an unattended run. This is
  what makes the trigger-script-content limb of T44181 unmeasurable; see that case's review.
- Memory **`scapy-for-traffic-tests`** and **`tcpdump-nfs-root-squash-capture`** -- A2 is a new
  member of the same family.
