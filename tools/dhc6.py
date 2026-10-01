#!/usr/bin/env python3
"""dhc6.py <iface> <tag> [--tries N] [--wait S] [--duid-seed X] [--iaid N] [--pcap FILE]

A minimal DHCPv6 client, written for T5093 (DHCPv6 Relay basic), run as root on the
testbox because it uses raw sockets. It sends SOLICIT to ff02::1:2 from the interface's
link-local address. The SOLICIT carries IA_NA (IAID --iaid, default 0x5093), a DUID-LL
built from the interface MAC and an optional seed, Elapsed Time and ORO(DNS). It then waits up to --wait seconds for an ADVERTISE, trying
up to --tries SOLICITs in all. When an ADVERTISE arrives it sends a REQUEST for the
advertised address and waits for the REPLY.

It installs NOTHING on the host: no address, no route. The leased address is printed and
checked against the server's reply only. Every DHCPv6 packet seen on the interface (both
directions, UDP 546/547) goes to --pcap. Exit status: 0 = REPLY with an address,
1 = no ADVERTISE, 2 = ADVERTISE but no usable REPLY.
"""
import sys, time, argparse, binascii

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("iface"); ap.add_argument("tag", help="label printed on every line")
ap.add_argument("--tries", type=int, default=3)
ap.add_argument("--wait", type=float, default=4.0)
ap.add_argument("--duid-seed", default="", help="hex byte XORed into the DUID MAC (a second client)")
ap.add_argument("--iaid", type=lambda x: int(x, 0), default=0x5093, help="IA_NA IAID (default 0x5093)")
ap.add_argument("--pcap", default=None, help="write every DHCPv6 packet seen here (default: none)")
a = ap.parse_args()

from scapy.all import (Ether, IPv6, UDP, sendp, get_if_hwaddr, AsyncSniffer, wrpcap)
from scapy.layers.dhcp6 import (DHCP6_Solicit, DHCP6_Advertise, DHCP6_Request, DHCP6_Reply,
                                DHCP6OptClientId, DHCP6OptServerId, DHCP6OptIA_NA,
                                DHCP6OptIAAddress, DHCP6OptElapsedTime, DHCP6OptOptReq,
                                DHCP6OptStatusCode, DUID_LL)
from scapy.arch import in6_getifaddr

def ts(): return time.strftime("%H:%M:%S") + ".%03d" % (int(time.time() * 1000) % 1000)
mac = get_if_hwaddr(a.iface)
ll = [x[0] for x in in6_getifaddr() if x[2] == a.iface and x[0].startswith("fe80")][0]
lladdr = mac
if a.duid_seed:                       # a different client identity on the same NIC
    b = bytearray(binascii.unhexlify(mac.replace(":", "")))
    b[5] ^= int(a.duid_seed, 16) & 0xff
    lladdr = ":".join("%02x" % x for x in b)
duid = DUID_LL(lladdr=lladdr)
iaid = a.iaid
FLT = "udp and (port 546 or port 547)"
seen = []
sn = AsyncSniffer(iface=a.iface, filter=FLT, store=False, prn=lambda p: seen.append(p))
sn.start(); time.sleep(0.8)

def base(dst="ff02::1:2", dmac="33:33:00:01:00:02"):
    return Ether(src=mac, dst=dmac) / IPv6(src=ll, dst=dst, hlim=1 if dst.startswith("ff02") else 64) / UDP(sport=546, dport=547)

def wait_for(cls, xid, t):
    t0 = time.time()
    while time.time() - t0 < t:
        for p in list(seen):
            if p.haslayer(cls) and p[cls].trid == xid and p[UDP].dport == 546:
                return p
        time.sleep(0.1)
    return None

def addrs(p):
    out = []
    ia = p.getlayer(DHCP6OptIA_NA)
    if ia is None: return out
    for o in ia.ianaopts:
        if isinstance(o, DHCP6OptIAAddress):
            out.append((o.addr, o.preflft, o.validlft))
    return out

