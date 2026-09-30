#!/usr/bin/env python3
"""mkospf.py <src_mac> <router_mac> <src_ip> <count> <frame_len> <out.pcap>

T10624: one routed UDP frame per advertised prefix 10.(124+n//256).(n%256).0/24, n = 0..count-1,
to host .10 in it, from a fake host <src_ip>/<src_mac> to the DUT router MAC. <frame_len> =
bytes on the wire excl. FCS. The UDP payload carries n so a capture shows which prefix it
belongs to. A --loop replay spreads line-rate traffic evenly over every prefix."""
import sys, struct
from scapy.all import Ether, IP, UDP, Raw, wrpcap
smac, dmac, sip, count, flen, out = sys.argv[1:7]
count, flen = int(count), int(flen)
pk = []
for n in range(count):
    d = "10.%d.%d.10" % (124 + n // 256, n % 256)
    p = Ether(src=smac, dst=dmac) / IP(src=sip, dst=d, ttl=64) / UDP(sport=6000, dport=6001)
    pay = struct.pack("!I", n)
    pk.append(p / Raw(pay + b"\x5a" * max(flen - len(p) - len(pay), 0)))
wrpcap(out, pk)
print("%d frames %s..%s len %d -> %s" % (len(pk), pk[0][IP].dst, pk[-1][IP].dst, len(pk[0]), out))
