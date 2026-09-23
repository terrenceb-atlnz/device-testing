---
name: act-on-terrence-stated-live-faults
description: When Terrence reports a live bench fault he caused or can see (e.g. "there's definitely a loop"), fix it immediately — don't spend a read-only verification pass first
metadata:
  type: feedback
---

2026-09-23: after Terrence cabled two parallel stack↔standalone links with RSTP off, I started a
read-only check for a loop. He rejected it: *"theres definitely a loop. dont bother checking, just
program the LAG"*. Same session he asked me to run `findme 5` "literally" and I had instead
expanded it to a 5-minute `findme member 2 timeout 300`.

**Why:** a live loop is doing damage every second; his first-hand observation of the physical bench
is better evidence than a probe, and the probe itself is slow through a storm.
**How to apply:** when he states a live fault or gives a literal command, take the fix/command as
given. Break a loop first (shut one leg), then configure. Verify *afterwards*, not before. This
narrows, not replaces, "verify facts yourself" — that still applies to records and assumptions.
Related: [[lacp-passive-hides-links-from-stp]], [[rejected-tool-calls-keep-running-remotely]].
