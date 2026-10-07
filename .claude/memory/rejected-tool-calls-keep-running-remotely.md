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

**Incident 3 (2026-09-23) — it ran to the end and collided with Terrence's own session.** He
rejected a config script (standalone `sa3` rebuild + stack `no shutdown` + `write`) because he
needed the console for his boss. It had already started: 82 s later `fuser` showed my
`python3` AND his `minicom` both on `/dev/ttyUSB7`, and every command, including the `write`,
had gone out. Its reply was stolen by minicom (`#-s`), so completion had to be verified
afterwards. Killed by PID within ~90 s of the rejection. Then, killing his minicom on request:
**minicom ignored SIGTERM**, and SIGHUP is what closed it (after `stty -F <tty> -hupcl`).

**Incident 4 (2026-09-23, 14:51): rejected while he switched permission modes, and it ran
anyway.** The master-side script (repoint the AMF backup server, add a knownhosts entry) was
rejected, but it had already been dispatched. Found 1:33 later, it had changed config (a route
removed, server 1 replaced), was holding `/dev/ttyUSB1`, and had left the master at a
`(yes/no)` prompt. It then died on its own: its stdout was the dead ssh channel, so the next
`print()` raised BrokenPipe. That skipped the log write for its last step, so the console state
had to be read fresh (bare CR, then `no`). **Scripts that `print()` before writing their log
lose the step that matters. Write the log line first.**

**Incident 5 (2026-10-08, 12:3x): a rejected read held the stack master's console under Terrence's minicom.**
A read-only `ckcon` read of `/dev/u5` at 115200 was rejected because he was about to fix the stack bauds. About 45 s
later `precheck` showed my `python3` (pid 338371) AND his `minicom` both on `/dev/ttyUSB1`. Killed by PID; `fuser` then
showed minicom only. A second rejected call the same afternoon (a `show log` on u0) had already exited when checked.
Step 0 below caught both; `bench_probe precheck --consoles <list>` is the one-call version of steps 1–2.

**How to apply — after ANY rejected or interrupted tool call that touched the bench:**
0. Do this FIRST, in the very next call, before replying: a rejection often means Terrence
   is about to use the hardware himself, so a leftover process means two readers on his port.
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
