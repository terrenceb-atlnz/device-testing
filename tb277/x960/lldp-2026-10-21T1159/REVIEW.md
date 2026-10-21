# Group process review -- lldp-2026-10-21T1159

Reviewed 2026-10-22 by /create-logs from the tester's transcript and the working files.

## Token usage

| segment | calls | cache write | cache read | output | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- |
| T44296 | 122 | 194,365 | **25,789,240** | 20,129 | 3,756 s | 122,241 |
| T33398 | 11 | 25,537 | 3,955,523 | 146 | 441 s | 1,161 |
| overhead | 44 | 147,161 | 11,837,928 | 1,438 | 1,225 s | 161,782 |
| **total** | **177** | **367,063** | **41,582,691** | **21,713** | **90 min** | **285,184** |

**Group overhead: 28.5 %.**

## 🔴 T44296 alone is 25.8 M — 18 % of the whole campaign, in one case

122 tool calls, 63 minutes, and **11.6x T33398's cache-read** for a case in the same subsystem.
It is the most expensive case of the campaign by a wide margin, and the review has to say
honestly whether that was worth it.

**It was, and here is the case for it.** T44296 had **zero** authored steps — `steps = []`, not
even a placeholder. Twelve graded steps were designed from the title, the TPS row and the DUT's
CLI surface. It produced the campaign's first reboot-persistence measurement, the
blocked-port contrast, two reusable tools, and five of the group's findings. The cost bought
the method that every later case reused.

**But two thirds of it need not be paid again.** The expensive part was discovery: enumerating
the LLDP surface, building and instrument-controlling `lldpsend.py` and `lldpwire.py`, and
learning the TLV model. **All of that is now written down.** A second run of T44296 should look
much more like T33398's 4.0 M.

## Findings for the whole group

1. **Replacing a partner with the testbox produced BETTER evidence, not a workaround.** Both
   partner consoles were locked out, so the tester drove crafted LLDPDUs from eth3 instead of
   using swi_b. That meant **choosing** the chassis ID, port ID and TTL — so neighbour ageing
   was graded against a 20 s TTL the sender set rather than waiting out 120 s, and the DUT's
   learned values could be checked against values known in advance. **When a partner is
   unavailable, ask whether a crafted one is actually better before calling the case blocked.**
2. **Instrument control before trust, twice.** `lldpwire.py` was proved on a synthetic frame and
   `ntpc`-style self-tests were run before any device reading was believed. That is what makes
   a later silence a measurement.
3. **Two findings here would mislead a later reader**, and both are in the campaign queue: the
   **empty `Sys Name` column is correct default behaviour** (only three mandatory TLVs plus one
   OUI TLV are advertised), and **`no lldp receive` drops the frame BEFORE the counter**, so
   `In` counts frames accepted, not arrived.

## Next run

- Reuse `tools/lldpsend.py` (TTL is an argument — that is what made ageing cheap) and
  `tools/lldpwire.py`. `tools/lldpmed_phone.py` is now hardware-verified.
- Read `platforms/x960.md` and this campaign's queue findings before designing LLDP steps; most
  of T44296's discovery cost is now a read rather than an experiment.
- An x960-56YSQ cold-boots to a login prompt in **60 s** — `ckreload.py`'s 720 s default is
  wildly conservative here.
