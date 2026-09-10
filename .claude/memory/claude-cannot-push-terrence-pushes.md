---
name: claude-cannot-push-terrence-pushes
description: "Claude cannot `git push` from this environment — Terrence's company-set permissions deny it every time (3/3 on 2026-09-11, incl. one he had just approved) and it cannot force/overwrite either. Contract: Claude COMMITS with a full message and stops; Terrence pushes. Never retry a denied push."
metadata:
  node_type: memory
  type: feedback
  originSessionId: 49dcf692-ded5-46ac-ab73-fffb9e6ddec8
---

**What happened (2026-09-11, device-testing wrap):** three `git push origin main` attempts were
denied by the permission layer — once chained onto the wrap commit, once after Terrence had
explicitly chosen "pull, commit, push", and once standing alone. The pull and the commit in the
same session went through; only the push is blocked. Terrence: *"my company-set-permissions do
not allow you to push, so I have to do it after your commits. I cannot overwrite them either."*

**The fact:** in this environment Claude **can** `git add`, `commit`, `fetch`, `pull --rebase`
and read the remote, and **cannot** `git push` (nor force-push, nor otherwise overwrite the
remote). This is a standing organisational permission, not a per-session prompt hiccup, so a
denial is the expected outcome and asking again does not change it.

**Why it matters:** a wrap that ends on a "push" step either stalls waiting for permission or
misreports the branch as landed. The remote lagging local is the normal end-of-session state
here, not an error.

**How to apply:**
- End every commit sequence at the commit. State the hash and say plainly *"committed, not
  pushed — the push is yours"*; give the one-liner (`git push origin main` from the repo root).
- Never chain `&& git push` onto a commit, never retry a denied push, never propose `--force`.
- Before committing on top of a remote that may have moved (Terrence pushes from GitHub's UI
  too — the 1-line README on repo creation), `git fetch` and `pull --rebase --autostash` first.
- Applies to both repos. The Test-cases memory `commit-and-push-on-session-end` still says
  Claude should push; that side's stream owns that file — flag it, don't edit it from here.

Related: [[no-stray-scripts]], [[prefer-pragmatic-fix-over-infra-debugging]].
