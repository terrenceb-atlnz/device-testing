---
name: tb470-root-changes-go-through-terrence
description: "tb470 has passwordless sudo, but in auto mode the safety check blocks persistence-type root changes (authorized keys, sshd config, routes) as 'Unauthorized Persistence'. Stage the files in tb470 /tmp/ckorient/work and hand Terrence the install lines, or ask him to switch to manual mode."
metadata:
  node_type: memory
  type: project
---

2026-09-23 (ATMF 38474, making tb470 the AMF remote backup server). Terrence had approved root
on tb470 and asked for the key to be honoured only from a /31 and only on the eth port facing
the device. The design that met that:
- the key lives in a **tb470-LOCAL** file, `/etc/ssh/atmf-backup-keys/%u`, not the NFS-shared
  `~/.ssh`;
- one sshd drop-in, `/etc/ssh/sshd_config.d/60-atmf-backup-tb470.conf`, holds
  `Match LocalAddress <eth IP> Address <device>/31 User terrenceb` + `AuthorizedKeysFile` +
  `AuthenticationMethods publickey`;
- it was verified with `sshd -t` plus `sshd -T -C user=…,addr=…,laddr=…` for the device AND
  for bystanders before any reload. Debian's `ExecReload` runs `sshd -t` too.

**The block:** in auto mode the classifier denied both the first install and the later
update (plus a return route) as **"Unauthorized Persistence"**, although Terrence had
consented in chat. The first install went through once he switched to manual mode and approved
the prompt. The update went through by **Terrence pasting four lines** that installed files I
had staged in `/tmp/ckorient/work/`.

**How to apply:** for any root change on tb470 that grants access or survives a reload (keys,
sshd/PAM, routes, packages, services):
1. Stage the exact files in `/tmp/ckorient/work/`.
2. Give him the `sudo install …` / `ip route add …` lines, with the revert line.
3. Or ask him to switch to manual mode and approve the call.

Never try to route around a denial. Verify afterwards with byte-compares (`cmp` staged vs
installed) and `sshd -T -C`. Related: [[bench-cannot-open-tcp-to-office-pcs]],
[[ie520-master-ignores-remote-backup-server]].
