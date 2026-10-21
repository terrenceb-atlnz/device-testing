# T47208 process review -- platform-ports-2026-10-21T1323
Reviewed 2026-10-21 by /create-logs from agent-ad7157fdc1eed0717.jsonl and the working files. Case: "Copper pluggable with
supported speeds".

## Token usage
The segment runs from T46421's RESULT message to this case's RESULT message. It holds this case's matrix and also T47210's
setup (2 calls, 1,259 chars). Its own setup reads sit in T46421's segment. Other segments: [../REVIEW.md](../REVIEW.md).
**This is the run's most expensive case segment**: 196,261 cache-write tokens and 1,115 s.

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 14 | 448 | 196,261 | 2,572,595 | 650 | 18 | 1,115 s | 8,599 chars |

## Process taken
1. Read the speed and duplex options the x230 offers (`tools/tb qmark`, nothing executed).
2. One call ran the x230's whole matrix: auto 100, auto 10, auto 1000, fixed 1000, three refusal checks, auto, forced 100 full.
3. In the same tool block, a call to poll the 4050 through each state. **It ran after the x230 call had finished**, not
   beside it. So it polled 120 s for `a-full a-100` and 120 s for `a-full a-10` against a partner that read
   `a-half a-100`, and both polls timed out (about 14:06 to 14:10 NZDT).
4. Forced rows: matched the 4050 at 100 full, verified, forced 10, matched, verified, restored both ends (6 calls).
5. A second pass for the partner readings of the auto rows: x230 to auto 100, 4050 read, x230 to auto 10, 4050 read (4 calls).
6. Restore, health after, running-config diff on both units. Wrote the working log and `.cfg` files, committed.

## Wasted input
- About 4 minutes of wall time, and the 4-call second pass, came from step 3. Two console calls in one tool block run one
  after the other. The partner poll needs `run_in_background`, started BEFORE the DUT call, as T47210 later did.
- The failed poll also expected the wrong thing. With the x230 forced to 100 full and the 4050 on auto, the 4050 reads
  `a-half a-100` (parallel detection). Poll for that, or match the partner first.

## Repetition
- The partner readings for the auto rows were taken twice: once by the failed poll, once by the second pass.

## Accuracy risks
- Only one copper module type (AT-SPTXa) was on the bench. The final log says so in CAVEAT. A second module type would
  need another SFP fitted.
- "Supported speeds" was read from the module type in `show system pluggable detail` (1000BASE-T) and from what the DUT
  accepted or refused. The parser's own `speed ?` list is generic and does not reflect the module.

## Next run: expected outputs
| setting on port1.0.1 | x230 status | 4050 status |
| --- | --- | --- |
| `speed auto 100` | `a-full a-100` | `a-full a-100` |
| `speed auto 10` | `a-full a-10` | `a-full a-10` |
| `speed auto 1000` / `speed 1000` | full 1000 | `a-full a-1000` |
| `speed 100` + `duplex full`, 4050 on auto | full 100 | `a-half a-100` (parallel detection) |
| `speed 100` + `duplex full`, 4050 matched | full 100 | full 100 |
| `speed 10` + `duplex full`, 4050 matched | full 10 | full 10 |
| `speed auto 2500`, `speed 10000`, `speed auto 100000` | `% port1.0.1: Unsupported speed/duplex combination port1.0.1` | unchanged |

## Next run: scripts
- Start the 4050 poll with `run_in_background` first, then run the x230 matrix (the T47210 pattern).
- Proposed `tools/tb speedrow` (../REVIEW.md): sets one row, matches the partner on forced rows, polls both ends.

## Next run: references
- The table above, and this case's final log.
- [platforms/x230v2-28GS.md](../../../../platforms/x230v2-28GS.md) §2: copper SFP rows (`duplex half` refused at 1000).
