# T30403 process review -- cli-2026-10-13T0949
Reviewed 2026-10-13 by /create-logs from `agent-a3ab1e57621c1d438.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 16 | 32 | 27,332 | 2,004,507 | 3,641 | 17 | 228 s | 17,450 chars |
| *apportioned:* 11 | 22 | 21,672 | 1,380,246 | (not re-split) | 12 | ~170 s | 9,138 chars |

The measured segment (`tools/case_tokens.py`, first call naming `/30403/` to `RESULT 30403`) also holds
T45543's whole device run (#11-#13, 3 calls, 2,802 chars) and two reads for T20358 (#3-#4, 5,510 chars),
because the T30403 working log was written last. The apportioned row moves them to those cases
(per-call usage measured from the transcript). Call #1 is also the group baseline (`prerun-u0/u1.out`)
for every case, so even the apportioned row overstates T30403's own cost.

## Process taken
1. #1 `mkdir` of all four case folders + group baseline (`show clock/system/boot/running-config` on u0 and u1).
2. #2 re-read the baseline running-config from the file; #3-#4 read the LACP memory and the linerate/vsend README sections (T20358 prep).
3. #5-#6 queue row to RUNNING.
4. #7 `qmark` help probes (config `ip m`/`ipv6 m`/`ip p`, exec `show ip m`/`show ip p`); #8 one `ckcon` with the four refused config lines, two refused shows, `show license`, `show running-config`.
5. #9-#10 two greps of the baseline for clocks, versions and serials (for the group facts).
6. #11-#13 T45543's run (see its review); #14 `rc2cfg.py` + `rcdiff.py`; #15 working log; #16 commit; #17 RESULT.

## Wasted input
- #2 (1,501 chars): the baseline running-config was printed back right after #1 had saved it; `rc2cfg.py`
  (#14) and `rcdiff.py` work from the file, so nothing needed it in context.
- #9-#10 (2,179 chars): two passes of grep over the same two baseline files for clock / version / serial.
  One `grep -a -E 'UTC Time|Local Time|Software version|Build date|Bootloader|Serial'` would do.

## Repetition
- The group facts (devices, builds, MACs, clocks, NICs) were collected here and pointed to by the three later
  working logs: good, once per group as logged-output.md §2 asks.

## Accuracy risks
- none found. Every "absent" claim is a printed `% Invalid input` / `% Unrecognized command`; the licence
  reading is a printed `show license`. `platforms/x230v2-28GS.md` §2 already held the same finding from the
  2026-10-09 triage, so the case was predictable.

## Next run: expected outputs
| step | command | expected on this build |
| --- | --- | --- |
| 0 | `ip m ?` (config) / `show ip m ?` | `% Unrecognized command` |
| 1 | `ip multicast-routing`, `ip mroute 10.38.215.64/27 vlan105`, `ipv6 multicast-routing`, `ip pim sparse-mode` | `% Invalid input detected at '^' marker.` each |
| 1 | `show ip mroute`, `show ip pim sparse-mode interface` | `% Invalid input detected at '^' marker.` |
| 1 | `show license` | Base License features without PIM / multicast routing; ACCESS licence |
| 2-3 | - | NOT RUN (depend on step 1) |

## Next run: scripts
- Existing tools fit: `tools/qmark.py` for the help probes and one `tools/ckcon.py` call for the refusals.
  The whole case is two device calls plus `rcdiff.py`; no new script is warranted.

## Next run: references
- `platforms/x230v2-28GS.md` §2, row "No multicast routing" (static-mroute cases UNSUPPORTED, T30403): read it
  at triage, then capture the refusal evidence in one call.
