---
name: reboot-heavy-runs-after-hours
description: Repeated PDU power-cycles / reloads on tb470 are audible and distressed the office (2026-10-07); a colleague stopped the run. Schedule reboot-heavy suites after hours.
metadata:
  type: feedback
---

2026-10-07: calanm opened minicom on our u0 at 14:53 and stopped 5700.2005.5 *"at the behest of
those around him, the automated rebooting was causing distress due to the noise"* (Terrence).
The 5700 bootloader suite power-cycles the x230 via the PDU every few minutes for hours. Terrence's
answer: *"queue the test again to start at 6pm and watch it until its done"*.

**Why:** the bench sits among people; fan spin-up on every power cycle, for hours, is noise they
cannot escape, and they will stop the run themselves, which confounds it.

**How to apply:** at triage, estimate how many reboots a group causes. For a reboot-heavy group
(the 5700 suite, failover/reload campaigns), ask whether to run it during office hours or after hours,
and don't launch a new reboot-heavy case into office hours without asking. A console taken mid-run by a
colleague may be someone stopping the noise, not someone wanting the device: say so when
surfacing it. Related: [[shared-testbox-console-occupancy]], [[sentinel-session-keeps-long-runs-moving]].
