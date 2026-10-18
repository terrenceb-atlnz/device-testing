# T43863 process review -- mcast-2026-10-16T1406
Reviewed 2026-10-19 by /create-logs from `a81d52aff45c3f339.output` and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 73 | 146 | 111,702 | 13,395,700 | 789 | 78 | 41m 06s | 38,714 |

78 tool calls, the most of any case in the group, and **the cheapest per call: 171,740 cache-read
per tool call, against 361,810 for T43866**. It is the group's expensive case in absolute terms
and its cheapest in marginal terms, because it ran first -- see REVIEW.md finding 1.
About half of this segment is not T43863 the test case: calls 32-51 build the group's two-router
underlay, and calls 45-47, 52-55 and 64 build the instruments (see "Process taken").

## Process taken
1. **(32-34)** Pre-case `show running-config` from all three units into `work/pre-u{2,3,5}.log`,
   each greped down rather than read whole. 842 chars read back for swi_a, less for the others.
2. **(35-37)** Queue read, the group's setup + restore recipe written to the scratchpad, the
   queue's group-C row flipped to RUNNING.
3. **(38-39)** `service pim` / `service pdm` sent on swi_b **alone** -- the licence probe (O-20)
   -- and the answer reported to the sentinel. This settled the partner in the first eight
   minutes and is the single highest-value call in the segment.
4. **(40-44)** First underlay batch: STP priority 0, shut `port1.0.2` / `port1.0.14`, vlan 61,
   retire the DUT's vlan48 SVI, trunk `port1.0.4`. The batch truncated twice.
5. **(45-47)** Diagnosed the truncation in `tools/console.py` and fixed it -- the **prompt-splice**
   defect, O-23 (REVIEW.md finding 3). 3,388 chars read back, the largest read of the segment.
6. **(48-51)** Underlay re-applied and verified from **both ends** -- DUT `show spanning-tree
   brief`, swi_a `show spanning-tree brief` + `ping 10.0.61.1`.
7. **(52-55)** `tools/arpleg.py` read and extended with multicast link-layer derivation;
   `tools/igmp.py` written from nothing.
8. **(56-57)** STEP 0 -- baseline with the feature off and the receiver already joined.
9. **(58-65)** PIM-SM up on both routers: the `service` gate, the `ip multicast-routing` gate
   captured deliberately, adjacency, RP mapping. Call 64 is the second `console.py` fix.
10. **(66)** `work/setup-u{2,5}.log` + `rc2cfg.py` → `swi_d.cfg`, `swi_a.cfg`.
11. **(67-79)** STEP 2, the F-13 diagnosis: the failing leg, then `show ip igmp groups` /
    `local-members` / `rp mapping` / `show ip route 10.38.22.40` / a 16 s wire sniff of the
    report / `show ip igmp interface vlan48` -- the read that named the cause -- then `ip igmp`
    and the same reads again.
12. **(80-95)** STEPs 3-6: forwarding, the transit-wire Register decode (two tcpdump captures),
    prune on leave, and the RP A/B.
13. **(96-101)** STEP 7: stage `flash:/ck43863.cfg`, reload, re-read STP twice, measure, restore
    the boot pointer, delete the staged file.
14. **(102-104)** STEP 8 removal, then post-case captures and `rcdiff.py` against the pre-group
    baseline on both devices.
15. **(105-109)** `work/run1.log`, the queue's findings (F-13, O-20..O-24), the `tools/README.md`
    entry for the arpleg change, and `RESULT T43863 PASS`.

## Wasted input
- **`sed -n '40,75p;215,250p' tools/console.py` (3,388 chars)** and
  **`sed -n '180,215p' tools/arpleg.py` + `sed -n '215,235p' tools/arpleg.py` (1,734 + 950)**.
  These were necessary -- the tester was editing both files -- but the second `arpleg.py` read
  overlaps the first by nothing and was a second guess at the right line range. **A
  `command grep -n 'def build\|--udp\|l2_dst' tools/arpleg.py` first would have found the splice
  point in one read instead of two.** The tester did exactly that in the overhead segment for the
  same file; doing it again here would have cost 200 chars instead of 950.
- **The post-case `show running-config` pair (1,833 chars read back, call 104)** prints the
  `rcdiff.py` output *and* the line counts of both captures. The diff is the result; the line
  counts are not. Minor.
- Nothing else. Every console read in this segment is greped or `sed`-ranged at the point of
  capture, and the two long `tcpdump` outputs were taken as background tasks and then read with
  a `grep -aE 'PIMv2|239\.2\.2\.2|IGMP'` filter rather than in full.

