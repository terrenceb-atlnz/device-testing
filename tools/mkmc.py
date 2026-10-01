#!/usr/bin/env python3
"""mkmc.py <src_mac> <src_ip> <group> <frame_len> <count> <out.pcap> [--sport N] [--dport N] [--ttl N]

Write a pcap of <count> IPv4 multicast UDP frames (sport 5000 -> dport 5001, TTL 16
by default) from a fake source host to <group>, <frame_len> bytes on the wire excl.
FCS.  The UDP payload carries a sequence number so a capture can show which frames
were lost.  Nothing is sent; the pcap goes only to <out.pcap>."""
import sys, struct

USAGE = ("usage: mkmc.py <src_mac> <src_ip> <group> <frame_len> <count> <out.pcap> "
         "[--sport N] [--dport N] [--ttl N]\n")
argv = sys.argv[1:]
def flag(name, default):                                 # pull "--name N" out of argv
    if name not in argv:
        return default
    i = argv.index(name)
    if i + 1 >= len(argv) or not argv[i + 1].isdigit():
        sys.stderr.write(USAGE); sys.exit(2)
    v = int(argv[i + 1]); del argv[i:i + 2]
    return v
sport, dport, ttl = flag("--sport", 5000), flag("--dport", 5001), flag("--ttl", 16)
if len(argv) != 6 or not argv[3].isdigit() or not argv[4].isdigit():
    sys.stderr.write(USAGE); sys.exit(2)
from scapy.all import Ether, IP, UDP, Raw, wrpcap

smac, sip, grp, flen, count, out = argv[0:6]
flen, count = int(flen), int(count)
g = [int(x) for x in grp.split(".")]
dmac = "01:00:5e:%02x:%02x:%02x" % (g[1] & 0x7f, g[2], g[3])
pk = []
for i in range(count):
    p = Ether(src=smac, dst=dmac) / IP(src=sip, dst=grp, ttl=ttl) / UDP(sport=sport, dport=dport)
    pay = struct.pack("!I", i)
    pay += b"\x5a" * max(flen - len(p) - len(pay), 0)
    pk.append(p / Raw(pay))
wrpcap(out, pk)
print("%d frames %s -> %s len %d -> %s" % (len(pk), sip, grp, len(pk[0]), out))
