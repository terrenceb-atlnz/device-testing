# bfd-vrrp-2026-10-16T1406

tb277, AT-x960-56YSQ (swi_d, S/N A2WQS700B, `sin_x96056-20261012-24`), 2026-10-16 18:24–19:25 NZDT.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T47201 | IPv4_BFD - With RIP v1/v2 | [T47201/T47201-unsupported.log](T47201/T47201-unsupported.log) | **UNSUPPORTED**. No RIP-to-BFD binding exists on this platform: `bfd` is unrecognized in both interface and `router rip` mode, neither mode's complete command list holds it, `neighbor <addr> ?` takes no suffix, and the RIP guide has zero occurrences of "bfd" — while `ip ospf bfd` is accepted on the same interface in the same minute and both daemons are running. BFD itself works: 3 × 300 ms on the wire, detecting a silent neighbour failure in ~1.4 s (v2) and ~1.1 s (v1), during which RIP kept the dead prefix in the FIB marked `best` for ~171.6 s and the dataplane measured 0/5 with its instrument at 5/5. |
| T47873 | VRRP(v3) | [T47873/T47873.log](T47873/T47873.log) | **PASS**. All three authored claims graded on the wire: VRRPv3 read off the advertisement's own version field with virtual MAC `00:00:5e:00:01:0a` as the Ethernet source and the ARP reply for the virtual IP carrying it; the end device reached 5/5 through the loss of either router; role transition measured in the dataplane as ttl 63 → 62 → 63 with the instrument held at 63 and an unowned-MAC control at 0. Transition mode emits paired v2/v3 advertisements 26 µs apart; survives a cold boot with the tracking relationship re-armed; removal returns to the measured baseline. Carries the measured checksum evidence of STEP 4. |
