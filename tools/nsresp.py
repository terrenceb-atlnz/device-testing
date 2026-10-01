#!/usr/bin/env python3
"""nsresp.py <iface> <prefix/64> <stats.json> [stopfile]

IPv6 Neighbor Solicitation responder, written for T8770 (the T6057 responder method, IPv6).
Answers every NS whose TARGET is inside <prefix>/64 with a solicited NA (S=1, O=1)
carrying a UNIQUE fake MAC 02:87:70:<low 24 bits of the target>, sent FROM that MAC
so the DUT's FDB learns it on the ingress port. Multicast (solicited-node) and
unicast (NUD probe) NS are both answered; DAD (src ::) is ignored.

Raw AF_PACKET socket, promiscuous (membership only, dies with the socket), with a
kernel BPF filter `icmp6 and ip6[40] == 135` so line-rate data traffic on the same
NIC never reaches Python. Stats are written as JSON every second and at exit:
ns_mcast, ns_ucast, na_sent, distinct targets answered, first/last NS time.
Stops on SIGTERM/SIGINT or when [stopfile] exists. Run as root (sudo -n); needs tcpdump
(only to compile the filter). <stats.json> and [stopfile] are wherever the arguments say."""
import ctypes, ipaddress, json, os, signal, socket, struct, subprocess, sys, time

USAGE = "usage: nsresp.py <iface> <prefix/64> <stats.json> [stopfile]\n"
if len(sys.argv) not in (4, 5):
    sys.stderr.write(USAGE); sys.exit(2)
iface, pfx, statsfn = sys.argv[1], sys.argv[2], sys.argv[3]
stopfile = sys.argv[4] if len(sys.argv) > 4 else None
try:
    net = ipaddress.IPv6Network(pfx)
except ValueError as e:
    sys.stderr.write("%s: %s\n" % (pfx, e) + USAGE); sys.exit(2)
if net.prefixlen != 64:
    sys.stderr.write("%s: the prefix must be a /64\n" % pfx + USAGE); sys.exit(2)
P8 = net.network_address.packed[:8]

ETH_P_ALL, SOL_PACKET, PACKET_ADD_MEMBERSHIP, PACKET_MR_PROMISC = 3, 263, 1, 1
SO_ATTACH_FILTER = 26
s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))
s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8 << 20)

# kernel BPF: compiled by tcpdump -dd, attached before bind so nothing else queues
out = subprocess.check_output(["tcpdump", "-dd", "-i", iface, "icmp6 and ip6[40] == 135"]).decode()
ins = [tuple(int(x, 0) for x in l.strip().strip("{},").split(",")) for l in out.strip().splitlines()]
class SF(ctypes.Structure):
    _fields_ = [("code", ctypes.c_uint16), ("jt", ctypes.c_uint8), ("jf", ctypes.c_uint8), ("k", ctypes.c_uint32)]
class FP(ctypes.Structure):
    _fields_ = [("len", ctypes.c_uint16), ("filter", ctypes.POINTER(SF))]
arr = (SF * len(ins))(*[SF(*i) for i in ins])
prog = FP(len(ins), arr)
s.setsockopt(socket.SOL_SOCKET, SO_ATTACH_FILTER, ctypes.string_at(ctypes.addressof(prog), ctypes.sizeof(prog)))
s.bind((iface, 0))
ifindex = socket.if_nametoindex(iface)
s.setsockopt(SOL_PACKET, PACKET_ADD_MEMBERSHIP, struct.pack("iHH8s", ifindex, PACKET_MR_PROMISC, 0, b""))
s.settimeout(0.5)

def csum(b):
    if len(b) % 2:
        b += b"\0"
    t = sum(struct.unpack("!%dH" % (len(b) // 2), b))
    while t >> 16:
        t = (t & 0xFFFF) + (t >> 16)
    return (~t) & 0xFFFF

st = {"iface": iface, "prefix": pfx, "ns_mcast": 0, "ns_ucast": 0, "na_sent": 0,
      "ignored": 0, "targets": 0, "first_ns": None, "last_ns": None, "started": time.time()}
seen = set()
run = True
def stop(*_):
    global run
    run = False
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)

def dump():
    st["targets"] = len(seen)
    tmp = statsfn + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f)
    os.replace(tmp, statsfn)

last = 0
while run:
    if stopfile and os.path.exists(stopfile):
        break
    now = time.time()
    if now - last >= 1.0:
        dump(); last = now
    try:
        fr, addr = s.recvfrom(2048)
    except socket.timeout:
        continue
    if addr[2] == socket.PACKET_OUTGOING or len(fr) < 78 or fr[12:14] != b"\x86\xdd":
        continue
    src6, tgt = fr[22:38], fr[62:78]
    if fr[54] != 135 or tgt[:8] != P8 or src6 == b"\0" * 16:
        st["ignored"] += 1
        continue
    if fr[0] == 0x33:
        st["ns_mcast"] += 1
    else:
        st["ns_ucast"] += 1
    st["first_ns"] = st["first_ns"] or now
    st["last_ns"] = now
    fake = b"\x02\x87\x70" + tgt[13:16]
    icmp = struct.pack("!BBHI", 136, 0, 0, 0x60000000) + tgt + b"\x02\x01" + fake
    ph = tgt + src6 + struct.pack("!I", len(icmp)) + b"\0\0\0" + bytes([58])
    c = csum(ph + icmp)
    icmp = icmp[:2] + struct.pack("!H", c) + icmp[4:]
    ip6 = struct.pack("!IHBB", 0x60000000, len(icmp), 58, 255) + tgt + src6
    s.send(fr[6:12] + fake + b"\x86\xdd" + ip6 + icmp)
    st["na_sent"] += 1
    seen.add(tgt)
st["stopped"] = time.time()
dump()
