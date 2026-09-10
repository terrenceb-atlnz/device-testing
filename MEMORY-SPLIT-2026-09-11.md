# Memory split — executed 2026-09-11

Device-testing's memories were carved out of `claude/Test-cases/.claude/memory/` into
`claude/device-testing/.claude/memory/`, which is now **the primary store** for anything the
tb470 bench work needs. Both sessions inventoried the 88 files independently (this side's
proposal, the Ask-CK side's `Test-cases/MEMORY-SPLIT-INVENTORY.md`); they agreed on 83, and
Terrence settled the rest. Rule applied: *mine → move; both → move + leave a symlink in
Test-cases; theirs → untouched; neither → delete.*

## Result — 88 = 15 moved + 12 moved-and-symlinked + 48 untouched + 13 deleted

**Moved (device-testing only) — 15**
bootloader-media-parse-bug · x230v2-5700-control-corpus · run-attribution-5700-campaign ·
ie520-4stack-flashprep · ie520-bootloader-console-driving · ie520-dos-test-method ·
ie520-mcast-l3-test-method · ie520-release-naming-and-drift · ie520-silent-reboot-watch-2026-09-02 ·
ie520-spiflash-goes-dark · ie520-tftp-boot-needs-usb-nic · ie520-two-bootloaders ·
i2c-stress-tooling · tb470-ie520-flash-boot-reboots-ok · log-is-the-deliverable

**Moved here, symlink left in Test-cases — 12**
- agreed "both": no-stray-scripts · prefer-pragmatic-fix-over-infra-debugging ·
  read-the-whole-function-before-judging · awplus-speed-duplex-constraint ·
  setup-file-declares-topology · grep-shim-honors-gitignore
- Terrence's call (both): testbox-console-access · read-the-transcripts-before-driving-hardware ·
  legacy-scripts-vs-framework · awplus-service-gated-routing-daemons ·
  awplus-cli-confirmations-need-enter
- symlinked only because an Ask-CK memory links to it (`topology-profiles-contract`):
  tb470-topology-and-setup

**Untouched in Test-cases — 48** (Ask-CK's buckets A and B minus the shared ones above).

**Deleted — 13** (closed work the Test-cases repo already records; both sides agreed):
adversarial-review-2026-07-27c · backlog-quality-items-done · atp-search-merge-ux ·
llm-health-check-button · pending-approved-plans · pytest-creator-llm-config-bug ·
pytest-artefact-review-worklist · d1-fragment-resolver-boundaries · d3-py2-fragment-translation ·
part3-grading-session · run-thread-contextvar-lock · db-only-single-source ·
testbox-framework-readonly (this side conceded it — `/orient-dt` §0/§4 and Test-cases CLAUDE.md
invariant 3 already state it).

## Mechanics

- Symlinks in Test-cases are **relative** (`../../../device-testing/.claude/memory/<name>.md`), so
  they survive the tree being re-mounted at a different absolute path.
- `MEMORY.md` was rebuilt on both sides from the original index lines: this store lists its 27;
  Test-cases keeps its 48 plus the 12 symlinked.
- `~/.claude/projects/<slug>/memory` links: `…-claude-device-testing` (new) and
  `…-mnt-testbox-home` (the lab home, re-pointed) → this store; `…-claude-Test-cases` unchanged.
- The Test-cases-side changes were **staged, not committed** — the Ask-CK `/wrap-ck` reviews and
  commits them together with its `tool/check_memory_links.py` update (that tool assumed one store).

## Known dangling `[[links]]` — deliberate, per the memory contract ("a link with no file marks
something worth writing later, not an error")

- From moved files into Ask-CK memories: checks-must-not-match-their-own-advice,
  ckdb-cli-command-hyphen-collapse, topology-profiles-contract, autonomous-judgement-divergence,
  user-prefers-manual-ui-testing, dont-ceremonialize-a-clear-fix, mutate-before-you-claim,
  atlnz-docs-cli-reference, generator-cli-hallucination, pytest-creator-askck,
  silent-degradation-audit-2026-07-30, cli-fabrication-originates-step2.
- In Test-cases, links to the 13 deleted files (e.g. `db-is-permanent-source → db-only-single-source`,
  several → `part3-grading-session` / `pending-approved-plans`) — for `/wrap-ck` to tidy.
