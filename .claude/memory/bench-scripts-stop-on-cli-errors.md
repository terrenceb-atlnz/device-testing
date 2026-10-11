---
name: bench-scripts-stop-on-cli-errors
description: "A multi-step console script must STOP on any `% ` error line and GATE each dependent step on the previous step's proven success. Mine carried on past `% ATMF requires AMF-MASTER-X license` and demoted the only AMF master, leaving the network masterless."
metadata:
  node_type: memory
  type: feedback
---

2026-09-23, tb470. The script was meant to make the x230 AMF master and then demote the
IE520 stack. The x230 answered `% ATMF requires AMF-MASTER-X license`. My `do()` helper only
stopped on unexpected `(y/n)` prompts, so it went on: `no atmf master` on the stack left the
AMF network with **no master for ~4 minutes**. The stack saw 2 nodes and the x230 saw only
itself, until I restored `atmf master` on the stack. Data paths were unaffected, but any AMF
test running then would have measured an outage I caused.

**Why:** AW+ reports a refused command as a `% ...` line and returns a normal prompt. To a
prompt-driven driver, a refusal therefore looks exactly like success. The damage lands on the
NEXT step, which assumed the first one took.

**How to apply:**
- Every config helper raises on `^\s*% ` unless that call passes `allow_err=True` for an
  expected error.
- When step B is only safe because step A worked (demote after promote, remove the old path
  after the new one is up, delete the vlink after the atmf-link is Full), **read the state A was
  meant to create** (`show atmf` → `Role : Master`, `show atmf links` → `Full`) and stop if it
  isn't there.
- The rebuilt pattern that ran cleanly the same day: promote the 4050 → gate on
  `Role : Master` → only then demote the stack.

Related: [[awplus-cli-confirmations-need-enter]] (the prompt side of the same "the CLI
answered, but not how you assumed" problem), [[rejected-tool-calls-keep-running-remotely]].

## 2026-10-09, tb277 — the same failure from the other end: I HID the `% ` line

Twice in one session I ran a config driver as `cfg.py ... >/dev/null 2>&1` inside a loop, to
keep the output readable. Both times the device refused a command and I never saw it:

- `% This access-list is currently attached to an interface so cannot be edited.` — three ACL
  entries were silently not added, and the next measurement read the OLD rule and looked like a
  sensible result.
- `% Invalid input detected at '^' marker.` on `access-class 1` under `line vty` (AW+ uses the
  global `vty access-class`) — four test rows in a row showed "no effect", which I nearly wrote
  up as the feature not working.

The driver was behaving correctly: `cfg.py` DID stop and DID return non-zero. I had thrown the
evidence away, and in a loop the exit code went to the loop, not to me. **The symptom is always
the same: a device that silently did not change, and a measurement that therefore measures the
previous state.**

**How to apply:**
- **Never redirect a config driver's stdout to /dev/null.** Filter it (`| grep -E '>>>|%'`) if it
  is noisy, but never discard it. Shows can be quiet; configuration cannot.
- In a loop, a driver's exit code is NOT seen — check it explicitly or keep the output.
- When a measurement says "no effect", **re-read the config before believing the feature is
  broken**. Both times above, one `show` would have shown the change was never applied.

Related: [[never-send-cli-help-through-a-cr-driver]].
