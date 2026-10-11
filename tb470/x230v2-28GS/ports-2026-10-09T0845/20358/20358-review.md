# T20358 process review -- ports-2026-10-09T0845
Reviewed 2026-10-12 by /create-logs from `agent-a4163fdf23e120522.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 20 | 21,333 | 2,369,007 | 95 | 10 | 314 s | 6,695 chars |

Plus overhead #26 (4.3k chars, `linerate.py` source read for the planned broadcast), made between T47210's RESULT
and this case's first call, so counted as group overhead.

## Process taken
1. #1 stack capture (u5: running-config, spanning-tree, loop-protection, link status) and RSTP enabled on the x230
   with a 35 s settle (u0).
2. #2 stack port1.0.3 into VLAN 103 (the stack now bridges both x230 links); the gate: `@poll 20` for port1.0.4
   Backup/Discarding, then `show spanning-tree interface` for both ports. Gate failed ("Received None").
3. #3 the stack change reverted at once.
4. #4-#5 `qmark` on the stack for a BPDU-passing option (`no spanning-tree rstp enable ?`, `spanning-tree ?`,
   `l ?`, then `l2 ?`, `la ?`, `lo ?`).
5. #6 teardown on the x230 (RSTP off) + diffs. #7-#8 `.cfg` capture and working log. #9 commit.
   #10 NEEDS TEST ENGINEER with the recable (the RESULT line rode in the same message).

## Wasted input
- Overhead #26: 4.3k of `linerate.py` source read before the case for step S4 (broadcast from eth3), which never
  ran because the gate failed. Read a tool only once its step is reached.
- Otherwise lean: 6.7k in all.

## Repetition
- #4 probed `l ?` ("% Ambiguous command") and needed #5 to probe `l2 ?`, `la ?`, `lo ?`. Asking `l2 ?` directly
  (the L2 protocol tunnelling command family) answers the question in one call.

## Accuracy risks
- **"The stack terminates BPDUs" is inferred** from the x230 side only: x230 port1.0.4 and port1.0.3 both show
  "Received None" for 20 s while the stack bridged its two x230 links. No stack-side counter or capture shows the
  BPDUs arriving and being dropped. It is well supported (nothing else on the link changed), and the final log
  states the observation, not the mechanism. A stack `show interface port1.0.17` multicast-input count before/after
  (BPDUs arrive, ~0.5/s) against port1.0.3's multicast-output count (not forwarded) would close it.
- The safety design was sound: the data loop (x230 port1.0.4 into VLAN 103) was gated on port1.0.4 reading
  Backup/Discarding, and the stack's loop-protection was left on as a second net.
- The case text names "Port11" and an IXIA; the bench maps those to x230 port1.0.4 (or port1.0.7 after the recable)
  and tb470 eth3.
- Unsourced claims left out of the final log: none.

## Next run: expected outputs
| step | expected on this bench |
| --- | --- |
| RSTP on, before the loop | `Default: Bridge up - Spanning Tree Enabled`, x230 is root (Root Id = Bridge Id 8000:00c28f3f0f5d), all linked ports Designated Forwarding |
| via the IE520 stack (STP off) | port1.0.4 stays `Designated Forwarding`, `Received None`: do not close the loop |
| after the recable (port1.0.6 <-> 1.0.7 in one VLAN) | expected (not yet measured): port1.0.7 `Backup` `Discarding`, `Received RSTP`; its TX counter flat under eth3 broadcast |

## Next run: scripts
- Keep the `@poll` gate; add `Received` to what it prints (../REVIEW.md, scripts). For the traffic half after the
  recable: `tools/linerate.py` (broadcast from eth3) and the x230 port counters, or `tools/vcount.py` if a capture is
  wanted.

## Next run: references
- The UNBLOCK in `20358-partial.log` (the exact recable). `platforms/x230v2-28GS.md` §2, the BPDU row.
