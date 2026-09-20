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

---

## 8. Addendum 2026-09-21 — flash forensics, bootloader split, and a pinned reproduction

### 8.1 The "no trace" finding is now positive, not merely an absence

§2 said the hang left no trace on the device. That was inferred from the reboot history alone.
On 2026-09-21 member 1's flash and permanent log were read directly
(`evidence-cycle073-member1-forensics.txt`). The result **confirms it, and makes the absence
meaningful**:

| artefact class | newest on member 1's flash | vs. the hang (2026-09-18 ~22:42 NZST) |
| --- | --- | --- |
| `exception.log` | Sep 17 21:25 | **predates** |
| `kernel-*.txt` (3 files) | Sep 15 22:04 | **predates** |
| `debug-*.tgz` | Sep 17 21:25 | **predates** |

The crash-capture mechanism **exists and demonstrably works on this exact unit** — it wrote
three `kernel-IE520-awplus_main-20260913-1734-*.txt` dumps on Sep 15 and six
`debug-duplicate-master-*.tgz` tarballs between Sep 14 and Sep 17. It produced **nothing** for
the cycle-73 hang. That is consistent with hanging before any filesystem was writable, i.e.
genuinely at the kernel handoff and not in a later boot stage.

`show log permanent tail 60` has rolled well past the event window — it is now entirely
`LOOPPROT` warnings from Sep 20. **The permanent log holds nothing about this event**; do not
go looking again.

### 8.2 Bootloader version is NOT a lead — RULED OUT 2026-09-21

Read 2026-09-21 from `show system`:

| member | S/N | bootloader |
| --- | --- | --- |
| **1** | 264A23061 | **9.1.0** |
| 2 | 264A23068 | master-20260822-535 |
| **3** | 264A23066 | **9.1.0** |
| 4 | 264A23052 | pauld |

Member 1 hung at `Starting kernel ...`, the bootloader's last act, and runs a different variant
from members 2 and 4. **That is not a lead, and this section exists to stop the next session
chasing it.** Two independent reasons, in increasing order of strength:

1. Member 3 runs the same variant as member 1 and absorbed 24 member reboots (38377) plus 150
   master reboots (38376) with zero hangs.
2. **Decisive (Terrence, 2026-09-21): the IE520 bootloader variants differ only in how they
   relay output. They are surface-level printing changes — no bootloader work has been done
   under the hood in the past month.** The variants are therefore functionally the same code,
   and all of them predate the 2026-09-18 event (`master-20260822-535` is dated Aug 22). The
   bootloader is excluded both as a differentiator between members and as a recent-change cause.

**Corroborating evidence (Terrence, 2026-09-21):** a line-by-line diff of member 1's capture at
the moment of the hang against a clean boot of another member is **identical for every line up
to `Starting kernel ...`**, with exactly one differing line:

```
ubi0: max/mean erase counter: 12/7, WL threshold: 4096, image sequence number: 960062009   (hung)
ubi0: max/mean erase counter: 13/4, WL threshold: 4096, image sequence number: 1117579393  (clean)
```

Both values are per-device and change on every UBI attach. **Not diagnostic.** Same FIT image,
same kernel hash `bdfdbcd23e5108726c5ba066f21b7eadc9729d3b`, same `sha1+ OK` / `crc32+ OK`,
same `Booting image 04000000#IE520-28GSX`. The bootloader did its job identically on both.

### 8.3 Evidence strength, stated plainly

**Strong on *what*:** two independent captures of the same silence (the harness evidence file
and the framework's own `swi_a.log`, both ending at `Starting kernel ...`); an exact stopping
point with every FIT hash verified beforehand; a genuine within-run positive control (24
successful member-1 boots in the same run, 166–176 s, median 172 s, before the 25th hung);
stack-side corroboration; 0 bytes to a bare CR at +35 min; a clean 145 s recovery boot.

**Near-zero on *why*:** no kernel output at all, so no fault address and no subsystem; no
on-device artefact (§8.1); no environmental data at the moment of the hang; no JTAG; and
**n = 1**.

Sufficient to report the event — "a member can hang at kernel handoff on reboot and not
self-recover" is well founded. **Not** sufficient to file a diagnosed defect, and not
sufficient to attribute it to hardware versus firmware.

### 8.4 Reproduction attempt — run pinned to member 1

`--member 1` pins the loop to one target instead of rotating the backups. Member 1's own rate
in 38377 was **1 hang in 25 of its own boots**, so a pinned run is a cheap reproduction test:
~55 % chance of a second occurrence in 20 cycles, ~98 % in 100.

Run: `IE520/stack-tests/member1-pinned-2026-09-21/`, 20 cycles, `--settle 30`, self-healing
power recovery enabled (commit `3591f9d`) so a hang is recorded and the run continues.
Result is written up in that directory.

### 8.5 The console is blind across the whole kernel boot — this is the real evidence gap

Measured 2026-09-21 from member 1's own healthy recovery boot (`member1-powercycle-boot.log`),
and true of every boot capture in this corpus:

**A healthy IE520 boot on this build prints ZERO kernel log lines.** Grepped for the classic
markers — `Booting Linux on physical CPU`, `Linux version`, machine model, memory map, per-CPU
bring-up, `devtmpfs`, `Freeing unused kernel memory`, `random: crng init done` — **0 matches.**
The first thing on the console after `Starting kernel ...` is the Allied Telesis logo and
`AlliedWare Plus (TM)`, immediately followed by systemd `[  OK  ]` lines. That is **userspace**.

So the console sequence on a *good* boot is:

```
Starting kernel ...          <- last bootloader output
   ... total console silence, the entire kernel boot ...
<AT logo> / AlliedWare Plus (TM)   <- first userspace output
[  OK  ] Created slice ...          <- systemd
```

**Consequence:** the cycle-73 hang occurred somewhere inside a window that is silent on a
healthy boot too. Decompressor, arch setup, driver probe, rootfs mount, init hand-off — the
console cannot distinguish any of them, and "the kernel produced no output" (§2 item 3) is
therefore **not itself evidence of an early hang**. It is evidence that the hang was anywhere
before userspace. That is a weaker statement than the original write-up implied, and it is the
correct one.

**UNMEASURED:** the wall-clock width of that silent window on a healthy boot. It is bounded
above by the ~170 s reboot-to-`login:` figure, but the bootloader/kernel/userspace split was
not timed — a timestamped capture was proposed on 2026-09-21 and not run. Worth one reboot if
anyone wants the bound tightened.

### 8.6 What to ask for — corrected

An earlier draft of this write-up recommended "a build with early-boot console verbosity".
**That recommendation was wrong and is withdrawn.** The bench is already running the verbose
build, and per §8.2 the IE520 bootloader variants differ only in what they print. More
*bootloader* verbosity cannot help: §8.2 shows the bootloader phase is already byte-identical
between the hung unit and a clean one.

The gap is **kernel console output, which is a different lever entirely** — the kernel command
line (`earlycon`, `loglevel`, whether `quiet` is set, and where `console=` points), not the
bootloader build. Without a change there, every future occurrence of this failure will produce
exactly the same artefact we already have: `Starting kernel ...` and silence. **Collecting more
occurrences on the current configuration has no diagnostic value.**

Stated plainly for whoever picks this up: **console-based investigation of this event is
exhausted.** Everything observable is identical between the hung boot and a healthy one; the
divergence lies entirely inside the region the console does not report on.
