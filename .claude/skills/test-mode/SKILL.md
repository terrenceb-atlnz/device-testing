---
name: test-mode
description: Run a list of test cases on ANY testbox the Test Engineer names, as ONE bundle in this session. This session becomes the sentinel (the Test Engineer's channel to the tester, and its rescuer) and dispatches the bench-runner agent as the tester, one subagent per queue group. Setup questions first (testbox, U interfaces, PDU, constraints), then a no-console occupancy check of the box, then the probe with the Test Engineer's facts, then triage (all / some / none runnable, with the exact change that unblocks the rest), then the runs. Use when given a list of case ids or titles to execute, or asked to "run these tests", "run the campaign", "test mode", "run cases N, M on tbNNN", or to "resume the campaign" (`--resume`).
---

# Test mode — the one-session campaign bundle (any testbox)

The original ask (2026-09-28): *"a user should be able to invoke the skill / call the agent / use
an aliased phrase and start the process, which should boot the sentinel for interfacing, the
sentinel would hand off the list of tests to the agent, do the pre-checks on the bench to ensure
it can run all / some / none of them, return that as feedback to the user, allow the user to
proceed / reconfigure the bench, finalize bench if necessary, then proceed with the amount of
tests possible."* Revised 2026-10-01 to be **testbox-agnostic and user-agnostic**. The box and
everything about it come from the Test Engineer at the start of the session, never from this file.

**Two roles, one session.** From the moment this skill starts, **this session is the sentinel**
(orient-dt §10 shape A). It **never opens a console**: no console bytes, no config, no device
login. Its only contact with the box is the read-only ssh occupancy check in §3, which sends
nothing to any console. The tester is the `bench-runner` agent, dispatched as a background
subagent, one per queue group.

**Who is who.** The **Test Engineer** is the person invoking this skill. They own the decisions
this file reserves for a human. Their answers are relayed to the tester verbatim. Rulings in
`STANDING-ORDERS.md` were given by the bench owner and apply unless the Test Engineer's session
constraints tighten them; a session constraint never loosens anything marked **always**.

**Paths are names.** The repo-relative names (the sentinel kit, STANDING-ORDERS.md, the probe)
resolve through `/orient-dt` §0 (repo root = `claude/device-testing/`). The per-box files resolve
through `bench_probe.py --box <TB>`:
- tb470 keeps its flat files in `bench-setup/`;
- any other box uses `bench-setup/<TB>/`, which holds `bench-state.md`, `<TB>.static`,
  `<TB>.setup.current`, `captures/` and `backups/`.

**The Test Engineer's session facts are never overwritten.** Every answer to §1 is written into
the queue file's header (§2) word for word. When the bench, a recorded fact or a later step
disagrees with one, **ask them which is right** (AskUserQuestion). Never pick a side, never
"correct" their answer, and never edit `<TB>.static` or a `.setup` to make the disagreement go
away.

---

## 1. Before anything — the setup questions

1. **Arguments.** Either a list of cases (ids, titles, or a mix), or `--resume [queue file]`.
   With neither, ask for the list and stop. Read `STANDING-ORDERS.md` in full; do not re-ask
   anything it answers.
2. **Ask the setup questions in ONE AskUserQuestion call**, before touching any box. Each is
   free text through "Other"; offer the obvious options:
   - **Testbox:** which box (`tbNNN`)? Offer the box from the previous queue file, if there is
     one, plus "Other".
   - **U interfaces:** which `/dev/uN` consoles does this session use, and which device is on
     each, if known (for example `u2,u4,u5 = stack; u3 = DUT2`)? Only these consoles are ever
     probed or opened. Every other console on the box belongs to someone else.
   - **PDU:**
     - the PDU's IP;
     - the outlet for each U interface (for example `u2=6, u3=8`);
     - or "no PDU / do not power-cycle".
     This is asked BEFORE the probe because the probe writes it into the `.setup`'s `[power]`
     section. With no PDU the framework's post-failure power cycle silently does nothing
     (STANDING-ORDERS §1), so record that answer too.
   - **Session constraints:** anything specific to this session? Offer:
     - "Shared box: read-only probe, log out of consoles";
     - "None";
     - "Other" (time window, cases or devices not to touch, the box's lab segment / return
       path, who else uses the box).
3. **Multi-hour?** If the run is more than a handful of cases, or involves reloads, failovers or
   60 s observation windows, and the session is running inside the editor, say this in these
   terms and wait for the answer before arming anything:
   - In this shape the subagent lives inside this session's process. If the process dies (a
     closed window, an editor reload, an xrdp or VPN drop that takes the editor with it), the
     tester dies with it. The queue file and per-case commits survive, and `/test-mode --resume`
     picks up from the first row not DONE / BLOCKED, so the loss is the case in flight.
   - **A bare terminal is not safer than the editor:** closing it sends SIGHUP. **A terminal
     inside `tmux` (or `screen`) is safer:** `tmux new -s test-mode`, `cd` to the repo root,
     start `claude`, then re-run `/test-mode` with the same arguments. End this invocation with
     nothing armed.
