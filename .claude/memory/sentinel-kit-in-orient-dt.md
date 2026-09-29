---
name: sentinel-kit-in-orient-dt
description: "MANDATORY before any test session (2026-09-28). Asked to run a list of cases / a campaign, or to watch/unstick another session? DON'T REBUILD IT — the DEFAULT is ONE session: /test-mode (this session = sentinel, bench-runner subagents = tester, one per queue group). The two-session kit (sentinel.sh + brief + 15-min cron) is in orient-dt/sentinel/ and serves both shapes (SELF=1); procedure orient-dt §10."
metadata:
  node_type: memory
  type: reference
---

**The sentinel setup is already built. Use it; do not re-derive it.** On 2026-09-28 Terrence asked
how to replicate the 09-22 two-session campaign, and the answer had to be dug out of two raw
transcripts (worker `575cc8cd…`, sentinel `610b0e91…`). The sentinel's own `sentinel.sh` had
already vanished with its scratchpad. He asked for it to be written down *"so we stop
re-inventing the wheel"*.

- **Procedure:** orient-dt SKILL.md **§10**, covering setup, the worker's brief, the sentinel's
  rules and the traps.
- **Kit:** `.claude/skills/orient-dt/sentinel/`:
  - `sentinel.sh`: the Monitor watcher, parameterised with `PEER_PID`, `PEER_LOG`, `SCRATCH` and
    `UNTIL`, with normal/verbose modes. Tested 2026-09-28 on a fake tester plus real tb470 files.
  - `SENTINEL-BRIEF.template.md`
  - `cron-trigger.template.md`: the 15-min backstop.

**Two shapes since 2026-09-28 evening** (Terrence: *"coalesced into one device-testing agent
that does both parts equally"*):
- **A, the default — `/test-mode`** (`.claude/skills/test-mode/SKILL.md`): the session Terrence
  types into is the sentinel; it writes the queue, arms `sentinel.sh` with `SELF=1` on its own
  transcript (which locates the `<session>/subagents/*.jsonl` transcripts and never polls
  itself or its own task output), holds the cron, and dispatches `bench-runner` subagents —
  TRIAGE first (all/some/none + the exact unblock), then RUN, one per queue group. A subagent
  that ends early NOTIFIES the parent, so rescue is deterministic; the parent continues it by
  name. `--resume` restarts from the queue. The tester dies with the session's process, hence
  the tmux suggestion for multi-hour runs.
- **B — two sessions**, the 09-22 shape, for a tester that must outlive its sentinel. The
  facts below are B's.

The facts to recall without opening §10:
1. **Two sessions, same repo root.** `ListAgents` names the peer; `SendMessage(to: name)`
   delivers it as a `<cross-session-message>` prompt. The worker's PID is its
   `/run/user/1971/cc-socks/<pid>.sock`, and its transcript is the newest other `.jsonl` in
   the project dir.
2. **Terrence talks to the sentinel, and it relays both ways.** The tester has full authority
   within a test ([[tester-full-authority-within-tests]]). For anything beyond, it sends
   `NEEDS TERRENCE:` to the sentinel and keeps going. The sentinel surfaces it as **NEEDS YOU:**
   and relays his answer back.
3. **The sentinel never touches the bench.** It sends facts, the worker acts, and healthy ticks
   stay silent.
4. **Its own messages cause stalls**, so batch them and add "no reply needed". A peer message
   is not a turn boundary.
5. **Two modes** (2026-09-28), switched live by writing `normal`/`verbose` to
   `$SCRATCH/sentinel.mode`. normal = CLI transcripts (`console.py` + the framework's
   `swi_*/stk_*` logs) + alarms; verbose = everything the tester says, runs and gets back. The
   full feed is always in `$SCRATCH/sentinel.feed`, and a human `tail -f` of it costs no tokens.
   The sentinel never opens a console or rides the tester's ssh: `ptrace_scope=1` on both hosts,
   and a second reader on a tty steals bytes.
6. **Arm by sweeping strays first.** Monitors die silently and orphans keep a heartbeat fresh.
   Every liveness check self-matches unless it greps a `ps` snapshot with an assembled pattern
   ([[ssh-pgrep-watchers-self-match]]).

**MANDATORY for any test session, directly or via bench-runner** (Terrence, 2026-09-28). It
exists to rescue the tester and to let Terrence talk to it without waiting on its turn. No case
starts until one is armed.

Why a sentinel is worth running: [[sentinel-session-keeps-long-runs-moving]].

**Added 2026-09-29 (campaign lessons).** (1) An agent definition is read at session START: the bench-runner
type dispatched with NO tools three times because of an empty `tools:` key (fixed dd2b337, effective next
session); the workaround was a general-purpose subagent told to read bench-runner.agent.md. (2) A subagent
that runs out of usage credits dies mid-group and leaves the bench in its group setup (LAG legs freed and
VLAN-isolated at 14:57 on 09-29). Every group README must carry its setup AND restore recipe so a fresh
tester can restore; near a usage limit or the stand-down, dispatch only a bounded record-and-restore job.
(3) The sentinel's default globs do not watch a framework run dir under /tmp/ck*/; add a line-buffered
`tail -F run.stdout | stdbuf -oL tr | grep --line-buffered` Monitor for it. Related: [[restate-topology-gaps-before-dispatch]].

