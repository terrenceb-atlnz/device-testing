# T43865 process review -- mcast-2026-10-16T1406
Reviewed 2026-10-19 by /create-logs from `a81d52aff45c3f339.output` and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 29 | 58 | 34,337 | 8,970,149 | 275 | 29 | 21m 10s | 11,737 |

**29 tool calls and 11,737 chars read back -- the leanest case of the group, and the only one
with three authored steps to satisfy.** It is also the only case whose teardown diff came back
EMPTY on both devices. 309,315 cache-read per tool call: the position effect again (REVIEW.md
finding 1), on a case that did almost nothing wasteful.
What made it lean: the (S,G) discrimination, the wrong-source control and the different-group
control were carried in **one** `arpleg` leg via `--udp DST:PORT@SRC`, so the defining property
of SSM is a single measurement rather than a sequence of them.

## Process taken
1. **(147-148)** Pre-case captures copied forward from T43864; `service pim`; then one setup
   batch -- `ip multicast-routing`, `ip pim ssm default`, `ip pim sparse-mode` on both SVIs of
   both routers, plus `ip igmp` / `ip igmp version 3` on swi_a. `ip pim ssm ?` read read-only
   with `qmark.py` **before** being used.
2. **(149)** STEP 0 baseline: full SSM configuration, no join of any kind → 0 of 10.
3. **(150-151)** STEP 1: an IGMPv2 (*,G) join on 232.5.5.5 → not in `show ip igmp groups`, not in
   `show ip mroute`, 0 of 10 on the wire.
4. **(152-155)** STEP 2 (authored step 1): the IGMPv3 (S,G) join, `show ip igmp groups detail`,
   both authored table read-backs (with the authored group argument shown being refused), and the
   three-flow leg. Calls 154-155 wrote the two table reads to `work/` files.
5. **(156-157)** STEP 3 (authored step 2): the IGMPv3 leave, both tables empty, 0 of 10. Re-join
   and re-confirm.
6. **(158-160)** STEP 4 (authored step 3): both readings of "port interface down/up" -- the DUT's
   L2 access port, then swi_a's vlan48 SVI -- and the recovery leg.
7. **(161)** `work/setup-u{2,5}.log` + `rc2cfg.py` → `swi_d.cfg`, `swi_a.cfg`.
8. **(162-164)** STEP 5: `no ip pim ssm default` refused, `qmark.py` read the negation's real
   syntax, `no ip pim ssm` applied and verified gone from running-config.
9. **(165-167)** The F-14 admission test: v2 join on 232.7.7.7 with no SSM range at all, then an
   ACL-defined range, then both groups in one `show ip igmp groups`; and the dataplane
   consequence measured rather than assumed.
10. **(168-171)** Range restored; stage, reload, verify, post-reload leg, restore the pointer and
    delete the staged file.
11. **(172-175)** Post-case captures + `rcdiff.py` (EMPTY on both), `work/run1.log`, the queue's
    F-14 / O-27 / O-28 entries, and `RESULT T43865 PASS`.

## Wasted input
- **None found of any size.** The largest read of the segment is 1,034 chars -- the three-flow
  `arpleg` leg's own output, which is the case's central measurement. Every console read is
  greped or `sed`-ranged at the point of capture; the two table reads that needed to be quoted in
  full went to `work/` files (`s4-tables-u5.log`, `s4b-pimmroute-u5.log`, 14 and 22 lines) and
  were then read back filtered. **That is the pattern the other three cases should copy**, and it
  is exactly the fix T43863's STEP 6(a) needed.

## Repetition
- **`igmp join 232.5.5.5 … -3 --source 10.38.22.40` four times** (152, 157, 160, and inside 170
  for a different channel). Each is a real re-join required by a leave or an interface flap, not
  a repeat. Correct.
- **`show ip igmp groups` / `show ip mroute` as a pair, five times.** The authored steps ask for
  both at three separate points, so three of the five are the case text. Not reducible.
- `show spanning-tree brief` twice after the reload -- the group-wide pattern, REVIEW.md
  finding 5.

## Accuracy risks
- **Two authored read-backs do not exist on this platform, and the substitutions are declared
  rather than taken silently.** `show ip pim spare-mode mroute` is a typo for `sparse-mode`, and
  the real command **takes no group argument** -- the log captures
  `show ip pim sparse-mode mroute 232.5.5.5` → `% Invalid input detected at '^' marker.` rather
  than asserting it. `show ip igmp group` (singular) is `groups` on this build. Handled exactly
  right: the refusal is the evidence for the substitution.
