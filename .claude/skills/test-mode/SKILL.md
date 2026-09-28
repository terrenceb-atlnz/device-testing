---
name: test-mode
description: Run a list of tb470 test cases as ONE bundle in this session — this session becomes the sentinel (Terrence's channel to the tester, and its rescuer) and dispatches the bench-runner agent as the tester, one subagent per queue group. Triage first (all / some / none runnable, with the exact change that unblocks the rest), then the gate, then the runs. Use when given a list of case ids or titles to execute, or asked to "run these tests", "run the campaign", "test mode", "run cases N, M on tb470", or to "resume the campaign" (`--resume`).
---

# Test mode — the one-session campaign bundle (tb470)

Terrence, 2026-09-28: *"a user should be able to invoke the skill / call the agent / use an aliased
phrase and start the process, which should boot the sentinel for interfacing, the sentinel would
hand off the list of tests to the agent, do the pre-checks on the bench to ensure it can run
all / some / none of them, return that as feedback to the user, allow the user to proceed /
reconfigure the bench, finalize bench if necessary, then proceed with the amount of tests
possible."* And: *"coalesced into one device-testing agent that does both parts equally."*

**Two roles, one session.** From the moment this skill starts, **this session is the sentinel**
(orient-dt §10 shape A) and **never touches the bench**: no consoles, no config, no ssh to a
device. The tester is the `bench-runner` agent, dispatched as a background subagent, one per
queue group. That satisfies the mandatory-sentinel rule (orient-dt §10, `bench-runner` gate 8
"sentinel: parent").

**Paths are names.** Every path below resolves through `/orient-dt` §0 (repo root =
`claude/device-testing/`): the sentinel kit, STANDING-ORDERS.md, bench-state.md, the queue
file. When something moves, fix §0, not this file.

---

## 1. Before anything — read, then ask the two questions

1. If this session has not run `/orient-dt`, read its §0–§4 and §10 now. Read
   `STANDING-ORDERS.md` in full: it holds Terrence's standing answers (device authority, the
   log-NAME-is-the-verdict rule, the triage report shape, what stays his). Do not re-ask any of
   them.
2. **Arguments.** Either a list of cases (ids, titles, or a mix — a Jira/AWPTCM id per case) or
   `--resume [queue file]`. With neither, ask for the list and stop.
3. **Ask once, then proceed: is this a multi-hour campaign?** Roughly: more than a handful of
   cases, anything with reloads, failovers or 60 s observation windows, or anything you would
   not sit and watch. If YES and the session is running inside the editor, say this, in these
   terms, and wait for the answer before arming anything:
   - In this shape the subagent lives inside this session's process. If the process dies (a
     closed window, an editor reload, an xrdp or VPN drop that takes the editor with it), the
     tester dies with it. The queue file and per-case commits survive, and `/test-mode --resume`
     picks up from the first row not DONE / BLOCKED, so the loss is the case in flight.
   - **A bare terminal is not safer than the editor**: closing it sends SIGHUP to the session.
     **A terminal inside `tmux` (or `screen`) is**: the session is detached from any window, an
     xrdp / VPN drop or a closed terminal leaves it running, and you re-attach with
     `tmux attach -t test-mode`. That is standard process behaviour, not something measured on
     this seat; the 09-22 evidence is only that editor-attached Monitors were SIGTERMed by a drop.
   - If they want that: `tmux new -s test-mode`, then `cd` to the repo root and start `claude`
     there, and re-run `/test-mode` with the same arguments. End this invocation with nothing
     armed.
   If NO, or they choose to stay, carry on.

## 2. The queue file — the resume point

`IE520/CAMPAIGN-QUEUE-<YYYY-MM-DD>.md`, in the shape of the newest existing one (read it first;
copy its layout, not its rows): a header naming the ask verbatim, "**This file is the resume
point**", the rules block (which cites STANDING-ORDERS §2 for log names), a `## Queue` table
with **one row per group** — `# | case(s) | group dir | state | note` — and a `## Issues` list.

- **Group** the list the way the cases group themselves (suite / feature / topology need). A
  group is what one `bench-runner` dispatch runs, so keep groups small enough that one subagent
  context finishes them; a dozen simple cases or two or three reload-heavy ones.
- `--resume`: take the named queue file, else the newest `IE520/CAMPAIGN-QUEUE-*.md`. Do not
  rewrite it. The next row is the first not DONE / BLOCKED.
- Commit the new queue file before dispatching anything (it is the record if this session dies).

## 3. Arm the sentinel — on yourself

The kit is `/orient-dt` §0 "sentinel kit"; the procedure is §10 with `SELF=1`.

1. Find your own transcript: `~/.claude/projects/<slug>/<session-id>.jsonl`, where `<slug>` is
   the repo root with every non-alphanumeric character turned into `-` and `<session-id>` is
   the last path element of your scratchpad directory. Confirm the file exists.
2. Copy `SENTINEL-BRIEF.template.md` into your scratchpad and fill it: one-session shape,
   `PEER_LOG` = your own transcript, no PID, `<PEER_NAME>` = the subagent's name once dispatched
   (fill it in after step 5), `<CAMPAIGN>` and the queue file, `<UNTIL>` = when Terrence wants it
   to stand down (ask if he did not say; default the end of the working day).
