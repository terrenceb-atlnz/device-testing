# After-action — TEST 38377 (backup-member reboot ×300), tb470 IE520 4-member stack

**Written:** 2026-09-18, from this run directory's own logs, immediately after the event.
**Status: RUN STOPPED AT CYCLE 73 OF 300 — not a completed campaign.** The headline is the
cycle-73 event, not a pass rate.
**Harness:** `IE520/stack-tests/stack_reboot_test.py --mode member --cycles 300 --settle 30`,
framework-driven, bound from `/home/st-art/st-art/configs/tb470.setup`.
**Bench:** 4-member AT-IE520-28GSX VCStack, VC ID 3439, VMAC `0000.cd37.0d6f`, all members
`awplus_main-20260913-1734` (build Sun Sep 13 11:21 UTC), flash boot.

| member | S/N | console | PDU |
| --- | --- | --- | --- |
| 1 | 264A23061 | `/dev/u2` | outlet 6 (F) |
| 2 | 264A23068 | `/dev/u3` | outlet 8 (H) |
| 3 | 264A23066 | `/dev/u5` | outlet 5 (E) |
| 4 | 264A23052 | `/dev/u4` | outlet 4 (D) |

Master was member 2 throughout cycles 1–73. The loop rotates the three **backups**, so the
targets cycled 1 → 3 → 4 → 1 …; member 2 was never a target.

---

## 1. Headline

**72 cycles PASS. On cycle 73, member 1 (S/N 264A23061) failed to boot: it hung at kernel
handoff and never returned.** It did not self-recover in ~35 minutes and was restored only by
a PDU power cycle, after which it booted normally in 145 s and rejoined.

**Rate: 1 boot hang in 73 commanded member reboots** on this build. Cycles 1–72 were
uneventful — every one restored the stack to `Normal operation` with all eight stackports
showing a learnt neighbour, in a tight 297 ± 5 s.

## 2. What the evidence shows, in order

Raw: `evidence-cycle073.txt` (harness-collected at the moment of failure),
`evidence-cycle073-aftermath.txt`, `evidence-cycle073-recovery.txt`,
`member1-powercycle-boot.log`, `38377.log`, `38377-summary.json`, per-member framework
console transcripts `swi_a..swi_d.log`.

1. **The reboot was commanded and accepted normally.** 22:41:47 NZST, `reboot stack-member 1`
   from the master console, `(y/n)` prompt seen and answered. Member 1's own reboot history
   later shows `2026-09-18 10:42:05 Expected User Request` (device UTC ≈ host −12 h) — i.e. the
   unit logged our request before going down.
2. **The bootloader completed perfectly.** The capture holds exactly one `BootROM 1.41`
   banner, then DDR3 training, `BootROM: Image checksum verification PASSED`,
   `U-Boot 2025.01-04844-gd2292467da4d`, then the FIT image load — kernel (4 427 624 B),
   ramdisk (35 602 432 B) and FDT all loaded with **every hash verified**
   (`sha1+ OK`, `sha1+ OK`, `crc32+ OK`), UBIFS unmounted cleanly.
3. **It then went silent at the handoff and stayed silent.** The capture ends:
   ```
   Starting kernel ...
   ```
   **Exactly 24 bytes follow** (a trailing CR/LF). The kernel produced **no output at all** —
   not a panic, not an Oops, not a single line — for the remaining ~880 s of the 900 s window.
4. **No watchdog rescue.** One `BootROM` banner in 900 s. Thirty-five minutes after the
   reboot the console still returned **0 bytes to a bare CR**, read with the port held
   exclusively. Contrast the 2026-08-26 cycle-293 wedge, which self-reset in a fixed ~50–52 s.
5. **The stack behaved correctly around it.** Member 1 read `Provisioned` with no MAC and no
   status; its two neighbour ports (`port2.0.27`, `port3.0.28`) read `Down`; members 2, 4, 3
   held a healthy 2—4—3 chain, all `Ready`, at `Not all stack ports are up`. No split, no
   duplicate master, no `Disabled Master`.
6. **The unit is not dead.** PDU outlet 6 off → 20 s → on; member 1 reached a login prompt in
   **145 s**, went `Syncing` then `Ready`, and the stack returned to `Normal operation` with
   all eight stackports learnt.

### The critical evidence gap, stated up front

**The hang left no trace on the device itself.** Member 1's newest reboot-history entry is
still the `Expected User Request` we commanded — there is no entry for the hang, and none for
the power cycle (a unit that is wedged and then loses power cannot log either). Everything
known about this event was observed **from outside**: the serial capture and the surviving
members' view. This mirrors the cycle-293 finding, where member 1 likewise "retained no log of
its own wedge".

