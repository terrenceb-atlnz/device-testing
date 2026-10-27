# smtp-2026-10-23T1304 -- group process review

Reviewed 2026-10-28 by /create-logs from `agent-a1874e13c44700abf.jsonl` and the working files.
One case in the group. The per-case detail is in
[T33368/T33368-review.md](T33368/T33368-review.md); this file holds the group totals and the
findings that belong to the group rather than to the case.

## Token usage

| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T33368 | 65 | 130 | 135,356 | 8,929,468 | 12,792 | 69 | 2,736 s | 72,466 chars |
| overhead | 10 | 20 | 50,082 | 880,177 | 932 | 16 | 104 s | 47,282 chars |
| **total** | **75** | **150** | **185,438** | **9,809,645** | **13,724** | **85** | **2,840 s** | **119,748 chars** |

Overhead is 13% of the calls and 31% of the wall-clock-weighted cache write, but **40% of the
characters read back**. For a one-case group that ratio is the number to attack: the group paid
47 KB to read rules, the tool index and the queue before it touched the device.

## The overhead's own findings

1. **The campaign queue file was read four times**, in four ranges, totalling over 20 KB. The
   tester needs two things from it: the Session facts block and its own case row. A dispatch
   that carries both inline removes every one of those reads.
2. **`tools/README.md` was read twice**, 9.9 KB together, to find entries the tester already
   knew the names of. `grep -n '^### <tool>' tools/README.md` then one narrow range would cost
   under 1 KB.
3. **`logged-output.md` §2 was read in the case segment, not the group gate.** In a multi-case
   group that read repeats per case. Read the rules once, in the gate.
4. **One wasted probe cycle on a flag mistake**: `--outlet 1` where `bench_probe` wants
   `--outlet u2=1`. The error is silent enough to look like a probe problem.

## Findings that would recur across cases

- **Probe `CHECK_CABLE` on this bench is forwarding-database ageing, not a cable.** The gate
  probe reported `[portlink] tb-swi_d eth4 CHECK_CABLE bench=(absent)
  template=eth4-port1.0.48` and nothing was wrong. `--read-only` suppresses the probe's own
  pings, so the box's MAC ages out of the DUT's table. Expect it, and clear it with one ping
  rather than investigating it.
- **`bench-setup/tb277/bench-state.md` is rewritten by every probe** and a one-console probe
  reduces it to a single unit. This group regenerated it and restored it with
  `git checkout --` both times, and committed neither. Any group on this box must do the same.
- **Probe the CLI surface with `?` before sending anything.** It cost a few calls and it caught
  a grammar error that the triage notes had recorded wrongly. Had the tester trusted the note,
  the first configuration command would have failed and the failure would have looked like a
  product defect.
- **An unprivileged listener removes the root question entirely.** The box's Postfix advertises
  no AUTH, and adding SASL to it or binding port 25 needs root, which an unattended window
  cannot ask for. `mail smtpserver port <1-65535>` is configurable, so the instrument ran on a
  high port. Look for the configurable-port escape before declaring a case blocked on root.
