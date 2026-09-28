---
name: wrap-dt
description: Close out a tb470 IE520 bench session — stop what you started, restore what you changed on the DUTs and the host, ground-truth the FINAL bench state and record it in bench-state.md, write the dated session handover, fold durable lessons into /orient-dt and memory, then brief the user and stop. Use at the end of any session that touched the IE520 bench, or when asked to "wrap up", "hand over", "leave the bench", or "record where we got to". Pairs with /orient-dt, which reads these same records at the start of the next session.
---

# Wrap — tb470 IE520 bench

Leave the bench **re-runnable** and the records **true**, then stop. Pairs with `/orient-dt`,
which reads the same three records at the start of the next session — bench-state.md, the dated
`SESSION-HANDOVER`, and the skill itself — so those records, never memory, are the handoff.

**Scope: tb470 only.** Same as orient. `tb504` is not ours to touch.

**Paths: this file names things, `/orient-dt` §0 says where they are.** bench-state.md, the
handover directory, console.py, the memory directory, TESTBOX-ACCESS.md, TB470-HOST-NETWORKING.md
and the working-style doc are all resolved through that one table (repo root =
`claude/device-testing/`). When something moves, fix §0 there — not this file.

**Design rule for this file.** Every fact that can rot is a *lookup*, not a literal: no consoles,
serials, outlets, addresses, builds, boot source or cable maps are written here — they live in
**bench-state.md** and you read them from the hardware. What this file holds is the **order of
operations** and the **traps**, each of which has already cost a session. **One fact, one home:**
bench facts → bench-state.md; platform mechanics and framework traps → `orient-dt`; durable
non-obvious lessons → a memory file; everywhere else links.

Working style is the **"How we work"** section (`/orient-dt` §0): report what you *did*, not what
you intended; a step you skipped is reported as skipped; **ask** before any restore or revert that
is a decision rather than a cleanup.

---

## 1. Stop what YOU started — and only what you started

Nothing below is safe while a background job of yours still holds a console or a NIC.

```bash
# your own background jobs (harness task list, ssh'd monitors, sniffers, senders)
sock=/run/user/1971/keyring/ssh
SSH_AUTH_SOCK=$sock ssh tb470 'fuser -v /dev/u*; ls /var/lock/LCK..* 2>/dev/null'
SSH_AUTH_SOCK=$sock ssh tb470 'pgrep -a -f "tcpdump|AsyncSniffer|ckprobe|ckorient|drv\.py|ping -i" | grep -v "pgrep"'
```

- **`fuser` on the device node is the only reliable "is the console held" answer.** `pgrep -f`
  matches its own ssh wrapper even with the `[b]racket` trick (2026-09-09), and `pkill -f
  <script>` over ssh kills your own session. If you must kill by name, kill by **PID** after
  `ps -o user,lstart,cmd -p <pid>`.
- **Identify the owner before killing anything you didn't start.** A `bench_probe.py` holding four
  consoles for 45 minutes was Terrence's (2026-09-09). Ask; do not assume a stale job.
- Leaving a sniffer or a sender running is how the next session's traffic test measures yours.
- **The sentinel stands down with you** (orient-dt §10, mandatory for test sessions). In
  `/test-mode` both roles are yours: confirm no bench-runner subagent is still running, stop
  your Monitor, delete your cron trigger (`CronDelete`), and sweep stray `sentinel.sh`
  processes as in the kit's ARMING step. In the two-session shape: as the tester, SendMessage
  the sentinel a final "wrapped at <commit>, stand down"; as the sentinel, do the Monitor, cron
  and sweep steps above. Record in the handover that it stood down.

## 2. Restore what you changed on the DUTs

Read your own session for every `configure terminal` you sent. For each change decide — and say
which — **keep, revert, or record**:

- **Session-scoped settings always revert:** `terminal no monitor`, and **`end` on every console
  you touched.** A console left in `configure terminal` answers every plain `show` with
  `% Invalid input detected at '^' marker` and reads as a dead unit to the next session (u5,
  2026-09-09 — declared dead for an hour). Console mode persists across serial sessions.
- **Temporary addressing and test config** (a scratch SVI, an `access vlan` you moved a port into,
  a `channel-group`, a forced `speed`/`duplex`) — these are **decisions**: some are the bench's
  new intended state, some are debris. Do not guess. List them to the user with keep/revert per
  item; anything kept goes into the handover (and into the `.setup` via `bench_probe.py apply` if
  it changes the topology); anything reverted is reverted *and* confirmed by
  a re-read, not by the absence of an error.
- **`write` only what is meant to survive a reboot**, and say so. Unsaved config is not "safe" —
  a member that reboots (or netboots) comes back without it, silently.
- **Do not "tidy" a live stack's ring or aggregation config on the way out.** If it is wrong, it
  is a finding for the handover, not a wrap-time fix.

## 3. Restore what you changed on the host (tb470)

The host is shared infrastructure and it is also the DUTs' **boot server**.

