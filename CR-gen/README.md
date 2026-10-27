# CR-gen — Jira CR drafts from test runs

Drafts of Change Requests (Jira project **CR**, jira.atlnz.lc) written from this repo's case logs
and evidence. Each draft is a set of **paste-ready field blocks in Jira wiki markup** (Jira Server
9.4: `h4.`, `{noformat}`, `#`/`#-` lists, `||table||`), one block per field of the CR create/edit
screen. Nothing here talks to Jira; the Test Engineer pastes and files.

| path | what |
| --- | --- |
| `Example/new_CR.html` | Jira XML export of a blank CR (CR-92294): the field set and each field's template text |
| `Example/filled_CR.html` | Jira XML export of a filled CR (CR-92097, IE520 lockup): how each field is written in practice |
| `TEMPLATE.md` | the reporter's fields, in order, with what goes in each |
| `<case>-<CR key or DRAFT>.md` | one draft per CR, e.g. `T12589-CR-92294.md` |

## Rules

- **Fill only the reporter's fields** (`TEMPLATE.md`). **Never fill `RCA`**: it is the AI-generated
  root-cause report from the company's own AI analysis (Terrence, 2026-10-27). For the same reason,
  a draft states what was measured and what the data could not separate, and **offers no
  root-cause theory**.
- Developer/workflow fields (Resolution Details, Verification, ISSU, RED *, Decision, Risk, Release
  Notes, Sprint, Developer) are left alone.
- Every number and every console line comes from a file in this repo; the draft names its source.
  `Show System` is a real capture from the run's build (the case's evidence or the probe's
  `bench-setup/captures/<stamp>/`), never reconstructed.
- Priority is a suggestion; the Test Engineer sets it.
