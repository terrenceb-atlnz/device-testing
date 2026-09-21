---
name: ssh-pgrep-watchers-self-match
description: "A background watcher built on `ssh tb470 'pgrep -f <pattern>'` matches its OWN bash -c wrapper, so it reports \"still running\" forever and the completion notification never fires. Use a sentinel file instead."
metadata:
  node_type: memory
  type: feedback
---

Cost a parallel session 13.6 hours of idle time on 2026-09-21: it finished the work at 17:29
and sat waiting until the next morning for a watcher that could never fire.

**The bug.** The idiom is

```bash
until ! ssh -o BatchMode=yes tb470 'pgrep -f provrel.py'; do sleep 20; done
```

`ssh` runs the remote command as `bash -c 'pgrep -f provrel.py'`, so that wrapper's own cmdline
**contains the pattern**. `pgrep -f` matches it, the remote command succeeds, `! ssh` is false,
and the loop spins forever at 20s intervals. The script it was watching had exited minutes in.
Three such loops were still alive after 13.6 h, 14.9 h and 22.2 h.

The `[p]rovrel` bracket trick does **not** save you either — if the same command line contains
the plain string anywhere else (an `echo "provrel:"` label, the `RUN=` path, the log filename),
pgrep matches that instead.

**How to apply.**
- Prefer a **sentinel**: have the remote script `touch /tmp/<run>/done` on exit, and poll
  `ssh tb470 'test -f /tmp/<run>/done'`. Nothing to self-match.
- If you must pgrep, put it in a **script file on the testbox** and run that by path, so the
  pattern is not in any cmdline; or pipe a full `ps -eo pid,etime,cmd --no-headers` back and
  `grep` it **locally** — the filter never appears in a remote process.
- Verifying "is it still running?" has the same trap. `ssh tb470 'ps -eo pid,etime,cmd --no-headers' | grep -E 'foo' | grep -v 'ps -eo'`
  is the check that actually answers it.
- Cover the failure path: a watcher that only exits on success is silent through a crash, and
  silence looks identical to "still working".
- Symptom to recognise: a session idle for hours with its last message saying "the background
  task will notify me". Check `ps -eo pid,lstart,etime,cmd | grep 'until ! ssh'` on the dev host
  before assuming the remote job is slow.

Related: [[rejected-tool-calls-keep-running-remotely]] — the mirror image, where a process you
believed dead is very much alive.
