#!/usr/bin/env python3
"""igmp.py <iface> <join|leave> <group> <src_ip> <src_mac> [count] [interval_s]

Send IGMPv2 Membership Reports (join) or Leave Group messages (leave) from a
FAKE receiver host on <iface>, with scapy (run with sudo).  IP.src is a real
on-subnet address (an AW+ DUT's IGMP source-address check drops 0.0.0.0, seen on
IE520); igmpize() adds router-alert + TTL 1 and the checksum.  count defaults to 2,
interval_s to 0.5.  The receiver is a fake MAC so the host's own IP stack (which may
forward IP between its NICs) never answers as, or for, the receiver."""
import sys, time
if not 6 <= len(sys.argv) <= 8 or sys.argv[2] not in ("join", "leave"):
    sys.stderr.write("usage: igmp.py <iface> <join|leave> <group> <src_ip> <src_mac> [count] [interval_s]\n")
    sys.exit(2)
from scapy.all import Ether, IP, sendp
from scapy.contrib.igmp import IGMP

iface, what, grp, sip, smac = sys.argv[1:6]
count = int(sys.argv[6]) if len(sys.argv) > 6 else 2
gap = float(sys.argv[7]) if len(sys.argv) > 7 else 0.5
if what == "join":
    dst, typ = grp, 0x16
else:
    dst, typ = "224.0.0.2", 0x17
g = [int(x) for x in dst.split(".")]
dmac = "01:00:5e:%02x:%02x:%02x" % (g[1] & 0x7f, g[2], g[3])
p = Ether(src=smac, dst=dmac) / IP(src=sip, dst=dst) / IGMP(type=typ, gaddr=grp)
p[IGMP].igmpize()
for i in range(count):
    sendp(p, iface=iface, verbose=False)
    if i + 1 < count:
        time.sleep(gap)
print("%s %s %s x%d from %s/%s on %s" % (time.strftime("%T"), what, grp, count, sip, smac, iface))
