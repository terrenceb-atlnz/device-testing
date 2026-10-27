---
name: er-3353-guest-vlan-is-hw-forwarding
description: "ER-3353 'Suppress unicast flooding on Guest VLAN' (the AWPTCM folder of T28126-28129) is the `auth guest-vlan hw-forwarding` feature — its TFS never says unknown unicast is blocked; read the TFS rules before grading"
metadata:
  node_type: memory
  type: project
  originSessionId: 6367cfbd-1391-45b1-8b5b-525f6a98413a
  modified: 2026-10-27T01:06:55.866Z
---

The ck.db folder "(5.5.0-1)ER-3353: Suppress unicast flooding on Guest VLAN" (T28126–28129) names
a feature whose TFS (wiki `Suppress_unicast_flooding_on_Guest_VLAN_TFS`, read 2026-10-27 via tb470)
is purely **guest-VLAN hardware forwarding** (`auth guest-vlan hw-forwarding`, default off = CPU
forwards). Spec rules, hardware path: S3353.1.6 IPv4 — dst = VLAN's own IP dropped, dst in the
VLAN's subnet forwarded, outside dropped, **no IPv4 address = no restrictions**; S3353.1.7 IPv6 —
no restrictions. Not allowed with `auth-web enable` or `auth guest-vlan forward`. Nothing about
unknown-unicast suppression between supplicants. ER-3855 turned it on for all AW+ switches.

**Why:** in 2026-09 the "completely blocked" step 2 of 28126/28127 was read from the folder NAME as
unknown-unicast suppression and graded FAIL; the TFS doesn't support that reading (S3353.1.6
out-of-subnet drops are the likelier meaning, never tested). Found while drafting CRs 2026-10-27
([[cr-drafts-in-cr-gen]]).
**How to apply:** for any guest-VLAN case, read the TFS spec lines before inferring expectations
from a folder or ER title; test S3353.1.6 with an IPv4 address on the guest VLAN.
