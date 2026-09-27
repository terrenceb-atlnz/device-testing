---
name: ie520-awptcm-campaign-2026-09-22
description: "Pointer: the 72-case IE520 AWPTCM campaign (run 2026-09-22, re-runs 09-23/24) — now 52 PASS / 3 FAIL / 2 PARTIAL-or-PASS / 3 UNSUPPORTED / 7 UNMEASURED / 5 SKIPPED across 7 group dirs under IE520/. Group READMEs carry the current split."
metadata:
  node_type: memory
  type: project
---

Run 2026-09-22 on tb470 against the 4-member IE520 VCStack
(`awplus_main-20260913-1734`). Seven groups, one directory each under
`claude/device-testing/IE520/`, each with per-case `<case-id>.log` and a `README.md`
carrying the verdict split and the reasons.

| group | dir | 2026-09-22 | current (2026-09-28) |
| --- | --- | --- | --- |
| ACL | `acl-2026-09-22/` | 11 PASS / 2 UNMEASURED | 11 PASS / 2 UNSUPPORTED (38413, 942) |
| Authentication | `auth-2026-09-22/` | 1 PASS / 6 UNMEASURED | 3 PASS / 3 FAIL (28126–28128) / 1 UNSUPPORTED (38432) |
| MRP | `mrp-2026-09-22/` | 0 / 5 UNMEASURED | unchanged — no MRP partners |
| QoS | `qos-2026-09-22/` | 9 PASS / 3 UNMEASURED | 11 PASS / 1 SKIPPED (38148) |
| STP & storm control | `stp-2026-09-22/` | 6 PASS / 2 UNMEASURED | 8 PASS (38152/38153 on 3 of 4 — PASS-vs-PARTIAL rule open) |
| switching | `switching-2026-09-22/` | 6 PASS / 1 PARTIAL / 4 UNMEASURED | 7 PASS / 2 UNMEASURED / 2 SKIPPED (24032, 12067) |
| IPv6 routing & protocol | `ipv6-2026-09-22/` | 6 PASS / 10 UNMEASURED | 14 PASS / 2 SKIPPED (3116, 8770) |

**2026-09-22: 39 PASS · 1 PARTIAL · 32 UNMEASURED = 72.** **Current: 52 PASS (+38152/38153 = 54 if
counted as the STP README counts them) · 3 FAIL · 3 UNSUPPORTED · 7 UNMEASURED · 5 SKIPPED.**
The re-runs (09-23/24) came from the 09-23 recable (more cabled ports, two NICs on the stack) and
tcpreplay line rate. Rulings: 09-23 handover (skips, 38432); 09-24 (38413/942 UNSUPPORTED; 28126/
28127 FAIL, queue I-4). 38430's PASS is a CHOSEN call awaiting review (queue I-14).

**The 2026-09-22 UNMEASURED count had these causes — almost none were product results.** Needs a
line-rate generator (9) · needs more cabled ports (14) · needs a peer device the bench does
not have (6) · case has no steps in ck.db (3) · the feature's subject does not exist here
(4, e.g. no TACACS+ server, no `send-to-mirror` action for IPv6 hardware ACLs). See
[[tb470-bench-structural-limits]].

**Also here:** `IE520/RESUME-CAMPAIGN-2026-09-22.md` (written mid-run as continuity
insurance) and `IE520/test-harness/README.md` (harness DESIGN — the `.py` deliberately is
NOT in the lab tree, per the no-stray-py guard; the README says how to rebuild it and
records the open question about moving it to `ask-ck/functions/test-composer/`).

**Product behaviours worth carrying forward, all measured:**
- **No implicit deny** on a hardware IPv6 ACL applied with `ipv6 traffic-filter` — unmatched
  traffic forwards; `deny ipv6 any any` must be written.
- **The DUT does not learn ARP from unsolicited/gratuitous ARP** — 6000 gratuitous replies
  produced 0 entries while one ping produced one. Correct anti-poisoning behaviour, and the
  reason "ARP with full tables" is unreachable from one host.
- **Snooping floods the first frame of a new group**, then prunes completely
  (`1/10, 0/10, 0/10`). Grading "enabled" as exactly 0 is wrong.
- **`atmf cleanup` is refused on a VCStack** ("cannot be run when another stack member is
  present") — it works standalone. (2026-09-24: 38475 PASSED with the standalone IE520-sa as DUT;
  38474 is parked on the 4050's knownhosts fetch, not on this.)
- The AR4050S **lists MRP as licensed while exposing no MRP CLI**. A licence entry is not a
  capability.

Standing asks as of 2026-09-22: one recable (DONE 09-23), a line-rate source (DONE 09-24 —
tcpreplay), **two MRP-capable switches** (5, still open), **steps for undefined cases** (queue I-6, open).
