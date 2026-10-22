# T47209 process review -- ports-2026-10-22T1320
Reviewed 2026-10-22 by /create-logs from agent-a94e8f5311ee35935.jsonl (first tester, session e972c63b, died ~14:00
with its sentinel session), agent-a6d7520e50d81792d.jsonl (resuming tester, session f7014de7) and the working files.

## Token usage
| tester | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| first (13:44-14:00, no RESULT line, all counted as overhead by case_tokens.py) | 39 | 78 | 120,574 | 3,299,702 | 6,798 | 39 | 945 s | 82,815 |
| resuming (14:04-14:23), case segment | 37 | 74 | 118,213 | 3,176,230 | 1,674 | 39 | 1,127 s | 64,837 |
| resuming, overhead (hand-back) | 1 | 2 | 334 | 118,213 | 24 | 2 | 16 s | 143 |
| **total** | **77** | **154** | **239,121** | **6,594,145** | **8,496** | **80** | **2,088 s** | **147,795** |

## Process taken
1. First tester, calls 1-24: read the queue (12.2 k chars), the 10-09 review's "Next run" section, the platform file,
   tools/README.md (9.9 k + 5.9 k), logged-output.md + STANDING-ORDERS (10.1 k), `tools/tb --help`, vsend.py, ckcase.py.
2. Calls 25-34: gate (precheck, scratch, template, peek), `bench_probe.py run -h`, probe, queue row to RUNNING.
3. Calls 37-51: pre-reads, health before, setup via `tools/tb cfg`, run1.log opened (13:48).
4. Calls 52-61: wrote work/row.sh, ran R0, opened port1.0.26, ran R1 twice (marker regex rejected '-' in the tag), wrote a
   delta script in its scratchpad.
5. Calls 62-66: appended setup + R0-R1 to run1.log at 13:53, then ran R2-R6 (row files only) and died after R6's count.
6. Resuming tester, calls 1-11: read the queue's named line ranges (6.0 k), the 10-09 expected table + row.sh (3.8 k), run1.log
   lines 16-56; resume gate; live state check.
7. Calls 12-24: transcribed R2-R6 from the row files into run1.log (one 11.7 k and one 5.8 k grep across all row files).
8. Calls 25-31: rows R6b, R7, R8, R9, R10, R9b, R9c, R10b.
9. Calls 32-41: log read, pluggable diagnostics, health after, swi_f.cfg, restore + proof, logout, commit, RESULT.

## Wasted input
- First tester, call 3: the whole queue top (lines 1-103 + 138-200, 12.2 k chars). The dispatch-style short brief
  (Session facts + Group 1 recipe, ~6 k) was enough, as the resuming tester showed (call 1, 6.0 k).
- First tester, calls 9-13: 26 k chars of tools/README.md and logged-output.md read before the first console byte. The
  entries this case used are vsend, vcount, capture, sudotool, health, ckcon and cfg (about 4 k).
- Resuming tester, call 16: an 11.7 k grep over every row file at once, then a 5.8 k second pass (call 17). One pass with
  a tighter pattern (`marker=|frames$|% |current speed|configured`) would have done.

## Repetition
- R1 ran twice: the first pass used `TEST-R1-auto` as the marker, and vcount's marker regex `[A-Za-z0-9:._]+` rejects '-'.
  The frames arrived but were listed "unmarked". Cost: one full row (~75 s and two console sessions).
- R6 ran twice (R6 and R6b) because the first tester died before R6's AFTER counters.
- R9b ran as a mirror of R9 instead of "both ends fixed" because R10 had already reset port1.0.25 (tester's ordering
  error). R9c then ran the intended row. One extra row.
- Both testers re-derived the per-port counter deltas from `show interface` blocks with ad-hoc scripts (first tester:
  deltas.sh in its scratchpad; resuming tester: an inline parser).

