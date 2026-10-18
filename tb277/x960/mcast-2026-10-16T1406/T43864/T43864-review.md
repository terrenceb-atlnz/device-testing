# T43864 process review -- mcast-2026-10-16T1406
Reviewed 2026-10-19 by /create-logs from `a81d52aff45c3f339.output` and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 37 | 74 | 41,131 | 9,864,930 | 414 | 37 | 20m 07s | 12,922 |

37 tool calls and the shortest wall time of the four, on a case with 8 steps plus a baseline, 12
counted legs and a reload. **266,620 cache-read per tool call, 55% more than T43863's 171,740** --
the position effect, REVIEW.md finding 1. The efficiency came from inheriting a built bench, a
proven instrument and a protocol pattern: the case converted PIM-SM's structure into PIM-DM's in
one setup batch.

## Process taken
1. **(110)** Pre-case captures created by **copying T43863's post-case captures** -- the right
   move, and worth copying: the group shares one underlay, so `cp post-u2.log pre-u2.log` is both
   cheaper and *more* accurate than a fresh read. Then `service pdm` on both routers.
2. **(111)** `show process | include pdm` (the daemon instrument), a join, and the baseline leg
   with `pdmd` deliberately already running -- a stronger baseline than feature-off, isolating
   the configuration rather than the service.
3. **(112)** PIM-DM up on both: `ip multicast-routing`, `ip pim dense-mode` on vlan10 + vlan61,
   same on swi_a. No RP anywhere.
4. **(113-115)** The authored step, both halves: leg 3a with the pre-`ip igmp` membership (0/10),
   then the re-join and leg 3b (10/10) -- the F-13 addendum, below.
5. **(116-124)** STEP 3/4, three never-joined groups and the transit-wire decode. Call 117's
   unfiltered `tcpdump -c 24` was eaten by LDF (O-26); 120 retried with `-nn ip`.
6. **(125-129)** The 30/30 confirmation leg and the Graft capture.
7. **(130-135)** STEP 5 Graft A/B (0 of 50 → 20 of 20), then prune on leave.
8. **(136-139)** `work/setup-u{2,5}.log` + `rc2cfg.py`; stage, reload, re-read STP, post-reload leg.
9. **(140-143)** Boot pointer restored, staged file deleted, removal leg, post-case captures and
   `rcdiff.py`.
10. **(144-146)** `work/run1.log`, the queue's O-25 / O-26 / F-13-addendum entries, and
    `RESULT T43864 PASS`.

## Wasted input
- **`tools/tb grep tb277 '239.11.11.11|PIMv2' /tmp/ckt1406c/console-u2.log | tail -20`
  (1,452 chars, call 124)** -- the largest read of the segment, and it re-reads from the box's
  console transcript output the tester had **already** received from the same command's stdout at
  call 121/122. The `tcpdump` output had been captured as a background task and read with a
  filter; this is a third look at the same frames. **A background capture's `.output` file is the
  record; read it once, with the filter that answers the question.**
- **Calls 119, 122, 123, 126, 132, 133 all read the same two background-task `.output` files**
  (`b1l6cpn7k.output` three times, `biaon8s2j.output` twice) with slightly different greps --
  1,000 + 488 + the two `tail -18/-20` reads. Each read was cheap; the pattern is the waste.
  **One read with a union filter (`PIMv2|239\.|packets captured`) answers all of them.**
- The three `igmp join` + `arpleg` composite calls (575, 545, 472 chars) echo the full bench
  identity back in their output. Group-wide, REVIEW.md finding 4.

## Repetition
- **Three reads of one background capture file** and **two of another** (above). ~2.5 kB and six
  calls where two would do.
- **`show spanning-tree brief` twice** (138, 139) -- the post-reload Discarding-window re-read.
  Correct, and the candidate for `--wait-stp` (REVIEW.md finding 5).
- The reload/persistence block is this group's second hand-built copy of eleven identical steps.
  REVIEW.md finding 5.

