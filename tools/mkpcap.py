#!/usr/bin/env python3
"""mkpcap.py <v4|v6> <src_mac> <dst_mac> <src_ip> <dst_base_ip> <first> <count> <frame_len> <out.pcap> [fixed]
          [--dport N] [--sport-base N] [--ttl N]

Write a pcap of <count> routed UDP frames, one per destination address
<dst_base_ip> + first .. + first+count-1, each <frame_len> bytes on the wire
(excl. FCS), from <src_ip> to the router MAC <dst_mac>. `fixed` sends every frame
to <dst_base_ip> itself. UDP dport --dport (default 9), sport --sport-base + (i %
20000) (default 40000), TTL / hop limit --ttl (default 64). For tcpreplay: a slow
--pps replay makes the DUT resolve each destination (e.g. T8770 table fill); a
--topspeed --loop replay is line-rate traffic across every destination (e.g. T8770
traffic phase, T3116). Nothing is sent; the pcap goes only to <out.pcap>."""
import ipaddress, sys

USAGE = ("usage: mkpcap.py <v4|v6> <src_mac> <dst_mac> <src_ip> <dst_base_ip> <first> <count> "
         "<frame_len> <out.pcap> [fixed] [--dport N] [--sport-base N] [--ttl N]\n")
argv = sys.argv[1:]
def flag(name, default):                                 # pull "--name N" out of argv
    if name not in argv:
        return default
    i = argv.index(name)
    if i + 1 >= len(argv) or not argv[i + 1].isdigit():
        sys.stderr.write(USAGE); sys.exit(2)
    v = int(argv[i + 1]); del argv[i:i + 2]
    return v
dport, sport_base, ttl = flag("--dport", 9), flag("--sport-base", 40000), flag("--ttl", 64)
if len(argv) not in (9, 10) or argv[0] not in ("v4", "v6") or (len(argv) == 10 and argv[9] != "fixed") \
        or not all(x.isdigit() for x in argv[5:8]):
    sys.stderr.write(USAGE); sys.exit(2)
from scapy.all import Ether, IP, IPv6, UDP, Raw, wrpcap

fam, smac, dmac, sip, base, first, count, flen, out = argv[0:9]
fixed = len(argv) > 9 and argv[9] == "fixed"             # every frame to <dst_base_ip> itself
first, count, flen = int(first), int(count), int(flen)
b = ipaddress.ip_address(base)
pk = []
for i in range(first, first + count):
    d = str(b) if fixed else str(b + i)
    l3 = IPv6(src=sip, dst=d, hlim=ttl) if fam == "v6" else IP(src=sip, dst=d, ttl=ttl)
    p = Ether(src=smac, dst=dmac) / l3 / UDP(sport=sport_base + (i % 20000), dport=dport)
    pad = flen - len(p)
    pk.append(p / Raw(b"\x5a" * max(pad, 0)))
wrpcap(out, pk)
print("{} frames {}..{} len {} -> {}".format(len(pk), pk[0][1].dst, pk[-1][1].dst, len(pk[0]), out))
