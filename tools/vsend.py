#!/usr/bin/env python3
"""vsend.py <iface> <count> <spec> [--src MAC] [--dst MAC] [--vlan V] [--outer O] [--tag TEXT]
                                   [--sip IP] [--dip IP] [--sport N] [--dport N]
Send <count> frames of one kind out <iface> (run with sudo).  Each payload carries the
marker "CKVLAN-<tag>-<seq>" so a capture can be counted per burst (vcount.py).
spec: ip10   IPv4 192.168.10.1 -> 192.168.10.2 UDP        ip20  IPv4 192.168.20.1 -> 192.168.20.2 UDP
      ipx    EtherType 0x8137 (IPX, Ethernet II)          ipv6  IPv6 2001:db8::1 -> 2001:db8::2 UDP
      other  EtherType 0x88b5 (IEEE local experimental)   arp   ARP request (who-has 192.168.100.9
                                                                from 192.168.100.100)
      ipsrc:A.B.C.D  IPv4 from that source to 192.168.100.9 UDP
The addresses above are each spec's defaults: --sip / --dip replace the source / destination
(for arp: psrc / pdst; ipsrc keeps its source from the spec), so they can match the subnets
configured on the DUT.  UDP is sport 4000 -> dport 4010 (ip10), 4020 (ip20), 4060 (ipv6),
4100 (ipsrc) unless --sport / --dport is given.  --src / --dst default to the documentation
MACs 00:00:5e:00:53:01 / 00:00:5e:00:53:ff.
--vlan adds an 802.1Q tag (inner); --outer adds a second, outer 802.1Q tag (QinQ) around it."""
import sys, time

USAGE = __doc__.split("\n")[0] + "\n" + __doc__.split("\n")[1]
a = sys.argv[1:]
opt = {"--src": "00:00:5e:00:53:01", "--dst": "00:00:5e:00:53:ff", "--vlan": None, "--outer": None,
       "--tag": None, "--sip": None, "--dip": None, "--sport": None, "--dport": None}
SPECS = ("ip10", "ip20", "ipx", "ipv6", "other", "arp")
if len(a) < 3 or len(a) % 2 == 0 or any(a[i] not in opt for i in range(3, len(a), 2)) \
        or not a[1].isdigit() or not (a[2] in SPECS or a[2].startswith("ipsrc:")):
    sys.stderr.write("usage: " + USAGE.strip() + "\n(see the header of vsend.py for the specs)\n")
    sys.exit(2)
iface, count, spec = a[0], int(a[1]), a[2]
opt["--tag"] = spec
for i in range(3, len(a), 2):
    opt[a[i]] = a[i + 1]

from scapy.all import Ether, Dot1Q, IP, IPv6, UDP, ARP, Raw, sendp, conf
conf.verb = 0

def ports(dport):
    return UDP(sport=int(opt["--sport"] or 4000), dport=int(opt["--dport"] or dport))

def one(seq):
    mark = ("CKVLAN-%s-%04d" % (opt["--tag"], seq)).encode().ljust(40, b".")
    sip, dip = opt["--sip"], opt["--dip"]
    e = Ether(src=opt["--src"], dst=opt["--dst"])
    if opt["--outer"]:
        e /= Dot1Q(vlan=int(opt["--outer"]))
    if opt["--vlan"]:
        e /= Dot1Q(vlan=int(opt["--vlan"]))
    if spec == "ip10":
        return e / IP(src=sip or "192.168.10.1", dst=dip or "192.168.10.2") / ports(4010) / Raw(mark)
    if spec == "ip20":
        return e / IP(src=sip or "192.168.20.1", dst=dip or "192.168.20.2") / ports(4020) / Raw(mark)
    if spec.startswith("ipsrc:"):
        return e / IP(src=spec[6:], dst=dip or "192.168.100.9") / ports(4100) / Raw(mark)
    if spec == "ipv6":
        return e / IPv6(src=sip or "2001:db8::1", dst=dip or "2001:db8::2") / ports(4060) / Raw(mark)
    if spec == "ipx":
        e.lastlayer().type = 0x8137
        return e / Raw(b"\xff\xff\x00\x30\x00\x11" + mark)
    if spec == "other":
        e.lastlayer().type = 0x88b5
        return e / Raw(mark)
    if spec == "arp":
        return e / ARP(op=1, hwsrc=opt["--src"], psrc=sip or "192.168.100.100",
                       pdst=dip or "192.168.100.9") / Raw(mark)
    raise SystemExit("unknown spec " + spec)
pk = [one(i) for i in range(count)]
t0 = time.time()
sendp(pk, iface=iface, inter=0.003)
print("%s sent %d x %s src=%s dst=%s vlan=%s outer=%s on %s in %.2fs" % (
    time.strftime("%H:%M:%S"), count, spec, opt["--src"], opt["--dst"], opt["--vlan"], opt["--outer"], iface, time.time() - t0))