## Accuracy risks
- **🔴 The F-13 addendum caught this case even though the case had applied F-13's lesson, and that
  makes it an ORDERING rule rather than a configuration rule.** `ip igmp` was in the setup from
  the start, but the baseline join at 17:01:45 was sent **~45 s before the `ip igmp` line landed**,
  so it went into the snooping table only; the first forwarding leg read 0 of 10 for a group that
  looked joined, and an identical leg after a re-join read 10 of 10 with nothing else changed.
  **A membership learned while an interface was snoop-only does NOT migrate when router-side IGMP
  is later enabled -- it must be re-sent.** The tester handled it correctly -- both halves are in
  the log as legs 3a and 3b, which makes the mechanism part of the evidence -- but the next run
  should not pay for it again. Standing rule in REVIEW.md finding 7.
- **🔴 O-25: the FLOOD half of flood-and-prune is declared NOT MEASURED, with the instrument that
  would measure it named.** Three never-joined groups were streamed (40, 50 and 25 frames at
  4-5 frames/s), two with a capture armed on vlan 61 beforehand, and **not one data frame of any
  of them reached the transit segment or the receiver**. This is a stimulus limit, not a platform
  fault and not a defect in the case: State Refresh is active on this build (STEP 4), which is
  precisely the feature that suppresses the periodic re-flood, and the first-packet flood
  converges faster than a 0.2 s inter-frame gap can sample. **It is a standing gap for the next
  run**: a line-rate stimulus (`tools/linerate.py`, or tcpreplay) with a capture on vlan 61 and
  **per-frame timestamps**, so the flood/prune boundary is located in *time* rather than counted.
  The PRUNE itself is unambiguous and the verdict does not rest on the flood.
- **O-26 cost one capture.** An unfiltered `tcpdump -i vlan61 -c 24` was consumed by the DUT's
  1 Hz loop-protection LDF stream before much PIM or data landed. The retry with `-nn ip`
  succeeded. Exact filter and rationale in REVIEW.md finding 8.
- PIM-DM ASSERT is named as unreachable on this bench (two PIM routers on one shared segment; the
  only multi-router segment is a /30), and swi_a was never reloaded, so reboot persistence is
  claimed for the DUT only. Both are declared in the log's CAVEAT.
- **No verdict line rests on inference.** The authored objective and authored topology are each
  matched to a measured thing (swi_a running `service pdm` + `ip pim dense-mode` with the
  adjacency up, so `sw1` is a real PIM-DM router and not a simulation), and the PIM-DM-specific
  claims are decoded frames, not counters.

