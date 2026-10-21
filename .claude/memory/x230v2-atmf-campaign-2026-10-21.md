---
name: x230v2-atmf-campaign-2026-10-21
description: "tb470 2026-10-21: T46810 ATMF Backup + T28218 ATMF provisioning, 2 PASS with the AR4050S as AMF master (USB media) and the x230v2 as member; T46810 has NO steps in ck.db (functional reading CONFIRMED by Terrence 2026-10-21); provision-mode `delete` leaves an empty node dir; console.py now knows the [atmf-provision]# prompt; orient brief wrongly said no x230v2 platform file: `ls platforms/` first"
metadata:
  type: project
---

**What ran (tb470, u0 = AR4050S master, u1 = x230v2-28GS member, 2026-10-21, final logs `04bc3ce` (was 297190c before the 12:3x rebase),
`tb470/x230v2-28GS/atmf-2026-10-21T0835/`):**
- **T46810 "ATMF Backup"** has one EMPTY step and no objective in ck.db (folder names an ARX200S-GTX scale project).
  Terrence's answer "the backup should be with the provisioned node" was read as: back the x230 member up to the master's
  USB, and use that backup as T28218's file-set. PASS under that reading, which Terrence CONFIRMED the same afternoon ("yes, that is confirmed"): the verdict stands.
- **T28218** ran as written, all five steps on the master; `future_node` seeded from the x230's backup. Option (c), real
  provisioning with `atmf cleanup` + recovery, was out of scope (no TFTP fallback: tb470 eth1/2/3 down).

**Keepers:**
- The 4050's FULL licence makes it an AMF master; `Backup Media .......... USB` picks the stick by itself. `atmf backup
  now` is asynchronous: poll `show atmf backup` for `<node> … Yes Yes Good` (32 s for 36.7 MB).
- Provision-mode `delete` removes `<node>/flash/` but leaves an empty `usb:/atmf/<net>/nodes/<node>/`; `rmdir` it in the
  restore. The run also leaves `usb:/atmf/<net>/{info,logs,nodes,areas,guests}/` (empty) on the stick.
- Each AMF CLI case fits one `tools/tb ckcon --stop-on-error` pass (`CKTO=600` for a 36.7 MB usb→usb copy): 7 calls for
  T28218. `tools/console.py` matches `host[atmf-provision]#` since b29652b.
- **The orient brief claimed "no platform file for x230v2-28GS"; `platforms/x230v2-28GS.md` had existed since 10-09.**
  `ls platforms/` before saying a family has none; the memory index does not list platform files.
- A triage hand-back with questions stalled 32 min and cost a full cache re-write; where the defaults are safe, dispatch
  with "run on these defaults unless the Test Engineer objects" (group REVIEW.md).
- The sentinel session's process died mid-restore (09:33); the tester subagent resumed by name with its context intact
  and only re-verified. The device had taken every restore command: read the box transcript before assuming loss.

Related: [[ie520-master-ignores-remote-backup-server]], [[atmf-recovery-residue-and-reboots]],
[[session-restart-leaves-old-copy]], [[campaigns-measured-for-token-waste]].