4. **Read for the box, not from memory.**
   - tb470: `/orient-dt` §0–§4 and §10 apply as written.
   - Any other box: §2–§4 (platform, driver and framework traps) apply to its products. §1's
     tb470 specifics (NIC names, the boot-server role, `/nfsHome`) do not; ask the Test Engineer
     rather than assume them.
   - Read `TESTBOX-ACCESS.md` before the first ssh.

## 2. The session directory and the queue file — the resume point

Everything this session produces goes under **`<TB>/<FAMILY>/`** in the repo, where `<TB>` is
the testbox (`tb470`) and `<FAMILY>` is the DUT's product family (`IE520`). One campaign has one
stamp, `<STAMP>` = the campaign's start, local time, `YYYY-MM-DDTHHMM` (e.g. `2026-10-01T1430`):

```
<TB>/<FAMILY>/CAMPAIGN-QUEUE-<STAMP>.md          the queue: the resume point
<TB>/<FAMILY>/<group>-<STAMP>/<case-id>.log      one log per case, named per STANDING-ORDERS §2
<TB>/<FAMILY>/<group>-<STAMP>/README.md          the group's verdict table
<TB>/<FAMILY>/<group>-<STAMP>/evidence/…         captures, pre/post configs, helper tools
```

for example `tb470/IE520/routing-2026-10-01T1430/12589-fail.log`. Campaigns before 2026-10-01
live under `IE520/<group>-<date>/` (all tb470) and stay there.

- **Group** the list the way the cases group themselves (suite / feature / topology need). A
  group is what one `bench-runner` dispatch runs: a dozen simple cases, or two or three
  reload-heavy ones.
- **The queue file**: copy the layout of the newest existing one, not its rows.
  - The header names the ask verbatim and says "**This file is the resume point**".
  - A **`## Session facts`** block holds the Test Engineer's §1 answers word for word, dated:
    testbox, U interfaces, PDU, constraints.
  - The rules block cites STANDING-ORDERS §2 for log names.
  - A `## Queue` table has one row per group: `# | case(s) | group dir | state | note`.
  - A `## Issues` list.
- `--resume`: take the named queue file, else the newest `*/*/CAMPAIGN-QUEUE-*.md` (legacy:
  `IE520/CAMPAIGN-QUEUE-*.md`). Do not rewrite it. Re-ask §1 only for facts it lacks, and confirm
  the recorded ones still hold ("still u2–u5, PDU as before?"). The next row is the first not
  DONE / BLOCKED.
- Commit the new queue file before dispatching anything. It is the record if this session dies.

## 3. Occupancy check — BEFORE the probe opens a console

On a box other people use, the other writer on a console is a colleague
(memory `shared-testbox-console-occupancy`). Check without touching any console:

```bash
sock=/run/user/$(id -u)/keyring/ssh                  # the keyring agent (TESTBOX-ACCESS.md §0)
SSH_AUTH_SOCK=$sock ssh -o BatchMode=yes <TB> \
  'cd ~/claude/device-testing/bench-setup && <PY> bench_probe.py --box <TB> precheck --consoles <U-list>'
```

- **`<PY>`** is a Python ≥ 3.7 on the box. tb105's `python3` is 3.6, so use `python3.8` there.
  Check it with `<PY> -c 'import sys, serial; print(sys.version)'`. If the box does not mount
  the NFS home, copy `bench_probe.py` to the box's `/tmp/ckprobe/` and run it from there.
- **What it reports (it sends nothing to any console):**
  - per session console: its ttyUSB target, any `fuser` holder (with sudo when passwordless sudo
    works), and lock files;
  - box-wide: every screen / tmux / minicom / picocom-type process and every running python
    script, with the human behind a root-owned `sudo minicom`;
  - who is logged in.
- **Exit 0 = CLEAR.** Carry on.
- **Exit 5 = FOUND.** **Stop and return to the Test Engineer** with the FOUND list verbatim:
  which console, which process, which user, how long it has been up. Then end the turn. Never
  kill, detach or displace anything. "Idle" is not "free": a minicom idle for hours is still
  someone's console.
  - Re-run the check when they say it is clear, or when they narrow the U interfaces to the free
    ones.
  - "UNKNOWN" (no sudo, so a root-owned holder would not show) counts as FOUND. It is their call.
