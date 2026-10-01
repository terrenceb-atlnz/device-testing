#!/usr/bin/env python3
"""ra_decode.py <pcap>: print every Router Advertisement with its Prefix Information options."""
import sys, datetime
if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
    sys.stderr.write("usage: ra_decode.py <pcap>\n")
    sys.exit(2)
from scapy.all import rdpcap, ICMPv6ND_RA, ICMPv6NDOptPrefixInfo, IPv6, Ether
n = 0
for p in rdpcap(sys.argv[1]):
    if ICMPv6ND_RA not in p: continue
    n += 1; ra = p[ICMPv6ND_RA]
    t = datetime.datetime.fromtimestamp(float(p.time)).strftime("%H:%M:%S.%f")[:-3]
    print("%s RA %s (%s) -> %s  hlim=%d M=%d O=%d routerlifetime=%d" % (t, p[IPv6].src, p[Ether].src, p[IPv6].dst, ra.chlim, ra.M, ra.O, ra.routerlifetime))
    o = p.getlayer(ICMPv6NDOptPrefixInfo); i = 1
    while o is not None:
        print("    prefix %s/%d  L=%d A=%d valid=%d preferred=%d" % (o.prefix, o.prefixlen, o.L, o.A, o.validlifetime, o.preferredlifetime))
        i += 1; o = p.getlayer(ICMPv6NDOptPrefixInfo, i)
print("RA count:", n)
