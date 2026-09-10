# After-action — TEST 38378, IE520 stack-port shutdown ×300

**Written:** 2026-09-01, from this run directory's own logs.
**Run directory:** `~/old test runs/IE520/stack-tests/failover-300/`
**Bench:** tb470, AT-IE520-28GSX two-member VCStack, chassis-id 3439, VMAC `0000.cd37.0d6f`
**Software:** `IE520-tomahawk_ie520-continuous`, build 08/19/26 02:20:43, booted from
`flash:/IE520-20260825.rel`. Bootloader 9.1.0 / U-Boot 2025.01-04844-gd2292467da4d.

| | Member 1 | Member 2 |
|---|---|---|
| Serial | **264A23066** | 264A23052 |
| MAC | `84e3.2787.0740` | `84e3.2787.09c0` |
| Console | `/dev/u5` | `/dev/u4` |

Stacking is **two** pairs — `port1.0.27↔port2.0.28` and `port1.0.28↔port2.0.27`, both TE
Connectivity 1-2127931-2 copper direct-attach. No resiliency link configured.

**Headline:** 300 cycles, 17 h 48 m. **292 PASS / 0 FAIL / 8 UNMEASURED.** Member 1 hard-locked
on cycle 293 and was recovered by its own watchdog; cycles 294–300 could not be measured.

> Scoring note: the wedge was recorded **UNMEASURED, not FAIL**, because the harness could not
> read the stack to grade the cycle. Do not report this as "1 failure in 300" — the run produced
> zero graded failures and one unmeasurable event. The event is the finding.

---

## 1. What is the actual issue?

**The unit stops executing entirely — a whole-CPU lockup — and is recovered ~52 s later by an
unannounced hardware watchdog reset.** It is not a reload, not a kernel-load failure, and not a
stacking-protocol fault.

What the evidence shows, in order:

1. **The CLI stops echoing mid-session.** `38378-console-full.log` line 34515 is the last byte
   member 1 ever emitted. The next two commands (`end`, `show stack`) get **no echo at all** —
   not an error, not a prompt, nothing. A device that is merely busy still echoes.
2. **It stops transmitting on the stack link.** Member 2's TIPC keepalive to member 1 times out
   at `22:33:29Z` (`probe-2000ms.1`), then again at 2500 ms (`probe-2500ms.1`).
3. **The link itself was healthy.** Member 2's `vlan4094` counters in those same captures read
   `RX packets:3000960 errors:0 dropped:0 overruns:0 frame:0`. Nothing was corrupting traffic —
   member 1 simply went silent.
4. **HA failover then worked exactly as designed.** Member 2 detected the loss, elected itself,
   and took over at `22:33:34Z` — one second after detection (`m2-stacking.1`). The surviving
   stack behaved correctly throughout. *The failover is not the defect; it is the symptom
   working properly.*
5. **The unit emitted nothing on the way down.** No panic, no oops, no stack trace, no core file,
   no `exception.log` entry, no shutdown sequence. Confirmed as a genuine absence, not an unread
   file.
6. **It recovered by hardware watchdog, not by software.** The console goes straight from silence
   to `BootROM 1.41` with no intervening output.

**Critical evidence gap, stated up front:** member 1 retained *no log of its own wedge*. All four
files pulled from it (`messages.1`, `stacking.1`, `vcs-awplus-messages.2`, `startup_messages`)
begin at or after `22:35:34Z` — i.e. after the reset. The hard reset gave syslog no chance to
flush. Everything we know about the wedge is observed **from outside**, by member 2 and by the
tb470-side serial capture.

### Derived finding — the reset interval is fixed at ~52 s

Not stated in the original notes; it falls out of cross-checking the two independent events:

| Event | Freeze | Reset | Interval |
|---|---|---|---|
| Cycle 293 | ~`22:33:27Z` (last TX before the 2000 ms probe timeout at `22:33:29`) | `22:34:20Z` — member 2 logs `Link down event on stack link port2.0.27`, i.e. member 1's PHY dropping as it reset | **~52 s** |
| Repro iter 1550 | `13:20:30` NZST (last `NSM: port1.0.27 user shutdown`) | `13:21:20` — `BootROM 1.41` on the witness capture | **50 s** |

Two independent measurements agreeing at ~50–52 s is the signature of a **fixed-duration hardware
watchdog** (`f1020300.watchdog`, visible in `hafailover-monitor`), not of a software recovery
path — a software timeout would vary with load. This matters diagnostically: **the CPU was gone
for the whole 52 s**, unable even to service the watchdog kick. That rules out a stuck userspace
daemon and points at a lockup with interrupts disabled or a non-preemptible deadlock.

