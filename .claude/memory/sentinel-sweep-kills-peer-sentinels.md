---
name: sentinel-sweep-kills-peer-sentinels
description: "A sentinel ARMING sweep that kills EVERY sentinel.sh on the host kills OTHER sessions' watchers too: 2026-10-21 13:25 the tb101 and tb470 sessions killed each other's sentinel twice in 30 s. Filter the sweep by THIS session's SCRATCH path."
metadata:
  type: feedback
---

**What happened (2026-10-21 13:25, dev host terrenceb-dl).** Two `/test-mode` sessions ran at once on the same
host: this one (tb101, T17584) and a tb470 campaign (session `4ba10cb2…`). Each used the kit's ARMING step
"kill every sentinel.sh pid found". My Monitor expired at 13:25:02 (its sentinel got SIGTERM with it); my
re-arm sweep at 13:25:11 found two `sentinel.sh` pids and killed them — they were the tb470 session's. That
session re-armed at 13:25:3x and ITS sweep killed my fresh sentinel (pid 638188) at 13:25:32, so my Monitor
"stream ended" 15 s after arming. `sentinel.life` shows it: START 13:25:17, SIGTERM 13:25:32.

**Why:** the wrapper `bash -c … SELF=1 BOX=<tb> … SCRATCH=<path> … sentinel.sh` carries the owning session's
scratchpad, but the sweep matched only `sentinel.sh`.

**How to apply:** sweep only wrappers whose command line contains YOUR `$SCRATCH` (`grep -E "$PAT"
$SCRATCH/ps-now.txt | grep -F "$SCRATCH"`) and the `bash … sentinel.sh` children of those wrappers. A
`sentinel.sh` with another SCRATCH is a peer's: leave it. Also: an expired Monitor does NOT always take its
sentinel.sh with it (13:25 the 12:55 one survived its Monitor), so the own-session sweep is still needed.
Fixed in `cron-trigger.template.md` ARMING a/b and orient-dt §10 (2026-10-21).
