#!/usr/bin/env python3
"""vsend.py <iface> <count> <spec> [--src MAC] [--dst MAC] [--vlan V] [--outer O] [--tag TEXT]
Send <count> frames of one kind out <iface> (run with sudo).  Each payload carries the
marker "CKVLAN-<tag>-<seq>" so a capture can be counted per burst.
spec: ip10   IPv4 192.168.10.1 -> 192.168.10.2 UDP        ip20  IPv4 192.168.20.1 -> 192.168.20.2 UDP
      ipx    EtherType 0x8137 (IPX, Ethernet II)          ipv6  IPv6 2001:db8::1 -> 2001:db8::2 UDP
      other  EtherType 0x88b5 (IEEE local experimental)   arp   ARP request (who-has 192.168.100.9)
      ipsrc:A.B.C.D  IPv4 from that source to 192.168.100.9 UDP
--vlan adds an 802.1Q tag (inner); --outer adds a second, outer 802.1Q tag (QinQ) around it."""
import sys, time
from scapy.all import Ether, Dot1Q, IP, IPv6, UDP, ARP, Raw, sendp, conf
conf.verb = 0
a = sys.argv[1:]
iface, count, spec = a[0], int(a[1]), a[2]
opt = {"--src": "00:00:5e:00:53:01", "--dst": "00:00:5e:00:53:ff", "--vlan": None, "--outer": None, "--tag": spec}
for i in range(3, len(a), 2):
    opt[a[i]] = a[i + 1]
def one(seq):
    mark = ("CKVLAN-%s-%04d" % (opt["--tag"], seq)).encode().ljust(40, b".")
    e = Ether(src=opt["--src"], dst=opt["--dst"])
    if opt["--outer"]:
        e /= Dot1Q(vlan=int(opt["--outer"]))
    if opt["--vlan"]:
        e /= Dot1Q(vlan=int(opt["--vlan"]))
    if spec == "ip10":
        return e / IP(src="192.168.10.1", dst="192.168.10.2") / UDP(sport=4000, dport=4010) / Raw(mark)
    if spec == "ip20":
        return e / IP(src="192.168.20.1", dst="192.168.20.2") / UDP(sport=4000, dport=4020) / Raw(mark)
    if spec.startswith("ipsrc:"):
        return e / IP(src=spec[6:], dst="192.168.100.9") / UDP(sport=4000, dport=4100) / Raw(mark)
    if spec == "ipv6":
        return e / IPv6(src="2001:db8::1", dst="2001:db8::2") / UDP(sport=4000, dport=4060) / Raw(mark)
    if spec == "ipx":
        e.lastlayer().type = 0x8137
        return e / Raw(b"\xff\xff\x00\x30\x00\x11" + mark)
    if spec == "other":
        e.lastlayer().type = 0x88b5
        return e / Raw(mark)
    if spec == "arp":
        return e / ARP(op=1, hwsrc=opt["--src"], psrc="192.168.100.100", pdst="192.168.100.9") / Raw(mark)
    raise SystemExit("unknown spec " + spec)
pk = [one(i) for i in range(count)]
t0 = time.time()
sendp(pk, iface=iface, inter=0.003)
print("%s sent %d x %s src=%s dst=%s vlan=%s outer=%s on %s in %.2fs" % (
    time.strftime("%H:%M:%S"), count, spec, opt["--src"], opt["--dst"], opt["--vlan"], opt["--outer"], iface, time.time() - t0))
