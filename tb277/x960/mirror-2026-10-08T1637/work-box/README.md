# Raw group-1 evidence, preserved off the box by the sentinel — 2026-10-09 09:10

**Why this folder exists.** The tester handed back mid-group. It reported T44967 and T44968 as
PASS and reported two product defects, but **it had not written a per-case `work/run1.log` for
either case** — the evidence existed only in these files on tb277's `/tmp`, which does not
survive a reboot of the box. The sentinel copied the whole working directory here unchanged so
nothing could be lost. **Nothing in this folder has been edited, re-ordered or summarised.**

This is NOT a substitute for the per-case working logs that `logged-output.md` requires. When the
run resumes, T44967 and T44968 still need `work/run1.log` written, each ending in its `VERDICT:`
line and citing these captures.

## What the files are

- `cap-<state>.txt` — `tcpdump` on tb277 `eth3` (the mirror destination, swi_c `port1.0.10`)
  during a 6-ping flow. `cap-<state>.err` is tcpdump's own stderr, which carries the
  "N packets received by filter" line.
- `ping-<state>.txt` — the matching ping result, so "no frames mirrored" can be told apart from
  "no traffic to mirror".
- `console-u2.log`, `console-u3.log` — every byte sent to and received from the two consoles.
- `cap.sh` — the capture helper; counts echo REQUESTS (ingress on port1.0.48) against echo
  REPLIES (egress on port1.0.48), which is what distinguishes transmit from receive from both.

## The sizes are the finding

A 1-byte `cap-*.txt` means nothing was captured; ~540-553 bytes means frames arrived. Read in
time order, with the ping passing 0% loss throughout:

| file | time | state | size | frames |
| --- | --- | --- | --- | --- |
| `cap-d0.txt` | 08:54 | no mirror (baseline) | 1 B | none — correct |
| `cap-tx.txt` | 08:55 | transmit, FIRST EVER apply on this port | 541 B | **yes** |
| `cap-rx.txt` | 08:57 | removed, receive applied fresh | 1 B | none |
| `cap-tx2/rx2/tx3/rx3.txt` | 08:58-08:59 | further fresh applies | 1 B each | none |
| `cap-rx-bounce.txt` | 09:02 | receive + destination port bounced | 553 B | **yes** |
| `cap-tx-nobounce.txt` | 09:03 | `direction transmit` sent over a LIVE receive mirror | 553 B | yes, but receive behaviour |
| `cap-tx-fresh-nobounce.txt` | 09:05 | removed, transmit applied fresh, no bounce | 1 B | none |
| `cap-tx-fresh-bounce.txt` | 09:06 | same, then destination bounced | 541 B | **yes** |

Two claims follow, and both are reproducible from the table rather than from anyone's narrative:

- **M1** — a re-applied mirror does not copy frames until the destination port is bounced
  (`shutdown` / `no shutdown`). Only the first mirror ever applied to a port works without one.
  `show mirror` reports the mirror as `Enabled` with the right direction throughout, so the CLI
  gives no indication.
- **M2** — `mirror interface <src> direction <new>` over an existing mirror on that destination
  is accepted with no error, but neither `show mirror` nor the dataplane changes. See
  `cap-tx-nobounce.txt`: a `transmit` was configured, and the capture is 6 echo REQUESTS and 0
  replies, which is receive behaviour. `console-u2.log` has the exchange.

Both still need confirming against the DUT by whoever resumes, and the CR wording is the Test
Engineer's call. They are recorded here as measured observations, not as graded verdicts.