## Repetition
- **`show spanning-tree brief` four times** (calls 42, 51, 98, 99). Three of the four were right:
  before measuring, from the partner's end, and the post-reload re-read. See REVIEW.md finding 5
  for the proposed `--wait-stp` that would collapse the last two into one call.
- **`show ip pim sparse-mode mroute` on swi_a three times in four minutes** (calls 70, 71, and
  the re-read inside 74) while chasing F-13. Two of those were triggered by the sentinel's wrong
  diagnosis (below); the third found the real cause. The reads were right, the trigger was not.
- The long `arpleg` bench-identity argument block appears in all 12 legs of this case. Group-wide
  point, REVIEW.md finding 4.

## Accuracy risks
- **🔴 STEP 6(a): the read-back was recorded as prose, not as raw output.** The working log says
  `show ip pim sparse-mode rp mapping` on swi_a "then prints its header and no mapping" after
  `no ip pim rp-address 10.0.61.2`, and the final log repeated that wording rather than inventing
  a quote -- which is the correct handling of the source it had. But the transcript at 16:47:37
  shows the device output was captured and *does* end at `PIM Group-to-RP Mappings` with nothing
  after it, so the verbatim line existed and was lost to a `tail -3` that kept only the config
  echo. **Fix: when a read-back is the evidence for an A/B half, capture it to a `work/` file
  (`> work/s9-norp-u5.log`) and quote it, rather than greping it down to a summary at the point
  of capture.** The A/B's *measurement* (0 of 10 → 8 of 10) is unaffected and is on the wire.
- **🔴 A sentinel error cost this case time, and its fix is a standing rule.** At 16:39:48 the
  sentinel sent two diagnoses: that swi_a "does not know who the RP is" and that it had no RPF
  route to the source. The tester's own reads at 16:40:16 showed
  `Group(s): 224.0.0.0/4, Static  RP: 10.0.61.2  Uptime: 00:04:38` -- an uptime of 4m38s puts the
  mapping at ~16:35:38, **predating the message** -- and `show ip route 10.38.22.40` →
  `10.38.22.32/27 via 10.0.61.1, vlan61`. The sentinel withdrew both at 16:41:05. **What it
  misread:** `RP: 0.0.0.0` and `RPF nbr: 0.0.0.0 / RPF idx: None` were fields on an **(S,G,rpt)**
  entry in `RPT NOT JOINED` state, where zero is normal -- a per-entry state read as a global
  configuration gap. Cost: calls 70-74, ~2 minutes of bench time plus the context, in the middle
  of the group's hardest diagnosis. **Fix, for tester and sentinel alike: read the global
  group-to-RP mapping from `show ip pim sparse-mode rp mapping`, never from an (S,G,rpt) row's
  `RP:` field.** The episode is also a good outcome: the tester checked rather than acted, the
  sentinel corrected itself within 80 s, and the "before" state became legitimate baseline
  evidence in the log rather than a discarded false start.
- **O-21 is a live misreading hazard for the next tester.** `show ip igmp groups` prints
  `Last Reporter 0.0.0.0` on this build although the report on the wire carries a correct
  on-subnet source (10.38.22.70, confirmed by capture) -- both before and after `ip igmp`. It
  reads like a malformed report and **cost diagnosis time inside F-13**. The tester exonerated the
  host by sniffing the report before blaming the platform, which is the right order and should be
  the habit: **confirm the stimulus on the wire before diagnosing the DUT.**
- Two PIM-SM limbs are named as unreachable rather than silently omitted (ASSERT needs two PIM
  routers on one shared segment, and the only multi-router segment is a /30; BSR / candidate-RP
  election needs a third PIM router, and only two units hold the PIM licence). Both are declared
  in the log's CAVEAT. **No claim rests on inference anywhere in this case** -- every verdict line
  is a count at eth4 or a decoded frame on vlan 61.

