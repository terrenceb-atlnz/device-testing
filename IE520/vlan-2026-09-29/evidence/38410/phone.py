#!/usr/bin/env python3
"""phone.py <iface> <pcap-out> [--mac M] [--lldp-secs N] [--vlan V] [--no-dhcp]
Emulate an LLDP-MED IP phone (Endpoint Class III) on <iface> (run with sudo):
 1. send an LLDP-MED LLDPDU every second for --lldp-secs, and decode every LLDPDU the switch
    sends back (Network Policy TLV = OUI 00-12-BB subtype 2);
 2. DHCP DISCOVER/REQUEST 802.1Q-tagged in the VLAN the switch advertised (or --vlan), PCP 5;
 3. ARP + ICMP echo to the offered router, tagged the same way.
Everything received on <iface> is written to <pcap-out>.  Nothing is configured on the host."""
import sys, time, random, struct
from scapy.all import (Ether, Dot1Q, IP, UDP, BOOTP, DHCP, ARP, ICMP, Raw, sendp, AsyncSniffer,
                       wrpcap, conf)
conf.verb = 0
a = sys.argv[1:]
iface, pcap = a[0], a[1]
opt = {"--mac": "00:00:5e:00:53:10", "--lldp-secs": "8", "--vlan": None}
nodhcp = "--no-dhcp" in a
a = [x for x in a if x != "--no-dhcp"]
for i in range(2, len(a), 2):
    opt[a[i]] = a[i + 1]
MAC = opt["--mac"]; macb = bytes.fromhex(MAC.replace(":", ""))
LLDP_MC = "01:80:c2:00:00:0e"

def tlv(t, v):
    return struct.pack("!H", (t << 9) | len(v)) + v

def lldpdu():
    b = tlv(1, b"\x04" + macb)                       # chassis id, MAC
    b += tlv(2, b"\x03" + macb)                      # port id, MAC
    b += tlv(3, struct.pack("!H", 120))              # TTL
    b += tlv(5, b"ck-phone")                         # system name
    b += tlv(7, struct.pack("!HH", 0x0020, 0x0020))  # system caps: telephone / telephone
    b += tlv(127, b"\x00\x12\xbb\x01" + struct.pack("!H", 0x0033) + b"\x03")  # MED caps, class III
    b += tlv(127, b"\x00\x12\xbb\x05" + b"CK-PHONE-EMU")  # MED inventory: hardware rev (harmless)
    b += tlv(0, b"")
    return Ether(src=MAC, dst=LLDP_MC, type=0x88cc) / Raw(b)

def parse_lldp(raw):
    out = []; i = 0
    while i + 2 <= len(raw):
        h, = struct.unpack("!H", raw[i:i + 2]); t, l = h >> 9, h & 0x1ff
        v = raw[i + 2:i + 2 + l]; i += 2 + l
        if t == 0: break
        if t == 127 and v[:3] == b"\x00\x12\xbb":
            st = v[3]
            if st == 2 and len(v) >= 8:
                app = v[4]; w, = struct.unpack("!I", b"\x00" + v[5:8])
                U, T, vid, pri, dscp = (w >> 23) & 1, (w >> 22) & 1, (w >> 9) & 0xfff, (w >> 6) & 7, w & 0x3f
                out.append(("MED-network-policy", dict(app=app, unknown=U, tagged=T, vlan=vid, l2prio=pri, dscp=dscp)))
            elif st == 1:
                out.append(("MED-capabilities", v[4:].hex()))
            else:
                out.append(("MED-subtype-%d" % st, v[4:].hex()))
        elif t == 5:
            out.append(("system-name", v.decode(errors="replace")))
        elif t == 2:
            out.append(("port-id", v[1:].decode(errors="replace") if v[:1] in (b"\x05", b"\x07", b"\x01") else v.hex()))
        elif t == 127:
            out.append(("org-%s-%d" % (v[:3].hex(), v[3]), v[4:].hex()))
    return out

got = []
sn = AsyncSniffer(iface=iface, store=True, prn=lambda p: got.append(p))
sn.start(); time.sleep(1)
policy = None
t0 = time.time(); n = 0
print("%s phase 1: LLDP-MED from %s on %s for %ss" % (time.strftime("%T"), MAC, iface, opt["--lldp-secs"]))
while time.time() - t0 < float(opt["--lldp-secs"]):
    sendp(lldpdu(), iface=iface); n += 1; time.sleep(1)
time.sleep(1)
print("  sent %d LLDPDUs" % n)
for p in list(got):
    if p.haslayer(Ether) and p[Ether].type == 0x88cc and p[Ether].src.lower() != MAC:
        tl = parse_lldp(bytes(p[Ether].payload))
        print("  %.3f rx LLDPDU from %s: %s" % (p.time, p[Ether].src, tl))
        for k, v in tl:
            if k == "MED-network-policy" and v["app"] == 1:
                policy = v
