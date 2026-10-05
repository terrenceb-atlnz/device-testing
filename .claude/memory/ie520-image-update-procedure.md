---
name: ie520-image-update-procedure
description: The Test Engineer's procedure for loading a new .rel onto IE520s that boot from flash — TFTP to master, sync to members, set EACH bootloader to Flash + the new file (Boot Menu 2→1→file) without finishing, then 9 on all together, then delete old .rel files
metadata:
  type: feedback
---

The Test Engineer's procedure (2026-10-05) when the bootloaders boot from flash:

1. TFTP-copy the `.rel` to the master.
2. Have the master sync the `.rel` to the members (`boot system flash:/<file>` on the master syncs
   it, ~5 min for 40 MB).
3. Reload the **members one by one**. For each, open the bootloader (Ctrl+B), go to `2` (change the
   default boot source), choose `1` (Flash), and select the `.rel` just copied. **Do not let it
   finish rebooting**: leave it parked at the Boot Menu.
4. Reload the **master** and do the same.
5. Once every unit is set to the same flash `.rel`, press `9` (Quit and continue booting) on all
   of them, and let them boot and re-form the stack.
6. When the stack has re-converged, go into each device's flash and **delete the old `.rel`
   files**. Then it is done.

**Why:** the Test Engineer's bench standard is the bootloader set explicitly to Flash + a named
file. The banner then reads "forced to boot from a non-standard location", which is EXPECTED
here, not a fault. Relying on `boot system` alone, or on Boot Menu `2→9` ("Boot from default,
determined by main CLI"), is not their method. On 2026-10-05 the `2→9` route was used on all four
IE520s before they gave this procedure.

**How to apply:**
- Any IE520 image update follows these steps, the standalone SA included (for it, skip steps 2–4's
  member logic).
- Never leave a unit at the Boot Menu longer than the procedure needs.
- Drive the menu with bare keys only (platforms/IE520.md §2).
- **Step 1 — re-read the source right before the copy (2026-10-06).** `/tftproot/IE520-tb470.rel`
  is shared and changes under you: the nightly `20261006-51` landed at 08:49 and someone swapped
  in the `main-calanm` dev build at 08:53, between my listing and my TFTP. Read `ls -l` + the
  `.info` immediately before `copy`, pass that size to `tftp_copy.py`, and treat a size delta as
  "which build is this?", not as SPIFlash rounding.
- **Step 2 — `boot system` is a GLOBAL CONFIG command:** at the exec prompt it is `% Invalid
  input`. `configure terminal` → `boot system flash:/<file>` → wait for both
  `File synchronization with stack member N successfully completed` lines (195 s for 40 MB on
  2026-10-06) → `end`.
- Step 3's member reload: `reload stack-member N` on the master (`(y/n)` → `y\r`), with the park
  watcher already reading that member's console.
- Related: [[ie520-4stack-flashprep]], [[read-the-transcripts-before-driving-hardware]].
