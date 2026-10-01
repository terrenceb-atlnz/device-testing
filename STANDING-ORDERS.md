---
verified: 2026-10-02
---
# Standing orders — device-testing bench campaigns (any testbox)

**What this is.** The standing answers to the questions a bench session or the `bench-runner`
agent would otherwise stop to ask, so a campaign runs without interruption. The bench owner gave
them; they apply to every **Test Engineer** (whoever runs the session) on every testbox. Read
them at the start of every session (`/orient-dt` §0) and before every handed-over run
(`bench-runner` pre-run gate).

Two things may add to them, and neither may loosen anything marked **always**:
- a campaign's queue file may add overrides for that campaign only;
- the Test Engineer's **session constraints** (`/test-mode` §1, recorded in the queue's Session
  facts) may tighten them for that session.

Each order carries the date it was given. An order about *what a bench is* (outlets, which units
exist, which consoles) is NOT here. Bench facts live in the box's generated `bench-state.md`, its
`<TB>.static`, and the session facts (`/orient-dt` §0). Orders here are about *what you may do*.

## 1. Device state — you have authority (bench owner, 2026-09-28)

- **Every unit on the session's consoles may be power-cycled, rebooted and interacted with**, as
  a test requires. That includes partner units (routers, other switches), not only the DUT:
  on tb470 the bench owner put its AR4050S and x230 **in play, 100%** (2026-09-28).
  - Units on other consoles of the box are someone else's and are never touched.
  - A power-cycle needs the unit's PDU outlet: from the Test Engineer's session facts, or the
    box's `<TB>.static`. An outlet recorded as `-` produces no `[powerlink]`, and the framework
    then returns a silent False. A unit with no known outlet is asked for, not guessed. A
    session that says "no PDU" power-cycles nothing.
- **You may reconfigure and deconfigure devices as required to perform a test.**
- **Keep configs tidy between unrelated cases.** Remove configuration a case added before the
  next unrelated case starts, so one case's leftovers never become another case's variable.
  Verify by diffing `show running-config` against the pre-case copy (the 2026-09-24 queue rule).
- **Startup config:** nothing is written unless the case requires it (unchanged, 2026-09-24).
- **Licences and keys:** settled, and no longer a per-campaign question. If a case needs a
  feature the unit does not have, that is UNSUPPORTED with the reason (`logged-output.md` §1),
  not a request.

## 2. Outcomes and logs — see `logged-output.md` (moved 2026-10-02)

The verdicts (PASS / FAIL / PARTIAL / UNSUPPORTED / NOT TESTED) and their meaning, the tester's
working logs, the `RESULT` line to the sentinel, the results list, and the final per-case log
template all live in **[logged-output.md](logged-output.md)** at the repo root. The final logs
are made only by `/create-logs`, on the Test Engineer's request.

## 3. Triage first: how many cases can this bench run, and exactly what unblocks the rest (bench owner, 2026-09-28)

Before executing anything, read the whole list against the box's `bench-state.md` and report:

- **N runnable now**, in queue order;
- **M blocked by topology**, each with the **exact** change that removes the block, stated so
  that someone at the bench can do it without asking you a question:
  - which port to cable to which;
  - which device to add or move;
  - which outlet to record;
  - which unit to destack.
- **K blocked by something else** (a decision, a missing peer product, a case with no steps).

Then run the N. The blocked rows wait in the queue with their remedy in the note column, and a
session re-triages them after the Test Engineer reports the change made. A case is never
"fitted" to the bench by weakening what it checks.

## 4. Still the Test Engineer's, always — and never a blocking prompt

- Root on the testbox (keys, sshd, routes, firewall rules, mounts, device trust).
- A change to the standing topology (`bench_probe.py apply`, a recable, a destack).
- Anything that contradicts the Test Engineer's session facts, or a session fact against the
  box's `<TB>.static` (a USER-CONFLICT). Neither side is changed without their answer.
- A console outside the session's list, and any holder the occupancy check (`bench_probe.py
  precheck`) finds. Never displace anyone.
- Anything outside the box's own lab segment. Each box's segment is a session constraint, so
  ask; never assume another box's (tb470's, for example, is `10.38.215.0/24`).
- A box the Test Engineer does not own or has not been given: never target it or propose it.

For any of these:
1. Record the need in the case's working log (`logged-output.md` §2).
2. Send the sentinel one line starting `NEEDS TEST ENGINEER:`.
3. Carry on with the next runnable case.

The answer comes back relayed by the sentinel named at setup (memory
`tester-full-authority-within-tests`).

## 5. Keep going (the campaign is the unit of work)

Per the sentinel memory: commit the working log and evidence per case, send the sentinel the
case's `RESULT` line (`logged-output.md` §2), and end a turn only when you genuinely need the Test
Engineer, never on a status sentence. A **Sentinel** session watching the queue and the logs is
**mandatory** alongside a campaign (bench-runner gate, 2026-09-28). It:
- pokes a stalled session;
- relays §4 questions to the Test Engineer and their answers back;
- reports progress to the tester, so the tester is never blocked by a prompt.

## 6. Between TestCases of one TestSet: no setup changes by the tester; the framework's post-failure restart is ACCEPTED (bench owner, 2026-09-29)

The order, as given: *"we should not be cycling power or adjusting the setup between test Cases
in the same test set"*. Then came the learning: after any TestCase that ends FAIL / UNSUPPORTED /
ERROR, `ATTestCase._power_cycle()` reboots every control device via the PDU. `powerCycleOnFail`
is re-armed True before each case, and no run flag disables it. So the power cycle is the
framework's own design, and the answer was: *"ok, thats not the worst type of behavior. I dont
mind that restart."*

- **Do not engineer around the framework's post-failure restart.** No `powerCycleOnFail`
  overrides in generated scripts, and no base-class `_power_cycle` no-op. A failed case costs one
  full-bench cycle (about 4 min for tb470's six units); that is accepted.
- **What is NOT accepted is a script that fails every case at its defaulting step.** T33234's
  `no polarity` (2026-09-29) caused two full-bench cycles with nothing measured. The tester
  checks the defaulting commands against the platform before launch, and stops a run whose
  failures are systematic rather than letting N cases pay N cycles.
- **Bench setup (cabling, aggregators, VLAN isolation, boot pointers) is set ONCE before the
  TestSet and restored ONCE after it.** Between cases only the case's own steps and its
  `tear_down()` run. A case needing a different physical setup is a different TestSet (§3).
