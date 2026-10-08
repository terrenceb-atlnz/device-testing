---
name: ckdb-case-lookup-by-title
description: "ck.db IS reachable — at /home/terrenceb/claude/Test-cases/ask-ck/db/ck.db, not your own lab home; AWPTCM-T<id> numbers do NOT exist in it, so cross-reference a case by its TITLE in testlink_cases"
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

**🔥 THE IDs DO NOT MATCH, AND THAT IS THE WHOLE TRAP.** A case called `AWPTCM-T44967` has
**no row anywhere in ck.db under that number**. ck.db keys `testlink_cases` on `id` =
`AWP-<nnnn>` plus a separate `internal_id`. Searching for the AWPTCM number returns nothing and
reads exactly like "the case is not in the database".

**Join on `title` instead.** Measured 2026-10-07, all five checked titles were unique in
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

**How to apply:** before drafting or grading any case from its title, look the title up in
`testlink_cases` and quote the real `steps_text` / `summary` in the queue file and in every
final log. If the lookup is genuinely impossible, say so explicitly in the log, as that
campaign did — but check the other lab homes first.
