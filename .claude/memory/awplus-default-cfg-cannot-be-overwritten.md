---
name: awplus-default-cfg-cannot-be-overwritten
description: AW+ (x230v2, 2026-10-09) refuses every copy/delete onto flash:/default.cfg; only `write` changes it — so backup+copy-back cannot undo a test's startup change
metadata:
  type: project
---

On the x230v2-28GS (tb470 u0, awplus_main-20261008-57, 2026-10-09 T47115) the CLI refused every
attempt to put a backup back over `flash:/default.cfg`: `copy` (as the boot config file, and as
"the default config file" even with the boot pointer moved), `copy <file> startup-config`, and
`delete`. Only `write` updates it. Details and the restore recipe: `platforms/x230v2-28GS.md` §1.

**Why:** run 4 backed up default.cfg before `crypto secure-mode` + `write`, planning to copy it back.
That plan failed at the last step, the boot pointer ended up moved to a temp file, and the startup
config could only be rebuilt by `write` (not byte-identical: `service password-encryption` dropped,
two default `security-password` lines added). The difference is now a Test Engineer decision.

**How to apply:** before any case that must `write` on an AW+ DUT whose boot config is
`default.cfg`, plan the restore as "running-config = original, then `write`", and say up front it
will not be byte-identical. Or ask the Test Engineer first whether a byte-exact restore (start-shell
+ cp) is wanted. Unverified on the IE520/AR4050S (their boot config is `tb470-bench.cfg`, not the
default file). Related: [[awplus-config-prompts-abort-and-logout]].