## Next run: expected outputs
| step | value / CLI line this bench gave |
| --- | --- |
| licence probe | swi_b: `% Service is not currently licensed on this platform` to BOTH `service pim` and `service pdm`; nothing applied, running-config unchanged |
| service gate | `service pim` accepted on swi_d and swi_a; `show process \| include pim` → ` 4353 pimd   5  0.0  0.1   20 sleep` |
| second gate | `ip pim sparse-mode` before `ip multicast-routing` → `% IP Multicast Routing not activated` |
| absent command | `show ip multicast-routing` → `% Invalid input detected`. It is not a command on this build |
| SVI removal | `no interface vlanN` → `% Removal of interface not allowed` (O-22). Use `no ip address`, then `no vlan N` in `vlan database` |
| adjacency | `show ip pim sparse-mode neighbor` → `10.0.61.2  vlan61  00:00:57/00:01:18  v2  1 / DR`, up within ~60 s |
| RP mapping | `Group(s): 224.0.0.0/4, Static` / `RP: 10.0.61.2` on BOTH routers (static RP is not learned from a neighbour) |
| F-13 symptom | `show ip igmp interface vlan48` → `IGMP Disabled, Active(Snoop Only), Non-Querier, Version 3 (default)`, `IGMP querying router is 0.0.0.0`, while `show ip igmp groups` lists the group with a live expiry and `show ip pim sparse-mode local-members` is EMPTY |
| F-13 fix | one `ip igmp` on the interface → `IGMP Enabled, Active, Querier` and `(*, 239.1.1.1) : Include` |
| baseline OFF | joined receiver 0 of 10; routed ICMP control 5 of 5 arriving with swi_a's MAC |
| forwarding | 5 of 5 steady for the joined group, egress eth src `88:9d:98:df:26:02`; never-joined control 0 of 5 in the same leg. **First leg after a join is 4 of 5** -- 1-2 frames are consumed building the tree |
| Register | `PIMv2, Register, length 62/66` (data) and `length 28` (null) from `10.38.22.34` -- the DR address on the SOURCE interface, not the transit address |
| sequence | Register → RP `Join / Prune` **0.6 ms** later → native data on vlan 61 **340 ms** after that → `Register Stop, length 18` once the SPT is up → null Registers continue as keepalives |
| mroute (RP) | `Owner PIM-SM, Flags: TF`, `Incoming interface: vlan61`, `Outgoing interface list: vlan48 (1)` |
| prune on leave | left group 0 of 5 while a still-joined group holds 5 of 5 in the same leg |
| RP A/B | mapping removed → 0 of 10 for a JOINED group; restored → 8 of 10 |
| reload | `ckreload … 480` → `reboot system? (y/n):` → login after **61 s**; adjacency re-forms by itself in ~14 s |
| 🔴 post-reload STP | `port1.0.48 Designated Discarding` for a **17-21 s window** after login. Measuring there gives a FALSE ZERO. Re-read until Forwarding |
| post-reload leg | 8 of 10 for a group first used after the reload; control 0 of 10; instrument 10 of 10 |
| removal | `no ip pim sparse-mode` on vlan10 → the line is gone from `show running-config interface vlan10`, and 0 of 10 for a group that was forwarding 8/10 minutes before |

## Next run: scripts
- **Existing, and they carried the case:** `tools/arpleg.py` (every counted leg; the multicast L2
  derivation added here), `tools/igmp.py` (written here), `tools/cfg.py` / `tools/ckcon.py` /
  `tools/ckyn.py` / `tools/console.py`, `tools/qmark.py` for the read-only `?` probes,
  `tools/ckreload.py`, `tools/rc2cfg.py`, `tools/rcdiff.py`. The DUT's own
  `tcpdump -i vlan61 -nn` at privileged exec read the transit control plane.
- **Proposed `tools/bootcfgtest.py`** -- the reload/persistence limb, built by hand here and three
  more times in this group. Arguments and the `--wait-stp` rationale are in REVIEW.md finding 5.
- **Proposed `--profile` for `arpleg.py` and `igmp.py`** -- REVIEW.md finding 4.

## Next run: references
- **O-20** -- `service <x>` alone is the only clean licence probe; the read-only surface cannot
  settle it. REVIEW.md "Next run: references" has the full statement.
- `platforms/x960.md` §7.10 (single-instance RSTP, read STP from both ends), §7A.1 (the service
  gate), §7A.2 (sticky `no service`, and O-24's "the boot, not the daemon" discriminator).
- RFC 4601 for the PIM-SM mechanisms a verdict must show -- this case was designed from it,
  because **no authored step text exists** (ck.db `zephyr_cases` id 40183: no objective, no
  precondition, empty `steps`). `tools/ckcase.py` returns that in one call; confirm it and say so
  in the log rather than re-deriving the absence.
- The expected-output table above is the content of the **proposed `platforms/x960.md` §7D**
  (REVIEW.md finding 10).

---
Group-wide findings are in [REVIEW.md](../REVIEW.md) and are not repeated here.
Recommendations are the reviewer's; findings cite the transcript segment or working log they come from. A review never changes a verdict.
