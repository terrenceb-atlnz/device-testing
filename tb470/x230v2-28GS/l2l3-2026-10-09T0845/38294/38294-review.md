# T38294 process review -- l2l3-2026-10-09T0845
Reviewed 2026-10-12 by /create-logs from `agent-a416990ee48b8b1f0.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md). Call numbers are this segment's (after the
T15255 RESULT up to this case's RESULT).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 9 | 18 | 15,314 | 1,636,130 | 5,290 | 9 | 254 s | 6,955 chars |

A lean case: one ckcon call per phase, results to files, one working-log write.

## Process taken
1. #1 L2 baseline config on u0 (port1.0.5 into VLAN 1) plus `show interface vlan1` for the MAC.
2. #2 eth1/eth3 pings, then the bridged linerate baseline (514 chars back).
3. #3 setup + step 1 (route, show ip route, ping, show arp) in one ckcon call (1,497).
4. #4 `rc2cfg.py` -> swi_f.cfg; stk_a.cfg copied from the group pre-run capture.
5. #5 counters before, three linerate runs (1500/1518/64), counters after, log tail (2,040).
6. #6 teardown + `rcdiff.py` (1,609). #7 working log. #8 linerate README update. #9 RESULT.

## Wasted input
none found (the largest read, #5 at 2,040 chars, is the step's own evidence).

## Repetition
- #1 sent `show interface status port1.0.5`, which the x230 refuses (`% Invalid input`). It was the
  last command, so nothing was lost, but the same syntax would stop a `--stop-on-error` list
  mid-way. Use `show interface status` (no port) or `show interface port1.0.5` on the x230.

## Accuracy risks
- **"TTL-decremented"** (working log, step 2) is not printed anywhere: linerate's receive filter
  checks source MAC and length, not TTL. Left out of the final log. To prove it, have linerate
  print the received TTL/hop-limit histogram (proposed in REVIEW.md).
- **stk_a.cfg is the 19:33 group pre-run capture,** not a capture taken after this case's setup.
  The case did not configure the stack, so it is the right content, but nothing re-read the
  stack between 19:33 and 19:43. A `rcdiff` against a fresh `show running-config` would close it.
- **64-byte frames** were sent at 274 kpps (184 Mbps on the wire), the host sender's ceiling, so
  small-frame line rate is not measured (stated in the log's CAVEAT).
- The bridged baseline counted 822500 of 822501 (one frame short); routed runs were exact. See
  the one-frame pattern in REVIEW.md.

## Next run: expected outputs (this bench, this build)
| step | expected |
| --- | --- |
| 0 baseline | `rx eth1 822500 (100.0%)` of 822501 at 999.7 Mbps on the wire (1500 bytes, bridged) |
| 1 route | `S       192.0.2.0/24 [1/0] via 10.38.215.1, vlan1 weight 1`; `show arp` 10.38.215.1 `00f0.4d00.7716 vlan1 port1.0.2` |
| 2 traffic | 1500: 822001/822001 at 999.6 Mbps; 1518: 813001/813001 at 999.8 Mbps; 64: 2741001/2741001 at 274068 pps; x230 port1.0.5 input delta = sum sent exactly, port1.0.2 output = sum + 2 |

## Next run: scripts
- `tools/linerate.py` (extended here: `--rx-mac`, `--rx-len`, `--ipv6`, `--src-macs`) fits as is.
- Proposed `tools/ifdelta.py` (REVIEW.md) for the before/after `show interface` arithmetic done by hand here.

## Next run: references
- `tools/README.md` `linerate.py` entry (its Status line holds this case's numbers).
- T38295's log: the same path and method for IPv6.
