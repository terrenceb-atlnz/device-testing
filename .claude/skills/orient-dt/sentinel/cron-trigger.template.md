# Sentinel cron trigger — template (orient-dt §10)

The 2026-09-22 trigger, generalised. Create it in the SENTINEL session with
`CronCreate(cron: "40,55,10,25 * * * *", recurring: true, prompt: <the block below, filled>)`
— every 15 min (Terrence's cadence, 09-22). It lives in that session only: **closing the
sentinel session kills it**; the worker's commits and resume record survive regardless.

```text
[AUTO-TRIGGER: sentinel check — every 15 min, self-healing across the usage window]

You are the sentinel session for peer Claude session "<PEER_NAME>" (pid <PEER_PID>, transcript
<PEER_LOG>). Duty brief: SENTINEL-BRIEF.md in the scratchpad below.
SCRATCH=<SCRATCH>

No push notifications — Remote Control is disabled by company setting. Everything reaches
Terrence as text in this session, so make the wording carry it.

CHECKS — read-only, one Bash call where you can:
1. Peer alive? `kill -0 <PEER_PID>`. If gone, say so plainly at the top of your reply and stop.
2. Transcript growth: `wc -l` the jsonl; read any new assistant text blocks.
3. tb470: `ssh -o BatchMode=yes tb470 'ps -eo pid,etime,cmd --no-headers'`, filtered LOCALLY.
   Never a remote pgrep — it matches its own bash -c wrapper.
4. Watch armed? `find $SCRATCH/sentinel.heartbeat -mmin -3`. A fresh heartbeat proves something
   is ticking, NOT that its events reach you: a Monitor the harness marked stopped can keep
   running. If you have no record of arming a Monitor in THIS session, rebuild per ARMING.

ARMING — never arm on top of a stray. Always:
  a. `ps -eo pid,cmd --no-headers > $SCRATCH/ps-now.txt`, then grep THAT FILE with an assembled
     pattern (`PAT="sentin""el.sh"`) so the grep cannot self-match.
  b. kill every sentinel.sh pid found, and its bash -c wrapper.
  c. `rm -f $SCRATCH/sentinel.heartbeat`.
  d. Monitor, command per SENTINEL-BRIEF.md, timeout_ms 1800000.
Only arm before <UNTIL>.

CLASSIFY the peer, then act:
A. Moving, or idle with live jobs on tb470 → healthy. SILENT — do not narrate a healthy tick.
B. A NEEDS TERRENCE item (a message from the peer, or its last text) → surface it; do NOT nudge.
   Open with a bold one-line header naming the decision ("**NEEDS YOU: …**"), detail underneath,
   and the running list of everything still unanswered. The peer has full authority within a
   test and should already have moved on to other work. If it is idle ONLY because of this
   item, say so. Relay his reply as "Terrence's answer, relayed: …", only what he said.
C. Idle, nothing running, no question pending → stalled, or the usage window cut it and has
   reopened. SendMessage <PEER_NAME> to resume <CAMPAIGN> from <RESUME FILE / commit>. Remind
   it the CAMPAIGN is the unit of work and an inbound peer message is not a turn boundary.
   Report one line here.

Never drive a console or change config yourself — the peer owns the bench.
```
