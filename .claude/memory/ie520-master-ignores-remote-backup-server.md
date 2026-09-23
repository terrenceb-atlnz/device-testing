---
name: ie520-master-ignores-remote-backup-server
description: "An IE520 AMF master (awplus_main-20260923-20) ACCEPTS `atmf backup server id N <host> username <u> path <p>` but never checks or mounts it: server-status stays `No check`, no SSH connection is ever made, and `atmf backup now` says `No backup media found`. Use a documented master (x230/AR4050) or USB media."
metadata:
  node_type: memory
  type: project
---

Measured 2026-09-23 on tb470 for ATMF 38474/38475. The master was the 3-member IE520 stack; the
server was tb470 eth1 (10.38.215.1), `path /tmp/atmfbk`, user terrenceb. **Everything the server
side needs was proven in place:**

- `crypto key generate userkey manager rsa` on the master made a 3072-bit key. Its public key sat
  in a tb470-local AuthorizedKeysFile, scoped by an sshd `Match LocalAddress 10.38.215.1 Address
  10.38.215.10/31` drop-in, and `sshd -T -C` confirmed the scoping.
- `crypto key pubkey-chain knownhosts ip 10.38.215.1` fetched and stored tb470's RSA host key
  (SHA256:t+C9p31P...). So the master reaches tb470:22, and that fetch is the ONLY connection
  tb470's sshd journal ever logged from 10.38.215.10.

**Yet the master never tried the server.** Server 1 stayed `Configured (Unmounted)` and
server-status read `No check` for more than 20 minutes. Re-adding the server and toggling
`no atmf backup enable` / `atmf backup enable` changed nothing, and no login attempt ever reached
tb470. `atmf backup now IE520-sa` → `% No backup media found on this device`, and the 03:00 run
logged `atmffsd: ATMF backup: Scheduled backup not started because media not found`.

The wiki's platform tables for `atmf backup server` and `atmf master` list AR4050, AT-TQ7403R,
x230, x908Gen2, x930, x950, and not the IE520. Per [[awplus-cli-wiki-on-the-share]] a table is
not a gate, but here the behaviour agrees with it. **Whether this is "unsupported but
accepted" or a defect is Terrence's call; record it as a finding, not as bench misconfiguration.**

**How to apply:** don't spend setup time on a remote backup server behind an IE520 master. For
cases whose DUT is an IE520 MEMBER (38474), use a documented platform as the AMF master. **On
tb470 that means the AR4050S (`4050-5g`), measured 2026-09-23:** its FULL licence carries
AMF-MASTER-20…250, and `atmf master` took. **The x230-10GP cannot be master.** It answers `%
ATMF requires AMF-MASTER-X license`, and its licences list no AMF-MASTER feature. The 4050 sits
on 10.10.10.2 behind the stack, so tb470 needs a return route
(`10.10.10.0/27 via 10.38.215.10`) before it can serve as the backup server. For
recovery cases that only need master-side media (38475), a USB stick in the IE520 master is the
candidate: the IE520-sa logged `Updating ATMF backup location to "usb"`. Related:
[[bench-cannot-open-tcp-to-office-pcs]] (why the dev PC was not the server).
