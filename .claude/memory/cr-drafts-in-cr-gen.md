---
name: cr-drafts-in-cr-gen
description: "Jira CRs are drafted in CR-gen/ as paste-ready wiki-markup field blocks; never fill the RCA field (company AI analysis), offer no root-cause theory"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 6367cfbd-1391-45b1-8b5b-525f6a98413a
  modified: 2026-10-26T22:28:13.223Z
---

CR drafting for historical runs (started 2026-10-27, Terrence) lives in the repo's `CR-gen/`:
README (rules), TEMPLATE.md (reporter fields), one draft per CR (`<case>-<CR key>.md`), and Jira
XML exports in `CR-gen/Example/` (blank CR-92294, filled CR-92097). Tooling for producing CRs also
goes in `CR-gen/`.

`CR-gen/TEMPLATE.md` condenses the wiki's rules (read 2026-10-27 via tb470 `curl &action=raw`,
see [[lab-wiki-reachable-from-a-testbox]]): Jira_CR_Creation_and_Verifying_Guidelines §2.5–2.7,
CR_severity_definitions, Must_Fix_Decision_Process. Re-read those pages if a rule looks stale.

**Never fill the `RCA` field** — it holds the company's own AI root-cause report (Terrence,
2026-10-27). So drafts state what was measured and what the data could not separate, with no
root-cause guess.

**No `[SVT]` tag in the Summary** — SVT is another department (the CR-92097 example is theirs);
ours is `[<release> MF][<platform>] <symptom>`, MF only when on a must-fix list (Terrence, 2026-10-27).

**Why:** Terrence's instruction; an RCA guess from us would contaminate their AI analysis.
**How to apply:** fill only the reporter fields in TEMPLATE.md; quote a real `show system` (the
case evidence or the probe's `bench-setup/captures/<stamp>/`), never reconstruct one; check every
count against the evidence file it cites (12589's eth1 capture held 5 frames, not 5,080).
