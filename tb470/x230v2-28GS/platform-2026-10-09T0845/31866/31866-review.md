# T31866 process review -- platform-2026-10-09T0845
Reviewed 2026-10-12 by /create-logs from `agent-a591963d08f049547.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 10 | 179,556 | 694,105 | 82 | 5 | 643 s | 2,909 chars |

Segment #71-#75 (18:25:56-18:36:39). `case_tokens.py` gave it 1 call (the RESULT). Its help probes
were done in T31863's segment (#50/#51). **173,222 of the 179,556 cache-write tokens are one cache
expiry** (below).

## Process taken
1. #71 one call: pre-case capture + restart (`ckreload`, 165 s) + VLAN isolation + `exec-timeout 0`
   (stopped on the informational `% `) + verify + `exit` -- 5 min 13 s.
2. #72 (cache re-written) `tools/tb ckyn ... "YN?:platform prbs all-fabric duration 20"` ->
   `% PRBS not supported on this platform`, then `tools/tb poll ... 15 75 ... "show platform prbs"`.
3. #73 the other forms + show platform prbs + show exception log, the closing restart, VLAN/lldp
   restore, `rcdiff.py`.
4. #74 `.cfg`, working log, commit; #75 RESULT.

## Wasted input
- **#71 -> #72: a 173,222-token cache rewrite.** #71 blocked for 5 min 13 s, past the prompt cache's
  5-minute lifetime, so #72 re-wrote the whole context. Splitting #71 after the reload (two calls of
  ~3 min and ~1.5 min) would have kept the cache warm (../REVIEW.md cross-case 1).
- #72's 75 s results poll after an immediate refusal: once `platform prbs` answers `% PRBS not
  supported on this platform`, no results file can appear; one `show platform prbs` is the proof.

## Repetition
- The `exec-timeout 0` informational `% ` stopped ckcon again, as in T31863 (../REVIEW.md cross-case 2).
  The tester had learned it, so it cost only the verify inside the same call.

## Accuracy risks
- **The case's command `platform prbs all duration 20` does not exist on this parser**; it was sent
  as `platform prbs all-fabric duration 20` on the dispatch's instruction (the parser offers only
  `all-fabric | internal-fabric`). Every offered form was refused the same way, so the mapping does
  not change the verdict. Recorded in the final log's CAVEAT.
- **Unsourced in the final log:** the `?` help output (`platform prbs ? -> all-fabric |
  internal-fabric`, `duration ? -> WORD`) exists only as the working log's summary; the raw qmark
  captures were not saved into `work/`. The final log states the forms in the CAVEAT, not as quoted
  output.
- The verdict rests on printed refusals and `Unable to open results file. No previous PRBS run?`.

## Next run: expected outputs
| step part | command | expected on this bench |
| --- | --- | --- |
| baseline | `show platform prbs` | `Unable to open results file. No previous PRBS run?` |
| restart | `reload` (y) | login after ~165 s |
| timeout | `line con 0` / `exec-timeout 0` | informational `% The new exec-timeout settings will apply to new sessions only` |
| PRBS | `platform prbs all-fabric duration 20` / `internal-fabric duration 20` / `all-fabric` | `% PRBS not supported on this platform` each |
| results | `show platform prbs` | `Unable to open results file. No previous PRBS run?` |
| check | `show exception log` | `None` |
| closing restart | `reload` (y) | ~163 s; re-apply VLAN 103-105 + `lldp run` |

## Next run: scripts
- As T31863: `ckcon.py --allow-pct` (proposed), one non-stopping call for every form; no `poll.py`
  after a refusal. Keep each blocking call under ~4.5 min.

## Next run: references
- platforms/x230v2-28GS.md §2 (PRBS refused at run time; the parser's forms).
