# T31863 process review -- platform-2026-10-09T0845
Reviewed 2026-10-12 by /create-logs from `agent-a591963d08f049547.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 21 | 42 | 21,853 | 3,325,557 | 291 | 21 | 889 s | 12,669 chars |

Segment #50-#70 (18:10:51-18:25:40). `case_tokens.py` gave it 1 call (the RESULT). The most
expensive case of the group: a third of all cache reads. #50-#55 (help probes and wiki reading)
served T31866 too.

## Process taken
1. #50-#51 `tools/tb qmark` help probes for `platform`, `platform bist ...`, `platform prbs ...`
   (2.5k chars; captures left in the session scratchpad, not `work/`).
2. #52 read `ckyn.py`/`ckcon.py` for `CKTO`; #53-#55 searched the AW+ wiki (markdown, then x230 DITA)
   for platform bist/prbs; #56 read `ckcon.py` lines 55-110.
3. #57 pre-case capture + restart (`ckreload`, 165 s).
4. #58 VLAN isolation + `line con 0` / `exec-timeout 0`: stopped by `--stop-on-error` on the
   informational `% The new exec-timeout settings will apply to new sessions only`.
5. #59 verify `exec-timeout 0 0` + `exit` (logout; 90 s wait on the exit).
6. #60 `tools/tb ckyn ... "YN?:platform bist instance all"` -> `% BIST test not supported.`, exit 2.
7. #61 the other forms + show platform bist + show exception log.
8. #62-#65 teardown attempts by config: `no exec-timeout` (twice), `lldp run`, logout/login, each with
   `rcdiff.py` -- `exec-timeout 0 0` stayed.
9. #66 the step's closing restart + VLAN/lldp restore (3.5 min); #67-#69 `.cfg`, working log, commit;
   #70 RESULT.

## Wasted input
- #52 + #56 (2k chars) reading tool source for the timeout variable: `CKTO` is in tools/README.md's
  `ckcon.py` entry.
- #53-#55 (1.6k chars) wiki search: the parser's own help (#50/#51) already showed the forms, and
  the outcome is now in platforms/x230v2-28GS.md §2.

## Repetition
- #62-#65: four calls (~2 min, ~650k cache read) undoing `exec-timeout 0` by config before a restart
  that the step itself requires and that clears running-config anyway (#66 proved it: diff empty).
  Skip config-level teardown when the step ends with a restart into an unchanged boot config.
- #58 -> #59 and #60 -> #61: two "stopped, send the rest" pairs (../REVIEW.md cross-case 2 and 3).

## Accuracy risks
- **Unsourced in the final log:** the `?` help output (`platform bist instance ? -> <0-127> | all`,
  `all ? -> full | <cr>`) exists only as the working log's condensed summary; the raw `qmark`
  captures were not copied into `work/`. The final log states the forms as Method/CAVEAT text and
  quotes no help output. Close it by saving qmark captures with the case.
- The `exit` after the timeout change waited ~90 s (18:16:14 -> 18:17:44) before `awplus login:`
  showed; harmless, but the logout was not instant.
- Observation (not graded, noted for the Test Engineer): `no exec-timeout` under `line con 0` was
  accepted with the same informational `% ` line yet left `exec-timeout 0 0` in running-config, also
  after a fresh login (`work/ckcon-bist6/8/10.out`). Recorded in platforms/x230v2-28GS.md §2.
- The verdict itself rests on printed refusals of every form plus `show platform bist: Not run`;
  no inference.

## Next run: expected outputs
| step part | command | expected on this bench |
| --- | --- | --- |
| restart | `reload` (y) | login after ~165 s |
| timeout | `line con 0` / `exec-timeout 0` | `% The new exec-timeout settings will apply to new sessions only` (informational; applied) |
| verify | `show running-config \| begin line con` | ` exec-timeout 0 0` |
| BIST | `platform bist instance all` / `0` / `all full` | `% BIST test not supported.` each |
| results | `show platform bist` | `Switch Instance 0 ......... Not run` |
| check | `show exception log` | `None` |
| closing restart | `reload` (y) | ~165-168 s; `exec-timeout 0 0` gone, VLAN 103-105 + `lldp run` to re-apply |

## Next run: scripts
- `ckcon.py --allow-pct 'apply to new sessions only'` (proposed, ../REVIEW.md) for the timeout step.
- One non-stopping `tools/tb ckcon` call for all three BIST forms + the two show commands.
- Copy `qmark` captures to `work/` when help output is evidence.

## Next run: references
- platforms/x230v2-28GS.md §2 (BIST refused at run time; the `no exec-timeout` quirk).
- tools/README.md `ckcon.py` entry (`CKTO`, `--stop-on-error`).
