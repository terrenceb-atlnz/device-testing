#!/usr/bin/env python3
"""mkvrrp.py <vids,comma> <vrids,comma> <src_net_prefix> <dst_ip> <frame_len> <rounds> <out.pcap>

Write a pcap of 802.1Q-tagged routed UDP frames for T18948: for each ingress VLAN vid[i]
a fake host 10.118.<i+1>.2 (MAC 02:31:18:94:00:<i+1>) sends to <dst_ip> via the VRRP
virtual MAC 00:00:5e:00:01:<vrid[i]>. Frames are interleaved round-robin across the VLANs,
<rounds> frames per VLAN. <frame_len> = bytes on the wire INCLUDING the 4-byte tag, excl. FCS
(1518 -> IP length 1500 -> 1514 B untagged at the egress). The UDP payload carries
(vlan index, sequence) so a receiver can count per VLAN."""
import sys, struct
from scapy.all import Ether, Dot1Q, IP, UDP, Raw, wrpcap
vids = [int(x) for x in sys.argv[1].split(",")]
vrids = [int(x) for x in sys.argv[2].split(",")]
pfx, dip, flen, rounds, out = sys.argv[3], sys.argv[4], int(sys.argv[5]), int(sys.argv[6]), sys.argv[7]
pk = []
for r in range(rounds):
    for i, (v, vr) in enumerate(zip(vids, vrids)):
        p = (Ether(src="02:31:18:94:00:%02x" % (i + 1), dst="00:00:5e:00:01:%02x" % vr) /
             Dot1Q(vlan=v) / IP(src="%s.%d.2" % (pfx, i + 1), dst=dip, ttl=64) /
             UDP(sport=5000 + i, dport=5001))
        pay = struct.pack("!HI", i, r)
        pk.append(p / Raw(pay + b"\x5a" * max(flen - len(p) - len(pay), 0)))
wrpcap(out, pk)
print("%d frames, vids %s, vrids %s, len %d -> %s" % (len(pk), vids, vrids, len(pk[0]), out))
