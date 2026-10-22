---
name: test-mode-takeover-after-dead-session
description: A /test-mode sentinel session that dies takes its bench-runner with it mid-case; take over with /test-mode --resume after proving no copy lives, and rebuild the uncommitted rows from the case's row files
metadata:
  type: project
---

**2026-10-22, tb470 x230 campaign 2026-10-22T1320.** Terrence ran /test-mode from a second VS Code session
(`device-testing-43`). It exited ~14:00 mid T47209; its bench-runner subagent died with it after row R6.
`run1.log` held only R0-R1 (written 13:53); NOTHING of the case was committed. R2-R6 survived only because
the case's `work/row.sh` wrote one `row-<label>.out` per row INTO THE REPO. Terrence: "takeover the session
subagent running tests on the x230, fire up a sentinel".

**How it was taken over (worked, 14:03-14:04):**
1. `ListAgents` no longer listed the peer; `ps -p <its socket pid>` empty; only this session's claude
   process in the repo ([[session-restart-leaves-old-copy]]); `tools/tb precheck` CLEAR and `tools/tb ps`
   empty, so nothing of the dead tester was still on a console.
2. `/test-mode --resume <queue>` in THIS session: arm the Monitor + 15-min cron on yourself, then dispatch a
   fresh bench-runner with a SHORT brief: what died, the untracked files, "verify the live device state
   first (read-only)", named queue line ranges, and "write R2-R6 into run1.log from the row files, label the
   source, re-run any row whose AFTER reads are missing".
3. The dead tester's transcript is findable for /create-logs' review:
   `grep -l <its box scratch name> ~/.claude/projects/<slug>/*/subagents/*.jsonl` (newer than the start).

**Why:** a subagent cannot be adopted by another session; only its files survive. **How to apply:** a tester
writes `run<N>.log` per row (logged-output.md §2) and keeps per-row raw output in the case's `work/`, never
only in the box's `/tmp`. Run multi-group campaigns from tmux (test-mode §1 step 3). Related:
[[sentinel-session-keeps-long-runs-moving]], [[sentinel-kit-in-orient-dt]].