It also matches the **~42 s** self-reset recorded for the separate IE520 i2c lockup investigation
on this same platform — see §5.

---

## 2. What triggered it?

**A redundant `shutdown` — the `shutdown` command issued against a stackport that is *already* in
`disabled` state.**

The mechanism that creates the redundancy is a platform behaviour measured on the bench before
the run: **shutting one end of a stacking pair downs *both* ends.** So when the harness walks a
pair and shuts each port in turn, the second command is always redundant.

From `38378-console-full.log`, cycle 293 verbatim:

```
34495  >>> interface port1.0.27
34497  % port1.0.27 is currently configured as a stack-port. Use caution when altering its config
34500  >>> shutdown
34502  switch: port 1(port1.0.27) entered disabled state      <- near end goes down
34503  switch: port 47(port2.0.28) entered disabled state      <- FAR end goes down too
34504  % Warning: "shutdown" command is not saved to configuration for stackports
34507  >>> interface port2.0.28
34512  >>> shutdown                                            <- REDUNDANT: already disabled
34514  % Warning: "shutdown" command is not saved to configuration for stackports
34515  awplus(config-if)#switch: port 47(port2.0.28) entered disabled state
34517  >>> end                                                 <- NO ECHO. Wedged here.
```

Line 34512 is the last command the unit ever acknowledged.

Three qualifiers that matter for a defect report:

- **The victim is the physical unit, not the stack role and not the command direction.** In cycle
  293 member 1 was master and issued the redundant shutdown at member 2's port — *member 1*
  wedged, i.e. the **issuer**. In the reproduction member 2 was master and hammered member 1's
  port — *member 1* wedged again, i.e. the **owner of the targeted port**. The one invariant
  across both is the chassis: **264A23066**.
- **`shutdown` on a stackport is runtime-only.** It warns
  `% Warning: "shutdown" command is not saved to configuration for stackports`, persists nothing,
  and is undone by a reboot.
- **The trigger is a command, not a hotplug or cabling event.** Nothing was physically touched;
  the direct-attach cables stayed seated throughout.

---

## 3. Fastest reproduction

**`repro_38378.py` — reproduced the wedge in 21 minutes, against 17.8 hours for the full test.**
That is a **~50× speed-up**, and it is the tool to use for any further work on this.

The insight behind it: the 300-cycle test spends ~200 s per cycle shutting a pair, waiting for
convergence, restoring it, and waiting for the stack to re-form — but only **one command in each
cycle** is the trigger. Strip everything else away and issue that command in a loop.

### Requirements

- A **two-member IE520 stack with BOTH stackport pairs cabled**. This is essential: one pair is
  held up as the *carrier* while the other is hammered. With a single pair a shutdown splits the
  stack, which measures something else entirely.
- Console access to the master (`/dev/u4` or `/dev/u5` on tb470) and, for evidence, the peer
  console for a read-only witness.
- `console.py`, `repro_38378.py`, `witness_log.py` from this directory. Python 3 + pyserial. No
  framework, no `.setup`, no `sudo`.

### Commands

```bash
export SSH_AUTH_SOCK=/run/user/1971/keyring/ssh
ssh tb470
cd ~/old\ test\ runs/IE520/stack-tests/failover-300/

# timestamped read-only witness on the PEER console (the unit expected to wedge)
./witness_log.py /dev/u5 witness-member1.log &

# hammer: carrier pair stays up; victim pair shut once; then redundant shutdown in a loop
./repro_38378.py --master /dev/u4 --carrier port1.0.28,port2.0.27 \
    --shut-first port2.0.28 --target port1.0.27 --iterations 2000 --check-every 50
```

Swap `--shut-first` / `--target` to hammer the other member.

### Reading it

- `state=DEGRADED` is **expected and correct** — one pair is deliberately down. The failure
  signals are `carrier_ok=False` or a wedge.
- ~0.61 s/iteration, so 2000 iterations ≈ 21 minutes.
- On a wedge the script **stops sending, listens for 300 s, and skips the restore** — so a wedge
  always needs a manual stackport restore afterwards.
- It refuses to start unless the stack is FULL with all four ports `Learnt neighbor`, and aborts
  if the carrier pair degrades — shutting a pair while the survivor is down would split the stack.

### What the reproducer cannot show

