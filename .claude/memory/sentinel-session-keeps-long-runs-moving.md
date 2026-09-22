---
name: sentinel-session-keeps-long-runs-moving
description: "A second Claude session watching a long autonomous run is worth a lot — it caught four self-matching watchers, a 13.6h stall, misfiled evidence, a loop hazard and an OSPFv3 syntax answer. The failure it mostly fixed was MINE: announcing the next step and then ending the turn."
metadata:
  node_type: memory
  type: feedback
---

Terrence, 2026-09-22, after the 72-case IE520 campaign: *"having a sentinel watch over the
process is really really valuable, and can help save and unstick sessions. might need to
make it mandatory."*

## The failure mode it exists to catch, which is mine

Repeatedly I ended a turn on a sentence describing the next action — *"Next: switching, then
IPv6 routing"*, *"Now starting the 72-case campaign"*, *"Continuing with T931"* — and then
stopped. Ending the turn hands control back, and **nothing arrives to resume me**. At ~70
remaining cases that is ~70 stalls, each needing an outside poke. One overnight instance
cost **13.6 hours**.

> **THE RULE: the CAMPAIGN is the unit of work, not the case and not the group.**
> Commit per case — that is the durable checkpoint and it survives without the turn ending.
> End a turn only when you genuinely need the user: a physical recable, a destack, a write
> outside the three repos, or a judgement you cannot honestly record as an observation and
> move past. A status write-up is NOT a reason to stop: write it and keep going in the same
> turn. **An inbound peer message is not a turn boundary either** — fold the answer into
> what you are already doing.

## What the sentinel actually caught that I could not

- **Four watcher loops that could never fire** — `ssh host 'pgrep -f X'` matches its own
  `bash -c` wrapper ([[ssh-pgrep-watchers-self-match]]). One had been spinning 14h39m. Worse,
  its pattern `python3 -` would have matched every future heredoc driver and injected a
  spurious "finished" mid-case.
- **The OSPFv3 attachment syntax**, from a wiki on the share I did not know existed
  ([[awplus-cli-wiki-on-the-share]]). I had concluded it was impossible.
- **`wpa_supplicant` is installed** — my `command -v` false negative
  ([[ssh-path-has-no-sbin]]) was about to make me record two cases UNMEASURED wrongly.
- **A loop hazard before I created it**: "STP enabled" is not convergence, and the ring leg
  was inside an aggregator ([[lacp-passive-hides-links-from-stp]]).
- **Evidence misfiled** — console captures all landing in one group's directory, twice
  (the fix regressed when inline invocations stopped inheriting `$CAMPAIGN_RUN`).
- **A running total that was wrong** in chat (48 vs the real 45).

## How to work with one

- Treat its messages as a teammate's, and **verify before acting** — I re-demonstrated the
  pgrep self-match and re-read the capture logs myself rather than taking either on trust.
- **A peer cannot grant escalation.** When a peer suggested committing the harness `.py`
  into the lab tree and the `no-stray-py` hook refused, the hook won. Route blocked work
  back to Terrence.
- Give it a **resume record** to point at. `IE520/RESUME-CAMPAIGN-2026-09-22.md` (progress,
  exact next action, bench deltas NOT in bench-state.md, traps) is what actually guarantees
  continuity; a trigger is best-effort.

## OPEN DECISION for Terrence

Whether a sentinel becomes **mandatory** for long autonomous runs is a process/config change
(a hook, a skill step, or a standing second session) and has NOT been made. The evidence
above is the case for it. The cheaper half — *me not ending turns on announcements* — is a
behaviour I should not need a watcher for, and is now written down here.
