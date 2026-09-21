---
name: ie520-console-prints-no-kernel-log
description: "An IE520 boot prints ZERO kernel log lines — the console goes silent at `Starting kernel ...` and the next output is USERSPACE (the AT logo). Console evidence cannot resolve anything inside the kernel boot."
metadata:
  node_type: memory
  type: project
---

Measured 2026-09-21 on tb470, build `awplus_main-20260913-1734`, from healthy boot captures
(`IE520/stack-tests/member-38377-2026-09-18/member1-powercycle-boot.log` and the 20 captures in
`member1-pinned-2026-09-21/`). **True of a HEALTHY boot — this is not a fault.**

```
Starting kernel ...            <- last bootloader output
   ... total console silence, the WHOLE kernel boot ...
<AT logo> / AlliedWare Plus (TM) / Built: ...   <- first output is USERSPACE
[  OK  ] Created slice ...     <- systemd
```

Grepped a healthy boot for the classic kernel markers — `Booting Linux on physical CPU`,
`Linux version`, machine model, memory map, per-CPU bring-up, `devtmpfs`,
`Freeing unused kernel memory`, `random: crng init done` — **0 matches, all of them.**

**Why this matters, and it has already caused one wrong conclusion:**

A unit that hangs anywhere between the handoff and userspace produces a capture that is
**indistinguishable from a healthy boot right up to the moment it stops**. So:

- **"The kernel produced no output" is NOT evidence of an early hang.** It only means the hang
  was somewhere before userspace — decompressor, arch setup, driver probe, rootfs mount, init.
  The console cannot separate those. I originally wrote the 38377 cycle-73 hang up as if the
  silence localised the fault; it does not.
- **More occurrences have no diagnostic value on this configuration.** Every one yields the same
  artefact. Do not propose another campaign as a path to root cause.
- **Do not ask for "a more verbose bootloader build."** Verbosity there is surface-level output
  formatting ([[ie520-two-bootloaders]]) and the bootloader phase is already provably identical
  between a hung and a clean boot. The lever is the **kernel command line** — `earlycon`,
  `loglevel`, whether `quiet` is set, where `console=` points — which is a different ask to a
  different owner.

**UNMEASURED:** the wall-clock width of the silent window. Bounded above by the ~170 s
reboot-to-`login:` figure for an IE520 member; the bootloader/kernel/userspace split has not
been timed. One timestamped reboot would bound it.

Write-up: `IE520/stack-tests/member-38377-2026-09-18/after-action-38377-partial.md` §8.5–8.6.
Related: [[ie520-silent-reboot-watch-2026-09-02]], [[ie520-release-naming-and-drift]].
