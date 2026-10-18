# T43866 process review -- mcast-2026-10-16T1406
Reviewed 2026-10-19 by /create-logs from `a81d52aff45c3f339.output` and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 39 | 78 | 42,417 | 14,110,604 | 367 | 39 | 29m 13s | 15,186 |

**This case cost more cache-read than T43863 -- 14,110,604 against 13,395,700 -- on half the tool
calls, 39 against 78.** 361,810 cache-read per tool call, **2.1x T43863's 171,740**. Nothing about
T43866 is twice as expensive in itself; it is simply last, and every call carries the accumulated
context of the three cases before it. This is the group's most actionable measurement and it is
written up in REVIEW.md finding 1.

**One caveat, stated so the comparison is honest:** a case's segment runs to its `RESULT` line, so
**the group's entire end-of-group teardown and hand-back sit inside this segment** -- calls
202-213: the final reload that clears the sticky `no service` lines, the underlay restore, the
closing `bench_probe.py` run, the three-device final diffs, the console logouts and the `ps` /
`git status` check. About 12 of the 39 calls are the group's, not the case's. The per-call cost is
unaffected by that (it is a property of position, not of purpose), and the cost-per-call curve is
monotonic across all four cases, so the finding stands -- but T43866 *as a test case* is nearer 27
calls.

## Process taken
1. **(176-178)** Underlay converted from the two-router shape to the DUT-local one: the transit
   VLAN, its SVI, the trunk and the static routes removed from both units, vlan48's SVI returned
   to the DUT. `rcdiff.py` against the pre-GROUP baseline confirmed the conversion.
2. **(179-181)** `service pim`; `ip vrf red 1` / `ip vrf blue 2`; vlan10 → red, vlan48 → blue,
   with the addresses re-applied after each move. Call 180 is the **third `console.py` fix**:
   adding `All IP addresses configured on interface` to `ADVISORY`, without which `cfg.py`
   abandons the rest of every VRF batch.
3. **(182)** STEP 0 baseline: both VRFs created, no multicast anywhere → 0 of 10, 0 frames on eth4.
4. **(183-184)** `ip multicast-routing vrf red` / `vrf blue` with the global table left OFF; PIM +
   `ip igmp` on both SVIs; per-VRF RPs. Per-VRF IGMP read to show where the membership is held.
5. **(185)** STEP 2, the isolation leg -- source in red, receiver in blue.
6. **(186-188)** STEP 3, the A/B: vlan48 moved into red via the global domain (a direct VRF-to-VRF
   move is refused), re-join, identical leg → 10 of 10. STEP 4's per-VRF table reads to
   `work/v4-tables.log`.
7. **(189-191)** STEP 5, the F-9 check: vlan48 moved straight back to blue with the entry actively
   forwarding, the leg re-run **immediately**, no re-join and no `clear` of anything.
8. **(192-195)** STEP 6: stage, reload, verify VRFs/addresses/STP, post-reload leg, restore the
   boot pointer and delete the staged file.
9. **(196-199)** STEP 7 removal (per VRF and per feature), the **fourth `console.py` fix**
   (`Save the config and restart…` as an advisory), post-case captures and `rcdiff.py`.
10. **(200-201)** `work/run1.log` and the queue's F-9 answer / O-29 / O-30 entries.
11. **(202-213)** The group's end-of-group work: the reload that clears the DUT's sticky
    `no service` lines, the underlay restored for group D, the closing probe, the three-device
    final diffs, a last underlay sanity leg, the console logouts and the `ps` / `git` check.
12. **(214)** `RESULT T43866 PASS`.

## Wasted input
- **None of any size.** The largest read is 904 chars (a combined STP + interface-brief read,
  already greped to six lines). The pattern that kept it down: every multi-command `ckcon` call
  in this segment ends in a `command grep -aE '…'` naming the exact fields wanted, and the two
  reads that had to be quoted in full went to `work/` files (`v4-tables.log`, 44 lines;
  `pre-u2.log`) and were then read back filtered.
- The `tools/tb probe` call (760 chars) and the `ps` / `git status` call (606) are the group's
  closing gates, not this case's, and both are correctly `tail`-limited.

## Repetition
- **`show ip interface brief` four times and `show ip vrf` three times** (181, 186, 187, 193).
  Every one follows a VRF membership change and is the read that confirms the address survived
  it -- `ip vrf forwarding` removes the interface's addresses, so this is a required gate, not a
  repeat. Correct.
- **`show spanning-tree brief` three times** (178, 193, 207). The group-wide post-reload pattern,
  REVIEW.md finding 5.
