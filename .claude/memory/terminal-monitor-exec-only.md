---
name: terminal-monitor-exec-only
description: AW+ `terminal (no) monitor` is EXEC-only and does NOT toggle; the "Command [terminal no monitor] failed" lines came from tools sending it at host(config)# or into a busy console — `end` first, or use console.py monitor_off()
metadata:
  type: feedback
---

Measured 2026-10-02 on tb470 u3 (IE520-sa, `awplus_main-20260923-20`):
- exec `terminal monitor` → `% Warning: Console logging enabled`, log mirrored to the console.
- exec `terminal monitor` a second time → **still ON**. It does not toggle (the Test Engineer
  suspected it did; the test showed otherwise).
- exec `terminal no monitor` → accepted silently (`logconf: Update log configuration`), OFF.
- config-mode `terminal no monitor` → `% Invalid input detected`, logged as
  `user.err … Command [terminal no monitor] failed`.

The Test Engineer had seen that failure "issued erroneously multiple times". The causes were:
- tools logging in at a parked `host(config)#` prompt and sending it straight away;
- exit cleanups typing it into a console still busy with a long command (2026-10-02,
  `ckyn.py` during a stack `boot system` file sync), where it queued and ran later in config mode;
- `bench-runner.agent.md` telling the tester "`terminal no monitor` + `end`", in that order.

**Why:** a failed `terminal no monitor` leaves log mirroring ON. It also puts a misleading
`user.err` in the DUT log, which a later reader takes for a fault.

**How to apply:**
- Always `end` FIRST, then `terminal no monitor`, and only once a prompt has come back.
- In code, call `console.Console.monitor_off()` / `set_monitor()` (tools/console.py, 2026-10-02).
  It sends a CR, gives up having typed nothing more if no prompt returns, `end`s out of config,
  then sends the command. Every `tools/` driver uses it.
- Never re-issue `terminal monitor` to turn it off.

Related: [[awplus-cli-confirmations-need-enter]], [[never-send-cli-help-through-a-cr-driver]].
