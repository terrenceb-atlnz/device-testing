#!/usr/bin/env python3
"""Rewrite tb470.setup's portlink section from the 2026-09-01 measurements.

Run ON tb470. Idempotent-ish: it asserts the old text is present first, so a second
run fails loudly rather than corrupting the file.
"""
import io

P = "/home/st-art/st-art/configs/tb470.setup"
s = io.open(P, encoding="utf-8").read()
orig = s

OLD_START = "### VERIFIED 2026-08-31 by MAC cross-match from BOTH ends"
OLD_END = "###   That is a MUTATING check on a live bench and needs sign-off first.\n"
i = s.index(OLD_START)
j = s.index(OLD_END) + len(OLD_END)

NEW = '''### ===== MEASURED 2026-09-01 -- THIS SUPERSEDES THE 2026-08-31 MAPPING =====
### Method: LACP partner system-ID, plus `show mac address-table` / `show arp` read
### from both ends. The LACP trick is the cheap one: a partner system-ID IS the far
### end's base MAC, so it names the neighbour on every member link WITHOUT shutting
### a port -- which is what the old note below said would need sign-off.
### Raw capture (bench_probe.py, all three devices, 9 commands each):
###   ~/old test runs/IE520/stack-tests/bench-probe-2026-09-01/capture.json
###
###   stk_a po1  <->  swi_c po2      (LACP, 2 x 1G)
###     stack po1 = swi_b port1.0.1 + swi_a port2.0.1  (channel-group 1 mode active)
###     4050  po2 = port1.0.3 + port1.0.4              (formed PASSIVELY -- see below)
###     Proof in both directions: the stack reports Partner LAG
###     0x8000,00-00-cd-40-03-94,0x0002 (the AR4050S base MAC) and the 4050 reports
###     0x8000,00-00-cd-37-0d-6f,0x0001 (the stack VMAC). All links "synchronized".
###     WARNING -- WHICH LEG PAIRS WITH WHICH IS INFERRED, NOT MEASURED. LACP does
###     not report a per-link partner PORT. swi_b port1.0.1 <-> swi_c port1.0.4
###     carries over from the MAC cross-match taken before the aggregation formed;
###     the other leg then follows by elimination. To prove it: shut ONE 4050 member
###     and watch which stack port drops -- MUTATING, needs sign-off, and it degrades
###     the LAG while it runs.
###
###   tb eth3 <-> swi_c port1.0.1
###     The 4050 holds 00f0.4d00.7718 (tb470's own eth3) on port1.0.1, and maps
###     10.38.215.65 to it in ARP.
###
###   swi_d port1.0.2 <-> swi_c port1.0.2
###     STRONG INFERENCE, not independently pinned. The 4050 has exactly four ports
###     up (1.0.1-1.0.4) and three are accounted for above; swi_d has exactly ONE
###     port connected (port1.0.2) and learns the 4050 base MAC 0000.cd40.0394 on
###     its sa1.
###
### SUPERSEDED: the previous file declared `swi_b port1.0.1 <-> swi_d port1.0.1`,
### verified 2026-08-31. THAT CABLE HAS MOVED -- swi_d port1.0.1 now reads
### notconnect, and swi_b port1.0.1 LACP-partners with the AR4050S. The old line was
### true when written; it is kept here only as history.
###
### swi_c IS A ROUTER (AR4050S) and its bench role is 802.1X -- not a switch. Its
### port1.0.1-1.0.8 switch group is incidental to that, and so is po2: the 4050 runs
### `lacp global-passive-mode enable`, so it NEVER initiates an aggregation but will
### passively bond ANY links that present LACP to it. Two consequences:
###   * po2 appeared by itself the moment the IE520 side was configured. It is NOT in
###     the 4050's running-config, so `show running-config` will not reveal it --
###     only `show etherchannel detail` will.
###   * LOOP RISK: two links to the 4050 that are NOT aggregated on the OTHER end
###     stay independent, and loop. Measured 2026-09-01: the 4050's own MAC thrashing
###     between IE520 port1.0.1 and port2.0.9, costing ~30% of a `show tech-support`
###     collection, cured by unplugging one leg. Present two links to swi_c ONLY as a
###     single LACP channel.
###
### SEGMENTS / ADDRESSING as at 2026-09-01 -- tb470 fronts THREE /27s here:
###   tb eth1 10.38.215.1/27 | tb eth2 10.38.215.33/27 | tb eth3 10.38.215.65/27
###   stk_a vlan1   10.38.215.66/27  static  (ntp server 10.38.215.65 -> stratum 3)
###   swi_c vlan1   10.38.215.70/27  BY DHCP (its config reads `ip address dhcp`)
###   swi_d vlan100 10.38.215.2/27   -- sits inside tb470's eth1 pool .2-.10, beware
###   ACCESS-VLAN MISMATCH across swi_c <-> swi_d: the 4050 side is vlan1, the x230
###   side is vlan100. Both untagged, so they form ONE broadcast domain carrying TWO
###   IP subnets. That is why swi_d learns the 4050's MAC on vlan100.
'''

s = s[:i] + NEW + s[j:]

OLD_PL = "[portlink]\nswi_b-swi_d = port1.0.1-port1.0.1"
NEW_PL = """[portlink]
### Physical links only -- an aggregation is declared as its MEMBER links, and a
### portlink names the MEMBER switch, never the stack. Evidence for every line is in
### the MEASURED 2026-09-01 block above; nothing here is declared without it.
swi_b-swi_c = port1.0.1-port1.0.4
swi_a-swi_c = port2.0.1-port1.0.3
swi_d-swi_c = port1.0.2-port1.0.2
tb-swi_c = eth3-port1.0.1"""

assert OLD_PL in s, "portlink block not found in expected form"
s = s.replace(OLD_PL, NEW_PL, 1)
assert s != orig

io.open(P, "w", encoding="utf-8").write(s)
print("tb470.setup updated")
