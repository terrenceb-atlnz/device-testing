---
name: review-feature-docs-before-testing
description: "Before testing ANY feature, read its Feature Overview and Configuration Guide, plus the product's TPS and Test Strategy on the lab wiki — Test Engineer 2026-10-08; the case text alone is not enough grounding"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e2852736-283a-4261-9133-f7c5eb813935
  modified: 2026-10-08T03:10:07.360Z
---

**Test Engineer, 2026-10-08:** *"You would be able to find feature overview guide in the
internet, so going forward please review the feature overview guide for any feature testings
that you do. Another thing that might help you is the test strategy and Software TPS."*

Three documents, read BEFORE drafting steps or grading anything:

1. **Feature Overview and Configuration Guide (FoG)** — **2026-10-27: the local copy is GONE.**
   `claude/device-testing/Feature Overview Guides/` (repo root, gitignored, kept there from
   2026-10-15) no longer exists on the share; the Test Engineer is locating the PDFs again.
   **Until he says they are back, read the FoG from the Allied Telesis website.** The
   exhaustive list of every AW+ FoG (Test Engineer, 2026-10-27) -- start here to find a
   feature's guide:
   `https://www.alliedtelesis.com/nz/en/resource/alliedware-plus-feature-overview-and-configuration-guides/`
   Each guide has its own resource page, e.g. AMF:
   `https://www.alliedtelesis.com/nz/en/resource/amf-feature-overview-and-configuration-guide/`
   (Test Engineer, 2026-10-27). The pattern is
   `alliedtelesis.com/nz/en/resource/<feature>-feature-overview-and-configuration-guide/`; the
   AW+ CLI wiki's `introductions/*.md` pages also carry the exact link per feature (e.g.
   mirroring → `alliedtelesis.com/documents/remote-mirroring-feature-overview-and-configuration-guide`).
   The site is public, so fetch it from the dev host (WebFetch), not from a testbox. Do not
   `ls` for the old folder first: on 2026-10-27 that cost the T30403 tester three calls.
2. **Software TPS** (Target Platform Specification) — the per-product feature support matrix:
   every feature with Yes/No and the reason for a No. This is where an expected UNSUPPORTED is
   read off, instead of inferred from the DUT.
   `https://wiki.atlnz.lc/awpwiki/index.php/<Product>_platform_support_TPS`
3. **Test Strategy** — what this product's testing is actually for, its risk areas, what is
   explicitly Not Tested, and the limits to pay attention to.
   `https://wiki.atlnz.lc/awpwiki/index.php/Test:<nnnn>_Test_Strategy_-_<model>`

**Why:** the 2026-10-07 x960 campaign was drafted from case titles alone, then re-grounded in
ck.db, and still had no way to say whether an absent command was a platform limit or a defect.
The TPS answers that in one row. The Test Strategy for the x960-56YSQ also states, in as many
words, that *"ART on another platform proves nothing about this"* — which is the correct caveat
on any CR history or prior-platform result ([[ckdb-case-lookup-by-title]] pulls that history).

**How to apply:** at triage, for each case's feature, quote the TPS support row and the guide's
definition of correct behaviour into the queue file, and cite them in the final log. A case
whose TPS row says No is UNSUPPORTED with the TPS as the evidence. A case whose TPS row says Yes
but whose command is absent on the DUT is a **finding**, not a platform limit — that is the gap
worth reporting. Fetch them with [[lab-wiki-reachable-from-a-testbox]].