## Accuracy risks
- **run1.log was written in batches, not per row.** The first tester logged R0-R1 at 13:53 and then ran R2-R6 for 6 minutes
  without logging them. When its session died, R2-R6 survived only because row.sh wrote each row to a file in the repo.
  The resuming tester rebuilt them from those files. Had row.sh written to the box's /tmp instead, five rows would have been lost.
- **swi_f.cfg was captured at 14:18, after the rows, not after setup at 13:48.** The resuming tester re-verified the setup
  state first (VLAN membership, port1.0.26 open, no speed/duplex lines) and the file's header says so. Low risk, but it is
  a deviation from logged-output.md §2.
- R9/R9b (one end fixed against an auto end: "connected" with 0 frames) is graded as a negotiation mismatch, not a defect.
  That reading is the tester's. A developer may decide it is worth a defect too (a link that reads connected and carries
  nothing). It does not change the FAIL.

## Next run: expected outputs
| row | command on port1.0.25 | expected DUT answer | expected status | eth1 TEST / CTRL |
| --- | --- | --- | --- | --- |
| R0 | (port1.0.26 shut) | - | 1.0.25 notconnect, 1.0.26 disabled | 0 / 0 |
| R1 | auto | - | both `connected ... a-full a-1000` in 1 read (1.2 s) | 100 / 0 |
| R2 | `speed 1000` | no % | 1.0.25 `a-full 1000` | 100 / 0 |
| R3 | `speed 100` | **no % (the defect)** | 1.0.25 `a-full 100`, 1.0.26 `a-full a-1000` | **0** / 0 |
| R4 | `speed auto 100` | **no % (the defect)** | 1.0.25 `a-full a-100` | **0** / 0 |
| R5 | `speed 10` | `% port1.0.25: Unsupported speed/duplex combination port1.0.25` + EXFX "Invalid request vs capabilities" | stays a-1000 | 100 / 0 |
| R6 | `speed 2500` | same %, no EXFX line | stays a-1000 | 100 / 0 |
| R7 | `speed 10000` | same %, no EXFX line | stays a-1000 | 100 / 0 |
| R8 | `duplex half` | `% Duplex set failed port1.0.25` + EXFX "Failed to set the duplex mode on ifx 5025, rc 16" | stays a-1000 | 100 / 0 |
| R9 | `speed 1000` + `duplex full`, 1.0.26 auto | no % | 1.0.25 `connected full 1000`, 1.0.26 notconnect | 0 / 0 |
| R9c | same on BOTH ends | no % | both `connected full 1000` | 100 / 0 |
| R10 | `speed auto` + `duplex auto` | no % | both `a-full a-1000` | 100 / 0 |
DUT counters per passing row: 1.0.10 in +200, 1.0.25 out +101..102, 1.0.26 in +101..102, 1.0.2 out +101..103.

## Next run: scripts
- **Marker tags: use only `[A-Za-z0-9:._]`** in `vsend --tag` (no '-'). Better: make `vcount.py` warn when frames arrive
  with a tag that does not match its regex, instead of listing them "unmarked" (proposed change to tools/vcount.py).
- **Proposed tools/portdelta.py** `--before FILE --after FILE --ports port1.0.10,port1.0.25,...`: parse two saved
  `show interface` blocks and print in/out packet deltas per port. Both testers hand-built this.
- **Proposed tools/speedrow-like loop row for fibre self-loops**: the work/row.sh shape (config on one port, poll, before
  reads, capture + two vsend bursts + vcount, after reads, one output file per row) is generic apart from the ports and MACs.
  As `tools/tb looprow <TB> <run> <uN> <baud> --port A --far B --src-nic ethX --dst-nic ethY --label L [config-if cmds]`
  it would serve every pluggable-speed case. `tools/tb speedrow` covers two-device links only.

## Next run: references
- `ports-2026-10-22T1320/47209/47209-fail.log` STEP tables: the expected outputs above, with the exact DUT strings.
- `platforms/x230v2-28GS.md` §2 row "1000BASE-SX module accepts speed 100": the known defect.
- tools/README.md entries `vsend.py`, `vcount.py` (marker regex), `tb capture`, `tb sudotool` -- read those four only.