- The isolation leg was run **twice** (185, and again at 190 with a 40 s window). That is
  deliberate and it is the right instinct: the second run is what caught two of the DUT's own PIM
  hellos and so proved the capture alive over a longer window.

## Accuracy risks
- **🔴 The instrument control the rest of the group relied on is unavailable here by
  construction, and the substitute the tester found is better suited to the case.** Under VRF
  isolation *nothing* from eth3 may reach eth4 -- including the routed ICMP control -- so "a flow
  that must arrive on the far NIC" cannot exist. An ICMP aimed at the DUT's own red SVI was tried
  and produced no reply (the DUT would have to ARP for the crafted sender 10.38.22.40 and nothing
  answers that ARP). **The liveness proof actually used is the DUT's own PIM hellos**: with PIM
  enabled per VRF, the blue SVI sends `IP p103 10.38.22.66 > 224.0.0.13` on eth4's wire, so an
  isolation leg that captures a hello while counting zero subject frames has proved its own
  capture alive from traffic the DUT generated. **An isolation case is a case whose result IS a
  zero**, so this is the one case in the group where the liveness proof carries the verdict rather
  than supporting it. Every isolation leg carries it. Worth reusing in any future isolation case.
- **The A/B is the second control and it is the stronger one.** 0 of 10 multicast and 0 of 10
  unicast, against 10 of 10 and 10 of 10 on the identical leg, with **vlan48's VRF membership as
  the only variable in the whole bench** -- same cabling, same addresses, same group, same source,
  same ports -- plus a never-joined control group at 0 of 10 in the same leg, so what crossed is
  what was asked for and not everything.
- **O-29 is a misreading hazard in the read-back itself.** `show ip mroute` with **no** `vrf`
  keyword prints the VRF sections too, headed `[VRF: red]`, and its output here was byte-identical
  to `show ip mroute vrf red`. The global table was empty (global multicast routing is off), so
  **a reader skimming `show ip mroute` would reasonably but wrongly conclude the entries are in
  the global table.** Read the `[VRF: …]` heading. The case recorded this rather than relying on
  the unqualified command.
- **The configuration legitimately changes during the run, and the `.cfg` declares which state it
  captures.** This case's central A/B is moving vlan48 between VRFs; `swi_d.cfg` holds the
  BOTH-INTERFACES-IN-RED state, which is what the persistence and removal steps ran on, and the
  log says the isolation state differs from it by exactly three quoted lines. That declaration is
  the thing that keeps the `.cfg` honest -- a case with a moving configuration should always say
  which moment its `.cfg` is.
- **The DUT-local scope is a declared decision, not a shortcut.** swi_b has no VRF-Lite licence at
  all (Base only, `VRF-LITE-FULL/63/8` absent); swi_a holds it but is under RISK-1 (never reloaded
  or power-cycled). The reasoning given -- VRF-Lite isolation is a property of ONE router's
  forwarding tables, and the sharpest test is two segments on one router that can and cannot reach
  each other depending only on VRF membership -- is sound, and it is why `swi_d.cfg` is the only
  config file.
- **F-9 was answered negatively and the negative is the useful part.** F-9 is a recorded unicast
  behaviour of this DUT: a removed inter-VRF static route kept forwarding from a stale ARP-derived
  per-host entry until `clear arp-cache vrf` was run. Tested here in the sharpest available form
  -- an actively forwarding `(S,G)` with `vlan48 (1)` in its outgoing list, vlan48 moved straight
  back to blue, the leg re-run immediately with no re-join and no `clear` -- the outgoing interface
  list **emptied at once** and the dataplane stopped in the same instant. **The multicast outgoing
  interface is torn down with the interface; the unicast hazard lives in an ARP-derived host entry
  that outlives its route.** That is a different mechanism, and saying so is more useful than a
  bare "did not reproduce".

