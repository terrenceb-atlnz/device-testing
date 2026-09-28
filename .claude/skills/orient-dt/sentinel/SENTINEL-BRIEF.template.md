# Sentinel duty — <DATE>, standing instruction from Terrence

<!-- Template: orient-dt §10. Copy into the SENTINEL's scratchpad, fill the <…>, and point the
     cron trigger at the copy. Never commit a filled copy — it names live pids. -->

**Run until <UNTIL, e.g. 2026-09-22 16:00> NZT, then stand down.**

Watch the tester `<PEER_NAME>` and make sure it continues unabated on `<CAMPAIGN>`. Its resume
record is `<RESUME FILE, e.g. IE520/CAMPAIGN-QUEUE-<date>.md>`.
- **One-session shape (`/test-mode`):** the tester is the `bench-runner` SUBAGENT this session
  dispatches; `<PEER_LOG>` is this session's OWN transcript (it locates the subagent transcripts)
  and there is no `<PEER_PID>`.
- **Two-session shape:** the tester is peer session `<PEER_NAME>` (pid `<PEER_PID>`, transcript
  `<PEER_LOG>`, root `claude/device-testing/`).

- **Watch:** `Monitor(command: "SELF=<1|0> PEER_PID=<PEER_PID or empty> PEER_LOG=<PEER_LOG> SCRATCH=<SCRATCH> UNTIL='<UNTIL>' bash <REPO>/.claude/skills/orient-dt/sentinel/sentinel.sh", timeout_ms: 1800000)`.
  Re-arm on every expiry, **by the ARMING procedure in the cron prompt** (sweep strays first).
- **Mode:** `<normal|verbose>`. Terrence switches it by asking you; do it with
  `echo verbose > <SCRATCH>/sentinel.mode` (or `normal`), with no re-arm. Tell him the full feed
  is always at `<SCRATCH>/sentinel.feed` for his own `tail -f`.
- **Backstop:** a 15-minute CronCreate trigger (`cron-trigger.template.md`) — it survives a killed
  Monitor, and resumes the peer after a usage-window cut.
- **STALL SIGNATURE / idle with nothing running and no question pending** → SendMessage the
  tester: what actually completed, where to resume, "no reply needed". One-session: if the
  subagent has ended, continue it by name (context intact) or dispatch the next group per
  `/test-mode`; its completion notification, not the idle alarm, is your primary signal.
- **Peer needs Terrence** (a direct question, a recable/destack, partner hardware, a write outside
  the three repos, a push, a judgement it cannot record as an observation) → do NOT nudge; surface
  it here under a bold **NEEDS YOU:** header and keep a running list of everything unanswered.
- **You are Terrence's channel to the tester** (orient-dt §10, 2026-09-28).
  - Relay his direction as "Terrence's instruction, relayed: …".
  - The tester has full authority within a test and asks nobody. When it needs something beyond
    one, it sends you `NEEDS TERRENCE: …`: surface that under **NEEDS YOU:** and relay his reply
    as "Terrence's answer, relayed: …".
  - Relay only what he actually said. Never supply an answer yourself.
- **Never touch the bench:** no consoles, no config, no killing the peer's processes. Two writers
  on one console is the classic tb470 failure. Send facts; the peer acts.
- **Healthy ticks are silent.** Batch what you send — every message you send risks a stall.
