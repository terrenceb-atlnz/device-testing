#!/usr/bin/env python3
"""mkpcap.py <v4|v6> <src_mac> <dst_mac> <src_ip> <dst_base_ip> <first> <count> <frame_len> <out.pcap>

Write a pcap of <count> routed UDP frames, one per destination address
<dst_base_ip> + first .. + first+count-1, each <frame_len> bytes on the wire
(excl. FCS), from <src_ip> to the router MAC <dst_mac>. For tcpreplay: a slow
--pps replay makes the DUT resolve each destination (T8770 table fill); a
--topspeed --loop replay is line-rate traffic across every destination (T8770
traffic phase, T3116)."""
import ipaddress, sys
from scapy.all import Ether, IP, IPv6, UDP, Raw, wrpcap

fam, smac, dmac, sip, base, first, count, flen, out = sys.argv[1:10]
first, count, flen = int(first), int(count), int(flen)
b = ipaddress.ip_address(base)
pk = []
for i in range(first, first + count):
    d = str(b + i)
    l3 = IPv6(src=sip, dst=d, hlim=64) if fam == "v6" else IP(src=sip, dst=d, ttl=64)
    p = Ether(src=smac, dst=dmac) / l3 / UDP(sport=40000 + (i % 20000), dport=9)
    pad = flen - len(p)
    pk.append(p / Raw(b"\x5a" * max(pad, 0)))
wrpcap(out, pk)
print("{} frames {}..{} len {} -> {}".format(len(pk), pk[0][1].dst, pk[-1][1].dst, len(pk[0]), out))
