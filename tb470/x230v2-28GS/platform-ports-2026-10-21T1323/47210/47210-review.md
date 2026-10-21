# T47210 process review -- platform-ports-2026-10-21T1323
Reviewed 2026-10-21 by /create-logs from agent-ad7157fdc1eed0717.jsonl and the working files. Case: "MAC/Phy TLV with
combination of user defined speed, duplex and auto nego".

## Token usage
The segment runs from T47208's RESULT message to this case's RESULT message. Its setup (2 calls) sits in T47208's segment.
It has the run's highest context per API call (about 223,000 tokens). Other segments: [../REVIEW.md](../REVIEW.md).

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 15 | 450 | 35,697 | 3,342,648 | 1,237 | 17 | 600 s | 8,596 chars |

## Process taken
1. Setup (in T47208's segment): `lldp tlv-select mac-phy-config` on both ports, local info, health before, running-configs.
2. A background watcher on the 4050 to catch the TLV for each auto row, then one x230 call for the four auto rows
   (C2 auto 100, C3 + half, C9 auto 10, C8 fixed 1000), 12 s hold each. One read of the watcher's four catches.
3. Forced rows C4 to C7: two calls per row (x230 side, then 4050 side), 8 calls.
4. Restore on both ends, final TLV read, `no lldp tlv-select`, health after, running-config diffs.
5. Wrote the working log and `.cfg` files, checked the snmpd trap lines, committed. Closed both consoles with `tools/tb cfg`.

## Wasted input
none found. Each call read back 207 to 1,357 chars.

## Repetition
- The forced rows took two calls each (8 in all). One call per row that sets both ends and reads the TLV would make it 4.
  The proposed `tools/tb speedrow` covers it.

## Accuracy risks
- The fixed `speed 1000` row (C8) advertises auto-negotiation "Disabled" while the link runs 1000 full. The final log
  shows it as an observation from the output. It is not graded.
- The TLV must be read soon after link-up. The background watcher caught each row in order. Keep that method.

## Next run: expected outputs
TLV decoded at the 4050 (`show lldp neighbors detail` on port1.0.2):

| row | x230 setting | auto-negotiation | advertised | operational MAU type |
| --- | --- | --- | --- | --- |
| C1 | auto | Enabled | full set | 30 |
| C2 | `speed auto 100` | Enabled | | 16 |
| C3 | `speed auto 100` + `duplex half` | Enabled | | 15 |
| C9 | `speed auto 10` | Enabled | | 11 |
| C8 | `speed 1000` | Disabled | [none] | 30 |
| C4 | `speed 100` + `duplex full` | Disabled | [none] | 16 |
| C5 | `speed 100` + `duplex half` | Disabled | [none] | 15 |
| C6 | `speed 10` + `duplex full` | Disabled | [none] | 11 |
| C7 | `speed 10` + `duplex half` | Disabled | [none] | 10 |

The advertised column for C2, C3 and C9 is in this case's final log.

## Next run: scripts
- The background-watcher pattern used here: `tools/tb ckcon ... u0 ...` with `run_in_background`, started before the DUT call.
- Proposed `tools/tb speedrow` (../REVIEW.md).

## Next run: references
- The table above, and this case's final log.
