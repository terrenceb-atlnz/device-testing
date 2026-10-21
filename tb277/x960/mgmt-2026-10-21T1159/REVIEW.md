# Group process review -- mgmt-2026-10-21T1159

Reviewed 2026-10-22 by /create-logs from the testers' transcripts and the working files.

## Token usage

| segment | calls | cache write | cache read | output | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- |
| T33387 | 9 | 21,334 | 1,209,211 | 164 | 301 s | 3,743 |
| T33386 | 16 | 36,375 | 3,123,648 | 147 | 618 s | 11,159 |
| T47192 | 15 | 33,714 | 3,605,031 | 137 | 596 s | 15,873 |
| overhead | 51 | 141,348 | 7,895,645 | 1,362 | 1,270 s | 190,088 |
| **total** | **91** | **232,771** | **15,833,535** | **1,810** | **46 min** | **220,863** |

Reboot-persistence limbs for T33386 and T47192 were measured later, in another tester's
segment: **6,357,050** and **5,700,261** cache-read respectively.

## 🟠 Group overhead reads 49.9 %, and that number needs qualifying

The ratio is the highest of the four groups, but **the absolute overhead, 7.9 M, is the second
lowest.** What inflates the ratio is a very small denominator: these are the cheapest cases in
the campaign, and **T33387 cost 1.2 M over 9 calls** because it is a desk verdict against a TPS
row. A ratio is the wrong instrument when one group's cases are an order of magnitude cheaper
than another's — read the absolute number beside it.

That said, 51 overhead calls against 40 case calls is still inverted, and the cause is the same
as the previous campaign's: the rules and reference corpus read in many small calls. **Read it
in one combined `sed` expression, or put the facts in the group brief.**

## Findings for the whole group

1. 🔥 **The campaign's sharpest defect came from this group.** A NUMBERED hardware ACL holds
   exactly ONE rule — each `access-list <n> <rule>` silently replaces the previous, with no
   error and nothing in running-config. Since every management filter is permit-then-deny, the
   numbered form **collapses to the deny and locks the administrator out**.
2. **What made it reportable was the pairing, and the pairing crosses two cases.** T33386
   captured the driver error `exfx_cExt_dxch_rules_pclIdActionUpdate` at the instant of the
   loss; T47192 then showed the NAMED form taking an add, an in-place edit and a delete with a
   clean log. **Neither case's own log can carry that contrast** — it is in the campaign queue.
   When a finding needs two cases to be credible, the queue is where it lives.
3. **The CLI surface was probed before the test was designed**, which is why nobody wasted a run
   on `access-class` — it does not exist under `line vty` on this platform, and
   `ip access-list` does not exist in global config.

## Next run

- One combined read for the rules corpus.
- `tools/arpleg.py --tcp` now gives the three-way SA / R-RA / no-reply discrimination that a
  management-filter verdict needs. Use it; do not write another TCP prober.
- Always run the filter-OFF baseline leg first, so a silence later is a measurement.
