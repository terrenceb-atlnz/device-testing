---
name: awplus-default-cfg-cannot-be-overwritten
description: AW+ (x230v2, 2026-10-09) refuses every copy/delete onto flash:/default.cfg; only `write` changes it. FIX 2026-10-12: tb470's x230 now boots its own flash:/tb470-bench.cfg
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

**Fix, 2026-10-12 (Terrence: "make a new .cfg … set the default boot config to that new config"):**
the x230 (tb470 u0) now boots **`flash:/tb470-bench.cfg`**, the same name the other tb470 units boot
(`copy running-config flash:/tb470-bench.cfg` + `boot config-file flash:/tb470-bench.cfg`; 967 B). It holds
the VLAN 103/104/105 isolation and `lldp run`, so they survive a reload (verified: one reload 14:14,
login 166 s, running-config = the file, probe 2026-10-12T011811Z MATCH). `default.cfg` is untouched and
stays the fallback. `service password-encryption` is obsolete on this build ("Password encryption is
already always enabled"), so its absence from the rewritten default.cfg is no difference at all.
A case that changes startup config now backs up and copies back `tb470-bench.cfg`, which CAN be
overwritten (it is not the default file) — re-verify that the first time it is relied on.

**How to apply:** before any case that must `write` on an AW+ DUT whose boot config is
`default.cfg`, plan the restore as "running-config = original, then `write`", and say up front it
will not be byte-identical. Or ask the Test Engineer first whether a byte-exact restore (start-shell
+ cp) is wanted. Unverified on the IE520/AR4050S (their boot config is `tb470-bench.cfg`, not the
default file). Related: [[awplus-config-prompts-abort-and-logout]].
