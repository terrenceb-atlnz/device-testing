---
name: lab-wiki-reachable-from-a-testbox
description: "wiki.atlnz.lc (10.32.16.107) is reachable from a testbox but NOT from the dev host — fetch TPS/Test-Strategy pages with curl ON the box, using action=raw for clean wikitext"
metadata: 
  node_type: memory
  type: reference
  originSessionId: e2852736-283a-4261-9133-f7c5eb813935
  modified: 2026-10-08T03:10:07.395Z
---

**Measured 2026-10-08 from tb277.** `wiki.atlnz.lc` resolves to `10.32.16.107`, ports 80 and 443
are open, and an unauthenticated `curl` returns HTTP 200 — no login needed for the AW+ wiki
pages. The dev host does not reach it, and WebFetch does not either (internal `.lc` domain), so
**run the fetch on the testbox**, as with everything else on the lab segment.

```bash
ssh tbNNN 'curl -sk -o /tmp/x.raw \
  "https://wiki.atlnz.lc/awpwiki/index.php?title=X960_platform_support_TPS&action=raw"'
```

**Use `action=raw`.** It returns MediaWiki source (~70 KB for a TPS) instead of ~170 KB of
rendered HTML, and the feature-support matrix stays legible as wikitext tables: each row is
`!<n>` then the feature name, priority, `Yes`/`No`, then the reason column. URL-encode the title
(`Test:3331_Test_Strategy_-_x960-56YSQ` has a colon).

The pages worth fetching for a campaign are in [[review-feature-docs-before-testing]]. Note a TPS
is templated (`{{{1|x960}}}`), so some headings render as placeholders in raw form — the tables,
which are what matter, do not.

Related: [[bench-cannot-open-tcp-to-office-pcs]] — the lab segment blocks TCP to office PCs
(10.33.22.x), but lab infrastructure like this wiki is fine. Test the transport before assuming
either way.
