---
name: ckdb-case-lookup-by-title
description: "ck.db IS reachable — at /home/terrenceb/claude/Test-cases/ask-ck/db/ck.db, not your own lab home. CORRECTED 2026-10-16: `zephyr_cases` IS keyed on the AWPTCM-T<id> directly — use tools/ckcase.py. The title-join on testlink_cases is the LEGACY fallback, not the first move"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 87016784-78a9-4107-8bc9-8db7a57a86ad
  modified: 2026-10-07T20:22:36.033Z
---

**Where it is.** `/home/terrenceb/claude/Test-cases/ask-ck/db/ck.db` — 465 MB, mode
`-rw-r--r--`, on the lab NFS (`tbhome.st.atlnz.lc:/home`), so any testbox can read it.
**It is NOT in bidhanc's lab home**: `~/claude/` there holds only `device-testing`, with no
`Test-cases` checkout. Measured 2026-10-07, after a whole campaign was drafted from case titles
alone on the false conclusion that ck.db was unreachable. Checking your own `~/claude` proves
nothing about the lab — check the other homes.

**How to read it.** tb277 has **no `sqlite3` binary**; use Python's module with the read-only URI
(never open the live db read-write while the CK server runs):

```python
import sqlite3
c = sqlite3.connect("file:/home/terrenceb/claude/Test-cases/ask-ck/db/ck.db?mode=ro", uri=True)
```

The dev host cannot reach it — it mounts only bidhanc's home — so run this **on a testbox**.

**🔴 CORRECTED 2026-10-16 — THE FIRST MOVE IS `zephyr_cases`, NOT A TITLE JOIN.** This memory
previously said the AWPTCM numbers "do NOT exist in ck.db". **That is wrong, and following it
wastes a lookup on every case.** ck.db has a **`zephyr_cases` table keyed on `key` = the AWPTCM
id exactly as the Test Engineer writes it** (`AWPTCM-T43870`), holding `objective`,
`precondition` and `steps`. Use **`tools/ckcase.py <KEY>`**, which reads it directly; it was
built and used across the whole 2026-10-16 campaign (10 cases) and settled the authored-text
question for every one of them.

What the original note got right, and what it is still for: **`testlink_cases` is the LEGACY
`AWP-<nnnn>` corpus and is NOT keyed on the AWPTCM number.** When a case has no `zephyr_cases`
row, fall back to joining `testlink_cases` on `title` (`ckcase.py --title`). Both tables matter;
the order was the error.

**The legacy title join, when you need it.** Measured 2026-10-07, all five checked titles were unique in
`testlink_cases` (verify per lookup — uniqueness is not guaranteed, and derived duplicates exist,
e.g. `AWP-17615  "AWP-5316:CLI show mirror interface direction set to transmit"`):

| the Test Engineer's id | ck.db `id` / `internal_id` | title (the join key) |
| --- | --- | --- |
| AWPTCM-T44967 | AWP-5316 / 43287 | CLI show mirror interface direction set to transmit |
| AWPTCM-T44968 | AWP-5317 / 43290 | CLI show mirror interface direction set to receive |
| AWPTCM-T44969 | AWP-5318 / 43293 | CLI show mirror interface direction set to both |
| AWPTCM-T44973 | AWP-6299 / 50353 | CLI Remove mirror interface |
| AWPTCM-T44974 | AWP-25167 / 453292 | Mirror set to interface none |
| AWPTCM-T44990 | AWP-8657 / 62263 | ACL: Named Hardware on port copy-to-mirror IP |
| AWPTCM-T44991 | AWP-8655 / 62257 | ACL: Named Hardware on port copy-to-cpu IP |

**The tables that matter.** `testlink_cases` (21,620 rows): `id, internal_id, title, suite_top,
suite, summary, preconditions, importance, status, steps, steps_text, content_sha1`.
`atp_tests` (10,157 rows): `tid, suite_id, suite_name, test_set, case_id, description,
reference, past_crs, current_crs, log_analysis, is_functional, content_sha1`. `cli_commands` is
the CLI reference ([[read-the-transcripts-before-driving-hardware]]).

**`steps_text` can be empty, and then `summary` carries the real intent.** `Mirror set to
interface none` (AWP-25167) has no steps at all; its summary is what defines the case —
*"External issue CR56263 … Can be used in conjunction with copy-to-mirror ACL … Make sure system
is stable (was NSM crash)"*, i.e. a crash regression test, not a "turn the mirror off" test.
This is the `num_steps = 0` category from [[ie520-awptcm-campaign-2026-09-22]]: read `summary`
and `preconditions` before concluding a case has no definition.

**Why it matters:** drafting steps from a case title is a reconstruction, and it gets cases
wrong in ways that survive into the deliverable. On 2026-10-07 it produced three wrong drafted
steps and one inverted expectation across five cases — each caught only by checking against the
DUT. One query would have avoided all of them. Related: [[log-is-the-deliverable]],
[[awplus-cli-wiki-on-the-share]] (the wiki has no IE520/x960 pages; ck.db does have the cases).

**How to apply:** before drafting or grading any case, run **`tools/ckcase.py <AWPTCM-T…>`**
first and quote whatever authored text it returns in the queue file and in every final log; only
if that is empty, fall back to the `--title` join on `testlink_cases`. **An empty result is
itself a finding to record** — five of the ten cases in the 2026-10-16 campaign had no authored
step text at all (one had a steps array holding a single completely empty step), and each log
says so explicitly rather than implying the steps were authored. If the lookup is genuinely impossible, say so explicitly in the log, as that
campaign did — but check the other lab homes first.