- **Undo every `ethtool` pinning** you made — and if the bench **netboots** (bench-state.md's "boot image" column;
  `/orient-dt` §1), above all on the NIC that serves TFTP: a NIC left at `advertise 0x20`
  (1000-only) cannot negotiate with the bootloader's 10/100-class ASIX dongle, so **the next
  member that reboots boot-loops** (`Failed to load tftp://…` → `Restarting system in 5..`).
  Restore with `ethtool -s ethN autoneg on advertise 0x2f` (10/100/1000) and **read the multi-line
  "Advertised link modes" back** — a one-line `grep` truncates it and reports 10baseT only. Under
  flash boot the pinning still breaks the host↔DUT edge it sits on; undo it regardless.
- Remove temporary IPs, routes and ARP entries you added; leave the DHCP/TFTP services as you
  found them (**TB470-HOST-NETWORKING.md** is the reference).
- `/tmp/ckprobe/`, `/tmp/ckorient/` (tmpfs on tb470) and the session scratchpad die with the
  session — **that is correct**. Anything worth running twice becomes a repo tool; anything worth
  running once is already gone; the *recipe* goes into the handover (§5). Never leave a `.py` in
  Terrence's lab tree ([[no-stray-scripts]] — enforced by a hook, Bash heredocs included). The
  one exception that recurs: the tb470-side driver scratch (`drv.py` + a copy of **console.py**) —
  recreate it from the maintained copy named in `/orient-dt` §0 when tmpfs has been wiped.

## 4. Ground-truth the FINAL state and record it — this is the handoff

Recorded state is always stale; the next session's `/orient-dt` will re-read the hardware, but it
needs to know what you *left*, and why. Read, don't recall:

- Every IE520 console: `show stack` (members `Ready`? who is master? — it moves after every
  failover and never pre-empts), `show epsr` (if any ring is configured), `show boot` (**does the
  boot image read `(file exists)`?** — a stale pointer strands the next reload), `show system`
  **build date on BOTH members against each other** (a mismatch is the split hazard, and `show
  boot` will not show it), `show reboot history` (any new entries since your start), free flash
  (`dir`), and **running-config vs startup-config** — `show running-config | include <what you
  added>` against `show startup-config`; anything running-only reverts on the next reload.
- **Power state of every unit** — a member you powered off to stop a boot-loop **must be
  written down**; to the next person it is a dead unit. Same for anything left `shutdown`.
- Host: `cat /sys/class/net/eth{1,2,3}/carrier`, `ip -br addr`, and — if the bench netboots —
  whether the TFTP path (`/tftproot/IE520-tb470.rel`, the serving NIC up) is currently usable.

Then regenerate **bench-state.md** from the hardware — on tb470,
`cd ~/claude/device-testing/bench-setup && ./bench_probe.py run` (`/orient-dt` §0, ~2 min). It reads
every console, rewrites bench-state.md (measured facts only — there is nowhere in it to type a
note, and that is deliberate) and diffs the bench against the deployed `.setup`:

