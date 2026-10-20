---
name: cli-surface-is-not-the-device-surface
description: "Test Engineer, 2026-10-20: a case graded NOT MEASURABLE from an exhaustive CLI probe was wrong — `start-shell` reaches the Linux tree where the thing IS settable. Before grading UNSUPPORTED or NOT MEASURABLE because no command exists, ask whether the platform exposes it another way"
metadata:
  node_type: memory
  type: feedback
---

**What happened (2026-10-20, tb277, AT-x960-56YSQ).** T33413 "Trap - Temperature" needed an
over-temperature notification. The tester enumerated the AW+ CLI surface and found: no
`temperature` command, no `environment` command, `snmp-server enable trap ?` with no temperature
group, and the coolest sensor reading 27 °C against a hardware limit of 61 °C. It graded the real
over-temperature limb **NOT MEASURABLE** and I agreed, in writing, twice.

Every one of those observations was accurate. **The inference from them was wrong.**

The Test Engineer asked: *"Is it not possible for you to go to start-shell of the DUT and
simulate high temperature"* and supplied a worked example from another product — write a lower
threshold into `/sys/class/hwmon/hwmonN/tempN_max`. The re-run produced the real trap on the
wire: three assert/clear cycles, six transitions, six traps, against a silent baseline. PASS.

**The lesson, which is not about temperature.** On AW+ the CLI is a *view* of the device, not the
device. `start-shell` drops to a root Linux shell (kernel 6.12.110 aarch64 on this unit) where
sysfs, procfs and the real drivers are reachable. **Before grading a case UNSUPPORTED or NOT
MEASURABLE because no command exists, ask whether the platform exposes the thing some other
way.** An exhaustive CLI probe proves something about the CLI. It does not prove something about
the device.

**Why this is worth remembering.** The failure mode is seductive: the enumeration was thorough,
it was correct, and being thorough is what made the wrong conclusion feel safe. Rigour inside
too narrow a frame still gives the wrong answer.

**How to apply.**
- Treat "no CLI command exists" as a fact about the CLI, and say so in exactly those words.
- Try `start-shell` before writing NOT MEASURABLE for anything with a hardware or kernel limb.
- **Node numbering is per-platform — never copy a path from another product.** On the
  x960-56YSQ `hwmon0` is an MDIO PHY that appears in no CLI output; `Temp: Front Right` is
  `hwmon1/temp1` (adt7476). There are no label files, so join hwmon to the CLI sensors on
  reading + low limit + high limit *together*. PSU sensors take their CLI limit from
  `tempN_rated_max`, not `tempN_max`.
- **Prove the restore with `od -c`, not with `rcdiff`.** A sysfs write is not in running-config,
  so a clean config diff says nothing about it.
- The driver for this is `tools/awshell.py` (added 2026-10-20). No earlier driver could do it:
  `console.PROMPT_RE` cannot match `[root@awplus flash]#`, because the character before the `#`
  is `]`, so every shell command ran to full timeout and the batch was silently abandoned.

Related: [[tb277-x960-management-campaign-2026-10-20]], [[campaign-measurement-discipline]],
[[satisfactory-level-of-testing]], [[grading-authority-tier-list]].
