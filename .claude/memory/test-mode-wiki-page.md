---
name: test-mode-wiki-page
description: The /test-mode wiki page lives at wiki.atlnz.lc Ask-ck/test-mode; its source is docs/WIKI-Ask-ck-test-mode.wiki, which Terrence pastes in; read the live page raw with curl, no auth
metadata:
  type: reference
---

The team-facing `/test-mode` + `/create-logs` how-to is the AWP wiki page
**https://wiki.atlnz.lc/awpwiki/index.php/Ask-ck/test-mode** (2026-10-06). Its source of truth in
this repo is `docs/WIKI-Ask-ck-test-mode.wiki` (MediaWiki markup). Claude edits the repo copy;
**Terrence publishes it to the wiki by hand.**

- Read the live page's source with `curl -sS 'https://wiki.atlnz.lc/awpwiki/index.php?title=Ask-ck/test-mode&action=raw'`
  (works from the dev host, no login), then `diff` it against the repo copy to see what he
  changed on the wiki. `&action=render` gives the parsed HTML, which shows markup bugs (an
  unclosed `<code>` on 2026-10-06 turned the top of the page monospace).
- Terrence added a clone line at the top on the wiki (2026-10-06); keep the repo copy in step with
  his wiki edits.
- When the skills, the tester agent, logged-output.md, STANDING-ORDERS.md or tools/README.md
  change, the page drifts: re-check it against them and bump its "Last updated" line.

Related: [[sentinel-kit-in-orient-dt]], [[log-is-the-deliverable]].
