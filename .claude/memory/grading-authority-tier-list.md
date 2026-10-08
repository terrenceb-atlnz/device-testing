---
name: grading-authority-tier-list
description: Who decides a test verdict, highest first — Terrence, a validated pytest script, the session agent (sentinel), a sub-agent's recommendation, anything else. Agents never override a validated script's framework verdict; only Terrence re-grades
metadata:
  type: feedback
---

Stated by Terrence on 2026-10-09. It was relayed by the Test-cases session `test-cases-2b` while
Ask-CK's Validation and Test Composer features were being planned.

**Who decides a test verdict, highest first:**
1. **Terrence.**
2. **A validated pytest script:** *"because both you would have validated the run AND i would
   have approved it as a source of truth"*.
3. **The session agent** (the sentinel).
4. **A sub-agent's recommended result** (e.g. `bench-runner`'s `RESULT` line).
5. **Results from anywhere else** (historical data, scripts, etc.).

**Why:** *"the script ran and passed to the tests it was written for — that bit is
non-negotiable."* Agents never override a validated script's framework verdict; only Terrence
re-grades. That must not stop analysis: *"they are Static, dont have good exception handling, and
go stale... If the tests themselves are outdated, we need to update them, and i value your input
immensely. Especially if the tests can be run in a better, more efficient structure, without
reducing the quality of output."*

**How to apply:**
- In `/test-mode` results, Ask-CK's results table and `/create-logs`, a sub-agent's verdict is a
  recommendation. The session agent may overrule it, and says why in the Results row.
- A validated script's verdict stands unless Terrence changes it.
- Always offer critique and improvement suggestions for the script alongside the verdict:
  staleness, exception handling, a better or more efficient structure that keeps output quality.
- Related: [[tester-full-authority-within-tests]] (authority over device ACTIONS within a test,
  which is a different question from who GRADES).