If the true cause is cumulative (a leak or drift over ~17 h) rather than the command itself, this
loop can stay clean indefinitely from a fresh boot. **A dry run weakens the command hypothesis but
does not clear it.**

---

## 4. Occurrence rate

**Order 10⁻³ — roughly 1 in 300 to 1 in 1550 redundant shutdowns, and only ever on one unit.**

Every measurement taken:

| Run | Unit hammered | Trigger events | Wedges | Rate |
|---|---|---|---|---|
| TEST 38378, 300 cycles | **264A23066** | 293 (one redundant shutdown per completed cycle) | **1** | **1 in 293** (0.34 %) |
| Repro, wedge run | **264A23066** | 1550 | **1** | **1 in 1550** (0.065 %) |
| Repro, pre-swap control | 264A23052 | 2000 | 0 | 0 |
| Repro, post-swap Run A | 264A23061 | 2000 | 0 | 0 |
| Repro, post-swap Run B | 264A23052 | 2000 | 0 | 0 |

- **On 264A23066: 2 wedges in 1843 trigger events ≈ 1 in 920.**
- **On every other unit: 0 wedges in 6000 trigger events.**

Two cautions before this number is quoted anywhere:

1. **The two rates differ by 5×** (1/293 vs 1/1550) and the loops are not the same shape, so the
   point estimates should be read as bracketing an order of magnitude, not as a precise figure.
   §5 argues the difference is itself informative.
2. **The clean runs are weaker evidence than they look.** At the observed 1-in-1550 rate, a clean
   2000-iteration run happens `exp(-2000/1550)` ≈ **27 %** of the time by chance — so each clean
   run carries only ~73 % confidence. Reaching 95 % needs ~4650 iterations (~49 min); 99 % needs
   ~7500 (~79 min). **Say "suggestive", not "proven".**

**The unit-specific conclusion is confounded and is not established.** 264A23066 is the only unit
that ever wedged — but it is also the only unit that was hammered in the run that wedged. It was
**never re-tested before it was physically removed** on 2026-08-26, so the conclusion rests on the
absence of a repeat rather than on a positive control.

---

## 5. Why only at that rate, and not every run? *(analysis — labelled opinion)*

Everything below is inference from the evidence in §1. There is no log from the failing unit, so
none of it is proven.

### The signature constrains the mechanism tightly

A total console freeze — no echo, no oops, no panic — followed by a **fixed** ~52 s hardware
watchdog reset means the CPU could not run *anything*, not even the watchdog kick. That excludes
a hung userspace daemon (the kernel would still echo) and excludes a normal deadlock that a
software timeout would eventually break. What fits is a lockup **with interrupts disabled** or a
deadlock in non-preemptible context.

### Primary hypothesis: a narrow timing race, not a logic bug

If a redundant `shutdown` were simply mishandled, it would fail *every* time — the command is
deterministic and the port state is identical on each pass. It doesn't. So the command cannot be
sufficient on its own; **something concurrent has to coincide with it.**

A redundant shutdown is a no-op at the hardware level but still runs the full port-state-change
path, and on a *stackport* it also crosses to the remote member. That puts the CLI-driven update
in contention with the VCS/TIPC stack-link handler over the same port and stack state. If those
two contexts can interleave badly, the bad window is milliseconds wide inside a ~600 ms iteration
— which lands squarely at the 10⁻³ rate actually measured. **The observed rate is what a
millisecond-wide window sampled once per iteration would produce**, and that agreement is the
main reason I favour this reading.

**This hypothesis makes a prediction the data already matches.** More concurrent stack activity
should mean a wider window and a higher hit rate. TEST 38378 surrounds each redundant shutdown
with a full pair shut, convergence wait, restore, stack re-form and repeated `show stack` polling
— lots of concurrent VCS/TIPC work. The reproducer strips all of it away. And the rates are
**1 in 293 with the churn, 1 in 1550 without it** — 5× higher where there is more to race
against. That is a real, if single-point, corroboration rather than a post-hoc story.

Supporting but weaker: at the failover instant member 2 was at **0.0 % idle** (68.5 % usr /
31.4 % sys, load 2.61, `hafailover-cpu`). Load shifts timing windows. Caveat: that snapshot is
the *survivor's*, not the wedged unit's, so treat it as context only.

### Strong alternative: this may be the known IE520 i2c lockup, reached by a different door

I rate this close to the primary hypothesis, and it may not even be a competing explanation so
much as the layer underneath it. Four things line up:

- **The watchdog interval matches.** The separately-documented IE520 i2c lockup self-resets at
  **~42 s**; we measured **50–52 s**. Same order, same mechanism class.
