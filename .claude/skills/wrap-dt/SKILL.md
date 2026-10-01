---
name: wrap-dt
description: Wrap a device-testing session on ANY testbox — stop what the session started (sentinel included), restore what it changed, ground-truth and re-probe the session's bench (the one it oriented or tested on, else the last test bench run this Test Engineer recorded, else this dev host's line in bench-setup/default-boxes, else SKIPPED), write the dated session handover with its Session facts, fold durable lessons into orient-dt / memory, and commit. Use at the end of any device-testing session. Pairs with /orient-dt.
---

# Wrap — device-testing bench (any testbox)

Leave the bench **re-runnable** and the records **true**, then stop. Pairs with `/orient-dt`,
which reads the same three records at the start of the next session: the box's bench-state.md,
the dated `SESSION-HANDOVER`, and the skill itself. Those records, never memory, are the handoff.

**Paths: this file names things, `/orient-dt` §0 says where they are.** That one table resolves
bench-state.md, `<TB>.static`, the handover locations, console.py, the memory directory,
TESTBOX-ACCESS.md, TB470-HOST-NETWORKING.md and the working-style doc (repo root =
`claude/device-testing/`). When something moves, fix §0 there, not this file.

**Design rule for this file.** Every fact that can rot is a *lookup*, not a literal: no box,
consoles, serials, outlets, addresses, builds, boot source or cable maps are written here. They
live in the box's bench-state.md and `<TB>.static`, and you read them from the hardware. What
this file holds is the **order of operations** and the **traps**, each of which has already cost
a session. **One fact, one home:** bench facts → bench-state.md; platform mechanics and framework
traps → `orient-dt`; durable non-obvious lessons → a memory file; everywhere else links.

Working style is the **"How we work"** section (`/orient-dt` §0): report what you *did*, not what
you intended; a step you skipped is reported as skipped; **ask** before any restore or revert that
is a decision rather than a cleanup. **The Test Engineer** is whoever ran this session.

---

## 0. Which bench this wrap is about

Take the FIRST rule that gives an answer, and say in the brief (§8) which one it was:

1. **The session's own bench.** The box this session oriented on (`/orient-dt` §0b), tested on
   (`/test-mode`'s Session facts) or was told to use, with the consoles and facts it used. If the
   session touched more than one box, wrap each one in turn.
2. **The last test bench run** for this Test Engineer: `/orient-dt` §0b rule 2, the newest record
   whose Session facts says `Test Engineer: <whoami>@<hostname>`.
3. **This dev host's default:** its line in `bench-setup/default-boxes` (`/orient-dt` §0b rule 3).
4. **SKIPPED.** No bench identified: no record and no `default-boxes` line for this host. **Skip
   §1's box checks, §2, §3 and §4 entirely**, and do not ssh to any box. Still do
   §1's own-process cleanup, §5 (only if the session changed records) and §6. The brief's first
   line is `Bench: SKIPPED — no test bench identified`.

**Only this session's consoles.** Every check, read and restore below touches the consoles named
for this session and nothing else on the box.

## 1. Stop what YOU started — and only what you started

Nothing below is safe while a background job of yours still holds a console or a NIC.

```bash
sock=/run/user/$(id -u)/keyring/ssh
# on the box, opening NO console: holders, locks, screen/tmux/minicom sessions, python scripts
SSH_AUTH_SOCK=$sock ssh -o BatchMode=yes <TB> \
  'cd ~/claude/device-testing/bench-setup && <PY> bench_probe.py --box <TB> precheck --consoles <list>'
```

- **Read FOUND as a list of owners, not of things to kill.** Kill only what is yours: by **PID**,
  after `ps -o user,lstart,cmd -p <pid>`.
  - A holder you did not start belongs to someone else. On 2026-09-09 a `bench_probe.py` holding
    four consoles for 45 minutes was the bench owner's. Ask; do not assume a stale job.
  - On a shared box it may be a colleague's minicom.
- **`fuser` on the device node is the only reliable "is the console held" answer.** `pgrep -f`
  matches its own ssh wrapper even with the `[b]racket` trick (2026-09-09), and `pkill -f
  <script>` over ssh kills your own session.
- Leaving a sniffer or a sender running is how the next session's traffic test measures yours.
- **On a shared box, log out of every console you opened** (`exit` at the exec prompt). The probe
  and console.py leave a console logged in as manager, which is someone else's console afterwards.
- **The sentinel stands down with you** (orient-dt §10, mandatory for test sessions).
  - In `/test-mode` both roles are yours: confirm no bench-runner subagent is still running, stop
    your Monitor, delete your cron trigger (`CronDelete`), and sweep stray `sentinel.sh`
    processes as in the kit's ARMING step.
  - In the two-session shape: as the tester, SendMessage the sentinel a final "wrapped at
    <commit>, stand down"; as the sentinel, do the Monitor, cron and sweep steps above.
  - Record in the handover that it stood down.

## 2. Restore what you changed on the DUTs

Read your own session for every `configure terminal` you sent. For each change, decide **keep,
revert, or record**, and say which:

- **Session-scoped settings always revert:** `terminal no monitor`, and **`end` on every console
  you touched.** A console left in `configure terminal` answers every plain `show` with
  `% Invalid input detected at '^' marker` and reads as a dead unit to the next session (u5,
  2026-09-09: declared dead for an hour). Console mode persists across serial sessions.
- **Temporary addressing and test config** (a scratch SVI, an `access vlan` you moved a port
  into, a `channel-group`, a forced `speed`/`duplex`) are **decisions**: some are the bench's new
  intended state, some are debris. Do not guess. List them to the Test Engineer with keep/revert
  per item.
  - Anything kept goes into the handover, and into the `.setup` via `bench_probe.py apply` if it
    changes the topology.
  - Anything reverted is reverted *and* confirmed by a re-read, not by the absence of an error.
- **`write` only what is meant to survive a reboot**, and say so. Unsaved config is not "safe": a
  member that reboots (or netboots) comes back without it, silently.
- **Do not "tidy" a live stack's ring or aggregation config on the way out.** If it is wrong, it
  is a finding for the handover, not a wrap-time fix.

## 3. Restore what you changed on the testbox

The box is shared infrastructure, and it may be the DUTs' **boot server** (tb470 was, under
netboot; the box's bench-state.md "boot image" column says whether it is now).

- **Undo every `ethtool` pinning** you made. On a netbooting bench, above all undo it on the NIC
  that serves TFTP:
  - A NIC left at `advertise 0x20` (1000-only) cannot negotiate with the bootloader's
    10/100-class ASIX dongle, so **the next member that reboots boot-loops** (`Failed to load
    tftp://…` → `Restarting system in 5..`).
  - Restore with `ethtool -s ethN autoneg on advertise 0x2f` (10/100/1000; add bit 47,
    `0x80000000002f`, where the NIC also offered 2500baseT). Then **read the multi-line
    "Advertised link modes" back**: a one-line `grep` truncates it and reports 10baseT only.
  - Under flash boot the pinning still breaks the host↔DUT edge it sits on, so undo it regardless.
- Remove temporary IPs, routes, ARP entries and firewall rules you added, and leave DHCP/TFTP as
  you found them. On tb470 the reference is **TB470-HOST-NETWORKING.md**. A rule the Test Engineer
  added themselves is theirs to remove; list it in the handover.
- `/tmp/ckprobe/`, `/tmp/ckorient/` and the session scratchpad are scratch, and **losing them is
  correct** (on tb470 `/tmp` is tmpfs and dies with the box).
  - Anything worth running twice becomes a repo tool. Anything worth running once is already
    gone. The *recipe* goes into the handover (§5).
  - Never leave a `.py` in the lab tree ([[no-stray-scripts]], enforced by a hook, Bash heredocs
    included). The one exception that recurs is the box-side driver scratch (`drv.py` + a copy of
    **console.py**): recreate it from the maintained copy named in `/orient-dt` §0 when tmpfs has
    been wiped.

## 4. Ground-truth the FINAL state and record it — this is the handoff

Recorded state is always stale. The next session's `/orient-dt` will re-read the hardware, but it
needs to know what you *left*, and why. Read, don't recall, on this session's consoles only:

- **Every DUT console:**
  - `show stack`: are members `Ready`, and who is master? Mastership moves after every failover
    and never pre-empts.
  - `show epsr`, if any ring is configured.
  - `show boot`: **does the boot image read `(file exists)`?** A stale pointer strands the next
    reload.
  - `show system`: compare the **build date on every member against each other**. A mismatch is
    the split hazard, and `show boot` will not show it.
  - `show reboot history`: any new entries since your start? Match framework power cycles
    against the run's `Power cycle … completed` lines.
  - Free flash (`dir`).
  - **Running-config vs startup-config:** `show running-config | include <what you added>`
    against `show startup-config`. Anything running-only reverts on the next reload.
- **Power state of every unit.** A member you powered off to stop a boot-loop **must be written
  down**: to the next person it is a dead unit. The same goes for anything left `shutdown`.
- **The box:** host NIC carrier (`cat /sys/class/net/<nic>/carrier`), `ip -br addr`, and, if the
  bench netboots, whether the TFTP path is currently usable.

Then regenerate the box's **bench-state.md** from the hardware, with the session's facts. On the
box:

```bash
cd ~/claude/device-testing/bench-setup && <PY> bench_probe.py --box <TB> run --consoles <list> \
   [--pdu <ip> --outlet …] [--read-only]
```

| result | what to do |
| --- | --- |
| **MATCH** | the bench is the intended template. Nothing more to do here |
| **MISMATCH** | either you left the bench changed (restore it and re-run), or the bench has legitimately changed and the template must follow it. `apply` writes the new `.setup` (snapshot into `backups/<stamp>.*`; refuses over a hand-edit; `--force` only with the Test Engineer's say-so). **That is a decision, not a cleanup**: never `apply` from a bench that is mid-campaign, split or missing a member |
| **NEEDS-CHECK** | something the run could not verify: a console someone else held, a NIC with no carrier, a MAC not learned. Report it in the handover as OPEN; do not `apply` over it |
| **USER-CONFLICT** | a session fact disagrees with `<TB>.static` or the bench. Ask the Test Engineer which is right; change neither side on your own; record the answer |

Inferences, open questions, why a port is shut, what you powered off: all of that goes in the
**handover** (§5), never in bench-state.md.

## 5. Write the session handover

Where it goes (`/orient-dt` §0 "session handovers"):
- `<TB>/<FAMILY>/SESSION-HANDOVER-<YYYY-MM-DD>.md` for a session on a bench;
- `handovers/SESSION-HANDOVER-<YYYY-MM-DD>-<user>.md` for a SKIPPED session that still changed
  records.

A same-day re-wrap adds a dated section at the top of the existing file. Look at the previous one
for shape.

**It opens with a Session facts block.** This is what `/orient-dt` §0b reads to find "the last
test bench run":

```
## Session facts
Test Engineer: <whoami>@<hostname>
Testbox: <TB>            (or: none — SKIPPED)
Consoles: u2,u3,u4,u5
PDU: <ip>; outlets u2=6, u3=8, …   (or: none)
Constraints: <verbatim, or none>
```

Copy these from the session's queue file or orient, as given. Never "correct" them.

It must be **self-contained**: the next session has none of your scratchpad, so every command
sequence it will need is written in, not referenced. If the session is **paused rather than
wrapped**, still write it, headed "PAUSED, not wrapped", listing what is running-only vs saved and
what was mid-flight (the 2026-09-11 tb470 handover is the model).

Sections that earn their place:
- **TL;DR**: where things are, and whether the bench is whole or *parked*.
- **Current bench state and how to verify it**, in one command block.
- **What was accomplished.**
- **Results**, with each run labelled *clean* or *confounded, and why*. A flow sourced on the
  member that failed measures nothing; an outage that includes a member that could not reboot is
  not a failover number.
- **Findings**, separated into *measured* and *inferred*.
- **OPEN questions** as questions, with the evidence path.
- **Ordered next steps.**
- **Recipes.**
- **Pointers.**

Link the box's bench-state.md for the topology rather than duplicating it.

**Deliverables are not the handover's job.** Each case's final `.log` and its `.cfg` files are
made only by `/create-logs`, on the Test Engineer's request (`logged-output.md`). The wrap
never writes or edits a case log. The handover's **Results** section is built from the queue's
`## Results` table, and it says, per campaign group, either:
- **final logs created** (the `/create-logs` commit hash), or
- **final logs NOT created yet: `<n>` cases still hold `work/`. Run `/create-logs <queue file>`
  after review.** Find these with `find <TB>/<FAMILY> -type d -name work`.

An `after-action-<suite>.md` is written only when the Test Engineer asks for one.

## 6. Fold durable lessons into the records that outlive the session

Four homes, no duplication, every entry dated:

- **`platforms/<FAMILY>.md`** gets what is true of the DUT's product family only: hardware
  limits, boot and bootloader behaviour, build naming, CLI differences, measured quirks, with
  the box and build each was measured on (`platforms/README.md`). No file for the family yet →
  start one when the session measured something worth keeping.
- **`orient-dt`** gets *mechanics and traps* true of any AW+ product: driver behaviour,
  framework behaviour, stack mechanics, diagnosis signatures.
  - **Git is the history.** Do not leave `SKILL.md.pre-<date>` snapshot copies (retired
    2026-10-02, when the 21 existing ones were deleted); commit the edit with a message saying
    what changed. Date every claim, and mark observed vs inferred. Say which box it was measured
    on.
  - It does **not** get bench facts, **not even as a "dated hint"**. A bench fact found there is
    deleted (the probe measures it into bench-state.md) and replaced with a pointer (bench owner,
    2026-09-11).
  - Paths go in its §0 table only.
- **bench-state.md** is regenerated by the probe (§4), so nothing is typed into it. A hand-entered
  fact (a new unit's name, a PDU outlet) goes in the box's `<TB>.static`, and only on the Test
  Engineer's word.
- **Memory** gets the *non-obvious, cross-session* lesson: the kind that would otherwise be
  re-learned at hardware cost.
  - Check for an existing file first, and update it rather than adding a twin.
  - Keep the `MEMORY.md` index line under ~200 chars; the index has exceeded its size limit
    once, so prefer detail in the topic file.
  - Never put a credential in a memory.
  - The memory directory is `.claude/memory/` **in this repo**: commit memories here; the
    Test-cases repo symlinks to ours for the few it shares.
- **Commit this repo, and ask about anything large.** Run `git status` before you finish.
  - Large and binary artefacts (`*.rel`, `*.tgz`/`*.tar.gz`, `*.stdout`, `*.pcap*`, tech-support
    bundles, anything over ~10 MB) are **gitignored by default and normally NOT retained**.
  - If the session produced one, **ask the Test Engineer whether to commit it (`git add -f` /
    Git LFS) or delete it**. Do not leave it untracked on the share as a decision for someone
    else.
  - Then **commit** the records (bench-state.md, the handover, skill edits, memories, the
    queue's Results table, and any working logs not yet committed), **and stop there.** Never
    delete a `work/` folder at a wrap; only `/create-logs` does that.
- **Claude cannot `git push` here.** Company-set permissions deny it every time, including
  straight after a human approved it (three attempts on 2026-09-11), and nothing on the remote can
  be overwritten or forced. So:
  - commit locally with a complete message;
  - **the Test Engineer pushes** after the session;
  - do not retry a denied push, and do not chain it onto the commit;
  - report the branch as *committed, not pushed* with the hash, so the push is a one-liner
    (`git push origin main`).

## 7. Traps of wrapping — each has already happened

| Trap | What it looked like | What to do instead |
|---|---|---|
| **Declaring a unit dead that is in config mode** | `% Invalid input at '^'` on every `show` | `end` / `disable` / `enable` raw, then re-read. Always `end` before you leave a console. |
| **Leaving the TFTP-serving NIC pinned 1000-only** | Nothing, until the next member reboots and boot-loops | §3. Restore the full advert, and read the multi-line list back. |
| **Powering a member off and not writing it down** | A "dead" unit next session | §4: power state is part of the recorded final state. |
| **Trusting a stale bench-state.md** | A record describing a bench that no longer exists | It changes only when `bench_probe.py run` runs: check its "Generated <stamp>" line, and re-run it at every wrap. |
| **Wrapping the wrong bench** | tb470 re-probed by a session that worked on another box, or by another user's session | §0: the session's own bench, else the last recorded run, else this host's `default-boxes` line, else SKIPPED. |
| **Touching someone else's console on the way out** | A colleague's minicom logged out, or a probe across every `/dev/uN` | Only the session's consoles; `precheck` first; never displace. |
| **Writing a *confounded* run up as a result** | A "failover outage" that was really a member that could not reboot; a "slave-failure" flow sourced on the slave | Label every run *clean* or *confounded — because …*. A confounded run still teaches; it does not grade. |
| **Recording an inference as a fact** | "The FDB is split across members" from one exactly-half observation | Date it, write *observed* and *cause inferred*, and say what would prove it. |
| **Hand-editing the `.setup` on the box** | Fixed until the next `apply` silently discards it | Re-run `bench_probe.py run`, then `apply`. Never a `.bak` beside the live file. |
| **`pkill -f` / `pgrep -f` over ssh** | Your own session dies; or a "still running" that is your own wrapper | `fuser` on device nodes; kill by PID after inspecting the owner. |
| **Reporting a step as done that you skipped** | The next session builds on it | "Skipped" is a status. Say it. |

## 8. Brief the user, then stop

Dense and skimmable, with clickable relative paths: the mirror of `/orient-dt` §9.

- **(0) Bench:** `<TB>` and how §0 chose it (session's own / last recorded run / this host's
  `default-boxes` line), the consoles, and the occupancy result. Or `SKIPPED — no test bench identified`.
- **(a) Bench left as:** whole or *parked*. Per unit: power, role, stack/ring state, boot source
  and whether its pointer is valid, and anything still `shutdown`, running-only or unrecovered.
  Also the host NICs, and the TFTP path if the bench netboots. From §4's reads, not from memory.
  With SKIPPED: "not checked: no bench".
- **(b) What was restored, what was kept, what was skipped:** one line each, with decisions
  attributed to the Test Engineer where they made them.
- **(c) Records updated:**
  - bench-state.md (regenerated; quote its stamp, plus `backups/<stamp>` if you applied);
  - the handover path;
  - final logs: created (hash) or **pending `/create-logs`** (how many cases);
  - any `orient-dt` edit, with its commit hash;
  - any memory written;
  - **the local commit hash, stated as "committed, NOT pushed — push is yours"** (§6).
- **(d) OPEN items and the first action for the next session.**

Then stop. Do not start the next session's work, and do not invent an agenda.
