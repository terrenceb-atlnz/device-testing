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

**Why:** the final log is what the Test Engineer attaches to Zephyr. It must be the proof and
nothing else, and it must not be produced before a human has reviewed the verdicts.

**How to apply:** as a tester, keep a rich working log and send `RESULT`. As the sentinel, keep
the results list and end with the `/create-logs` prompt. Never write a final log unasked. Related:
[[campaign-measurement-discipline]], [[product-dirs-archive-to-old-test-runs]].
