---
name: log-is-the-deliverable
description: The deliverable of a case is ONE final <id><suffix>.log + one .cfg per device, made only by /create-logs on request; every rule now lives in logged-output.md — this memory keeps only the why
metadata:
  verified: 2026-10-02
  node_type: memory
  type: feedback
---

**Every logging rule lives in `logged-output.md` at the repo root (2026-10-02).** That covers
the verdicts, the working logs, the `RESULT` line, the results list, the final template,
`/create-logs` and the group README. Read it; do not restate it here or anywhere else.

What this memory keeps is the *why*: Terrence's rulings in the order he gave them.

- **2026-08-18:** *"we dont need write-ups for everything, the .log is enough."* A per-case
  after-action is written only when asked for.
- **2026-09-22:** a group README verdict table, so a reader gets the true picture without
  opening every log.
- **2026-09-23:** *"ONE log file of the most RECENT run, no fluff or side-stories. just the
  outputs and proof it passed."*
- **2026-09-28 / 09-30:** the file name carries the verdict (`<id>.log` = PASS only), and the
  verdicts were redefined (PASS / FAIL / PARTIAL / UNSUPPORTED / NOT TESTED).
- **2026-10-02:**
  - The final log is built **only on request**, by `/create-logs`, from the tester's working
    logs, after the Test Engineer reviews the results list. The tester never writes it.
  - Each case gets its own folder holding the log plus one `<dev>.cfg` per device; a stack is
    one device.
  - Each run stands alone: *"the historical memories are for the agent, not the output."*
  - The template takes 38472's structure and 30142's per-step proof.

- **2026-10-19:** two rulings about *who the log is written for*.
  - *"the english is high level. We need to make sure a junior engineer who is non native
    english speaker should be able to understand these logs without having to read it twice or
    thrice."* Plain English is now a rule for every word **we** write (logged-output.md §4);
    device output still stays verbatim. The test: understandable on the FIRST read.
  - The header's `Run:` is **one short sentence**, and `Build:` must quote the DUT's own
    **`show system`** output in full. The tester must capture `show system` with its setup reads
    or `/create-logs` has nothing to quote — all ten cases of the 2026-10-16 campaign missed it
    for exactly that reason, and were left as they were because back-filling it would have been
    inventing a source.
  - Scope, in his words: *"for all the test that we run in the future by me or someone, not just
    my campaign or testbox but anyone who would be using this skills and tools and ask CK."*

- **2026-10-19, same session, a third ruling: the DUT's HEALTH is now part of every case.**
  He asked whether `show log` (crashes, kernel errors), `show reboot history`, memory leaks and
  CPU were checked during a run. **They were not.** `show reboot history` lived only in
  `/orient-dt` and `/wrap-dt` — once at session start, once at session end — and CPU and memory
  appeared nowhere in a tester's required workflow. Now every case reads
  `show reboot history`, `show exception log`, a filtered `show log` + `show log tail 150`,
  `show cpu` and `show memory` **twice**: with the setup reads and again after the last step.
  Both samples go in the working log; the final log carries a five-line `HEALTH:` block
  (logged-output.md §2 "Check the DUT's health" and §4). Four traps are written in beside it:
  AW+ logs **normal** events at `user.crit` so severity alone is not a fault; the framework's
  post-failure power cycle reads as `Unexpected System reboot`; the console wraps at 80 columns
  so a one-line match misses a split line; and **one case cannot prove a memory leak** — two
  samples show only a step change that did not come back.

**Why:** the final log is what the Test Engineer attaches to Zephyr. It must be the proof and
nothing else, and it must not be produced before a human has reviewed the verdicts.

**How to apply:** as a tester, keep a rich working log and send `RESULT`. As the sentinel, keep
the results list and end with the `/create-logs` prompt. Never write a final log unasked. Related:
[[campaign-measurement-discipline]], [[product-dirs-archive-to-old-test-runs]].
