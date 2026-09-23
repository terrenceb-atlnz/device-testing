---
name: awplus-cli-wiki-on-the-share
description: "There is an AW+ CLI wiki on the share — claude/github-copilot-awplus-wiki/awplus_cli_wiki/commands/, 3437 pages, one per command, with syntax, MODE and a platform table. Look syntax up there FIRST; probing a live CLI is slower, riskier and misses commands."
metadata:
  node_type: memory
  type: reference
---

**Path:** `claude/github-copilot-awplus-wiki/awplus_cli_wiki/commands/` on the lab share
(one of the three human-owned non-repo directories under `claude/`). **3437 markdown
pages**, one per CLI command, each with:

- an Overview and the `no` variant
- a **Syntax** block
- the **Mode** it is valid in (this is the bit that keeps being the problem)
- a **Platform table** and links to family pages

There is also `.../families/` for grouped command sets.

```
W=/media/terrenceb/mnt/testbox_home/claude/github-copilot-awplus-wiki/awplus_cli_wiki/commands
command ls $W | command grep -i '^show-bgp-ipv6'
command grep -A6 '^```text' $W/ipv6-router-ospf-area.md
```
Use `command grep`/`command ls` — the shell `grep` is a shim that honours .gitignore
([[grep-shim-honors-gitignore]]).

**WHY THIS MATTERS MORE THAN IT SOUNDS.** On 2026-09-22 I spent a long stretch trying to
attach an interface to OSPFv3. I probed `ipv6 ospf ?` on the interface, saw no `area`
option, tried the router sub-mode, tried tagged and untagged processes, and concluded the
attachment was not possible on this platform. The answer was one page away:

```
interface vlan10
 ipv6 router ospf area 0        <- the command is under `ipv6 router ...`, not `ipv6 ospf ...`
```

A live `?` probe only shows you completions of the prefix you guessed. If you guess the
wrong prefix you get a confident-looking "this option does not exist". The wiki is indexed
by command name, so it finds what you could not have guessed.

**It also avoids the `?`-plus-CR hazard entirely** — see
[[never-send-cli-help-through-a-cr-driver]], where a syntax probe executed the command and
enabled ATMF secure mode on a live bench.

**CAVEAT, measured:** the platform tables are a GUIDE, NOT A GATE. `ipv6-router-ospf-area.md`
lists AR4050, x230, x908Gen2, x930, x950 — **not the IE520** — and the command works fine on
the IE520. Absence from a table is a reason to TEST, not a reason to record UNMEASURED.
(Conversely `neighbor-fall-over-bfd-bgp.md` also omits the IE520, and there the command
genuinely was not usable end to end — so the table predicts nothing either way. Test it.)

**THE WIKI HAS NO IE520 PAGES AT ALL (checked 2026-09-23).** Its platforms are AR4050,
AT-TQ7403R, x230, x908Gen2, x930, x950 — and there are no pages for the IE520 or for the models
Terrence names as its closest relatives: **IE560, IE360, x230v2, and "close-ish" IE340.** Of
those, only **x230** is in the wiki (3420 pages), so read the x230 section of a page. The
**Mode and default values can still differ on the IE520**, as measured on awplus_main-20260923-20:
- `crypto key pubkey-chain knownhosts ...`: the wiki says Privileged Exec, but the IE520 rejects
  it there (caret at `pubkey-chain`) and accepts it in **Global Config**.
- `crypto key generate userkey manager rsa`: the wiki's default is 2048 bits; the IE520 made a
  **3072**-bit key.
If a documented command is `% Invalid input` in its documented mode, try the other mode before
concluding it is absent. The `show` variant existing is a hint that the command exists.

Related: [[ckdb-cli-command-hyphen-collapse]] for reading exact CLI tokens out of ck.db;
[[read-the-transcripts-before-driving-hardware]] for the same principle applied to menus.
