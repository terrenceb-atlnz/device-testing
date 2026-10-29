# MRP group — IE520 stack + IE520-sa two-node ring, tb470, 2026-09-29 campaign

Queue: [../CAMPAIGN-QUEUE-2026-09-29.md](../CAMPAIGN-QUEUE-2026-09-29.md) rows 15 (T28863) and 9
(T38093, T38097, T38098, T38099). Hand-driven through console.py wrappers on tb470; the tools are in
[evidence/28863/tools/](evidence/28863/tools/). This group supersedes
[../mrp-2026-09-22/](../mrp-2026-09-22/), which had no MRP-capable partner. T28863's log moved here
by `git mv`; the other four 09-22 logs are row 9's to handle.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T28863 | MRP - Stack failover master/slave | [28863.log](28863.log) | **PASS** (re-graded 2026-09-30 on Terrence's "re-grade. what does the test title want you to do?" -- was FAIL). Graded against the title: MRP survives master AND backup failover -- traffic recovers (worst unicast 196 ms), roles carry over, ring re-closes, stack re-forms. OBSERVATION kept: the failover / member rejoin makes the MRM falsely open a closed ring and loop ~0.3-0.5 s (runs A, C; D, B); that defect is graded in T38093 FAIL (ring closure) |
| T38093 | MRP ring with DUT as MRM | [38093-fail.log](38093-fail.log) | **FAIL** (2026-09-30), reproduced 3x. MRM steps work: ring operational after save, forwarding-port shutdown recovers in 108 ms (copper 1.0.13) / 70 ms (fibre 4.0.26), one port re-blocked on restore, ring up + traffic after save + reboot (config load clean). But EVERY ring closure loops VLAN 1: at link-up / post-boot ring-up the MRM logs `Ring closed` -> `TestTimerExpired` -> `Ring opened` and forwards both ring ports; loops of 42-303 ms, one frame up to 410x, echoes on both NICs, DUT thrash-limiting on sa2. A false open also fired 39 s after ring-up with no event. Same mechanism as T28863, no stack event needed. Two-node ring (sw2 step not run) |
| T38097 | MRP ring with DUT as MRC | [38097.log](38097.log) | **PASS** (2026-09-30), labelled confounded: roles swapped (SA = MRM). The DUT's MRC config was accepted; switch-over 92-98 ms when the DUT's copper or fibre ring port was shut; ring re-blocked on restore; save + reboot clean, ring and traffic back. Every ring closure still looped 26-40 ms, from the SA MRM's false TestTimerExpired (the T38093 defect, which is the MRM's on either IE520). The DUT MRC forwards a returning port only on the MRM's TopologyChange |
| T38098 | MRP ring switch over with 200ms recovery time | [38098.log](38098.log) | **PASS** (2026-09-30). 8 switch-overs (copper SFP+ 1.0.13 and fibre SX 4.0.26/1.0.26, shut at the MRM end and at the MRC end, two rounds): worst outage 94-146 ms, all < 200 ms, no duplicates during any switch-over. Fixed-port sub-step UNSUPPORTED (no fixed ports). Observation: every restore looped 31-62 ms (T38093's FAIL) |
| T38099 | MRP ring switch over with 500ms recovery time | [38099.log](38099.log) | **PASS** (2026-09-30), graded on the title (text says 200 ms). `profile 500` on both nodes; 8 switch-overs 90-416 ms, all < 500 ms (MRC-end copper shuts 296-416 ms: the MRM's copper port reports link-down late, so the test-frame window decides). Fixed ports UNSUPPORTED. O-1: `profile` on a live MRM restarts the manager and loops 79 ms (+ EXFX local7.err STARGV lines). O-2: with 500 ms, only 1 of 8 restores looped (vs 10/10 at 200 ms) |

## The ring -- built in row 15, used by row 9, RESTORED 2026-09-30 16:00-16:09

Restore reference: the capture taken BEFORE the ring, [pre-test-configs/2026-09-30/](pre-test-configs/2026-09-30/).
Result: [post-test-configs/2026-09-30-row9/](post-test-configs/2026-09-30-row9/). Running-config on the stack,
SA, x230 and 4050 is **IDENTICAL** to the pre capture. Boot config is `flash:/tb470-bench.cfg` (file exists) on all
four. Probe `2026-09-30T030933Z` reads **MATCH**, with no advisory. The stack master at the end is **member 3**;
it never pre-empts.

Row 9 changed the roles (T38097: SA = MRM, stack = MRC) and the profile (T38099: 500, then back to default).
The restore removed all of it:

1. Stack: `interface port4.0.26` / `shutdown` / `no mrp ring 1` / `switchport access vlan 4000`;
   `interface port1.0.13` / `no mrp ring 1`; `no mrp ring 1`; `no service mrp`. Then `show mrp ring` reads
   "% MRP feature is not currently enabled." (= baseline).
2. SA: `interface port1.0.26` / `no mrp ring 1` / `switchport access vlan 4000`; `interface port1.0.13` /
   `no mrp ring 1`; `no mrp ring 1`; `no service mrp`.
3. sa3: stack port1.0.13 `static-channel-group 3`, then SA port1.0.13 `static-channel-group 3`. At that moment
   1.0.13 was the only live link between the two, so no loop was possible. Then stack `no shutdown` on port4.0.9
   and port4.0.26. After: sa3 = {1.0.13, 4.0.9} on the stack and {1.0.9, 1.0.13} on the SA, SX link
   connected in VLAN 4000, loop-protection table as in pre2-u5/pre2-u3.
4. **Boot configs.** T38093/T38097 `write memory` had put the ring into `tb470-bench.cfg` on both units, so the
   pre-write snapshot was copied back. **AW+ refuses to overwrite the file the boot pointer names**
   (`% Cannot overwrite flash:/tb470-bench.cfg as it is configured as the boot config file`). The fix is to
   stage the snapshot on every member, `boot config-file flash:/tb470-bench.row9.cfg` (63 s on the stack while it
   syncs), then `copy` the snapshot over `tb470-bench.cfg` on each member. That copy prompts
   `Overwrite ... (y/n)[n]:`, and the `[n]` suffix needed a wider y/n pattern in the driver. Then
   `boot config-file flash:/tb470-bench.cfg` and `delete` the snapshots. `show file` on members 1, 3, 4 and the SA:
   **byte-identical** to `evidence/row9/orig-*.cfg`, including the original "Startup-config saved on Tue Sep 29
   23:4x" header. Evidence: `evidence/row9/restore*.out`.

## Things learned in row 9 (for the next MRP session)

- **Every stack membership change can make the MRM loop the ring for a moment** (T28863). Row 9's
  "save and reboot" steps and any member reload will hit it. Measure with traffic, not `show mrp ring`.
- After `role manager` the prompt is `(config-mrp-ring-manager)#`; `exit` returns to `(config-mrp-ring)#`.
- MRP ring ports drop out of `show loop-protection` entirely. `show loop-protection interface <port>` is
  `% Can't find interface`.
- Probe while the ring is up: MISMATCH (3). The sa3 leg 1.0.9↔4.0.9 is absent, and eth2 maps to swi_a
  port1.0.13 instead of swi_b port1.0.2. That second one is an artefact: with sa3 dissolved, the stack
  learns eth2's MAC on the physical ring port. The cabling is unchanged.
- Async `switch: port … entered … state` lines printed after the prompt stall drivers whose prompt match is
  anchored at the end of the buffer (ckyn.py). `evidence/28863/tools/cfg.py` completes on prompt-after-echo
  and handles `YN:` lines.
- Traffic that transits the ring: tb470 eth3 → x230 → stack sa2 (member 1) → ring → SA → eth2, and back.
  `tools/flows.py` + `flowstat.py` (500 pps × 4 flows, loss/dup/echo counts).
