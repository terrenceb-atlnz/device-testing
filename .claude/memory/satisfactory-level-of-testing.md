---
name: satisfactory-level-of-testing
description: "Test Engineer 2026-10-08: the case's step text is the FLOOR, not the ceiling — a show-command case must also prove removal and reboot persistence; grounded in the feature guide + TPS + test strategy + own knowledge"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e2852736-283a-4261-9133-f7c5eb813935
  modified: 2026-10-08T03:14:05.177Z
---

**Test Engineer, 2026-10-08, verbatim:** *"For any testing use the feature overview guide,
review Software TPS, review test strategy, use your knowledge and perform a satisfactory level
of testing. For example, when the test case is show commands, test whether config persists after
reboot, whether you can remove the command and is removed from the running configuration etc."*

**The four inputs to every case** (the documents and how to fetch them:
[[review-feature-docs-before-testing]], [[lab-wiki-reachable-from-a-testbox]]):
feature overview guide · Software TPS · test strategy · your own knowledge of the feature.

**The step text is a floor, not a ceiling.** A TestLink case says the minimum; it was written
for an engineer who would naturally also check the obvious neighbours. Default depth for any
configuration or show case, beyond the literal step:

1. **Baseline first, feature OFF** — the control that makes everything after it readable.
2. **The literal step**, with positive proof (something only visible if the feature works).
   Absence of an error is never proof.
3. **Removal** — `no <command>` is accepted AND the line is gone from `show running-config`.
   Diff against the pre-case copy; residue is a finding.
4. **Persistence across reboot** — write it, reload, confirm it is still there and still
   working. This is the check the step text almost never states and the one that finds bugs.
5. **Re-apply / idempotence** — applying twice, or changing one parameter in place.
6. **Negative and non-matching traffic** — the case's inverse, and traffic the feature should
   NOT touch (an IP ACL must not affect ARP).
7. **The TPS's named risk areas for that feature** — e.g. on the x960-56YSQ's Falcon silicon,
   ACL/QoS TCAM contention.

**Two standing orders this interacts with, both resolved by this instruction:**
- *"Nothing is written to startup-config unless the case requires it"* (STANDING-ORDERS §1) —
  a persistence check **does** require it. Write it, verify, then restore.
- A reboot on a netbooting DUT with empty flash reloads from the boot server and the running
  config is lost unless saved; confirm `show boot` reads `(file exists)` for the boot config
  first (orient-dt §1).

**Why:** the campaign is 300+ cases spanning multicast, routing protocols and much more
(Test Engineer, 2026-10-08). At that scale a case graded only against its literal sentence
leaves defects undiscovered and the coverage is "completed in name only" — the exact risk the
x960-56YSQ test strategy names. Depth has to be the default, not a per-case decision.

**How to apply:** at triage, write the extra checks into the queue file as numbered steps of the
case, so the tester runs them as part of the case and the final log shows them as STEPs with
their own verdicts. Where a depth check cannot run on the bench, say so as a `CAVEAT:` in the
log rather than silently dropping it ([[campaign-measurement-discipline]]).
