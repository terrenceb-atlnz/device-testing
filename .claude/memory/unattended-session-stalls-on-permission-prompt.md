---
name: unattended-session-stalls-on-permission-prompt
description: "An unattended tmux sentinel finished the overnight run, then sat 11 h on a permission prompt (rm of a root-owned symlink), so its results post, /tftproot note and /wrap-dt never happened. Keep unattended post-run steps to commits; leave deletions and root-owned files to the Test Engineer."
metadata:
  node_type: memory
  type: feedback
---

Observed 2026-10-07/08, tb470 x230v2 5700 follow-up (queue `tb470/x230v2-28GS/CAMPAIGN-QUEUE-2026-10-07T0817.md`).

The tmux `/test-mode` session (device-testing-49, `--permission-mode auto`) ran its bench-runner overnight, and the
tester finished cleanly at 01:28 (2005.5–.8 PASS, group restore done, all committed). The sentinel then started the
queue's "when the group restore is done" list with `rm x230v2-28GS/bootloader-6.2.40/current_test.log`, a **root-owned**
symlink the framework had left in the repo. That tool call never returned: it was a permission prompt nobody was there to
answer. Everything after it on the list (post the results list, give Terrence the `sudo rm /tftproot/…` line, `/wrap-dt`)
never happened. The next session found it at 11:2x by reading that transcript's tail: the last entry was a `tool_use` with
no result, followed only by queued Monitor/cron events. The session had exited by 13:0x.

**Why it matters:** the run's *results* were safe (per-case commits), but the closing records were not, and nothing
signalled the stall. The sentinel was the thing that stalled, so no sentinel caught it.

**How to apply:**
- In an unattended end-of-run list, put the results post and the commit FIRST. Put anything that can prompt LAST (an
  rm/mv of a file you did not create, anything root-owned, anything outside the repo), or hand it to the Test Engineer
  as a line in the results post instead of doing it.
- When checking on an unattended session, read the tail of its transcript (`~/.claude/projects/<slug>/<id>.jsonl`). A
  final `tool_use` with no `tool_result` after it is a pending prompt, not a quiet session.
- Related: [[session-restart-leaves-old-copy]], [[sentinel-session-keeps-long-runs-moving]].