- An ssh failure is a FOUND too: report it, never work around it.

## 4. Arm the sentinel — on yourself

The kit is `/orient-dt` §0 "sentinel kit"; the procedure is §10 with `SELF=1`.

1. Find your own transcript: `~/.claude/projects/<slug>/<session-id>.jsonl`, where `<slug>` is
   the repo root with every non-alphanumeric character turned into `-`, and `<session-id>` is
   the last path element of your scratchpad directory. Confirm the file exists.
2. Copy `SENTINEL-BRIEF.template.md` into your scratchpad and fill it in:
   - one-session shape, `PEER_LOG` = your own transcript, no PID;
   - `<TB>`;
   - `<PEER_NAME>` = the subagent's name once dispatched;
   - `<CAMPAIGN>` and the queue file;
   - `<UNTIL>` = when the Test Engineer wants it to stand down (ask if they did not say; the
     default is the end of their working day).
3. Sweep strays, then arm by the cron template's ARMING steps: `Monitor(command: "SELF=1
   BOX=<TB> PEER_LOG=<own transcript> SCRATCH=<scratchpad> UNTIL='<until>' bash
   <repo>/.claude/skills/orient-dt/sentinel/sentinel.sh", timeout_ms: 1800000)`. Re-arm on
   every expiry; the expiry notification is itself a wake-up, so use it.
4. `CronCreate` the backstop from `cron-trigger.template.md`, one-session wording, every 15 min.
5. Tell the Test Engineer in one line: it is armed, which mode, where the full feed is
   (`<scratchpad>/sentinel.feed` for their own `tail -f`), and how to switch modes.

## 5. Probe and triage — the tester measures, with the Test Engineer's facts