- **O-27: `ip pim ssm` has an asymmetric negation.** `no ip pim ssm default` → `% Invalid input
  detected`; the negation takes neither `default` nor `range`. The tester read it off the device
  with `qmark.py` (a read-only `?` probe, no CR) instead of guessing -- the right habit, and the
  one that the memory `never-send-cli-help-through-a-cr-driver` exists to protect.
- **O-28 is a false-failure trap for the next tester.** "Port interface down" has two readings on
  a two-router bench and **only one updates the multicast table**. Shutting the DUT's
  `port1.0.48` -- the host's own L2 access port -- leaves `show ip igmp groups` and `show ip
  mroute` on swi_a unchanged, because swi_a's vlan48 SVI is still up over the trunk and the
  membership is soft state that must time out. Shutting swi_a's `interface vlan48` clears both
  immediately. **A tester who shuts the host's port and expects the table to clear will record a
  false FAIL.** The case took both readings and distinguished them, which is why it passed.
- **F-14 was measured, not inferred, and its impact was measured too.** The claim is that the
  IGMPv2 any-source-join rejection is bound to the hardcoded IANA 232/8 range only and is not
  applied to a `ip pim ssm range <acl>` range. Evidence: one router, one interface, two groups,
  **in a single `show ip igmp groups`** (239.20.20.20 listed, 232.7.7.7 absent), plus the control
  that 232/8 is still rejected with **no SSM configuration at all** -- so `ip pim ssm default` is
  not what enforces it. The tester then measured the consequence rather than asserting one:
  traffic to 239.20.20.20 from an arbitrary source is **0 of 10**, because no RP is configured, so
  the accepted membership is inert. **A spec-conformance gap (RFC 4607 §4.2), not a forwarding
  hole** -- and saying which is the difference between a useful finding and an alarm.
- **The SSM claim could not be layer-2 artefact and the log proves it.** Both flows in the
  discriminating leg -- (10.38.22.40, 232.5.5.5) delivered and (10.38.22.44, 232.5.5.5) dropped --
  share the link-layer address `01:00:5e:05:05:05`, and the eth3 capture shows all four flows
  reaching the DUT. The discrimination is therefore at layer 3 by source. **This is only
  measurable because `arpleg.py` derives a multicast destination's own L2 address** (REVIEW.md
  finding 3) and supports `--udp DST:PORT@SRC`.
- No verdict line rests on inference. The one place the case could not prove removal in the
  dataplane -- removing the SSM range does not tear down an existing (S,G), which is correct
  behaviour since an IGMPv3 include join is legitimate in plain PIM-SM -- is **stated as such**
  and removal is proved by an admission test instead.

## Next run: expected outputs
| step | value / CLI line this bench gave |
| --- | --- |
| authored text | ck.db `zephyr_cases` id 40185, `num_steps` 3, objective "PIM-SMM is entered entries dynamically" (sic). Three authored steps, all with expected result "Multicast routing table updates accordingly" |
| 🔴 authored commands | `show ip pim spare-mode mroute` does not exist (typo for `sparse-mode`, and the real one takes **no group argument**); `show ip igmp group` is `groups`. Declare the substitutions |
| CLI surface | `ip pim ssm ?` → `default  Use 232/8 group range for SSM` / `range  ACL for group range to be used for SSM` |
| 🔴 negation | `no ip pim ssm default` → `% Invalid input detected`. The negation is bare **`no ip pim ssm`** (O-27). Read it with `qmark.py` before sending |
| IGMP version | swi_a `show ip igmp interface vlan48` → `IGMP Enabled, Active, Querier, Configured for version 3` after `ip igmp` + `ip igmp version 3` |
| baseline | full SSM config, no join → 0 of 10, instrument control 10 of 10 |
| v2 join on 232/8 | **rejected outright**: no `show ip igmp groups` entry, no mroute entry, 0 of 10. The same v2 join creates an entry every time on a 239.x group on this bench |
| v3 (S,G) join | `igmp.py … -3 --source 10.38.22.40` → report type `to-include(3)` to 224.0.0.22 |
| IGMP read-back | `show ip igmp groups` → `232.5.5.5  vlan48  00:00:07  stopped  10.38.22.70`. Note `Expires` reads **`stopped`** for a v3 include-mode group, not a timer |
| detail read-back | `show ip igmp groups detail` → `Group mode: Include ()`, `Last reporter: 10.38.22.70`, include source list `10.38.22.40 … Fwd Yes` |
| mroute | `(10.38.22.40, 232.5.5.5)`, `Owner PIM-SM, Flags: TF`, `Incoming interface: vlan61`, `Outgoing interface list: vlan48 (1)` |
| pure-SSM table | `show ip pim sparse-mode mroute` → `(*,*,RP) 0`, `(*,G) 0`, `(S,G) 1`, `(S,G,rpt) 0`, `RPF nbr: 10.0.61.1`, `RPF idx: vlan61`, **`SPT bit: 1`**, `Upstream State: JOINED`. No RP configured anywhere |
| the SSM property | joined channel **9 of 10** first leg (1 frame to the tree build), 10 of 10 steady; SAME group from a DIFFERENT source **0 of 10 in the same leg**; a different group from the joined source 0 of 10. All flows reach the DUT (check the eth3 capture) |
| leave | v3 leave = `to-include` with an EMPTY source list → 0 of 10, `show ip igmp groups` header only, `show ip mroute` empty |
| 🔴 interface down (a) | DUT `port1.0.48` (the host's L2 access port) shut → **both tables UNCHANGED**, and that is correct (O-28). Soft state must time out |
| interface down (b) | swi_a `interface vlan48` shut → both tables empty immediately; `show ip pim sparse-mode interface` → `Total active interfaces: 1` |
| interface up | `no shutdown` + re-join → 9 of 10 for the channel, 0 of 10 for the wrong source in the same leg |
| F-14 | with NO SSM range: v2 (*,G) on 232.7.7.7 still rejected. With `access-list 20 permit 239.20.20.20 0.0.0.0` + `ip pim ssm range 20`: v2 (*,G) on 239.20.20.20 **ACCEPTED** (`00:00:07  00:04:14  0.0.0.0`) while 232.7.7.7 stays absent 40 s later. Traffic to 239.20.20.20 is 0 of 10 -- the membership is inert, no RP |
| reload | login after 61 s; `show running-config \| include ssm` → `ip pim ssm default`; 17-21 s STP Discarding window as elsewhere |
| post-reload leg | 8 of 10 for a channel first used after the reload, 0 of 10 for its wrong-source twin in the same leg |
| teardown | `rcdiff.py` EMPTY on BOTH devices |

## Next run: scripts
- **`tools/igmp.py -3` is the reason this case has a verdict.** `-3 / --v3`, `--source A[,B]`,
  `--record {is-include|is-exclude|to-include|to-exclude|allow|block}`; defaults are
  `to-include` on join and `to-include` with an empty source list on leave. Reports go to
  224.0.0.22 and the tool picks the right L2 address per version. `--source` with `-2` is refused
  rather than silently ignored. **Do not rebuild it; do check `tools/README.md` first.**
- **`tools/arpleg.py --udp 'DST:PORT@SRC,…'`** -- the per-spec source override is what lets the
  joined channel and a wrong-source flow to the SAME group ride one leg. Combined with the
  multicast L2 derivation, it is the whole instrument for an SSM verdict.
- **`tools/qmark.py`** for any asymmetric negation. Read-only, no CR.
- Proposed `tools/bootcfgtest.py` and `--profile`: REVIEW.md findings 5 and 4.

## Next run: references
- **O-27** (the bare `no ip pim ssm`) and **O-28** (the two readings of "interface down") --
  both are time sinks, and O-28 is a false-FAIL trap.
- **F-14** -- if the next run re-tests it, the measurement that settles it is a single
  `show ip igmp groups` holding a configured-range group and an IANA-range group at once.
- RFC 4607 §4.2 for what a router is expected to do with its configured SSM range.
- `platforms/x960.md` -- and the proposed §7D (REVIEW.md finding 10), for which the table above
  is the SSM half.

---
Group-wide findings are in [REVIEW.md](../REVIEW.md) and are not repeated here.
Recommendations are the reviewer's; findings cite the transcript segment or working log they come from. A review never changes a verdict.
