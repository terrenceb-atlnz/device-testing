# Session handover — 2026-10-27 — CR drafts from historical IE520 runs

## Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: none — no hardware used (tb470 was only an ssh hop to wiki.atlnz.lc; no console opened)
Consoles: none
PDU: none
Constraints: none

## TL;DR
A records-only session. Terrence picked IE520 cases from past campaigns, and Jira CRs were
drafted for them in [CR-gen/](../CR-gen/) as paste-ready Jira wiki-markup field blocks. No
bench was touched, so there is nothing to restore. Four drafts exist. Three are waiting on
Terrence's decisions and a duplicate search; none is filed by us.

## What was accomplished
- [CR-gen/README.md](../CR-gen/README.md) and [CR-gen/TEMPLATE.md](../CR-gen/TEMPLATE.md) are new.
  TEMPLATE condenses three wiki pages, read 2026-10-27 through tb470: Jira_CR_Creation_and_Verifying_Guidelines
  §2.5–2.7, CR_severity_definitions and Must_Fix_Decision_Process.
- [CR-gen/Example/](../CR-gen/Example/) holds Terrence's Jira exports: a blank CR-92294 and the
  filled CR-92097 (SVT's).
- Drafts:

| case | draft | claim | suggested priority | Desktop attachments |
| --- | --- | --- | --- | --- |
| T12589 | [T12589-CR-92294.md](../CR-gen/T12589-CR-92294.md) | PBR sends matched traffic to an unrelated host when the next hop is down/unresolved | 3 - Major | `~/Desktop/CR-92294-T12589-attachments/` |
| T8770 | [T8770-CR-DRAFT.md](../CR-gen/T8770-CR-DRAFT.md) | IPv6 neighbours learned but not programmed in hardware once the table is full (~1.9K), traffic to them lost | 4 - Minor | `~/Desktop/CR-DRAFT-T8770-attachments/` |
| T38093 | [T38093-CR-DRAFT.md](../CR-gen/T38093-CR-DRAFT.md) | MRP manager falsely declares the ring open and loops traffic on every ring closure (16 out of 23 closures across 4 cases) | 3 - Major | `~/Desktop/CR-DRAFT-T38093-attachments/` |
| T28128 | [T28128-CR-DRAFT.md](../CR-gen/T28128-CR-DRAFT.md) | IPv6 between guest VLAN supplicants dropped with hw-forwarding off unless the guest VLAN has an address in the clients' subnet | 4 - Minor | `~/Desktop/CR-DRAFT-T28128-attachments/` |

- Every pasted field names the attachment that backs it. Every count was re-checked against its
  evidence file.

## Findings
- **Measured (re-read from the wiki): ER-3353 "Suppress unicast flooding on Guest VLAN" is the
  `auth guest-vlan hw-forwarding` feature.** Its TFS never says unknown unicast between
  supplicants is blocked. It does give rules for the hardware path:
  - S3353.1.6, IPv4: the guest VLAN's own IP is dropped, the subnet is forwarded, anything
    outside the subnet is dropped, and with no address there are no restrictions.
  - S3353.1.7, IPv6: no restrictions.

  Memory: `er-3353-guest-vlan-is-hw-forwarding`.
- **Inferred:** the 28126/28127 step-2 FAIL (unknown-unicast flooding, Terrence's ruling
  2026-09-24, CAMPAIGN-QUEUE-2026-09-24 I-4) has no spec behind it. Step 2 more likely means the
  S3353.1.6 drops, which were never tested. No CR is drafted for it, and the logs were not edited.
- **A re-run of 28126–28129 is not possible now.** Terrence took the IE520 stack down at tb470,
  and the units are on tb101. The x230v2 comparison on tb470 was dropped as well. Peer
  device-testing-62 did a read-only triage at 14:19–14:21 and was told to stand down.

## OPEN (Terrence's)
1. Each draft has its own "Decisions before filing" list: priority, splits, the new-platform
   comparison, regression wording, and a duplicate search on http://bugsearch.atlnz.lc/ (none done yet).
2. T8770: the capacity limit is not a spec failure, because the TPS has no IPv6-neighbour row.
   Ask the TPS owner?
3. T38093: the profile change on a live MRM loops for 79 ms and logs EXFX STARGV errors (T38099
   O-1). Is that a separate CR?
4. 28126/28127: re-grade step 2, or re-test it against S3353.1.6 on tb101?
5. T12589: was CR-92294 filed with this draft? Its fields were not given the "name the
   attachment" pass the other three got.
6. The Desktop folders are named `CR-DRAFT-…`. Rename them once the CR keys exist, and rename the
   drafts to `<case>-<CR key>.md`.

## Ordered next steps
1. Terrence works through each draft's Decisions and the duplicate search, then files.
2. Record the CR keys in the case logs' rows, the campaign READMEs, and CAMPAIGN-QUEUE-2026-09-24
   I-5 / plan A.2. Its other "raise as defect?" items are still open: I-17, I-16, I-15 and I-7.

## Recipes
- **Wiki page, raw:**
  `SSH_AUTH_SOCK=/run/user/$(id -u)/keyring/ssh ssh tb470 "curl -sk 'https://wiki.atlnz.lc/awpwiki/index.php?title=<Page>&action=raw'"`.
  Search with `api.php?action=query&list=search&srsearch=<terms>&format=json`.
- **A real Show System for a past run:** use the bench probe's capture nearest the run, on the
  same build: `bench-setup/captures/<UTC stamp>/uN.show_system.txt`. Strip NUL and CR before
  pasting. Never reconstruct one.
- **Case text:** `python3 tools/ckcase.py AWPTCM-T<id>`.

## Pointers
[CR-gen/](../CR-gen/) · memories `cr-drafts-in-cr-gen`, `er-3353-guest-vlan-is-hw-forwarding` ·
source logs: `IE520/routing-2026-09-29/` (12589), `IE520/ipv6-bgp-2026-09-29/` (8770),
`IE520/mrp-2026-09-29/` (38093 group), `IE520/auth-2026-09-22/` (28126–28129).
