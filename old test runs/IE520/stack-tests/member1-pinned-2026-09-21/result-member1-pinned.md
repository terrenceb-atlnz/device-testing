# Result — member-1 pinned reboot ×20 (reproduction attempt for the 38377 cycle-73 hang)

**Run:** 2026-09-21 08:29:47 → 10:19:29 NZST, **1.8 h**, unattended.
**Harness:** `stack_reboot_test.py --mode member --member 1 --cycles 20 --settle 30
--case-id 38377-m1 --setup /home/st-art/st-art/configs/tb470.setup`
**Purpose:** try to reproduce the 2026-09-18 cycle-73 event, where member 1 hung at
`Starting kernel ...` and did not self-recover. See
`../member-38377-2026-09-18/after-action-38377-partial.md` §8.
**Bench:** unchanged 4-member AT-IE520-28GSX VCStack, VC 3439, VMAC `0000.cd37.0d6f`, all
members `awplus_main-20260913-1734`, flash boot, master 3 throughout. **No configuration was
changed at any point.**

## Headline

**20 PASS / 0 FAIL / 0 UNMEASURED. The hang did NOT reproduce.**

**This does not clear the platform.** A clean 20 was always a coin-flip: at the 38377 point
estimate of 4 % per boot, P(0 hangs in 20) = **0.44**. The run was worth doing and its outcome
is genuinely uninformative about whether the defect exists — it only tightens the rate.

## Measurements (n = 20)

| | min | median | max |
| --- | --- | --- | --- |
| target boot — reboot → member 1's own `login:` | 164.0 s | **170.2 s** | 176.0 s |
| stack whole — reboot → all Ready, all stackports learnt | 278.5 s | **288.7 s** | 293.7 s |
| whole cycle (incl. 30 s settle) | 290 s | 300 s | 305 s |

**Compare the 24 successful member-1 boots in 38377 before the hang: 166.0–176.1 s, median
172.1 s.** Statistically indistinguishable. Member 1 shows **no degradation, no drift and no
creeping symptom** — the hang is not the tail of a distribution that is getting worse.

## Health evidence — all positive, none inferred

- **20/20** boot captures carry **exactly one** `BootROM` banner (a second would mean a
  mid-boot self-reset).
- **20/20** cycles ended with **zero** unlearnt stackports.
- **0** collateral reboots, checked positively from the device: member 1's reboot history
  gained **exactly 20** `Expected / User Request` entries across the run window
  (device `2026-09-20 20:30:19` → `22:14:58`, UTC ≈ host −12 h), and members **2, 3 and 4
  gained no entry of any kind**.
- **0** `Unexpected` entries created anywhere on the stack.
- **0** exception-log growth; **0** fatal signatures; **0** power-recoveries invoked.
- Bench at exit: `Normal operation`, 4/4 `Ready`, 8/8 stackports learnt, master 3.

## What the rate now is

Clopper-Pearson 95 % intervals:

| population | hangs / boots | rate | 95 % CI |
| --- | --- | --- | --- |
| member 1, 38377 only | 1 / 25 | 4.00 % | 0.10 – 20.35 % |
| member 1, this run only | 0 / 20 | 0 % | 0 – 16.84 % |
| **member 1, combined** | **1 / 45** | **2.22 %** | **0.06 – 11.77 %** |
| any member, all member-reboot cycles | 1 / 93 | 1.08 % | 0.03 – 5.85 % |

**The honest reading: the rate is somewhere under ~12 % and above zero, and 45 boots cannot
say more than that.** n = 1 is still n = 1.

## Recommendation

Do **not** run another 20. At the combined 2.2 % estimate, a second occurrence needs
**~103 cycles for a 90 % chance** (~8.6 h) or ~134 for 95 % (~11.2 h). A short run mostly buys
another ambiguous clean sheet.

Two options that are actually worth the hardware time, in order:

1. **Bundle it into the 38377 re-run.** That case needs a 300-cycle verdict anyway (~27 h), the
   harness is now self-healing so a hang is recorded and the run continues, and 300 cycles
   rotating three backups gives member 1 ~100 boots — i.e. the ~90 % reproduction chance comes
   free with a test we owe regardless. **This is the recommended path.**
2. **Do NOT plan on "more occurrences will explain it".** They will not, on this configuration.
   See `../member-38377-2026-09-18/after-action-38377-partial.md` §8.5–8.6: a healthy boot on
   this build prints **zero** kernel log lines, so every occurrence yields the same artefact —
   `Starting kernel ...` and silence. Resolving the cause needs a **kernel command-line** change
   (`earlycon` / `loglevel` / `quiet` / `console=`), not a different bootloader build. The bench
   already runs the verbose bootloader, and the IE520 bootloader variants differ only in what
   they print.

**Correction, 2026-09-21:** the first version of this file recommended asking for "a build with
early-boot console verbosity". That was wrong — it is already the verbose build. Withdrawn; see
§8.6 above.

## Files

`38377-m1.log` (campaign log), `38377-m1-summary.json` (per-cycle records), `run.stdout`,
`38377-m1-progress.txt`, framework transcripts `swi_a..swi_d.log`, `stk_a.log`, `setup.log`.
