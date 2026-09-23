---
name: atmf-recovery-residue-and-reboots
description: "An IE520 AMF node whose auto-recovery FAILED keeps residue until it reboots: it reads 'Special Link Not Present' with a Full vlink, writes no USB recovery file, and the master aborts its backup 'due to the node being in safe mode'. A SUCCESSFUL recovery reboots the node a second time."
metadata:
  type: project
---

Measured 2026-09-24 on tb470 (ATMF 38475 repeat, `IE520-sa`, build awplus_main-20260923-20).

**Residue of a failed recovery.** Run 1 (2026-09-23) ended with `Automatic node recovery
failed - user intervention required`. The node was then configured by hand, but it was never
rebooted. From then until its next reboot:
- `show atmf recovery-file` read `Special Link Not Present`, although its virtual link was
  Full / Forwarding.
- No `atmf_recovery_file` was written to its USB stick.
- On the master, `atmf backup now IE520-sa` printed `Backup successfully initiated`, and then
  the log read `ATMF backup: Aborted backup for node IE520-sa due to the node being in safe mode`.
- Meanwhile the node itself reported `Recovery State : None` and had no err-disabled ports.

One `reload` cleared all of it. After the reboot the node read `Special Link Present`, wrote
its USB recovery file, and the master's backup read `Good`. This happened once (n=1), but it
explained run 1's "candidate root cause".

**A successful recovery has two reboots.** The first is `atmf cleanup` itself. About 15 min
later the node logs `File recovery from master node succeeded. Node will now reboot`, and
reboots again. `Unable to remove recovery link` (user.err) is logged during a recovery that
succeeds, so it is not a failure signal.

**How to apply:**
- Before any AMF recovery or backup test, **reboot a DUT that has ever failed a recovery**.
  Then check its own `show atmf recovery-file`, and the master's log for "safe mode".
- A recovery watcher must survive the second reboot. Don't treat the master's
  `show atmf nodes` listing the node as proof it rejoined: a departed node lingers there. Watch
  the node's own `show log permanent | include atmffsd` until `succeeded` or `failed` appears.
- In `show atmf links`, a vlink row has no Link Status column. Match `vlink1\s+Uplink\s+Full`,
  not `Up`.

Related: [[ie520-master-ignores-remote-backup-server]], [[bench-scripts-stop-on-cli-errors]].
