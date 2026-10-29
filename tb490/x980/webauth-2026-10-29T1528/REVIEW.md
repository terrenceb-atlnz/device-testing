# webauth-2026-10-29T1528 process review
Reviewed 2026-10-30 by /create-logs from agent-a5c31a5061ad810f0.jsonl (group A RUN: T44274, T44275, T44276
runs 1-2) and agent-a68a7860f1d768bd5.jsonl (T44276 runs 3-5).

| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T44274 | 36 | 80 | 45,125 | 3,397,346 | 26,174 | 39 | 893 s | 27,226 |
| T44275 | 16 | 32 | 25,826 | 2,140,446 | 15,377 | 21 | 464 s | 17,969 |
| T44276 (runs 1-5) | 110 | 228 | 393,974 | 12,229,879 | 83,776 | 110 | 4,250 s | 118,834 |
| overhead (group A RUN) | 47 | 96 | 106,731 | 6,284,282 | 30,897 | 48 | 1,238 s | 77,821 |
| **total** | 209 | 436 | 571,656 | 24,051,953 | 156,224 | 218 | 6,845 s | 241,850 |

## Overhead
- The group A RUN's overhead (1,238 s, 77.8 k chars read) is larger than T44274 and T44275 together. The reads were:
  the queue ranges (8.9 k), platforms/x980.md + STANDING-ORDERS (8.2 k), tools/README.md slices (8.0 k), the
  previous campaign's group A recipe (6.1 k) and logged-output.md (6.0 k).
- The previous campaign's recipe and this campaign's group A recipe overlap. Point the next dispatch at ONE of them.
- tb5's `ckcon ... exit` hangs every time (the console prints `login:`, not a prompt). Each tb5 logout cost a 45-300 s
  timeout and a `killmine`. A `--logout` mode in ckcon that waits for `login:` would remove this.

## Cross-case findings
- **Grade on `show auth supplicant brief` and ICMP, never on the HTTP body.** Every case followed this (platforms/x980.md §1).
- **`arpleg` sends from 192.168.10.2 unless `--src` is given.** It cost one invalid leg in T44274 and one in T44276 run 4.
- **The first ICMP leg after an authentication change can lose replies** (3/4 or 1/4). All three cases needed a second leg.
- **Under-sampled controls.** T44276 run 1's single-DISCOVER "control" created a wrong platform fact that took four more runs to undo. A control must be able to show the feature working: send enough tries for the known first-packet drops.
- Proposed helpers, one each: `tools/authleg.py` (auth state + ICMP per leg) and `tools/dhcpleg.py` (K DISCOVERs per MAC); details in T44277-review.md (dot1x group) and T44276-review.md.
