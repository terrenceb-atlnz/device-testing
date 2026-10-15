---
name: sentinel-replays-shared-nfs-logs
description: "sentinel.sh reads /home/st-art/pytest-create/*/*/ on the SHARED NFS home, so a first arm replays every box's old logs; let one pass baseline the offsets at EOF, then re-arm"
metadata:
  node_type: memory
  type: reference
---

Measured on tb277, 2026-10-15.

**What happened.** The first arm of the one-session sentinel delivered roughly **11 MB of stale
log content**, including logs from **tb470**, a box this session had nothing to do with. The feed
was unreadable and the real console events were buried.

**Why.** `sentinel.sh` tails `/home/st-art/pytest-create/*/*/`, which lives on the **shared NFS
lab home**, not on the box. Every testbox writes there. With no recorded offsets, a fresh arm
treats every file's whole history as new.

**The fix.** Stop the Monitor, let one pass run so it baselines every remote offset at EOF, then
re-arm. From then on only genuinely new lines arrive. Budget one throwaway arm at the start of a
campaign rather than trying to filter the output.

**Do not** try to narrow it by grepping the feed for the current box — the paths do not reliably
carry the box name, and a filter that silently drops lines is worse than a noisy first pass.

Arming hygiene that goes with this ([[sentinel-kit-in-orient-dt]]): never arm on top of a stray.
Snapshot `ps -eo pid,cmd --no-headers` to a file first, then grep **that file** with an assembled
pattern (`PAT="sentin""el.sh"`) so the grep cannot match itself, kill what you find by PID, and
remove the heartbeat before re-arming.

Related: [[sentinel-session-keeps-long-runs-moving]], [[ssh-pgrep-watchers-self-match]].
