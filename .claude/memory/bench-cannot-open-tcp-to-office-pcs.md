---
name: bench-cannot-open-tcp-to-office-pcs
description: "Nothing on the lab side (tb470's own 10.36.201.215 or the bench 10.38.215.0/24) can open a TCP connection to the office subnet (dev PC 10.33.22.17). ICMP passes, so ping lies. A bench device cannot use the dev PC as an SSH/file server; put such servers on tb470."
metadata:
  node_type: memory
  type: project
---

Measured 2026-09-23 while pointing the IE520 stack's AMF backup server at the dev PC
(`10.33.22.17`) for ATMF 38474/38475:

- **ICMP works both ways**: the stack pinged 10.33.22.17 3/3 (after
  `ip route 10.33.22.0/24 10.38.215.1` on the stack), and the dev PC reaches 10.38.215.1.
- **TCP from the lab side times out on EVERY port**: open ones (22, 5666, 8000, 3389) and a
  closed one (23) alike, so not even a RST comes back. This held from tb470's own address and
  from bench source 10.38.215.1 (`nc -s`). AW+ reported it as
  `% Cannot retrieve public key from "10.33.22.17"`.
- On the dev PC, ufw is `ENABLED=no` and nftables/firewalld are inactive. iptables can't be read
  without sudo, so the block is almost certainly the **lab→office network firewall**. The
  office→lab direction works: that is how we ssh to tb470.

**Why:** I configured the route, the userkey and an authorized_keys line before testing the
transport. That cost about 15 minutes, and the line had to be removed again.

**How to apply:** any case where the bench must connect TO a server (AMF remote backup,
SCP/SFTP/TFTP from a PC, syslog over TCP, a RADIUS/TACACS host) needs the server on **tb470**
(10.38.215.1 / .33 / .65), never on the dev PC. **Test the transport first**:
`ssh tb470 'timeout 6 bash -c "</dev/tcp/<ip>/<port>"'`. A timeout on a CLOSED port means the
traffic is filtered, not that the service is down. This fact belongs in `TB470-HOST-NETWORKING.md`
(Test-cases repo) at the next wrap. See [[tb470-topology-and-setup]] and
[[prefer-pragmatic-fix-over-infra-debugging]].
