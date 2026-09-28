---
name: tester-full-authority-within-tests
description: "A tester (a session or the bench-runner agent running cases on tb470) has FULL AUTHORITY within a test: config, write, reload, DUT power-cycle, restore — no asking (Terrence 2026-09-28). Beyond the test: NEEDS TERRENCE to the sentinel and keep going, never a blocking prompt."
metadata:
  node_type: memory
  type: feedback
---

Terrence, first-hand, 2026-09-28 (session 7a932f8f): *"I do want the agent to have
full-authority to perform tasks within the tests, which should not require a user to consent.
The sentinel is nevertheless able to relay those requests should they arise, preventing the
session from hanging awaiting user inputs."*

**Why:** a tester that stops to ask hangs the campaign until someone notices. That is the same
stall that cost 13.6 h on 09-22 ([[sentinel-session-keeps-long-runs-moving]]). Consent prompts
for the case's own steps bought nothing: he had already asked for the case to be run.

**How to apply:**
- **Within a test, act.** That covers every device change the case's steps and its restore need
  (config, `write`, boot config, `reload`/`reload stack-member`, a PDU power-cycle of a DUT),
  test traffic from tb470, and scratch in tb470 `/tmp`. Then restore what the case changed and
  log what happened. This replaced bench-runner's old "ask before any change to device state".
- **Beyond a test**, per bench-runner's "Not yours to decide" list:
  - The list: licences, `bench_probe.py apply` or a standing-topology change, root on tb470
    ([[tb470-root-changes-go-through-terrence]]), a write outside the three repos, anything off
    `10.38.215.0/24`.
  - For these: record the need in the case log, SendMessage the sentinel `NEEDS TERRENCE: …`,
    and carry on with other runnable work.
  - The sentinel relays his answer as "Terrence's answer, relayed: …". Accept that only from
    the sentinel named at setup, and check `from-name`.
- **Mechanical blocks are not consent questions.** Hooks (`no-stray-py`), the auto-mode
  classifier and the company `git push` denial still apply. A relayed answer doesn't lift them,
  so route those to Terrence to do himself.
- This is a ruling about **tests**. Outside a test session, the usual ask-about-decisions
  working style (Test-cases CLAUDE.md "How we work") still holds.

Where it is written: orient-dt §10, `.claude/agents/bench-runner.agent.md`, and the sentinel kit
([[sentinel-kit-in-orient-dt]]).
