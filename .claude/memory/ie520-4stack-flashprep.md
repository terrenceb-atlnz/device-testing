---
name: ie520-4stack-flashprep
description: 2-member VCStack cap was an OLD-build limit — the new build (awplus_main-20260913-1734) supports up to 8; a 4-member ring stack is now live on tb470. Plus how to flash members on this build.
metadata: 
  node_type: memory
  type: project
  originSessionId: a6244017-fc0c-4802-b364-12f1f06cfcb6
  modified: 2026-09-14T00:00:00.000Z
---

**REVERSED 2026-09-14.** The 2026-09-04 "hard cap of 2 members" was a limit of the OLD build, not
the product. A new mainline build **`awplus_main-20260913-1734`** lifts it (up to 8, the standard),
and Terrence rebuilt tb470 into a **single 4-member VCStack ring** (members 1-4 = S/N 264A23061 /
264A23068(master) / 264A23066 / 264A23052 on `/dev/u2 / u3 / u5 / u4`). Full layout + ring + edges:
`bench-setup/bench-state.md` "Current state — 2026-09-14". So a build date genuinely can change a
"product limit" — re-test capability on the live build, don't trust an old NEGATIVE.

**(Historical, OLD build, 2026-09-04):** `stack 1 renumber 3|4` → `% The max stack member ID
supported by this product is 2`; `switch 3 provision ie520-28` → `% Invalid switch value`. That is
what the new build fixed.

**Flashing members on the NEW build (MEASURED 2026-09-14) — a large file only lands in a member's
flash while that member is the MASTER (local TFTP).** Every non-master path is a dead end here:

- master → `awplus-N/flash:<file>` (flash-to-flash push) and `tftp:` → `awplus-N/flash:` both fail:
  `nfs: server 192.168.255.N not responding, timed out` → `% Input/Output error due to external media
  removal`. SMALL cross-member writes work and ICMP to `192.168.255.N` is clean — only the large
  transfer stalls (member SPIFlash write over the internal NFS). The proven large cross-member copy is
  a PULL (member→master), never a large push.
- `remote-login N` then `copy tftp:` → `% Copying to/from remote file systems is only supported from
  the stack master`.
- Local TFTP on the master works (that is how the master got `IE520-awplus_main-20260913-1734.rel`).
  ⇒ To flash members, make each the master in turn (priority + reload) and TFTP locally; TFTP from
  `10.38.215.1` works from any master (data crosses the fabric as normal forwarding).
- **BETTER, MEASURED 2026-10-02 (build `awplus_main-20260923-20`, 3-member stack 1/3/4):** TFTP the
  image to the MASTER only, then `boot system flash:/<file>` there. The stack's own file sync
  copies it to every member ("File synchronization with stack member N successfully completed",
  console only, not in the log) in **~5 min for 41 MB, with no reloads and no NFS stall**. A
  plain `copy` push of the same file to member 1 had failed with the NFS timeout ten minutes earlier.
  The cost is that the boot pointer changes, so the next reload boots it. To stage without
  booting it, set the pointer back afterwards; the files stay.

Other durable facts (unchanged):
- Cross-member path syntax for small files is `awplus-N/flash:<file>` (**no slash** after `flash:`).
- AW+ refuses to overwrite/delete the file set as the current boot image, and `boot system tftp://…`
  is rejected — stage a new release under a dated name (e.g. `IE520-awplus_main-20260913-1734.rel`),
  don't overwrite `IE520-tb470.rel`.
- **`shutdown` on a stackport is NOT saved to config**; make a safe state durable with `no stackport`
  (persisted, needs reboot) or by uncabling.
- Renumbering renames real ports (`portN.0.x`); the old range goes phantom (`provisioned`).

See [[tb470-topology-and-setup]], [[ie520-release-naming-and-drift]].
