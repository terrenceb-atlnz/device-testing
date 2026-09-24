---
name: tb470-reboot-nfshome-unmounted
description: "After a tb470 reboot /nfsHome can come up UNMOUNTED, so /home/st-art/st-art (a symlink to /nfsHome/st-art/) dangles and /home/st-art/st-art/configs/tb470.setup 'does not exist'. The file is intact. Fix: Terrence runs `sudo mount /nfsHome`. Check this after any tb470 reset."
metadata:
  type: project
---

Measured 2026-09-24. Terrence reset tb470 (`uptime -s` 11:57:54). The box then stayed
unreachable on its 10.36.201.x management network until ~14:15: tb105, on the same
`bootnet`, saw its ARP as FAILED. When it came back:
- `bench_setup.py check` died with `cat: /home/st-art/st-art/configs/tb470.setup: No such
  file or directory`.
- `/home/st-art/st-art` is a symlink to `/nfsHome/st-art/`. fstab mounts
  `10.36.250.11:/home` on BOTH `/home` and `/nfsHome`, but only `/home` had come up.
- The file was intact, with the same sha1: `/home/st-art/configs/tb470.setup` is the same
  export reached through `/home`.

**Why it matters:** every framework run, and `bench_setup.py`, uses the canonical
`/home/st-art/st-art/configs/…` path. Until the mount is back they fail as if the `.setup`
had been deleted.

**How to apply:**
- After any tb470 reset, run `findmnt /nfsHome` before trusting a missing `.setup`.
- If it is unmounted, Terrence runs `sudo mount /nfsHome` (a root change, see
  [[tb470-root-changes-go-through-terrence]]).
- Do NOT repoint `bench_setup.py` at the `/home/st-art/configs/` alias.
- A reset also wipes tb470's `/tmp` (the `/tmp/ckorient` helpers, `/tmp/atmfbk`) and any
  runtime route (the ATMF `10.10.10.0/27`).
- The ~2 h gap between the reset and the box being reachable was the management network, not
  the boot. Say so rather than assuming the box is still booting.
