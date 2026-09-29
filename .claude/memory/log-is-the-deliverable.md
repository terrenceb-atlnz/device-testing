---
name: log-is-the-deliverable
description: For lab test runs the per-case `<case-id>.log` IS the deliverable — do NOT write an after-action-<id>.md for every test; produce a write-up only when Terrence asks for one
metadata:
  verified: 2026-09-10
  node_type: memory
  type: feedback
---

Terrence, 2026-08-18, after a run of five IE520 stack test cases: *"we dont need write-ups
for everything, the .log is enough."*

So the default deliverable for a hardware test case is a well-structured
`<case-id>.log` in the run directory — nothing else. An `after-action-<id>.md` is written
**only when explicitly requested** (as it was for 17688, which was a multi-round defect
investigation worth summarising).

**Why:** the `.log` already carries the whole evidence chain — config applied, commands
issued, raw device output, controls, measurements and verdict. A second document restates
it in prose and is work that was not asked for. This is the same over-production failure as
[[autonomous-judgement-divergence]]: producing artefacts on my own initiative rather than
on request.

**How to apply:** write results into the case `.log` as the run proceeds, with the same
rigour a write-up would have had — headline verdict, per-step results, the control that
makes each result interpretable, and any measurement traps hit along the way. Then *offer*
a write-up in a sentence rather than producing one. When asked for one, write it.

**CAMPAIGN ADDITION, 2026-09-22.** For a multi-group campaign the per-case `.log` still is
the deliverable, plus **one `README.md` per group directory** — a verdict table, the split of
PASS vs UNMEASURED *with the reason for each*, and the bench limits that capped anything. That
is the difference between "Authentication: 1 PASS / 6 UNMEASURED" (which reads like failure)
and a headline that says MAC-auth, web-auth and 802.1X were each proven end to end and the
cases are blocked on TACACS+ and port count. A reader should get the true picture without
opening every file. A campaign-level pointer memory is worth writing too:
[[ie520-awptcm-campaign-2026-09-22]]. Grading rules: [[campaign-measurement-discipline]].

**TIGHTENED 2026-09-23 (Terrence, ATMF 38474/38475):** *"Please ensure that the end-result of
these is ONE log file of the most RECENT run, no fluff or side-stories. just the outputs and
proof it passed."* So:
- **One `<case-id>.log` per case, holding the latest run only.** A repeat REPLACES the earlier
  run's log; git history keeps the old one.
- Its content is the **step outputs and the proof of the verdict**: the case steps, the
  commands, the device output that shows each step's result, and the verdict.
- **Leave out the side-stories**: setup detours, blocked approaches, prior-run comparisons,
  infrastructure findings. Those go in the session handover or a memory.
- **Raw console captures** (`*-raw.log`, `console-*.log`) are working files. Write them to
  tb470 `/tmp/ckorient/work/`, not the run directory, and never commit them.

This probably generalises to every lab case; apply it by default unless he asks for more.

Note this **qualifies** the `orient-dt` skill's §8 line that "the deliverable convention
is `after-action-<suite>.md` in that run's directory" — that still holds for a **campaign**
(a whole suite, or an investigation spanning many rounds), but not for each individual test
case. Related: [[user-prefers-manual-ui-testing]] — the same preference for less
scaffolding and fewer unrequested artefacts.

**NAMING ADDITION, 2026-09-28 (Terrence).** Still one log per case, but **the file name states
the outcome**: `<id>.log` is reserved for a run that explicitly PASSED; anything else is
`<id>-fail.log`, `<id>-partial.log` or `<id>-unsupported.log` (was `-skip`, retired 2026-09-30), with as much evidence as possible of what
was tried and what went wrong. The agent that judges the run names the file. A re-run replaces
the file under the new name (`git mv`). Full text: `STANDING-ORDERS.md` §2 at the repo root.

**VERDICTS REDEFINED, 2026-09-30 (Terrence).** A platform gap is UNSUPPORTED
(`<id>-unsupported.log`). A case with UNSUPPORTED steps or TestCases inside is still a PASS. FAIL
means it ran unsuccessfully, or the platform prevented it from running. PARTIAL means it was
unable to run (physical or other misconfiguration, a script error), with no FAIL condition met.
A case never attempted is NOT TESTED and gets no log. `-skip.log` is retired. Applied the same
day: 22653 and 22654 went PARTIAL → PASS (their only non-passing steps were PoE, which the
IE520 lacks), and 33234-skip became 33234-unsupported.
