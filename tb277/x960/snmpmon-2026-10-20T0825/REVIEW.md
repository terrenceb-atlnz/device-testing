# Group process review -- snmpmon-2026-10-20T0825

Reviewed 2026-10-20 by /create-logs from the testers' transcripts and the working files.

## Token usage

| segment | calls | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T44308 | 52 | 104,096 | 8,032,994 | 477 | 54 | 1,800 s | 62,646 |
| T33413 (run 1) | 17 | 40,896 | 4,032,239 | 137 | 17 | 614 s | 26,756 |
| T44301 | 12 | 30,152 | 3,288,817 | 108 | 12 | 853 s | 11,208 |
| T44309 | 36 | 71,288 | 11,932,705 | 5,683 | 36 | 2,340 s | 26,844 |
| overhead | 23 | 84,896 | 2,502,553 | 979 | 31 | 248 s | 113,180 |
| **total** | **140** | **331,328** | **29,789,308** | **7,384** | **150** | **5,855 s** | **240,634** |

**Group overhead: 8.4 %.**

T33413 was run a second time in its own dispatch: **89 calls, 230,488 cache-write,
13,761,085 cache-read, 1,689 s, 226,133 characters of tool output read back**, with 3.3 %
overhead. The re-run cost 3.4x the original attempt's context and produced the correct answer.

## The finding that matters more than the numbers

**T33413 run 1 concluded the case was NOT MEASURABLE, and that conclusion was wrong.** It was
reached by enumerating the AW+ CLI surface: no `temperature` command, no settable threshold,
`snmp-server enable trap ?` offering no temperature group. Every one of those observations was
accurate. The inference from them was not.

The threshold is writable from the DUT's own Linux shell, at
`/sys/class/hwmon/hwmon1/temp1_max`, reached with `start-shell`. Run 2 wrote it and produced the
real trap.

**The generalisable lesson: the CLI surface is not the device's surface.** Before grading a case
UNSUPPORTED or NOT MEASURABLE because no command exists, ask whether the platform exposes the
thing some other way. On AW+ that means `start-shell` and the Linux tree underneath.

A second, narrower lesson from the same run: **the node numbering is per-platform.** The worked
example from another product used `hwmon0`. On the x960-56YSQ `hwmon0` is an MDIO PHY and
appears in no CLI output. The right node had to be found by joining all six hwmon devices to
the 14 CLI sensors on reading, low limit and high limit together, because there are no label
files. PSU sensors take their CLI limit from `tempN_rated_max`, not `tempN_max`.

## Other findings across the group

1. **Two cases' narrative timestamps disagree with their own source files** (T44308's
   negative re-test, T44301's leg-1 flap). In both the source file is right. **Write the time
   from the marker the script emitted, never from memory of when the command was sent.**
2. **T44301 never opened its partner's console**, so it has no `swi_b.cfg`, and its partner
   build data in the working log cannot have been measured by that run.
3. **T44309's two defects did not reproduce.** The case is graded PASS with both recorded. An
   unreproduced defect is worth more written down than argued about; the trigger is still
   unknown.

## Next run

- `tools/awshell.py` now exists for `start-shell` work and is catalogued. No existing driver
  could reach the device shell, because `console.PROMPT_RE` cannot match `[root@awplus flash]#`.
- Enumerate hwmon against the CLI once and record the map in `platforms/x960.md` rather than
  rediscovering it.