## Next run: expected outputs
| step | value / CLI line this bench gave |
| --- | --- |
| authored text | **None.** ck.db `zephyr_cases` id 40186: no objective, no precondition, `num_steps` 1 with an empty `steps` column. Designed from the VRF-Lite guide C613-22142-00 REV B, `platforms/x960.md` §7B.6-7B.7 and the CLI surface -- and said so in the log |
| VRF creation | `ip vrf red 1` with no LO number **auto-creates lo1** (and lo2 for blue). `show ip vrf` lists it under the VRF |
| 🔴 address loss | `ip vrf forwarding <name>` / `no ip vrf forwarding <name>` **removes the interface's IP addresses** and answers `% All IP addresses configured on interface <if> have been removed`. That is an **advisory, not a rejection** -- re-apply the address immediately after. Two wordings exist (`…on interface vlan10…`, `…on interfaces in VRF red…`) |
| 🔴 direct move refused | `ip vrf forwarding red` while the interface is in blue → `% vlan48: VRF is already associated`. Go via the global domain: `no ip vrf forwarding blue`, then `ip vrf forwarding red`, then the address, then `ip pim sparse-mode` + `ip igmp` |
| per-VRF multicast | `show running-config \| include multicast` → `no ip multicast-routing` (global OFF) with `ip multicast-routing vrf red` and `vrf blue` both ON and both working. **It is not a modifier on a global switch** |
| per-VRF PIM | `show ip pim vrf red sparse-mode interface` → `Total active interfaces: 2`, `v2/S`, each SVI its own DR |
| baseline | 0 of 10, and **0 frames on eth4 at all** before any multicast feature |
| isolation | source in red, receiver in blue → **0 of 10 multicast AND 0 of 10 unicast**, with `x1 IP p103 10.38.22.66 > 224.0.0.13` (the blue SVI's own PIM hello) in the same capture proving it live. Per-VRF IGMP shows the membership held in blue; both mroute tables empty |
| the A/B | move vlan48 into red, re-join (the VRF changed, so the membership must be re-sent) → **10 of 10 group and 10 of 10 unicast**, egress eth src `e0:1a:ea:d4:70:43`. Never-joined control 0 of 10 |
| per-VRF tables | `show ip mroute vrf red` → the joined group with `Outgoing interface list: vlan48 (1)` and the never-joined control group with an **empty** one, in the same table at the same instant |
| 🔴 O-29 | `show ip mroute` with **no** `vrf` keyword prints `[VRF: red]` sections too, identical to `show ip mroute vrf red`. Read the heading before concluding anything about the global table |
| F-9 check | move the interface out with the entry actively forwarding → the outgoing interface list **empties immediately** and the dataplane stops in the same instant. No stale forwarding, nothing to clear. F-9's shape does **not** occur in the multicast path |
| reload | login after **60 s**; VRFs, loopbacks, memberships, addresses, per-VRF multicast routing, PIM and the per-VRF RPs all survive; `port1.0.10` and `port1.0.48` both Designated Forwarding |
| post-reload leg | 9 of 10 for a group first used after the reload (1 frame to the tree build), 0 of 10 for the never-joined control |
| removal | `no ip multicast-routing vrf red` → red's line gone, **blue's untouched**; 0 of 10 for a group forwarding 9/10 a minute before, **while unicast inside the same VRF keeps working at 10 of 10**. Surgical in both dimensions at once |
| teardown | `no service pim` answers `% Save the config and restart for this change to take effect` -- an **advisory**. On the DUT the sticky `no service` line is cleared by the end-of-group reload (O-24: the discriminator is the boot, not the daemon) |

## Next run: scripts
- **Existing:** `tools/arpleg.py`, `tools/igmp.py`, `tools/cfg.py`, `tools/ckcon.py`,
  `tools/ckyn.py`, `tools/console.py` (with this case's two `ADVISORY` entries),
  `tools/ckreload.py`, `tools/rc2cfg.py`, `tools/rcdiff.py`. No helper was hand-built for this
  case; the two `console.py` entries are what made the existing drivers survive it.
- **Proposed `tools/bootcfgtest.py` and the `--profile` flag** -- REVIEW.md findings 5 and 4.
- **Proposed: a `--liveness` note in `tools/README.md`'s `arpleg.py` entry** recording that for an
  isolation leg the far-side liveness proof is the DUT's own per-VRF PIM hello, not a crafted
  control flow, with the one-line reason (nothing from the source segment may arrive by
  construction). This case worked it out; the next should read it.

## Next run: references
- **`platforms/x960.md` §7B.6-7B.7** -- VRF-Lite on the unicast path, including F-9. This case is
  the multicast comparison against that baseline and **answers F-9 for multicast**; the answer
  belongs back in §7B.6 as a cross-reference, and the rest in the proposed §7D (REVIEW.md
  finding 10).
- The VRF-Lite Feature Overview and Configuration Guide **C613-22142-00 REV B** in
  `Feature Overview Guides/` -- its "securely isolated" claim is what the isolation step tests.
- **O-29** before reading any unqualified `show ip mroute` on a VRF-configured DUT.
- **O-24** for what the teardown will leave behind and why one end-of-group reload clears it.
- `tools/ckcase.py` returns the empty authored text in one call. Confirm it and declare it;
  do not re-derive the absence.

---
Group-wide findings are in [REVIEW.md](../REVIEW.md) and are not repeated here.
Recommendations are the reviewer's; findings cite the transcript segment or working log they come from. A review never changes a verdict.