print("  voice network policy: %s" % policy)
vlan = int(opt["--vlan"]) if opt["--vlan"] else (policy["vlan"] if policy and policy["tagged"] else None)
prio = policy["l2prio"] if policy else 5
if nodhcp or vlan is None:
    sn.stop(); wrpcap(pcap, got); print("no DHCP phase (vlan=%s)" % vlan); sys.exit(0 if policy else 1)

def tagged(pl):
    return Ether(src=MAC, dst="ff:ff:ff:ff:ff:ff") / Dot1Q(vlan=vlan, prio=prio) / pl

def wait(pred, secs):
    t = time.time()
    while time.time() - t < secs:
        for p in list(got):
            if pred(p): return p
        time.sleep(0.2)
    return None

def vlan_of(p):
    return p[Dot1Q].vlan if p.haslayer(Dot1Q) else None

xid = random.randint(1, 0xffffffff)
print("%s phase 2: DHCP in VLAN %d prio %d, xid 0x%08x" % (time.strftime("%T"), vlan, prio, xid))
bo = BOOTP(chaddr=macb + b"\x00" * 10, xid=xid, flags=0x8000)
disc = tagged(IP(src="0.0.0.0", dst="255.255.255.255") / UDP(sport=68, dport=67) / bo /
              DHCP(options=[("message-type", "discover"), ("hostname", "ck-phone"),
                            ("param_req_list", [1, 3, 6, 51, 54]), "end"]))
isreply = lambda mt: (lambda p: p.haslayer(DHCP) and p[BOOTP].xid == xid and p[BOOTP].op == 2 and
                      any(o[0] == "message-type" and o[1] == mt for o in p[DHCP].options if isinstance(o, tuple)))
offer = None
for attempt in range(3):
    sendp(disc, iface=iface)
    offer = wait(isreply(2), 6)
    if offer: break
if not offer:
    sn.stop(); wrpcap(pcap, got); print("  NO OFFER"); sys.exit(2)
opts = {o[0]: o[1] for o in offer[DHCP].options if isinstance(o, tuple)}
yi = offer[BOOTP].yiaddr; sid = opts.get("server_id")
print("  OFFER from %s (%s) vlan=%s: yiaddr=%s server_id=%s router=%s lease=%s" % (
    offer[Ether].src, offer[IP].src, vlan_of(offer), yi, sid, opts.get("router"), opts.get("lease_time")))
req = tagged(IP(src="0.0.0.0", dst="255.255.255.255") / UDP(sport=68, dport=67) / bo /
             DHCP(options=[("message-type", "request"), ("requested_addr", yi), ("server_id", sid),
                           ("hostname", "ck-phone"), ("param_req_list", [1, 3, 6, 51, 54]), "end"]))
sendp(req, iface=iface)
ack = wait(isreply(5), 8)
if not ack:
    sn.stop(); wrpcap(pcap, got); print("  NO ACK"); sys.exit(3)
opts = {o[0]: o[1] for o in ack[DHCP].options if isinstance(o, tuple)}
print("  ACK from %s vlan=%s: yiaddr=%s router=%s lease=%s mask=%s" % (
    ack[Ether].src, vlan_of(ack), ack[BOOTP].yiaddr, opts.get("router"), opts.get("lease_time"), opts.get("subnet_mask")))
ip = ack[BOOTP].yiaddr; gw = opts.get("router")
print("%s phase 3: ARP + ICMP %s -> %s in VLAN %d" % (time.strftime("%T"), ip, gw, vlan))
sendp(tagged(ARP(op=1, hwsrc=MAC, psrc=ip, pdst=gw)), iface=iface)
ar = wait(lambda p: p.haslayer(ARP) and p[ARP].op == 2 and p[ARP].psrc == gw, 5)
print("  ARP reply: %s" % (("%s is-at %s vlan=%s" % (ar[ARP].psrc, ar[ARP].hwsrc, vlan_of(ar))) if ar else None))
if ar:
    for s in range(3):
        sendp(Ether(src=MAC, dst=ar[ARP].hwsrc) / Dot1Q(vlan=vlan, prio=prio) / IP(src=ip, dst=gw) / ICMP(id=0x4b43, seq=s) / Raw(b"CKVOICE"), iface=iface)
        time.sleep(0.3)
    time.sleep(1)
    rep = [p for p in got if p.haslayer(ICMP) and p[ICMP].type == 0 and p[ICMP].id == 0x4b43]
    print("  ICMP echo replies: %d/3, vlan=%s" % (len(rep), sorted({vlan_of(p) for p in rep})))
sn.stop(); wrpcap(pcap, got)
print("%s done, %d frames written to %s" % (time.strftime("%T"), len(got), pcap))
