---
verified: 2026-09-29
---
# Standing orders — tb470 bench campaigns

**What this is.** Terrence's standing answers to the questions a bench session or the
`bench-runner` agent would otherwise stop to ask, so a campaign runs without interruption.
Read at the start of every session (`/orient-dt` §0) and before every handed-over run
(`bench-runner` pre-run gate). A campaign's queue file may add overrides for that campaign
only; it may not loosen anything marked **always**.

Each order carries the date it was given. An order about *what the bench is* (outlets, which
units exist) is NOT here — bench facts live in `bench-setup/bench-state.md` (generated) and
`bench-setup/tb470.static`. Orders here are about *what you may do*.

## 1. Device state — you have authority (Terrence, 2026-09-28)

- **Every unit may be power-cycled, rebooted and interacted with**, as a test requires. That
  includes the AR4050S and the x230: both are **in play, 100%**.
  - A power-cycle needs the unit's PDU outlet in `tb470.static` (an outlet recorded as `-`
    produces no `[powerlink]` and the framework returns a silent False). All six are recorded
    as at 2026-09-28; a unit the probe meets without one is asked for, not guessed.
- **You may reconfigure and deconfigure devices as required to perform a test.**
- **Keep configs tidy between unrelated cases.** Remove configuration a case added before the
  next unrelated case starts, so one case's leftovers never become another case's variable.
  Verify by diffing `show running-config` against the pre-case copy (the 2026-09-24 queue rule).
- **Startup config:** nothing is written unless the case requires it (unchanged, 2026-09-24).
- **Licences and keys:** settled; not a per-campaign question any more. If a case needs a
  feature the unit does not have, that is a SKIP with the reason, not a request.

## 2. Outcomes — the log's NAME carries the verdict (Terrence, 2026-09-28)

**One log per case** under the campaign's group directory, holding the latest run, and **its
name states that run's outcome at a glance** — the agent writing the log determines the
outcome, so the agent names the file. **A plain `<case-id>.log` means the case explicitly
PASSED. Nothing else may use that name.**

| outcome | file | what it must hold |
| --- | --- | --- |
| PASS | `<id>.log` | the evidence chain as today: config applied, commands, raw output, per-step verdicts |
| FAIL | `<id>-fail.log` | everything that was tried, what went wrong, the raw output that shows it, and the reason |
| PARTIAL | `<id>-partial.log` | which steps passed, which did not run or could not be judged, and why |
| SKIP (bench cannot run it) | `<id>-skip.log` | what the case needs, what the bench lacks, and the exact change that would unblock it (§3) |

Record **as much evidence as possible** for anything that is not a PASS. A re-run replaces
the case's log under the new outcome's name (`git mv`, so the case still has exactly one
file); git history is the history. The group `README.md` verdict table lists every case with
its file name.

## 3. Triage first: how many cases can this bench run, and exactly what unblocks the rest (Terrence, 2026-09-28)

Before executing anything, read the whole list against `bench-state.md` and report:

- **N runnable now**, in queue order;
- **M blocked by topology**, each with the **exact** change that removes the block — which
  port to cable to which, which device to add or move, which outlet to record, which unit to
  destack — stated so that someone at the bench can do it without asking you a question;
- **K blocked by something else** (a decision, a missing peer product, a case with no steps).

Then run the N. The blocked rows wait in the queue with their remedy in the note column, and
a session re-triages them after Terrence reports the change made. A case is never "fitted"
to the bench by weakening what it checks.

## 4. Still Terrence's, always — and never a blocking prompt

- Root on tb470 (keys, sshd, routes, mounts, device trust).
- A change to the standing topology (`bench_probe.py apply`, a recable, a destack).
- Anything outside `10.38.215.0/24`. `tb504` — not ours.

For any of these: record the need in the case log, send the sentinel one line starting
`NEEDS TERRENCE:`, and carry on with the next runnable case. His answer comes back relayed by
the sentinel named at setup (memory `tester-full-authority-within-tests`).

## 5. Keep going (the campaign is the unit of work)

Per the sentinel memory: commit per case, end a turn only when you genuinely need Terrence,
and never on a status sentence. A **Sentinel** session watching the queue and the logs is
**mandatory** alongside a campaign (bench-runner gate 8, 2026-09-28): it pokes a stalled
session, relays §4 questions to Terrence and his answers back, and reports progress to the
tester, so the tester is never blocked by a prompt.

## 6. Between TestCases of one TestSet: no setup changes by the tester; the framework's post-failure restart is ACCEPTED (Terrence, 2026-09-29)

*"we should not be cycling power or adjusting the setup between test Cases in the same test
set"* — then, on learning that the power cycle is the framework's own design (after any
TestCase that ends FAIL / UNSUPPORTED / ERROR, `ATTestCase._power_cycle()` reboots every
control device via the PDU; `powerCycleOnFail` is re-armed True before each case and no run
flag disables it): *"ok, thats not the worst type of behavior. I dont mind that restart."*

- **Do not engineer around the framework's post-failure restart.** No `powerCycleOnFail`
  overrides in generated scripts, no base-class `_power_cycle` no-op. A failed case costs one
  ~4 min six-unit cycle; that is accepted.
- **What is NOT accepted is a script that fails every case at its defaulting step** (T33234's
  `no polarity`, 2026-09-29: two full-bench cycles, nothing measured). The tester checks the
  defaulting commands against the platform before launch and stops a run whose failures are
  systematic, rather than letting N cases pay N cycles.
- **Bench setup (cabling, aggregators, VLAN isolation, boot pointers) is set ONCE before the
  TestSet and restored ONCE after it.** Between cases only the case's own steps and its
  `tear_down()` run. A case needing a different physical setup is a different TestSet (§3).