- **MATCH** — the bench is the intended template. Nothing more to do here.
- **MISMATCH** — either you left the bench changed (restore it and re-run), or the bench has
  legitimately changed and the template must follow it: `./bench_probe.py apply` writes the new
  `.setup` in place (it snapshots the outgoing pair into `backups/<stamp>.*` and refuses if the box
  was hand-edited; `--force` only with the user's say-so). **That is a decision, not a cleanup** —
  never `apply` from a bench that is mid-campaign, split or missing a member.
- **NEEDS-CHECK** — something the run could not verify: a console someone else held, a NIC with no
  carrier, a MAC not learned. Report it in the handover as OPEN; do not `apply` over it.

Inferences, open questions, why a port is shut, what you powered off — all of that goes in the
**handover** (§5), not in bench-state.md.

## 5. Write the session handover

`IE520/SESSION-HANDOVER-<YYYY-MM-DD>.md` in this repo — the established location (`/orient-dt`
§0 "session handovers"; look at the previous one for shape). It must be **self-contained**: the
next session has none of your scratchpad, so every command sequence it will need is written in,
not referenced. If the session is **paused rather than wrapped**, still write it, headed
"PAUSED, not wrapped", listing what is running-only vs saved and what was mid-flight — the
2026-09-11 one is the model.

Sections that earn their place: **TL;DR** (where things are, and whether the bench is whole or
*parked*); **current bench state and how to verify it** in one command block; **what was
accomplished**; **results** — with each run labelled *clean* or *confounded, and why* (a flow
sourced on the member that failed measures nothing; an outage that includes a member that could
not reboot is not a failover number); **findings**, separated into *measured* and *inferred*;
**OPEN questions** as questions, with the evidence path; **ordered next steps**; **recipes**;
**pointers**. Link bench-state.md for the topology rather than duplicating it.

Deliverables follow the house rule: for an individual lab test case the per-case `<case-id>.log`
**is** the deliverable; an `after-action-<suite>.md` is for a whole campaign, written from that
run's own logs, and only when it is a campaign or Terrence asks.

## 6. Fold durable lessons into the records that outlive the session

Three homes, no duplication, every entry dated:

- **`orient-dt`** gets *mechanics and traps* — platform behaviour, driver behaviour, framework
  behaviour, diagnosis signatures. **Snapshot first** (`cp -p SKILL.md SKILL.md.pre-<YYYYMMDD>`,
  the directory's convention), date every claim, and mark observed-vs-inferred. It does **not**
  get bench facts — **not even as a "dated hint"**: a bench fact found there is deleted (the
  probe measures it into bench-state.md) and replaced with a pointer (Terrence, 2026-09-11). Paths go in its §0 table only.
- **bench-state.md** is regenerated by the probe (§4) — nothing is typed into it; a hand-entered
  fact (a new unit's name, a PDU outlet) goes in `bench-setup/tb470.static`.
- **Memory** gets the *non-obvious, cross-session* lesson — the kind that would otherwise be
  re-learned at hardware cost. Check for an existing file first and update it rather than adding a
  twin; keep the `MEMORY.md` index line under ~200 chars (the index has already exceeded its size
  limit once, so prefer detail in the topic file). Never a credential in a memory. The memory
  directory is the one `/orient-dt` §0 names: after the 2026-09-11 split it is `.claude/memory/`
  **in this repo** (device-testing is its own git repository from then on — commit memories and
  records here; the Test-cases repo symlinks to ours for the few it shares). Until the split has
  landed, memories are still under Test-cases and are committed by its `/wrap`, not from here.
- **Commit this repo, and ask about anything large.** `git status` before you finish. Large and
  binary artefacts (`*.rel`, `*.tgz`/`*.tar.gz`, `*.stdout`, `*.pcap*`, tech-support bundles,
  anything over ~10 MB) are **gitignored by default and are normally NOT retained** — the
  2026-09-11 repo creation deleted the ones it found. If the session produced such a file, **ask
  Terrence whether it should be committed (via `git add -f` / Git LFS) or deleted**; do not leave
  it sitting untracked on the share as a decision for someone else. Then **commit** the records
  (bench-state.md, the handover, skill edits, memories, per-case logs) — **and stop there.**
  **Claude cannot `git push` in this environment: Terrence's company-set permissions deny it, and
  they deny it every time — three attempts on 2026-09-11, including one Terrence had just
  approved.** Nor can Claude overwrite or force anything on the remote. So the contract is:
  Claude commits locally with a complete message; **Terrence pushes** after the session. Do not
  retry a denied push, do not chain it onto the commit, and report the branch as *committed,
  not pushed* with the hash so the push is a one-liner for him (`git push origin main`).

## 7. Traps of wrapping — each has already happened

| Trap | What it looked like | What to do instead |
|---|---|---|
| **Declaring a unit dead that is in config mode** | `% Invalid input at '^'` on every `show` | `end` / `disable` / `enable` raw, then re-read. Always `end` before you leave a console. |
| **Leaving the TFTP-serving NIC pinned 1000-only** | Nothing — until the next member reboots and boot-loops | §3. Restore `advertise 0x2f`, read the multi-line advert back. |
| **Powering a member off and not writing it down** | A "dead" unit next session | §4: power state is part of the recorded final state. |
| **Trusting a stale bench-state.md** | A record describing a bench that no longer exists | It changes only when `bench_probe.py run` runs: check its "Generated <stamp>" line, and re-run it at every wrap. |
| **Writing a *confounded* run up as a result** | A "failover outage" that was really a member that could not reboot; a "slave-failure" flow sourced on the slave | Label every run *clean* or *confounded — because …*. A confounded run still teaches; it does not grade. |
| **Recording an inference as a fact** | "The FDB is split across members" from one exactly-half observation | Date it, write *observed* and *cause inferred*, and say what would prove it. |
| **Hand-editing the `.setup` on the box** | Fixed until the next `apply` silently discards it | Re-run `bench_probe.py run`, then `apply`. Never a `.bak` beside the live file. |
| **`pkill -f` / `pgrep -f` over ssh** | Your own session dies; or a "still running" that is your own wrapper | `fuser` on device nodes; kill by PID after inspecting the owner. |
| **Reporting a step as done that you skipped** | The next session builds on it | "Skipped" is a status. Say it. |

## 8. Brief the user, then stop

Dense and skimmable, with clickable relative paths — the mirror of `/orient-dt` §9:

- **(a) Bench left as** — whole or *parked*, and per unit: power, role, stack/ring state, boot
  source and whether its pointer is valid, anything still `shutdown`, running-only or unrecovered;
  host NICs and (if netbooting) the TFTP path. From §4's reads, not from memory.
- **(b) What was restored, what was kept, what was skipped** — one line each, decisions attributed
  to the user where they made them.
- **(c) Records updated** — bench-state.md (regenerated — quote its stamp; plus `backups/<stamp>` if you applied), the handover path,
  any `orient-dt` edit (with its `pre-<YYYYMMDD>` snapshot), any memory written — **and the local
  commit hash, stated as "committed, NOT pushed — push is yours"** (§6: Claude cannot push here).
- **(d) OPEN items and the first action for the next session.**

Then stop. Do not start the next session's work, and do not invent an agenda.
