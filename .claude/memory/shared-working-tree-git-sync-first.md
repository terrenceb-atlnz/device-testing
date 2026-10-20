---
name: shared-working-tree-git-sync-first
description: "Terrence 2026-10-21: every session starts with git fetch + ff/rebase (orient-dt §0a) and wrap reports the count to push. Several seats commit to origin/main while this host's commits wait for his push; this NFS checkout is SHARED by every session on the host (visible in ListAgents or not), so a rebase rewrites their files — put peers on hold first, keep BOTH sides' facts in conflicts."
metadata:
  type: feedback
---

**What happened (2026-10-21, tb101 follow-up):** local main was 5 commits ahead of and 231
behind `origin/main` — the tb277 x960 campaigns had pushed from another seat for two weeks while
this host's commits waited for Terrence's push. Terrence: *"roll back my commits, pull fresh,
then recommit; update /orient-dt to ensure it does a fresh pull every time it runs, and sorts out
the git before we start a session."* The rebase hit three conflicts (MEMORY.md, .gitignore,
tools/tb), and a third session nobody could see in `ListAgents` had just committed to and probed
in the same working tree.

**Why:** two things compound. Divergence grows silently because Claude cannot push
([[claude-cannot-push-terrence-pushes]]); and the working tree is one NFS checkout for every
session on the host, so git state is shared state — a rebase, checkout or reset lands on peers
mid-work, and their uncommitted probe output appears in your `git status`.

**How to apply:**
- Orient = `git fetch` first, then ff-pull or `rebase --autostash` (orient-dt §0a); wrap = fetch
  again and report `<n> to push, <m> behind`.
- Before a rebase: `ListAgents`, tell every peer in this repo root to hold git, wait for the ack;
  afterwards tell them main is stable and the hashes changed. Assume an invisible session too:
  be quick, never leave a rebase half done.
- Conflicts: merge BOTH sides' facts (same index line extended at both ends → both; `BOX_PY`
  gained a box on each side → union; a rule added twice → once). Never `--skip`, `reset --hard`
  or `--force`. Not obviously mergeable → `rebase --abort`, report, stop.
- Dirty files that are not yours stay untouched; commit only what this session produced.
