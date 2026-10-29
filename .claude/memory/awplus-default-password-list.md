---
name: awplus-default-password-list
description: The framework's default AW+ login list is no longer just manager/friend — 5 passwords since 2026-10-19 (in-house security changes); 5 tries = the AW+ lockout threshold, so never walk the list on an unknown unit
metadata:
  type: reference
---

**The default credentials are NOT only `manager` / `friend` any more** (Test Engineer jacobm, 2026-10-29: the
framework *"has updated the default password permutations … increased in-house cybersecurity changes … now
there are several options"*).

**The list, read from the framework itself on 2026-10-29** (`/home/st-art/framework/ATDrivers/ATSwitch.py`,
`__resolve_username_and_password()`, line 398; file dated 2026-10-19, identical on tb490 and tb5):

- user: `manager`
- passwords, in the framework's order: `friend`, `P@ssw0rd`, `A11iedWare+`, `0neC0nnect`, `V1staManager`
- **`awplus` is no longer in it.** Older notes and tools that say `['friend','P@ssw0rd','awplus']` are stale.

**Re-read it, don't trust this copy**, before relying on it: `ssh tbNNN 'grep -n "passwordList = \[" /home/st-art/framework/ATDrivers/ATSwitch.py'`
(read-only, no console). The source of truth is the framework, not this file.

**🔴 Five defaults = the AW+ lockout threshold.** AW+ locks an account at 5 failed logins and every further
failure re-arms the 5-minute timer ([[console-driver-retries-are-lockout-generators]]). A tool that walks all
five defaults against a unit whose password is none of them **locks it in one pass**. So:
- A unit whose password is known and non-default: pass it per console (`CK_PASSWORD_U<n>` / `CK_USER_U<n>`)
  so it is the ONLY password tried.
- A unit whose password is unknown: **do not walk the list.** Ask the Test Engineer. If it is already logged in
  at a prompt, do not log it out unless you can log back in (2026-10-29: tb5 u1's swi_x530 was logged in all day;
  the wrap's logout left it at `login:`, and the next open made 5 failed attempts).
- Know what each repo tool tries: `bench-setup/bench_probe.py` `PASSWORDS` = the framework's five (updated
  2026-10-29, Test Engineer approved), and it stops at AW+'s "account is locked" reply; `tools/console.py` = ONE
  password, `friend` unless `CK_PASSWORD` is set. Either tool can also spend attempts with bare CRs at a
  `Password:` prompt (the 2026-10-29 tb5 u1 case: 5 failures from one `ckcon` open).

**Why:** the in-house security changes mean units are increasingly NOT on `friend`, and a wrong list either
misses the real password or spends the lockout budget.

**How to apply:** at `/test-mode` §1 and triage, ask which consoles have non-default passwords before any probe,
and carry them in `~/.ckenv` (chmod 600, outside the repo) as `CK_PASSWORD_U<n>`. Never write a password into
the repo, a queue file, a handover or a memory — the default list above is published framework source, which is
why it may appear here. Related: [[testbox-console-access]], [[shared-testbox-console-occupancy]].