## Next run: expected outputs
| step | value / CLI line this bench gave |
| --- | --- |
| authored text | ck.db `zephyr_cases` id 40184 DOES carry content: objective "PIM-DM works as expected DUT can route multicast traffic using PIM-DM", precondition `IXIA -- DUT -- sw1(running PIM-DM)-- IXIA`, steps_text "Setup a PIM-DM network  Multicast client able to get multicast stream". No authored expected result |
| service gate | `service pdm` accepted on swi_d and swi_a, refused on swi_b (`% Service is not currently licensed on this platform`); `show process \| include pdm` → ` 3343 pdmd   5  0.0  0.1   20 sleep` |
| adjacency | `show ip pim dense-mode neighbor` → `10.0.61.2  vlan61  00:00:04/00:01:43  v2`, up within ~5 s |
| mode read-back | `show ip pim dense-mode interface` → `v2/D` on both vlan10 and vlan61. **`D` is the discriminator** |
| baseline (daemon up, no config) | joined receiver 0 of 10, instrument control 10 of 10 |
| 🔴 join ordering | a join sent BEFORE `ip igmp` lands gives 0/10; the identical leg after a re-join gives 10/10. Re-join every group after any `ip igmp` change |
| authored step | **10 of 10, then 30 of 30, with NO loss.** Dense mode on a warm bench loses nothing, where sparse mode loses 1-2 frames per group to the Register and tree build |
| no receiver | 0 of 40, 0 of 50 and 0 of 25 on three never-joined groups, each with 100% instrument control |
| paired table read | `show ip mroute <unjoined>` → `Owner PIM-DM, Flags: TF`, `Incoming interface: vlan10`, **empty** `Outgoing interface list`; `show ip mroute <joined>` → the same with `vlan61 (1)` |
| State Refresh | `IP 10.0.61.1 > 224.0.0.13: PIMv2, Prune Refresh, length 36` from the DUT, repeating every ~60 s (RFC 3973 §4.5) |
| upstream prune | `IP 10.0.61.2 > 224.0.0.13: PIMv2, Join / Prune, length 34` from sw1 |
| Graft | UNICAST `PIMv2, Graft, length 34` from sw1 → `PIMv2, Graft Acknowledgement, length 34` **206 µs** later (RFC 3973 §4.6); the same group goes 0 of 50 → 20 of 20 |
| prune on leave | left group 0 of 10 while a still-joined group holds 10 of 10 in the same leg |
| 🔴 capture filter | `tcpdump -i vlanN -c 30 -nn ip` -- a bare `ip` drops the 1 Hz LDF stream (802.3/LLC, no IP header) while keeping PIM, IGMP and the data. `proto 103` alone excludes the data flood, which is the interesting half here |
| reload | login after **61 s**; adjacency re-forms by itself in ~5 s; `port1.0.48 Designated Discarding` for 17-21 s -- re-read STP before measuring |
| post-reload leg | 8 of 10 (not 10 of 10: after a cold boot the dense-mode state is rebuilt from nothing); control 0 of 10 |
| removal | `no ip pim dense-mode` on vlan10 → line gone from `show running-config interface vlan10`, 0 of 10 in the dataplane a minute after 8/10 |
| NOT MEASURED | the initial FLOOD of flood-and-prune (O-25). Instrument named above |

## Next run: scripts
- **Existing:** everything T43863 used, unchanged. The copy-forward of the previous case's
  post-captures into this case's pre-captures (call 110) is a pattern worth keeping for any group
  on a shared underlay.
- **Proposed `tools/linerate.py` (or a documented tcpreplay recipe)** -- the O-25 instrument.
  It needs a line-rate stream to one group on `eth3`, a concurrent capture on the DUT's
  transit VLAN **with per-frame timestamps**, and output that reports the time of the first and
  last data frame seen on the transit wire. Suggested shape:
  `tools/linerate.py --iface eth3 --udp 239.7.7.7:5001 --sender-ip 10.38.22.40 --sender-mac
  00:11:22:33:44:01 --gw-mac e0:1a:ea:d4:70:43 --duration 5 --rate line --watch-dut
  tb277:ckt1406c:u2:vlan61 --tag flood`. Measuring the flood/prune boundary needs the stimulus to
  outrun the convergence, so the rate, not the count, is the parameter.
- **Proposed `tools/bootcfgtest.py` and the `--profile` flag** -- REVIEW.md findings 5 and 4.

## Next run: references
- The **F-13 addendum** is the ordering rule for every multicast case on this platform:
  REVIEW.md finding 7.
- **O-26** for the capture filter: REVIEW.md finding 8.
- **O-25** for the flood gap, including why the prune's unambiguity means the verdict does not
  depend on it.
- RFC 3973 §4.5 (State Refresh) and §4.6 (Graft / Graft-Ack) -- the two sections that make a
  PIM-DM verdict distinguishable from a PIM-SM one. A case that only shows "a joined client gets
  the stream" does not distinguish them at all.
- `platforms/x960.md` §7A.1 / §7A.2, and the proposed §7D (REVIEW.md finding 10).

---
Group-wide findings are in [REVIEW.md](../REVIEW.md) and are not repeated here.
Recommendations are the reviewer's; findings cite the transcript segment or working log they come from. A review never changes a verdict.
