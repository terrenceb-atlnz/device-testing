# IPv6 / BGP group — IE520 stack, tb470, 2026-09-29 campaign

Queue: [../CAMPAIGN-QUEUE-2026-09-29.md](../CAMPAIGN-QUEUE-2026-09-29.md) row 11. These cases are
hand-driven, with no framework script. `evidence/tools/ckcon.py` (a console.py wrapper; `CKTO` sets the
per-command timeout), `qmark.py` and `ckyn.py` drive the consoles. `nsresp.py` (the IPv6 NS
responder) and `mkpcap.py` with tcpreplay generate the traffic on tb470. Raw console transcripts are
in tb470 `/tmp/ck11/` (tmpfs).

| case | title | log | verdict |
| --- | --- | --- | --- |
| T8770 | IPv6 Neighbors - in silicon | [8770-fail.log](8770-fail.log) | **FAIL** (2026-09-30). The neighbours are learned by real ND (the T6057 responder method, for IPv6) and programmed as /128 host entries on all three members. Traffic to 2000 neighbours runs at 97–99 % of 984 Mbps at steady state. But the hardware holds only ~1.9 K (max 1904 rows), against the case's "approximately 5000". Beyond that the DUT still admits neighbours to software: with 5000 destinations it had 3030 learned vs 1567 in hardware, logged `EXFX … Unable to add NH Route entry … Table full` for 1893 addresses, and delivered 40 % of line rate. Also observed: at 300 pps ~50 % of valid NAs were dropped (in runs), and near 2.1 K the table evicts old entries rather than refusing new ones (IPv4 refuses at 2045, T6057). For review: the IE520's limits-DB figure was not available |
| T3116 | BGPv4 - Unicast Traffic | — | next |

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
