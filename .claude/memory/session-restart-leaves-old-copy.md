---
name: session-restart-leaves-old-copy
description: A VS Code Claude session restart can leave the OLD process alive on the same --resume id: two sentinels, two testers on one console (2026-10-07). Check ps before resuming; an unattended start goes in tmux with a one-shot cron.
metadata:
  type: feedback
---

2026-10-07, session 8733c1d4 (tb470 x230v2 follow-up): after a VS Code restart around 10:56, the
old `claude --resume=8733c1d4…` process kept running beside the new one. Both copies held a
sentinel, both resumed a bench-runner, and two testers drove u0 at once. 5700.2005.4 had to be
stopped and re-run (Test Engineer: "Stop it now, re-run"). It happened again at 14:59, and the old
copy's orphaned `sentinel.sh` had to be killed by PID.

**Why:** cron triggers and subagents live per process. Two processes on one session id means
everything the session does at a trigger happens twice, and nothing in the transcript shows it.

**How to apply:**
- Before resuming a tester, dispatching, or arming a sentinel after any restart, run
  `ps -eo pid,lstart,cmd | grep -- '--resume=<session-id>'`. More than one row: stop and ask the
  Test Engineer which copy to close. Never act from both.
- A run that must START unattended (after hours, [[reboot-heavy-runs-after-hours]]) or outlive the
  editor goes in a tmux session on the dev host: `tmux new -s test-mode`, `claude --permission-mode
  auto`, `/test-mode --resume <queue>`, with the hold and start steps written into the queue file.
  It arms a one-shot `CronCreate` for the start time. This worked 2026-10-07 (session
  device-testing-49, 18:01 start). The handing-over session deletes its own trigger so the run is
  dispatched once.
- A peer session stuck at an AskUserQuestion never reads its inbox. If its desktop can't be
  reached (device-testing-c7, 2026-10-07), it can't take a handover. Related:
  [[sentinel-kit-in-orient-dt]].
