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

Related: [[ckdb-cli-command-hyphen-collapse]] for reading exact CLI tokens out of ck.db;
[[read-the-transcripts-before-driving-hardware]] for the same principle applied to menus.