Dispatch `bench-runner` in the background with a prompt that carries, in this order:
- `mode: TRIAGE`;
- `sentinel: parent`, and how to reach you (`SendMessage`; the docs' address is `to: "main"`);
- **the session block**:
  - `box: <TB>`;
  - `consoles: <U-list>`;
  - `pdu: <ip | none>`;
  - `outlets: uN=O,…`;
  - `names: uN=swi_x,…` (only if given);
  - `constraints: <verbatim>`;
  - `session dir: <TB>/<FAMILY>/`, `stamp: <STAMP>`;
- the queue file path and the rows to triage (all of them);
- STANDING-ORDERS §3 as the report shape;
- "read-only apart from the probe; change no device state; run no case".

The tester re-runs the §3 precheck (time has passed), then runs the probe with those facts:

```bash
<PY> bench_probe.py --box <TB> run --consoles <U-list> --no-prompt \
     --pdu <ip> --outlet u2=6,u3=8 [--name u3=swi_b] [--read-only]
# --read-only when the constraints say "shared box", or the box is not the Test Engineer's own
```

The probe uses the facts for this run and appends a unit that is new to `<TB>.static`. It never
rewrites a recorded line. Its exit codes:

| exit | meaning | what you do |
| --- | --- | --- |
| 0 MATCH | the bench is the deployed `<TB>.setup` | triage proceeds |
| 1 MISMATCH | the bench is not the template | the tester triages against what the bench IS; you show the diff to the Test Engineer, and `apply` is theirs to call |
| 2 NEEDS-CHECK | something could not be verified | show it; it is theirs to resolve |
| 4 USER-CONFLICT | a session fact disagrees with the record or the bench (an outlet, a name, the PDU, a console with no device on it) | the tester stops TRIAGE and hands back the list; you **prompt** (below) |
| "no template" | a box with no deployed `.setup` yet | the generated `bench-state.md` is the only description; writing the template is `apply`, the Test Engineer's |

**On USER-CONFLICT, prompt; do not resolve.** Use one AskUserQuestion per conflict (up to four
per call): "*The session says PDU outlet 7 for u2 (S/N …); `bench-setup/<TB>/<TB>.static`
records 6. Which is right?*", with options "Session (7)" / "Recorded (6)" / Other.
- "Session" → with their go-ahead, change that one line in `<TB>.static` with a dated comment
  naming them.
- "Recorded" → correct the session-facts block in the queue file and say so.

Then re-dispatch TRIAGE. Never edit a session fact or a recorded fact without that answer.

Then **say one line and end your turn.** The subagent's completion notification wakes you; so
does anything the Test Engineer types. Do not poll.

On the triage report:
- Show it to the Test Engineer **verbatim**: N runnable / M blocked by topology, with the exact
  change each needs / K blocked otherwise. Do not soften it and do not add your own guesses.
- Ask the one question this skill is allowed to block on: **proceed with the N now, or
  reconfigure first?**
  - Proceed → §6 with the runnable rows. Mark the M and K rows BLOCKED in the queue with the
    reason, so `--resume` skips them until the bench changes.
  - Reconfigure → they do it (a recable, a destack, an `apply`: all theirs, never yours). When
    they say done, `SendMessage` the same subagent `mode: TRIAGE again — re-probe` (its context
    is intact), or dispatch a fresh one. Show the new report. Repeat until they say proceed.

## 6. Run — one subagent per group, in queue order

For each runnable group, in order:

1. Dispatch `bench-runner` in the background with:
   - `mode: RUN`;
   - `sentinel: parent` and the address;
   - **the same session block as §5**;
   - the queue file and **this group's rows only**;
   - "commit per case; hand back when the group is done or every remaining row is BLOCKED; if
     you stop for any other reason, say which row is next".
2. Fill the subagent's name into the brief. Say one line. **End your turn.**
3. On its completion notification, read the report against the queue file and the group's log
   directory, never from memory:
   - every row DONE or BLOCKED, logs named per STANDING-ORDERS §2, commit hashes given → next
     group;
   - rows left with no BLOCKED reason → the subagent ended early. Continue it by name with one
     message: what the queue shows completed, the exact next row, "no reply needed". If it has
     gone, dispatch a fresh RUN for the remaining rows;
   - a report you cannot reconcile with the queue → say so to the Test Engineer; do not guess.
4. Between groups, nothing runs on the bench. That is the moment a recable for a BLOCKED group
   costs least: say so if one is pending, and re-triage that group (§5) before running it.

The **campaign is the unit of work** for the tester (memory
`sentinel-session-keeps-long-runs-moving`). For you, the sentinel, the rule is inverted: end your
turn after every dispatch so notifications can reach you, and never end it with an
unacknowledged NEEDS YOU on the table.

## 7. While it runs — you are the channel and the rescuer

- **`NEEDS TEST ENGINEER:` from the tester** → surface it at once under a bold **NEEDS YOU:**
  header, with the running list of everything unanswered. Do not answer it yourself and do not
  nudge the tester: it has already moved on to other runnable work. When the Test Engineer
  answers, relay it with `SendMessage` as "Test Engineer's answer, relayed: …", only what they
  said.
- **Their direction** (priorities, "stop after this case", "write the handover now") → relay
  it as "Test Engineer's instruction, relayed: …". Batch what you send; every message risks a
  stall, so add "no reply needed" where none is.
- **A new session fact mid-campaign** (another console, a corrected outlet) → write it into the
  queue file's Session facts with the time, relay it, and have the next probe carry it.
- **Monitor events**: CLI transcripts in normal mode, the tester's narration in verbose. Healthy
  ticks are silent; do not narrate them.
  - An **IDLE** alarm with nothing running and rows left is §6 step 3.
  - An IDLE alarm while a case is mid-run and the box shows a live job is not.
- **Cron ticks** classify per the template: healthy → silent; NEEDS YOU → surface; idle with
  rows left → continue or dispatch.
- **Mechanical blocks** (the `no-stray-py` hook, the auto-mode classifier, the company `git
  push` denial) are not consent questions, and a relay cannot lift them. Route them to the Test
  Engineer to do themselves.
- **Never touch the bench.** Two writers on one console is the classic failure. Send facts;
  the tester acts.

## 8. Completion

When every group is DONE or BLOCKED:
1. Give a summary table built **from the queue file and the log names**, one row per case:
   outcome (from the file name), log path, commit.
2. List the BLOCKED rows, with the exact change each still needs.
3. Run `/wrap-dt`. Its §1 stands the sentinel down (Monitor, cron, stray sweep).
   - On tb470 it runs as written.
   - On any other box, read its tb470-specific steps against `<TB>`'s bench-state and the
     session facts, and write the handover as `<TB>/<FAMILY>/SESSION-HANDOVER-<YYYY-MM-DD>.md`.
   - On a shared box, confirm the tester logged out of every console it opened.

## 9. `--resume`

Same session or a new one, after a cut, a crash or a deliberate stop:
1. §1 step 1, and step 3 only if this is a fresh session; step 2 only for facts the queue file
   lacks, plus the one-line confirmation.
2. §2: the named or newest queue file; do not rewrite it. Say which row is next.
3. §3: the occupancy check, always. Time has passed and somebody may be on a console now.
4. §4: arm on yourself.
5. §5 only if the box's `bench-state.md` "Generated" stamp predates a recable the Test Engineer
   mentions. `bench-runner`'s own gate re-probes before every run anyway.
6. §6 from the first row not DONE / BLOCKED.
