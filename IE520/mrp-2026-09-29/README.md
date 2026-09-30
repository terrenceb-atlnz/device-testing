# MRP group — IE520 stack + IE520-sa two-node ring, tb470, 2026-09-29 campaign

Queue: [../CAMPAIGN-QUEUE-2026-09-29.md](../CAMPAIGN-QUEUE-2026-09-29.md) rows 15 (T28863) and 9
(T38093, T38097, T38098, T38099). Hand-driven through console.py wrappers on tb470; the tools are in
[evidence/28863/tools/](evidence/28863/tools/). This group supersedes
[../mrp-2026-09-22/](../mrp-2026-09-22/), which had no MRP-capable partner. T28863's log moved here
by `git mv`; the other four 09-22 logs are row 9's to handle.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T28863 | MRP - Stack failover master/slave | [28863-fail.log](28863-fail.log) | **FAIL** (2026-09-30), reproduced. A stack master failover makes the stack MRM log `TestTimerExpired` → `Ring opened` on a ring that is physically intact, and set its secondary port Forwarding. The result is an L2 loop of about 0.3–0.5 s: broadcast frames arrive up to 264×, and each host NIC receives its own broadcasts back (runs A, C). The same false open fires when a member rejoins the stack, even a backup member (runs D, B). PROVEN: traffic continues (worst unicast hole 196 ms), MRP roles carry over to the new master, the stack re-forms, and `show mrp ring` stays Closed / TC count 3 throughout. So the CLI never shows the flap; only the traffic and the syslog do |
| T38093 | MRP ring with DUT as MRM | [38093-fail.log](38093-fail.log) | **FAIL** (2026-09-30), reproduced 3x. MRM steps work: ring operational after save, forwarding-port shutdown recovers in 108 ms (copper 1.0.13) / 70 ms (fibre 4.0.26), one port re-blocked on restore, ring up + traffic after save + reboot (config load clean). But EVERY ring closure loops VLAN 1: at link-up / post-boot ring-up the MRM logs `Ring closed` -> `TestTimerExpired` -> `Ring opened` and forwards both ring ports; loops of 42-303 ms, one frame up to 410x, echoes on both NICs, DUT thrash-limiting on sa2. A false open also fired 39 s after ring-up with no event. Same mechanism as T28863, no stack event needed. Two-node ring (sw2 step not run) |
| T38097 | MRP ring with DUT as MRC | — | NOT TESTED yet (queue row 9) |
| T38098 | MRP ring switch over with 200ms recovery time | [38098.log](38098.log) | **PASS** (2026-09-30). 8 switch-overs (copper SFP+ 1.0.13 and fibre SX 4.0.26/1.0.26, shut at the MRM end and at the MRC end, two rounds): worst outage 94-146 ms, all < 200 ms, no duplicates during any switch-over. Fixed-port sub-step UNSUPPORTED (no fixed ports). Observation: every restore looped 31-62 ms (T38093's FAIL) |
| T38099 | MRP ring switch over with 500ms recovery time | — | NOT TESTED yet (queue row 9) |

## The ring (built in row 15, LEFT UP for row 9)

The restore reference is the capture taken BEFORE the ring: [pre-test-configs/2026-09-30/](pre-test-configs/2026-09-30/)
(`pre-u5.out` stack, `pre-u3.out` SA, `pre-u0.out` x230, `pre-u1.out` 4050). State at hand-back is in
[post-test-configs/2026-09-30/](post-test-configs/2026-09-30/). The running-config diff against the pre
capture is exactly this list; nothing was written:

- **stack**: `service mrp`; `mrp ring 1` / `role manager`; port1.0.13 `no static-channel-group` + `mrp ring 1`;
  port4.0.9 `shutdown` (sa3's other leg; sa3 now = 4.0.9 only); port4.0.26 `no switchport access vlan`
  (→ VLAN 1) + `mrp ring 1`.
- **SA**: `service mrp`; `mrp ring 1` (role client = default, not shown); port1.0.13 `no static-channel-group`
  + `mrp ring 1`; port1.0.26 `no switchport access vlan` + `mrp ring 1`.
- Ring state: MRM primary port1.0.13 Forwarding, secondary port4.0.26 Blocking, Network Status Closed;
  MRC both Forwarding. Profile 200ms (default). Ring VLAN = 1 (access).
- **Stack master at hand-back: member 4** (u4). It was member 3 at the start. After four reloads (3→4, backup 3,
  4→3, 3→4) roles never pre-empt back.

Restore (row 9's): reverse the list above. Remove `mrp ring 1` from the ports before `no mrp ring 1` /
`no service mrp`. Put 1.0.13 back in `static-channel-group 3` on both ends, and 4.0.26 / SA 1.0.26 back to
`switchport access vlan 4000`. Mind the ordering: shut stack 4.0.26 while re-forming sa3, or VLAN 1 loops,
because STP is off. Then `no shutdown` 4.0.9, diff against `pre-test-configs/2026-09-30/`, and run the probe.

## Things row 9 should know

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