## 3. Why the harness caught it (and which check did)

Three independent per-cycle checks; only one fired, and it was not the one that looks most
obvious:

| check | verdict on cycle 73 |
| --- | --- |
| target console shows a boot and returns to `login:` | **FAILED — this is what caught it** |
| `show reboot history` gains a new `Expected` entry for the target | **passed** — the entry exists; the unit logged the request before dying |
| no fatal signatures in the boot capture / log tail | **passed** — there were none to find; the unit emitted nothing |

Had the harness graded on reboot-history or on console-text signatures alone, this event would
have scored a clean PASS. That is the argument for positive, independent evidence per cycle.

## 4. Second event — member 2 unexpected reboot; CAUSE NOT ESTABLISHED, my action is the prime suspect

Member 2 logged `2026-09-18 11:14:05 Unexpected System reboot` (≈ 23:16 NZST), which moved
mastership from member 2 to member 3. **This is ~3 minutes after I killed the campaign process
(PID 15161) at ~23:13**, and I cannot exclude that I caused it:

- `AWPConsoleCore._connect_serial()` opens a **physical** console as plain
  `serial.Serial(tty, baudRate)` — **no `stty -hupcl`, no DTR guard** (only the VM branch sets
  `dsrdtr=True`). Killing the process closed all four bound ports, and on this platform a port
  close drops DTR, which the IE520 reads as a **BREAK**.
- Against that: a BREAK normally parks a unit at the bootloader rather than rebooting it, and
  the entry reads `System reboot`, not a bootloader park. Member 2 also carries by far the
  fleet's longest run of spontaneous `Unexpected System reboot` entries (2026-09-16, 09-15 ×3,
  09-09, 09-06 ×3, 09-05, 09-04) **including** `Rebooting due to critical process (marvell)
  failure!` on 09-15.

**Do not report this as a product fault.** It is recorded here so the next session knows it
happened and why it is ambiguous. Members 3 and 4 took no unexpected reboots at any point today.

**Durable lesson:** a framework-driven run must not be stopped by killing the process while it
holds consoles. Apply `stty -hupcl` to every `/dev/uN` the run will bind *before* starting it
(done on all four after this event), or stop the run by a means that lets it close cleanly.

## 5. Comparison with the prior corpus

| campaign | stimulus | events |
| --- | --- | --- |
| 38378, 2026-08-25/26 (2-member) | stackport shutdown ×300 | 1 whole-CPU wedge at cycle 293, watchdog-recovered ~52 s |
| repro, 2026-08-26 (2-member) | redundant shutdown ×2000 | 1 wedge at iteration 1550 (unit 264A23066), ~50 s |
| post-swap A/B, 2026-08-26 | redundant shutdown ×2000 each | clean |
| **38378, 2026-09-18 (4-member ring)** | **stackport shutdown ×300** | **clean — 300 PASS** |
| **38377, 2026-09-18 (4-member)** | **member reboot ×73** | **1 boot hang, NOT watchdog-recovered** |

The 2026-08-26 events were *running* units freezing and being recovered by a fixed ~52 s
hardware watchdog. **This is a different failure mode**: a unit that never finished booting,
with no watchdog recovery in 35 minutes. Whether they share a root cause is unknown and is not
claimed here. Note also that the suspect unit of the old campaign (264A23066) is now member 3
and was **not** the unit that hung — this was 264A23061.

## 6. Status of the case

**38377 is UNMEASURED as a 300-cycle case.** 72 clean cycles plus one hang is not a verdict on
"300 member reboots"; report the event, not a pass rate. A re-run is needed for a case verdict,
and the harness should power-cycle a member that fails to boot so the remaining cycles can
still be measured (see §7).

## 7. Follow-ups

1. **Make the harness self-healing** (not yet done): on a boot-timeout, collect evidence, then
   power-cycle the target through its declared `[powerlink]` and continue. The `.setup` already
   declares `pwr_a..pwr_d`, so this needs no bench change. Without it, one hang ends the run.
2. **Note for `ATPower.PduPower`:** it raises `OSError(40) Too many levels of symbolic links`
   when `logFilePath` equals the cwd (it symlinks its log onto itself), and
   `FileNotFoundError` if `logFilePath` does not already exist. Run from a different directory
   and `mkdir -p` the log dir first. Also `on()` can return `False` while having worked — the
   PDU's `status.xml` lags the command; re-read `is_on()` before believing it.
3. **Bench left whole:** stack `Normal operation`, all four `Ready`, all eight stackports
   learnt, **master is now member 3** (`/dev/u5`) — it moved off member 2 during this event and
   is not pinned. Consoles free; no config changed at any point in this campaign.