def status(p):
    s = p.getlayer(DHCP6OptStatusCode)
    return None if s is None else (s.statuscode, s.statusmsg)

print(ts(), "[%s] iface %s mac %s ll %s duid-ll %s iaid 0x%x" % (a.tag, a.iface, mac, ll, lladdr, iaid))
t_start = time.time()
adv = None
for i in range(a.tries):
    xid = (0x509300 + i + int(time.time()) % 256 * 16) & 0xffffff
    sol = base() / DHCP6_Solicit(trid=xid) / DHCP6OptClientId(duid=duid) / \
        DHCP6OptElapsedTime(elapsedtime=int((time.time() - t_start) * 100)) / \
        DHCP6OptOptReq(reqopts=[23]) / DHCP6OptIA_NA(iaid=iaid, T1=0, T2=0)
    sendp(sol, iface=a.iface, verbose=0)
    print(ts(), "[%s] SOLICIT %d/%d xid 0x%06x %s -> ff02::1:2" % (a.tag, i + 1, a.tries, xid, ll))
    adv = wait_for(DHCP6_Advertise, xid, a.wait)
    if adv is not None:
        break
    print(ts(), "[%s]   no ADVERTISE within %.1f s" % (a.tag, a.wait))

rc = 1
if adv is not None:
    sid = adv.getlayer(DHCP6OptServerId)
    print(ts(), "[%s] ADVERTISE xid 0x%06x from %s (%s) server-duid %s addrs %s status %s" % (
        a.tag, adv[DHCP6_Advertise].trid, adv[IPv6].src, adv[Ether].src,
        bytes(sid.duid).hex() if sid else None, addrs(adv), status(adv)))
    rc = 2
    offered = addrs(adv)
    if sid is not None and offered:
        xid = (xid + 1) & 0xffffff
        ianaopts = [DHCP6OptIAAddress(addr=x[0], preflft=0, validlft=0) for x in offered]
        req = base() / DHCP6_Request(trid=xid) / DHCP6OptClientId(duid=duid) / \
            DHCP6OptServerId(duid=sid.duid) / \
            DHCP6OptElapsedTime(elapsedtime=int((time.time() - t_start) * 100)) / \
            DHCP6OptOptReq(reqopts=[23]) / DHCP6OptIA_NA(iaid=iaid, T1=0, T2=0, ianaopts=ianaopts)
        sendp(req, iface=a.iface, verbose=0)
        print(ts(), "[%s] REQUEST xid 0x%06x for %s" % (a.tag, xid, [x[0] for x in offered]))
        rep = wait_for(DHCP6_Reply, xid, a.wait * 2)
        if rep is None:
            print(ts(), "[%s]   no REPLY within %.1f s" % (a.tag, a.wait * 2))
        else:
            got = addrs(rep)
            print(ts(), "[%s] REPLY xid 0x%06x from %s (%s) addrs %s status %s" % (
                a.tag, rep[DHCP6_Reply].trid, rep[IPv6].src, rep[Ether].src, got, status(rep)))
            if got and got[0][2] > 0:
                print(ts(), "[%s] LEASE %s preferred %s valid %s" % (a.tag, got[0][0], got[0][1], got[0][2]))
                rc = 0
time.sleep(0.5)
sn.stop(); res = list(seen)
for p in res:
    d = "OUT" if p[Ether].src == mac else "IN "
    print("   pcap %s %s %s -> %s %s" % (d, time.strftime("%H:%M:%S", time.localtime(float(p.time))),
                                        p[IPv6].src, p[IPv6].dst, p.lastlayer().summary() if False else p[UDP].payload.name))
if a.pcap:
    wrpcap(a.pcap, res)
    print(ts(), "[%s] %d packets -> %s" % (a.tag, len(res), a.pcap))
print(ts(), "[%s] RESULT rc=%d (%s)" % (a.tag, rc, {0: "LEASED", 1: "NO ADVERTISE", 2: "ADVERTISE, NO LEASE"}[rc]))
sys.exit(rc)
