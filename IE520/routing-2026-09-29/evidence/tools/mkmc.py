#!/usr/bin/env python3
"""mkmc.py <src_mac> <src_ip> <group> <frame_len> <count> <out.pcap>

Write a pcap of <count> IPv4 multicast UDP frames (dport 5001, TTL 16) from a
fake source host to <group>, <frame_len> bytes on the wire excl. FCS.  The UDP
payload carries a sequence number so a capture can show which frames were lost."""
import sys, struct
from scapy.all import Ether, IP, UDP, Raw, wrpcap

smac, sip, grp, flen, count, out = sys.argv[1:7]
flen, count = int(flen), int(count)
g = [int(x) for x in grp.split(".")]
dmac = "01:00:5e:%02x:%02x:%02x" % (g[1] & 0x7f, g[2], g[3])
pk = []
for i in range(count):
    p = Ether(src=smac, dst=dmac) / IP(src=sip, dst=grp, ttl=16) / UDP(sport=5000, dport=5001)
    pay = struct.pack("!I", i)
    pay += b"\x5a" * max(flen - len(p) - len(pay), 0)
    pk.append(p / Raw(pay))
wrpcap(out, pk)
print("%d frames %s -> %s len %d -> %s" % (len(pk), sip, grp, len(pk[0]), out))
