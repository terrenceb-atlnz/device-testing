# Group process review -- aaa-2026-10-20T0825

Reviewed 2026-10-20 by /create-logs from the tester's transcript and the working files.

## Token usage

| segment | calls | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T33407 | 47 | 88,818 | 7,914,375 | 17,829 | 47 | 1,024 s | 52,667 |
| T33408 | 55 | 76,604 | 13,738,358 | 3,622 | 55 | 1,236 s | 33,905 |
| T33409 | 36 | 45,148 | 11,272,631 | 415 | 36 | 774 s | 30,281 |
| overhead | 25 | 101,304 | 2,748,410 | 266 | 33 | 292 s | 146,020 |
| **total** | **163** | **311,874** | **35,673,774** | **22,132** | **171** | **3,326 s** | **262,873** |

**Group overhead: 7.7 %** — the best of the four groups in this campaign, and better than the
2026-10-16 campaign's 9 %.

## What the overhead was

25 calls, 292 s. The gate, the probe and the rules reading were done once and not repeated per
case. This is the pattern the other three groups should copy.

**But 146,020 characters of the overhead's 262,873 — 56 % — was tool output read back off
disk**, against 30–53 k inside each case. The reading was front-loaded correctly; the volume of
it was not trimmed.

## Findings that apply to the whole group

1. **Cost per case rose 1.4x from the first case to the second** (7.9 M to 13.7 M cache-read)
   even though T33408 made only 8 more calls than T33407. Every call carries the accumulated
   context. Order the reading-heavy case first; this group did, and it still shows.
2. **The three cases share one setup and one teardown shape.** Each re-derived it. A group-level
   setup recipe written once into the queue would remove one read per case.
3. **A real secret was in the evidence and nobody planned for it.** `show radius` prints a
   global RADIUS secret that was on the DUT before this campaign. No case set it. It reached
   three working logs and one saved capture before anyone noticed, and the final logs had to
   redact it at write time. **The next campaign that touches `show radius` should redact at
   capture time, not at log-writing time.**
4. **Two `.cfg` files were captured at the wrong moment** (T33408 at 09:31, T33409 at 09:45 —
   both after a later step rather than after setup). Their contents happen to be correct. The
   rule exists so that correctness is not an accident.

## Next run

- Redact `show radius`'s `Secret Key` line in the capture helper, not afterwards.
- Save the `.cfg` in the same command batch that ends setup, so it cannot drift later.
- Keep this group's single-pass overhead pattern.
