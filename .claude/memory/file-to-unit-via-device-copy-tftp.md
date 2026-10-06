---
name: file-to-unit-via-device-copy-tftp
description: To put a file on a unit's flash, run AW+ `copy tftp://<box IP in the unit's subnet>/<file> flash:/<name>` from the unit's own CLI, with the file in the box's /tftproot; don't go looking for repo helpers
metadata:
  type: feedback
---

To get a file (a bootloader `.kwb`, a `.rel`, a `.cfg`) onto a unit, put it in the testbox's
`/tftproot` (`/tftpboot` is a symlink to it) and run this on the unit's CLI:

`copy tftp://10.38.215.XX/<file> flash:/<name>`

`XX` is the box's address on whichever host NIC subnet reaches that unit (it varies by unit:
on tb470, eth2 is `.33` toward the x230 on u0). `<name>` can rename the file.

**Why:** Terrence, 2026-10-06, stopped a session that was reading `tools/tftp_copy.py` before a
plain bootloader copy: "from the device you can just run: copy tftp://… flash <name>". It is one
CLI line. A helper adds nothing for a small file and costs a detour.

**How to apply:**
- Send that line through `ckcon.py`.
- Before the copy, check that the file in `/tftproot` matches its source with sha256 on both
  ends.
- After the copy, `dir` must show the same byte count.
- Measured 2026-10-06: two 786,432 B x230 bootloaders TFTPed in about 1 s each, with no
  confirmation prompt for a new destination name.
- Large images that a stack must sync have their own procedure:
  [[ie520-image-update-procedure]].
