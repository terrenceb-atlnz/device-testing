# T47226 process review -- platform-2026-10-09T0845
Reviewed 2026-10-12 by /create-logs from `agent-a591963d08f049547.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3.6 | 7 | 6,402 | 419,268 | 38 | 3.6 | 63 s | 12,822 chars |

Apportioned (../REVIEW.md, Method): 1/8 of the shared read-only batch (#26-#40) plus #28 and #30,
which served only this case. `case_tokens.py` gave this case 8 calls / 1,005,297 cache read because it
saw the batch's first group-dir call as T47226's start.

## Process taken
1. #26 one `tools/tb ckcon tb470 x230plat-1800 u0 115200` login, 12 commands for all eight read-only
   cases (show clock, show running-config, show version, ... show system, show clock) -> scratch `ro.out`.
2. #27-#29 read the capture back: markers, then show version to the end (10,219 chars), then lines
   340-466 (5,458 chars).
3. #30 repo-wide `grep -r 'Build name : x220'` to judge the x220 build name (40 s, 931 chars).
4. #31-#38 (shared) rcdiff README entry, eight `.cfg` via `rc2cfg.py`, scratch `loglib.sh`, working
   logs generated, one read back (#35), console tail, commits.
5. #39-#40 SendMessage loaded, one message with all eight RESULT lines.

## Wasted input
- #28: show version read back in full (10,219 chars) to grade a one-step "does it answer" case. A
  check of the first and last lines (`sed -n '/>>> show version/,+3p'` and the GPL line) was enough to
  grade; the full text belongs in the log, copied by script, not in the context.
- #30: a repo-wide grep across every log (40 s) to compare the build name with other campaigns. The
  answer could not go in the final log (another campaign) and is now in platforms/x230v2-28GS.md §1.

## Repetition
none found (the batch itself avoided eight logins).

## Accuracy risks
- **The Build name line reads `x220-awplus_main-20261008-57.rel`** on an x230v2 running
  `x230v2_28GS-awplus_main-20261008-57.rel`. The tester did not grade it as a failure because every
  earlier x230v2 log shows the same; that comparison is with other campaigns, so the final log states
  only the mismatch and leaves the re-grade to the Test Engineer (CAVEAT).
- The case has no step text and no expected result; PASS means "answers in full".

## Next run: expected outputs
| step | command | expected on this bench |
| --- | --- | --- |
| 1 | `show version` | first line `AlliedWare Plus (TM) 0.0.0 10/08/26 00:10:09` (build-dependent); `Build name : x220-awplus_main-<build>.rel`; last line `downloaded from: http://www.alliedtelesis.co.nz/support/gpl/awp.html`; no `% ` line |

## Next run: scripts
- `tools/cliplan.py` (proposed, ../REVIEW.md): `47226  show version  ^AlliedWare Plus \(TM\)  ^% `.

## Next run: references
- platforms/x230v2-28GS.md §1 "The build name says x220" (replaces #30).
