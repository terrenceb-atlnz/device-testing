# After-action — TEST 38376 (stack-master reboot ×300), tb470 IE520 4-member stack

**Written:** 2026-09-20, from this run directory's own logs.
**Run:** 2026-09-18 23:53 → 2026-09-20 03:48 NZST, **27.9 h**, unattended.
**Harness:** `IE520/stack-tests/stack_reboot_test.py --mode master --cycles 300 --settle 30`,
framework-driven, bound from `/home/st-art/st-art/configs/tb470.setup`. Logs in this directory.
**Bench:** 4-member AT-IE520-28GSX VCStack, VC ID 3439, VMAC `0000.cd37.0d6f`,
`stack virtual-mac` on, all members `awplus_main-20260913-1734` (build Sun Sep 13), flash boot.
Ring 1—2—4—3—1 on ports 27/28. No device configuration was changed at any point.

## Headline

**300 PASS / 0 FAIL / 0 UNMEASURED.** Every cycle rebooted whichever member was Active Master
at that moment, confirmed a *different* member took over, confirmed the rebooted unit came back
on its own console, and confirmed the stack returned to `Normal operation` with all eight
stackports showing a learnt neighbour. No power-recovery was ever needed.

## Measurements (n = 300 unless stated)

| | min | median | p90 | max |
| --- | --- | --- | --- | --- |
| **failover** — reboot → a survivor reads a new Active Master `Ready` | 11.9 s | **13.1 s** | 14.5 s | 27.6 s |
| **target boot** — reboot → rebooted unit's own `login:` | 168.3 s | **174.7 s** | 177.7 s | 180.0 s |
| **stack whole** — reboot → all members `Ready`, all stackports learnt | 286.4 s | **293.0 s** | 296.6 s | 300.0 s |
| whole cycle (incl. 30 s settle) | 298.0 s | 304.9 s | 308.5 s | 315.5 s |

**Read `failover` as a poll-confirmed figure with ~3 s granularity** (one `show stack` round
trip plus the poll sleep) — it is an upper bound on the true failover, not a fine measurement.
The finer `has become the Active Master` console timestamp was visible on only **11 of 300**
cycles (median **8.7 s**, range 8.3–11.9 s); see "Why the promotion message is usually absent".
**Do not quote 13.1 s and 8.7 s as if they were the same measurement** — they are not.

For scale, the 2026-09-11 T10623 failover measurements on this bench (traffic-continuity, not
control-plane) were ~2.05–2.08 s of data-plane gap with `virtual-mac` on. That measures a
different thing again (packet loss through the stack, not when the CLI reports a new master).

## Mastership behaviour — exactly as the priorities predict

Targets split **150 / 150 between members 2 and 3**, and the resulting master split
150 / 150 the same way: mastership alternated **2 ↔ 3** for all 300 cycles and never landed on
member 1 or 4.

That is correct, not a harness artefact. Member 2 is `stack 2 priority 2` (lowest value wins an
election); among the priority-128 members, 3 holds the lowest MAC (`…0740` vs `…0ac0`, `…09c0`).
So rebooting 2 elects 3, and rebooting 3 elects 2. **Consequence worth stating: a master-reboot
loop on this bench exercises only members 2 and 3.** Members 1 and 4 are never the target, so
this case says nothing about their behaviour under reboot — that is what the member-reboot case
(38377) is for.

## Health evidence across the campaign — all clean

- **0** cycles with more than one `BootROM <ver>` banner in a boot capture (a second banner
  would mean the unit reset itself mid-boot).
- **0** collateral reboots: no member other than the cycle's target ever gained a new
  reboot-history entry. Every member's newest entry was checked every cycle.
- **0** `Unexpected` reboot-history entries created during the run. The newest `Unexpected`
  entries on the bench still date from 2026-09-17 and earlier, i.e. before this campaign.
- **0** exception-log growth, **0** fatal signatures in boot captures or `show log tail`.
- **0** power-recoveries invoked.
- No split, no duplicate master, no `Disabled Master`, no stranded member at any point.

## Why the promotion message is usually absent (and why that is not a defect)

`has become the Active Master` is a **log** message. This harness deliberately leaves
`terminal monitor` **off**, because the framework console driver was measured (2026-09-02) to
time out on ~17 % of commands with monitor on versus 0/24 with it off. A survivor console that
is *logged in* therefore never displays the message; one sitting at a *login prompt* does,
because the platform prints there regardless. Which state a survivor is in varies cycle to
cycle, which is exactly why the message appeared on only 11/300 cycles.

This was originally a harness bug, not just an observation: an earlier version waited the full
180 s promotion timeout *before* polling `show stack`, and so reported a fictitious **187.4 s**
"failover" on a cycle where the message was never going to arrive, against a real 13.9 s on the
next. Message-watch and poll now run concurrently. **A campaign that timed failover from that
console message alone would have produced garbage on ~96 % of cycles here.**

## What this case does and does not establish

**Establishes:** on this build and this 4-member ring, 300 consecutive master reboots are
handled cleanly — re-election in ~13 s, the old master rejoining in ~3 min, the stack whole in
~5 min, every time, with no crash artefact, no unexpected reboot and no stack disturbance.

**Does not establish:** anything about members 1 and 4 under reboot (never targeted, above);
anything about data-plane continuity (no traffic was run — T10623/T11427 cover that); and it
does **not** clear the platform of the boot hang seen in 38377 cycle 73, which happened to
member 1 on a *member* reboot. 300 clean master reboots and that one hang are compatible: the
hang was 1 in 73 on a different member and a different stimulus.

## Bench state at exit

`Normal operation`, all four members `Ready`, all eight stackports `Learnt neighbor`,
VMAC `0000.cd37.0d6f`. **Active Master is member 3** (`/dev/u5`) — mastership is not pinned and
moves with every failover; read `show stack`. Consoles free, no processes left running, no
configuration changed. Startup config untouched throughout (this case never writes).
