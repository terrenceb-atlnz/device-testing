# platform-2026-10-27T0855 process review
Reviewed 2026-10-27 by /create-logs from agent-a512b95ab36fe7ece.jsonl (group 1 tester, T31863 + T31866).

## Token usage
| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T31863 | 32 | 64 | 37,863 | 3,408,363 | 21,894 | 32 | 871 s | 24,842 |
| T31866 | 18 | 36 | 20,201 | 2,452,336 | 14,683 | 18 | 985 s | 9,820 |
| overhead | 24 | 48 | 90,057 | 1,747,597 | 10,067 | 26 | 178 s | 64,266 |
| **total** | 74 | 148 | 148,121 | 7,608,296 | 46,644 | 76 | 2,034 s | 98,928 |

Wall time is mostly the four reloads (~168 s each) the case text requires.

## Overhead findings
- 64 KB of the group's 99 KB tool output was overhead reading rules and catalogues:
  - the queue file, 12 KB (`sed -n '15,104p;153,400p'`);
  - logged-output.md §1-§2, 15 KB (two `sed` ranges);
  - tools/README.md, 17 KB (two `sed` ranges).
  A short "tester digest" of logged-output.md §2 and the tools a manual-CLI case uses (ckcon, ckyn, ckreload, qmark, health, rc2cfg, rcdiff) would cut this to 3-4 KB per group.
- `tools/ckcase.py` was run first without `--db` (fails on the dev host), then `--help`, then with `--db`: 3 calls where 1 would do. The memory `ckdb-case-lookup-by-title` and the queue already give the dev-host db path.
- The first `tools/tb probe` call used `--outlet 0=3,1=4` and failed; the queue's Session facts give the working form `--outlet u0=3,u1=4`.

## Findings across both cases
- Start-job extraction from the console transcript was rebuilt by hand for each of the four reloads. A helper (`tools/startjobs.py`, proposed in 31863-review.md) would do it in one call.
- `tools/health.py` false DIRTY on boot-time lines (31866-review.md). It recurred in group 2 (T30403).
