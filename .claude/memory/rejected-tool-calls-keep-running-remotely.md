---
name: rejected-tool-calls-keep-running-remotely
description: "Rejecting or interrupting a Bash tool call does NOT kill an ssh command already dispatched to the testbox — it keeps running, changes device state and holds consoles. Verify and clean up after every interrupt."
metadata:
  node_type: memory
  type: feedback
---

Observed twice on tb470 on 2026-09-21, both times with real consequences.

**What the harness rejection means:** it stops *me* from receiving the output. It does **not**
signal the remote end. Anything already written to the ssh channel runs to completion on the
testbox.

**Incident 1 — device state changed after a rejection.** A script that was going to do
`stack 1 priority 1` then `reboot stack-member 3` was interrupted. Both commands had already
gone out. Member 1's priority really was changed and member 3 really was rebooted
(`show reboot history` -> `Expected / User Request`). I had told Terrence the bench was
untouched, which was wrong until I re-checked.

**Incident 2 — a "rejected" call held a console for minutes.** An x230 provisioning probe was
rejected; `ps` later showed it still alive at 3m25s, holding `/dev/ttyUSB1`. The symptom was a
*different* script reading empty bytes from `/dev/u5` — two readers on one port, which looks
exactly like a dead console.

**How to apply — after ANY rejected or interrupted tool call that touched the bench:**
1. `pgrep -af python3` / `ps -eo pid,etime,cmd` on the testbox. The leftover may be a bare
   `python3 -` from a heredoc, so a pattern match on the script name finds nothing — check
   elapsed time and the parent `bash -c` line.
2. `for d in /dev/ttyUSB*; do fuser $d; done` to find held consoles.
3. Apply `stty -F <tty> -hupcl` to every port **before** killing, so the close does not drop
   DTR and BREAK the device ([[awplus-cli-confirmations-need-enter]]).
4. Re-read actual device state before telling Terrence anything is unchanged. Never report
   "nothing happened" from the rejection alone.

Related: [[never-send-cli-help-through-a-cr-driver]] — the other way a command runs when you
did not mean it to.