- **The signature matches** — total console freeze, no oops, hardware-watchdog recovery.
- **The unit matches.** 264A23066 is the same chassis the August 2026 i2c investigation
  identified as *its* failing unit. (That root cause was traced to pluggable
  `A10217F213300006`, since removed — so any surviving effect would have to be a *different*
  marginal module or the bus itself.)
- **The trigger plausibly touches i2c.** The stackports carry copper direct-attach modules, which
  are i2c-addressable pluggables; a port shutdown drives module state over that bus.
  `hafailover-monitor` shows `mv64xxx_i2c` at 3,667,363 interrupts — the bus is heavily used. An
  i2c transaction that never completes is a classic interrupts-disabled hang.

Under this reading the intermittency is bus contention rather than a state-machine race, and the
rate is set by how often the redundant shutdown's i2c access collides with other traffic on that
bus.

### What I do not believe

- **A stacking-protocol defect.** Failover detected the loss and completed correctly in ~1 s. The
  stack layer behaved well; it was the *chassis* that stopped.
- **A cabling or link fault.** `RX errors 0`, and the carrier pair stayed `Learnt neighbor`
  throughout.
- **Pure accumulation over 17 h.** The reproducer wedged 1550 iterations into a 21-minute run, so
  long uptime is not required. Not fully excluded — 1550 iterations is accumulation of a kind.

### The one test that separates all of this

**Hammer 264A23066 as a positive control.** Everything above is limited by the same gap: the
suspect unit was pulled without ever being re-tested. Two runs settle it:

1. **≥4650 iterations against 264A23066** (~49 min) — reproduces, or bounds the rate at 95 %.
2. **≥4650 against a known-good unit in the identical role** — separates "faulty unit" from
   "product defect".

Run 1 is now possible: as of **2026-09-01, 264A23066 is back on the bench** as member 1 on
`/dev/u5`. To distinguish the two hypotheses in §5, capture `show system pluggable diagnostics`
and the i2c interrupt count either side of a wedge.

---

## 6. Bench state and caveats

**Left at handover (2026-08-26):** stack `Normal operation`, all four stackports `Learnt
neighbor`, both consoles free, no processes running. Member 1 was then **264A23061**.

**Live at time of writing (2026-09-01):** stack formed and healthy, but the membership has
changed back — member 1 is **264A23066** (`84e3.2787.0740`, `/dev/u5`), member 2 is 264A23052
(`/dev/u4`). 264A23061 is absent. **No record of when or why the swap was reverted** was found in
this directory or the 2026-08-31 bench-check logs.

Also live, and relevant to any re-run:

- **Member 2 has priority 1 against member 1's 128, so the next stack reboot moves mastership to
  member 2.** Anything assuming "master = ID 1" will be wrong after one reload.
- Member 1's flash has **21.2 MB free** and holds two 41 MB `.rel` images plus ~60
  `tech-support-*.gz` and 6 `debug-*.tgz`.

Caveats on the evidence itself:

- The cycle-293 consolidated window assumes an exact +12 h device-UTC↔NZST offset; real skew was
  ~68 s on top of that. Sub-minute alignment across sources is approximate.
- The serial capture has **no timestamps** — it is anchored by content, correlated to UTC through
  member 2's logs.
- `repro_38378.py` **appends** to its logs and overwrites `repro-progress.txt`. Move them aside
  between runs or campaigns merge.
- Console logs contain NULs — `grep -a`, or a plain grep reports 0 matches indistinguishably from
  a real absence.

## 7. Evidence index

| Path | What it holds |
|---|---|
| `38378.log` | Harness verdict log, all 300 cycles |
| `38378-console-full.log` | Full member-1 serial capture (1.36 MB); the wedge is at line 34517 |
| `evidence-cycle293/38378-cycle293-CONSOLIDATED-WINDOW.txt` | Eight correlated sources across the wedge window |
| `evidence-cycle293/probe-{2000,2500}ms.1` | Earliest machine record of member 1 going silent |
| `evidence-cycle293/m2-stacking.1` | The only device-side file bracketing the wedge |
| `evidence-cycle293/hafailover-*` | Survivor's auto-captured state at failover |
| `evidence-repro-iter1550/` | The 21-minute reproduction, with timestamped witness |
| `archive-preswap-control/`, `postswap-run{A,B}-*/` | The three clean 2000-iteration runs |
| `SESSION-HANDOVER.md` | Campaign handover, incl. the unit swap and recovered config |
