#!/usr/bin/env python3
"""mk12589.py <router_mac> <vid> <dst_ip> <frame_len> <rounds> <out.pcap>

T12589 (PBR + RIP) traffic, in place of the case's IXIA1 streams. Each round is one frame from
each of 254 fake hosts 192.168.10.1-254 (MAC 02:12:58:90:10:<host>) in 802.1Q VLAN <vid>, sent
to the DUT's router MAC for <dst_ip>:
  Pkts1 = sources 192.168.10.1-127   (NOT matching the traffic class) -> UDP sport 5001
  Pkts2 = sources 192.168.10.128-254 (matching the traffic class)     -> UDP sport 5002
UDP dport 5009. <frame_len> = bytes on the wire including the tag, excluding FCS.
So <rounds> rounds = 127*<rounds> frames of each kind."""
import sys
from scapy.all import Ether, Dot1Q, IP, UDP, Raw, wrpcap
rmac, vid, dip, flen, rounds, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
pk = []
for r in range(rounds):
    for h in range(1, 255):
        p = (Ether(src="02:12:58:90:10:%02x" % h, dst=rmac) / Dot1Q(vlan=vid) /
             IP(src="192.168.10.%d" % h, dst=dip, ttl=64) /
             UDP(sport=5001 if h <= 127 else 5002, dport=5009))
        pk.append(p / Raw(b"\x5a" * max(flen - len(p), 0)))
wrpcap(out, pk)
print("%d frames (%d Pkts1 + %d Pkts2), vid %d, len %d, dst %s via %s -> %s"
      % (len(pk), 127 * rounds, 127 * rounds, vid, len(pk[0]), dip, rmac, out))
