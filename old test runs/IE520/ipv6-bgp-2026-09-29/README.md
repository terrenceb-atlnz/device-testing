# IPv6 / BGP group — IE520 stack, tb470, 2026-09-29 campaign

Queue: [../CAMPAIGN-QUEUE-2026-09-29.md](../CAMPAIGN-QUEUE-2026-09-29.md) row 11. These cases are
hand-driven, with no framework script. `evidence/tools/ckcon.py` (a console.py wrapper; `CKTO` sets the
per-command timeout), `qmark.py` and `ckyn.py` drive the consoles. `nsresp.py` (the IPv6 NS
responder) and `mkpcap.py` with tcpreplay generate the traffic on tb470. Raw console transcripts are
in tb470 `/tmp/ck11/` (tmpfs).

| case | title | log | verdict |
| --- | --- | --- | --- |
| T8770 | IPv6 Neighbors - in silicon | [8770-fail.log](8770-fail.log) | **FAIL** (2026-09-30). The neighbours are learned by real ND (the T6057 responder method, for IPv6) and programmed as /128 host entries on all three members. Traffic to 2000 neighbours runs at 97–99 % of 984 Mbps at steady state. But the hardware holds only ~1.9 K (max 1904 rows), against the case's "approximately 5000". Beyond that the DUT still admits neighbours to software: with 5000 destinations it had 3030 learned vs 1567 in hardware, logged `EXFX … Unable to add NH Route entry … Table full` for 1893 addresses, and delivered 40 % of line rate. Also observed: at 300 pps ~50 % of valid NAs were dropped (in runs), and near 2.1 K the table evicts old entries rather than refusing new ones (IPv4 refuses at 2045, T6057). For review: the IE520's limits-DB figure was not available |
| T3116 | BGPv4 - Unicast Traffic | [3116.log](3116.log) | **PASS** (2026-09-30). An eBGP IPv4 peering, stack AS 65116 ↔ IE520-sa AS 65117, over the SX link (scratch VLAN 3162). Each side advertises its host subnet, the routes are installed as `B` and in hardware, and the session stays Established throughout. Routed unicast in both directions at once, 30 s at 1514 B: 2,404,501/2,404,501 at 970.8 Mbps and 2,415,001/2,415,001 at 974.9 Mbps, 100 %. Controls: with no BGP, 0/~810 K each way; after the SA withdrew its prefix, the dependent flow was 0/803,001 while the other stayed at 100 %. Not measured: small-frame line rate (tcpreplay tops out at 170–229 K pps at 64 B, all delivered). I-19's '~26 Mbps harness' blocker no longer applies |

## Bench facts used (2026-09-30)
- tb470 has `ip_forward=1` and IPv6 `forwarding=1` (`/proc/sys`). Every receive-side "host" in these
  cases therefore uses a fake, locally administered MAC. A frame addressed to a real tb470 NIC MAC
  with a foreign destination IP would be routed onward by the host.
- tcpreplay's flow-statistics decoder warns once per packet on these pcaps. Use `--no-flow-stats`.

## Group setup and restore
Pre-group capture `pre-test-configs/2026-09-30/pre-u{5,3,1,0}.out` (17:32). It is IDENTICAL to
the row-10 baseline (../dhcpv6-2026-09-29/pre-test-configs/2026-09-30b/). Probe 2026-09-30T043141Z
MATCH. There is no group-wide setup: each case builds its own scratch config and removes it.
- T8770 removed its config at 18:05. The stack running-config is IDENTICAL to the pre-group
  capture (`evidence/8770/8770-post-u5.out`).
- T3116 removed its config at 18:17–18:18. The stack and the SA are back as they were: port3.0.13 and SA port1.0.2 in vlan 1, the SX link in vlan 4000.

## Group close (18:19–18:20, after T3116)
`post-test-configs/2026-09-30/final-u{5,3,1,0}.out`: `show running-config` is IDENTICAL to the pre-group
capture on u5, u3, u1 and u0 (0 diff lines each). Current boot config is `flash:/tb470-bench.cfg (file exists)` on
all four, and the stack's copy is unchanged (2927 bytes, 03:07:49 UTC). Nothing was written, and no file was created on any flash.
Stack members 1/3/4 Ready, member 3 Active Master, Normal operation. `bench_probe.py run`
2026-09-30T051943Z MATCH, no advisory. No console holders (fuser empty), no tcpdump/tcpreplay/responder left
running, and every console (u0–u5) is at an exec prompt.
