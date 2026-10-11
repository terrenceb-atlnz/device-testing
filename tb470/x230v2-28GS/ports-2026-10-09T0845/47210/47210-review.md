# T47210 process review -- ports-2026-10-09T0845
Reviewed 2026-10-12 by /create-logs from `agent-a4163fdf23e120522.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 11 | 22 | 24,005 | 2,336,485 | 93 | 11 | 635 s | 15,270 chars |

## Process taken
1. #1 setup on the x230 (VLAN 101 on port1.0.1, `lldp tlv-select mac-phy-config`) and the AR4050S (TLV, `no
   shutdown`), 2.5k back.
2. #2 C1 baseline at the AR4050S: an `@poll ... do show lldp ...` at exec mode timed out on "% Invalid input" (61 s),
   then a plain `show lldp neighbors detail` gave the reading.
3. #3 C2, C3, C9 through a `combo()` shell function (2.5k back). #4 the same function pasted again for C8, C4, C5,
   C6, C7 (2.5k back).
4. #5 reverse-direction readings (the x230's view of the AR4050S TLV) grepped from the files.
5. #6 restore and teardown on both units. #7 setup re-applied to capture the `.cfg` files, then torn down again.
   #8 `rc2cfg.py` + `rcdiff.py`.
6. #9 working log. #10 commit. #11 RESULT.

## Wasted input
- #2: 61 s and one call lost to `@poll 60 MAU do show lldp ...` at exec mode (`do` is a config-mode prefix). The
  failure is in the first read; ckcon could stop there (../REVIEW.md, scripts).
- #3/#4 printed each combination's full trace back (2.5k each) after writing it to files; a one-line summary per
  combination (status, TLV autoneg / advertised / MAU) would have been ~0.6k.

## Repetition
- The `combo()` function (≈1.2k of shell) was defined twice verbatim (#3, #4). One call with all eight combinations,
  or the proposed `tools/portmatrix.py`, avoids it.
- #7: the case setup was applied a second time after the teardown only to capture the `.cfg` files, because they
  were not saved after setup in #1. Capturing `show running-config` in the setup call is the rule (logged-output §2)
  and saves the re-setup and second teardown. As a side effect swi_e.cfg shows port1.0.2 `shutdown`, unlike the case.

## Accuracy risks
- **Unsourced, left out of the final log:** run1.log's C1 line "x230 status: port1.0.1 connected 101 a-full a-1000"
  has no x230 status read in the working files for C1 (the AR4050S side, `connected 10 a-full a-1000` at 19:03:35,
  is sourced and is what the log quotes). Evidence that would close it: `show interface port1.0.1 status` on u0 in
  the C1 call.
- run1.log says the x230's C7 read had "no 802.3 TLV in the x230 table"; the file shows no neighbour at all on
  port1.0.1 at 19:10:02 (`LLDP Detailed Neighbor Information:` and nothing more). The final log quotes it as is.
- C3: the x230 status reads `half a-100` (duplex configured) while the AR4050S negotiated `a-half a-100`; the poll
  for `a-half` timed out (41 s). The link and TLV were right; the regex was wrong for a configured duplex.
- C8 (fixed `speed 1000`): the TLV reports autoneg "Supported, Disabled", advertised [none], while the partner reads
  `a-full a-1000`. run1.log's explanation (1000BASE-T always negotiates, clause 40) is the tester's inference, not
  printed by the device, so the final log states only the observation and leaves the question to the case owner.
- Only one link (port1.0.1 <-> AR4050S) could run 10 Mb/s and half duplex on this bench.

## Next run: expected outputs
| combo (x230 / AR4050S) | x230 status | AR4050S status | TLV at the AR4050S: autoneg / advertised / MAU |
| --- | --- | --- | --- |
| C1 auto / auto | (not read) | a-full a-1000 | Supported, Enabled / 1000BaseTFD, 100BaseTXFD, 100BaseTX, 10BaseTFD, 10BaseT / 1000BaseTFD (30) |
| C2 speed auto 100 / auto | a-full a-100 | a-full a-100 | Enabled / 100BaseTXFD, 100BaseTX / 100BaseTXFD (16) |
| C3 speed auto 100 + duplex half / auto | half a-100 | a-half a-100 | Enabled / 100BaseTX / 100BaseTXHD (15) |
| C9 speed auto 10 / auto | a-full a-10 | a-full a-10 | Enabled / 10BaseTFD, 10BaseT / 10BaseTFD (11) |
| C8 speed 1000 + duplex full / auto | full 1000 | a-full a-1000 | Disabled / [none] / 1000BaseTFD (30) |
| C4 100 full / 100 full | full 100 | full 100 | Disabled / [none] / 100BaseTXFD (16) |
| C5 100 half / 100 half | half 100 | half 100 | Disabled / [none] / 100BaseTXHD (15) |
| C6 10 full / 10 full | full 10 | full 10 | Disabled / [none] / 10BaseTFD (11) |
| C7 10 half / 10 half | half 10 | half 10 | Disabled / [none] / 10BaseTHD (10) |
The TLV is at the AR4050S within one read (1.2 s) of the x230 link coming up in every combination.

## Next run: scripts
- Proposed `tools/portmatrix.py` (../REVIEW.md) with `--partner u1:port1.0.2 --tlv`: the table above becomes its
  expected-output file and grading becomes a diff.

## Next run: references
- `platforms/x230v2-28GS.md` §2, the fixed-1000 TLV row. ../REVIEW.md cross-case findings 1-3 (poll slips, status
  column, `.cfg` timing).
