# T38295 process review -- l2l3-2026-10-09T0845
Reviewed 2026-10-12 by /create-logs from `agent-a416990ee48b8b1f0.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md). Call numbers are this segment's (after the
T38294 RESULT up to this case's RESULT).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 7 | 14 | 11,107 | 1,372,221 | 4,804 | 7 | 194 s | 4,881 chars |

The cheapest case of the group. `tools/case_tokens.py` credits it only 4 calls, because #1-#3
name the case folder as `D=.../38295;` with no trailing slash (REVIEW.md).

## Process taken
1. #1 setup on u0: `ipv6 forwarding`, the two global addresses, `show ipv6 interface brief`, running-config (859).
2. #2 step 1: route, `show ipv6 route`, ping, `show ipv6 neighbors`, counters before (1,055).
3. #3 `rc2cfg.py`, stk_a.cfg copied from T38294's with its header line edited, three linerate
   runs (1500/1518/78), counters after (2,400).
4. #4 teardown + `rcdiff.py` (208). #5 working log. #6 commit. #7 RESULT.

## Wasted input
none found.

## Repetition
- The L2 baseline was not repeated: T38294's, taken four minutes earlier on the same unchanged
  path, serves this case. That is the right call; the final log quotes it with its time.

## Accuracy risks
- **One frame short at 1500 bytes:** eth1 counted 822000 of 822001, while the x230's port
  counters show every frame in and out (port1.0.5 +3788012 = 3788003 sent + 9 others; port1.0.2
  +3788013). The PASS stands on the device counters, but the host-side shortfall is unexplained
  (REVIEW.md, the one-frame pattern).
- **"Show ip route"** in the expected result was read as `show ipv6 route`. On AW+ `show ip route`
  is IPv4-only, so this is the only sensible reading, but it is the tester's interpretation of the case text.
- **78-byte frames** (the smallest IPv6/UDP frame linerate builds) reached 215 kpps / 168.8 Mbps:
  small-frame line rate not measured (CAVEAT in the log).
- **Hop-limit decrement** is not checked by linerate (same as T38294).
- **stk_a.cfg** is T38294's copy of the 19:33 pre-run capture with the header's case id changed by
  `sed`: correct content for an unchanged stack, but not a fresh capture.

## Next run: expected outputs (this bench, this build)
| step | expected |
| --- | --- |
| setup | `show ipv6 interface brief`: vlan1 `fd32:b1f0:dff8:d701::29/64 preferred`, vlan105 `fd32:b1f0:dff8:d703::90/64 preferred`, link-local `fe80::2c2:8fff:fe3f:f5d` on both |
| 1 route | `S       2001:db8:ffff::/64 [1/0] via fd32:b1f0:dff8:d701::1, vlan1`; neighbor `fd32:b1f0:dff8:d701::1 00f0.4d00.7716 vlan1 port1.0.2` |
| 2 traffic | 1500: 822000-822001 of 822001 at 999.2 Mbps; 1518: 813001/813001 at 999.8 Mbps; 78: 2153001/2153001 at 215257 pps |

## Next run: scripts
- `tools/linerate.py --ipv6 --src-ip ... --dst-ip ...` as used; no new tool needed for the case.

## Next run: references
- T38294's log for the path and baseline; this file for the IPv6 numbers.
