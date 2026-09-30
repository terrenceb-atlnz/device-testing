#!/usr/bin/env python3
"""rs.py <iface> <count>: send ICMPv6 Router Solicitations (to ff02::2) out <iface>, 2 s apart."""
import sys, time
from scapy.all import Ether, IPv6, ICMPv6ND_RS, ICMPv6NDOptSrcLLAddr, sendp, get_if_hwaddr
from scapy.arch import in6_getifaddr
iface, n = sys.argv[1], int(sys.argv[2])
mac = get_if_hwaddr(iface)
ll = [a[0] for a in in6_getifaddr() if a[2] == iface and a[0].startswith("fe80")][0]
p = Ether(src=mac, dst="33:33:00:00:00:02")/IPv6(src=ll, dst="ff02::2", hlim=255)/ICMPv6ND_RS()/ICMPv6NDOptSrcLLAddr(lladdr=mac)
for i in range(n):
    sendp(p, iface=iface, verbose=0); print(time.strftime("%H:%M:%S"), "RS sent", ll, "->ff02::2"); time.sleep(2)
