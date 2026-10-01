#!/usr/bin/env python3
"""vcount.py <pcap> [<pcap> ...] -- count captured frames per (marker burst, VLAN tags, EtherType, dst)
Only frames carrying a CKVLAN marker (vsend.py) are counted (the bench's own LLDP/ARP chatter
is listed separately as 'unmarked')."""
import sys, re, collections
if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
    sys.stderr.write("usage: vcount.py <pcap> [<pcap> ...]\n")
    sys.exit(2)
from scapy.all import rdpcap, Ether, Dot1Q, Raw
for f in sys.argv[1:]:
    try:
        pk = rdpcap(f)
    except Exception as e:
        print("%s: %s" % (f, e)); continue
    c = collections.Counter(); un = collections.Counter()
    for p in pk:
        if not p.haslayer(Ether): continue
        tags = []; l = p[Ether]; t = l.type
        while l.payload and isinstance(l.payload, Dot1Q):
            l = l.payload; tags.append(l.vlan); t = l.type
        raw = bytes(p[Raw].load) if p.haslayer(Raw) else bytes(p.payload)
        m = re.search(rb"CKVLAN-([A-Za-z0-9:._]+)-\d{4}", raw)
        key = (m.group(1).decode() if m else None, "tags=" + (",".join(map(str, tags)) or "none"), "type=0x%04x" % t, "dst=" + p[Ether].dst, "src=" + p[Ether].src)
        (c if m else un)[key] += 1
    print("### %s: %d frames" % (f, len(pk)))
    for k, n in sorted(c.items()):
        print("  %5d  marker=%-10s %-16s %-11s %s %s" % (n, k[0], k[1], k[2], k[3], k[4]))
    for k, n in sorted(un.items()):
        print("  %5d  unmarked         %-16s %-11s %s %s" % (n, k[1], k[2], k[3], k[4]))
