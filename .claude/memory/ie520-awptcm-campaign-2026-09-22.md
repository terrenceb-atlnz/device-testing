---
name: ie520-awptcm-campaign-2026-09-22
description: "Pointer: the 72-case IE520 AWPTCM campaign of 2026-09-22 — 39 PASS / 1 PARTIAL / 32 UNMEASURED across 7 group dirs under IE520/. Read a group's README before re-running anything in it."
metadata:
  node_type: memory
  type: project
---

Run 2026-09-22 on tb470 against the 4-member IE520 VCStack
(`awplus_main-20260913-1734`). Seven groups, one directory each under
`claude/device-testing/IE520/`, each with per-case `<case-id>.log` and a `README.md`
carrying the verdict split and the reasons.

| group | dir | result |
| --- | --- | --- |
| ACL | `acl-2026-09-22/` | 11 PASS / 2 UNMEASURED |
| Authentication | `auth-2026-09-22/` | 1 PASS / 6 UNMEASURED |
| MRP | `mrp-2026-09-22/` | 0 / 5 UNMEASURED |
| QoS | `qos-2026-09-22/` | 9 PASS / 3 UNMEASURED |
| STP & storm control | `stp-2026-09-22/` | 6 PASS / 2 UNMEASURED |
| switching | `switching-2026-09-22/` | 6 PASS / 1 PARTIAL / 4 UNMEASURED |
| IPv6 routing & protocol | `ipv6-2026-09-22/` | 6 PASS / 10 UNMEASURED |

**39 PASS · 1 PARTIAL · 32 UNMEASURED = 72.**

**Read the UNMEASURED count with its causes — almost none are product results.** Needs a
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
  present") — it works standalone. That single behaviour blocks ATMF 38474 and 38475.
- The AR4050S **lists MRP as licensed while exposing no MRP CLI**. A licence entry is not a
  capability.

Standing asks for Terrence, none of which blocked the run: **one recable** (~14 cases),
**a line-rate source** (9), **two MRP-capable switches** (5), **steps for 3 undefined cases**.
