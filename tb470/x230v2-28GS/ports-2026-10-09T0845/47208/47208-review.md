# T47208 process review -- ports-2026-10-09T0845
Reviewed 2026-10-12 by /create-logs from `agent-a4163fdf23e120522.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 13 | 26 | 22,571 | 2,464,450 | 109 | 13 | 558 s | 13,318 chars |

## Process taken
1. #1 step 1: speed matrix on x230 port1.0.5 / 1.0.3 / 1.0.2 (u0), stdout `step1-u0.out` (3.0k back).
2. #2 read back poll lines and 60 lines of `show system pluggable detail` (3.0k).
3. #3 x230 port1.0.1 into its own VLAN 101; AR4050S port1.0.2 `no shutdown` (u1).
4. #4 step 2: speed matrix on port1.0.1 against the AR4050S + LLDP.
5. #5 step 3a: on the stack, offer 10 then 100 on port1.0.17, try port1.0.2 (aggregator member), then force
   100/full on port1.0.17. #6 grep its `% ` lines.
6. #7 step 3b: force 100/full on x230 port1.0.3; then restore both ends (step3c/3d).
7. #8 teardown + `rcdiff.py` on three units. #9-#10 `.cfg` capture times. #11 working log. #12 commit. #13 RESULT.

## Wasted input
- #2: 3.0k, mostly `show system pluggable detail` for four ports (17 lines each). `show system pluggable` (one table
  row per port: device, serial, type) gives the same facts in 8 lines.

## Repetition
- The speed block (`speed auto 100/10/1000`, `speed 1000`, `speed auto`, each with a poll) was rebuilt as a bash
  array in #1 and again in #4. A matrix tool would take the port list as arguments (../REVIEW.md, `portmatrix.py`).

## Accuracy risks
- **10 Mb/s on the AT-SPTX is unproven.** Both SPTX ports face IE520 AT-SPTXa ports, which refuse 10 Mb/s
  ("% port1.0.17: Unsupported speed/duplex combination port1.0.17"). The tester proposed PARTIAL for that gap; the
  Test Engineer kept PASS, and the final log says it in CAVEAT and STEP 1C. To close it: put an SPTX against the
  AR4050S (swap the SPTX into x230 port1.0.1, or move the AR4050S cable onto port1.0.2/1.0.3) and run `speed auto
  10` and `speed 10` + `duplex full/half`.
- Forced (no autoneg) speed was exercised only at 100/full on port1.0.3; 10/full and the half-duplex forced modes
  were not run on any copper SFP in this case (T47210 ran them on port1.0.1).
- With the stack end forced to 100/full and the x230 still at auto, the x230 read `a-half a-100` (parallel
  detection falls back to half duplex): a duplex mismatch for those seconds. Harmless here; worth knowing.
- Unsourced claims left out of the final log: none.

## Next run: expected outputs
| port / partner | speed auto 100 | speed auto 10 | speed auto 1000 | speed 1000 | forced 100 full |
| --- | --- | --- | --- | --- | --- |
| 1.0.5 SPTXc / eth3 | a-full a-100 (2 reads) | a-full a-10 | a-full a-1000 | a-full 1000 | not run (host NIC) |
| 1.0.1 SPTXa / AR4050S | a-full a-100 | a-full a-10 | a-full a-1000 | a-full 1000 | (see T47210: full 100) |
| 1.0.3 SPTX / stack 1.0.17 | a-full a-100 | notconnect 25 s (partner refuses 10) | a-full a-1000 | a-full 1000 | full 100 both ends |
| 1.0.2 SPTX / stack 1.0.2 (sa2) | a-full a-100 | notconnect 25 s | a-full a-1000 | a-full 1000 | stack refuses: "Cannot configure aggregator member." |

## Next run: scripts
- Proposed `tools/portmatrix.py` (../REVIEW.md) with `--dut u0:port1.0.5,port1.0.3,port1.0.2 --combo "auto 100"
  --combo "auto 10" --combo "auto 1000" --combo "1000" --combo "auto"`.

## Next run: references
- `platforms/x230v2-28GS.md` §2, the SPTX-at-10 row. ../REVIEW.md bench link map (which partner can run 10 / half).