3. Sweep strays, then arm (the cron template's ARMING steps): `Monitor(command: "SELF=1
   PEER_LOG=<own transcript> SCRATCH=<scratchpad> UNTIL='<until>' bash
   <repo>/.claude/skills/orient-dt/sentinel/sentinel.sh", timeout_ms: 1800000)`. Re-arm on
   every expiry; the expiry notification is itself a wake-up, use it.
4. `CronCreate` the backstop from `cron-trigger.template.md`, one-session wording, every 15 min.
5. Tell Terrence in one line: armed, the mode, where the full feed is (`<scratchpad>/sentinel.feed`
   for his own `tail -f`), and how to switch modes.

## 4. Triage — hand the list to the tester, get all / some / none back

Dispatch `bench-runner` in the background with a prompt that carries, in this order:
`mode: TRIAGE`; `sentinel: parent` and how to reach you (`SendMessage`, the docs' address is
`to: "main"`; if that is refused, `ListAgents` and use the row for this session); the queue file
path and the rows to triage (all of them); STANDING-ORDERS §3 as the report shape; and
"read-only apart from the probe, change no device state, run no case".

Then **say one line and end your turn.** The subagent's completion notification wakes you; so
does anything Terrence types. Do not poll and do not wait in a loop.

On the report:
- Show it to Terrence **verbatim**: N runnable / M blocked by topology with the exact change
  each needs / K blocked otherwise. Do not soften it and do not add your own guesses.
- Ask the one question this skill is allowed to block on: **proceed with the N now, or
  reconfigure first?**
  - Proceed → §5 with the runnable rows; mark the M and K rows BLOCKED in the queue with the
    reason, so `--resume` skips them until the bench changes.
  - Reconfigure → he does it (a recable, a destack, a `bench_probe.py apply` — all his, never
    yours). When he says done, `SendMessage` the same subagent `mode: TRIAGE again — re-probe`
    (its context is intact), or dispatch a fresh one if it has gone. Show the new report. Repeat
    until he says proceed.

## 5. Run — one subagent per group, in queue order

For each runnable group, in order:

1. Dispatch `bench-runner` in the background: `mode: RUN`; `sentinel: parent` and the address;
   the queue file and **this group's rows only**; "commit per case; hand back when the group is
   done or every remaining row is BLOCKED; if you stop for any other reason say which row is
   next".
2. Fill the subagent's name into the brief. Say one line. **End your turn.**
3. On its completion notification, read the report against the queue file and the group's log
   directory, never from memory:
   - every row DONE or BLOCKED, logs named per STANDING-ORDERS §2, commit hashes given → next
     group;
   - rows left with no BLOCKED reason → the subagent ended early (the 09-22 failure). Continue
     it by name with one message: what the queue shows completed, the exact next row, "no
     reply needed". If it has gone, dispatch a fresh RUN for the remaining rows;
   - a report you cannot reconcile with the queue → say so to Terrence, do not guess.
4. Between groups, nothing runs on the bench; that is the moment a recable for a BLOCKED group
   costs least. Say so if one is pending, and re-triage that group (§4) before running it.

The **campaign is the unit of work** for the tester (memory
`sentinel-session-keeps-long-runs-moving`). For you, the sentinel, the rule is inverted: end your
turn after every dispatch so notifications can reach you, and never end it with an
unacknowledged NEEDS YOU on the table.

## 6. While it runs — you are the channel and the rescuer

- **`NEEDS TERRENCE:` from the tester** → surface it at once under a bold **NEEDS YOU:** header
  with the running list of everything unanswered. Do not answer it yourself, do not nudge the
  tester: it has already moved on to other runnable work. When Terrence answers, relay with
  `SendMessage` to the subagent as "Terrence's answer, relayed: …", only what he said.
- **Terrence's direction** (priorities, "stop after this case", "write the handover now") →
  relay as "Terrence's instruction, relayed: …". Batch what you send; every message risks a
  stall, so add "no reply needed" where none is.
- **Monitor events**: CLI transcripts in normal mode, the tester's narration in verbose. Healthy
  ticks are silent; do not narrate them. An **IDLE** alarm with nothing running and rows left
  is §5 step 3; an IDLE alarm while a case is mid-run and the bench shows a live job is not.
- **Cron ticks** classify per the template: healthy → silent; NEEDS YOU → surface; idle with
  rows left → continue or dispatch.
- **Mechanical blocks** (the `no-stray-py` hook, the auto-mode classifier, the company `git
  push` denial) are not consent questions and a relay cannot lift them; route them to Terrence
  to do himself.
- **Never touch the bench.** Two writers on one console is the classic tb470 failure. Send
  facts; the tester acts.

## 7. Completion

When every group is DONE or BLOCKED: a summary table built **from the queue file and the log
names**, one row per case — outcome (from the file name), log path, commit — then the BLOCKED
rows with the exact change each still needs. Then run `/wrap-dt`: its §1 stands the sentinel
down (Monitor, cron, stray sweep) and its handover records that it did.

## 8. `--resume`

Same session or a new one, after a cut, a crash or a deliberate stop:
1. §1 (read; the multi-hour question only if this is a fresh session).
2. §2: the named or newest queue file; do not rewrite it. Say which row is next.
3. §3: arm on yourself.
4. Skip §4 unless bench-state.md's "Generated" stamp predates the last recable Terrence
   mentions; `bench-runner`'s own gate 4 re-probes before every run anyway.
5. §5 from the first row not DONE / BLOCKED.
