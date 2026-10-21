# Group process review -- access-2026-10-21T1159

Reviewed 2026-10-22 by /create-logs from the tester's transcript and the working files.

## Token usage

| segment | calls | cache write | cache read | output | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- |
| T33379 | 71 | 124,953 | 13,253,065 | 886 | 1,718 s | 87,049 |
| T33380 | 36 | 45,602 | 9,994,410 | 683 | 790 s | 15,931 |
| T33381 | 34 | 47,116 | 11,310,222 | 364 | 1,054 s | 17,965 |
| overhead | 26 | 128,783 | 3,364,531 | 339 | 390 s | 153,879 |
| **total** | **167** | **346,454** | **37,922,228** | **2,272** | **65 min** | **274,824** |

**Group overhead: 8.9 %** — the best of the four groups, and the pattern worth copying: the gate,
the probe and the rules reading were done once and not repeated per case.

## Findings for the whole group

1. **T33379 cost 13.3 M against T33381's 11.3 M for comparable work**, and read back **87,049
   characters** of its own tool output against 15.9 k and 18.0 k. It was first, so it paid for
   building `tools/devclient.py` and discovering the telnet surface. That is real work, but
   **the next campaign inherits the tool** and should not pay it again.
2. **The group built one tool and it was the right call.** `tools/devclient.py` drives a
   device's *outbound* telnet/SSH client — nothing in `tools/` could do that, and both the
   telnet-client and SSH-client cases needed it. It is catalogued.
3. 🔴 **A tooling defect in this group put four failed logins on a throwaway account.**
   `subprocess.run(input=...)` **replaces** stdin rather than prepending, so a forwarded secret
   swallowed the far-end password and an empty one went out; the driver's recovery loop then
   typed `exit` at the password prompt, which the device reads as another guess. Fixed within
   the group. **The durable rule is in the campaign queue: a console driver's error recovery
   must never type a word at a login or password prompt.**

## Next run

- Reuse `tools/devclient.py`; do not rebuild an outbound client driver.
- Order the reading-heavy case first, as this group did.
- Extract what a step needs when the tool result first arrives — 87 k of re-read output in one
  case is the single biggest saving available here.
