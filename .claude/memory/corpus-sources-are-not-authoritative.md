---
name: corpus-sources-are-not-authoritative
description: "Test Engineer 2026-10-08: ck.db cases, prior run logs and ART suites can all be WRONG — check what correct behaviour actually is against the RFC/standard and your own knowledge before testing or grading"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e2852736-283a-4261-9133-f7c5eb813935
  modified: 2026-10-08T03:31:18.403Z
---

**Test Engineer, 2026-10-08, verbatim:** *"You need to remember that the knowledge you are
basing off from ck.db or previous execution history or even ART might sometime be inaccurate, so
you will have to use your general knowledge, or even look at the RFC documents to make sure what
you are testing is accurate and sufficient."*

**The evidence hierarchy, strongest first:**

1. **The standard** — RFC, IEEE 802.x. What the protocol is actually required to do. This is the
   only source that cannot be stale.
2. **The product spec** — the Software TPS and the Feature Overview guide
   ([[review-feature-docs-before-testing]]). What THIS product claims to do.
3. **The DUT** — what it actually does. The only source for real behaviour.
4. **The corpus** — ck.db `testlink_cases`, prior campaign logs, ART suites. These suggest
   *what to check*. They never establish *what is correct*.

**Why the corpus is weak, measured:**
- `testlink_cases` steps are terse, decades old in places, and sometimes describe a different
  platform's behaviour. T44992's steps demand a LAG straddling stack members against a
  standalone DUT.
- A case title alone is a reconstruction: drafting from titles on 2026-10-07 produced three
  wrong commands and one inverted expectation in five cases ([[ckdb-case-lookup-by-title]]).
- ART CR history is per-platform. The x960-56YSQ test strategy says it outright: *"ART on
  another platform proves nothing about this"* — the ACL suite's CRs were raised on FS980 and
  GS970EMX, different silicon from the DUT's Marvell Falcon.
- Prior run logs record what a previous session concluded, including its mistakes.

**How to apply:**
- Before testing a feature, state what the standard requires, from your own knowledge, and check
  the RFC where behaviour is subtle (timers, election, TLV contents, flag semantics, error
  cases). Fetching an RFC needs no lab access.
- When a corpus step contradicts the standard or the feature guide, **test the correct behaviour
  and record the discrepancy** in the working log. Do not quietly follow the corpus, and do not
  quietly ignore it.
- Cite the authority in the final log's step conclusion — "RFC 4541 §2.1.1 requires …" reads very
  differently from "the case says …", and it is what makes a FAIL defensible.
- "Sufficient" is as important as "accurate": the step list being complete is a judgement you
  own, per [[satisfactory-level-of-testing]].
