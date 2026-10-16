#!/usr/bin/env python3
"""hostsim.py <iface> <ip[,ip...]> <stats.json> [options]

A fake IPv4 host on one NIC: answers ARP who-has and ICMP echo requests for the
addresses given, from a fake MAC, installing nothing on the host and changing no
host IP, route or interface. The IPv4 counterpart of nsresp.py (which answers IPv6
Neighbor Solicitations).

Why it exists: several cases need a reachable neighbour that the test can make
UNREACHABLE on demand while the link and the switch port stay UP -- ping polling,
a VRRP client, a tracked next hop, an ARP ageing or deauth timeout. Shutting a port
or pulling an address also kills the measuring instrument and changes the thing
under test. Here, touching the --mutefile makes the host stop answering ICMP echo
within one packet, and removing it brings it straight back; ARP keeps being answered
throughout (unless --mute-arp), so the DUT's neighbour entry stays valid and the loss
the DUT sees is a pure echo-reply loss.

Raw AF_PACKET socket, promiscuous, with a kernel BPF filter ("arp or icmp") compiled
by tcpdump, so unrelated data traffic on the same NIC never reaches Python. Stats are
written as JSON every second and at exit. Stops on SIGTERM/SIGINT, when [--stopfile]
appears, or after [--duration] seconds. Run as root.

Options:
  --mac MAC        one MAC for every address (default: a per-address fake
                   02:87:71:<last 3 octets of the IPv4 address>)
  --stopfile F     stop as soon as this path exists
  --mutefile F     while this path exists, do NOT answer ICMP echo (link stays up)
  --mute-at S      go silent S seconds after start, with no file to create
  --unmute-at S    come back S seconds after start (use with --mute-at)
  --mute-ip IPs    only these addresses go silent when muted; the rest keep
                   answering throughout, which is how you keep an instrument
                   control in the same leg as the address you are silencing
  --log-echo F     append one line per ICMP echo request seen:
                   <epoch>\t<dst>\t<src>\t<id>\t<seq>\t<answered|muted>
                   -- this is the wire record a poll-interval measurement reads
  --mute-arp       --mutefile also silences ARP (a host that has truly vanished)
  --duration S     stop after S seconds (default: run until stopped)
  --no-arp         never answer ARP
  --no-icmp        never answer ICMP echo
  --quiet          no progress lines on stderr
"""
import argparse, ctypes, json, os, signal, socket, struct, subprocess, sys, time

ETH_P_ALL, SOL_PACKET, PACKET_ADD_MEMBERSHIP, PACKET_MR_PROMISC = 3, 263, 1, 1
SO_ATTACH_FILTER = 26


def mac2b(m):
    return bytes(int(x, 16) for x in m.replace("-", ":").split(":"))


def b2mac(b):
    return ":".join("%02x" % x for x in b)


def ip2b(a):
    return bytes(int(x) for x in a.split("."))


def b2ip(b):
    return ".".join(str(x) for x in b)


def csum(b):
    if len(b) % 2:
        b += b"\0"
    t = sum(struct.unpack("!%dH" % (len(b) // 2), b))
    while t >> 16:
        t = (t & 0xFFFF) + (t >> 16)
    return (~t) & 0xFFFF


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("iface")
    ap.add_argument("ips")
    ap.add_argument("stats")
    ap.add_argument("--mac", default="")
    ap.add_argument("--stopfile", default="")
    ap.add_argument("--mutefile", default="")
    ap.add_argument("--mute-at", type=float, default=0.0)
    ap.add_argument("--mute-ip", default="")
    ap.add_argument("--log-echo", default="")
    ap.add_argument("--unmute-at", type=float, default=0.0)
    ap.add_argument("--mute-arp", action="store_true")
    ap.add_argument("--duration", type=float, default=0.0)
    ap.add_argument("--no-arp", action="store_true")
    ap.add_argument("--no-icmp", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("-h", "--help", action="store_true")
    a = ap.parse_args()
    if a.help:
        sys.stdout.write(__doc__)
        return 0
    if os.geteuid() != 0:
        sys.stderr.write("hostsim.py must run as root (raw socket)\n")
        return 2

    ips = [x.strip() for x in a.ips.split(",") if x.strip()]
    if not ips:
        sys.stderr.write("no addresses given\n")
        return 2
    try:
        macs = {}
        for ip in ips:
            p = ip2b(ip)
            if len(p) != 4:
                raise ValueError(ip)
            macs[p] = mac2b(a.mac) if a.mac else b"\x02\x87\x71" + p[1:4]
    except Exception as e:                                    # noqa: BLE001
        sys.stderr.write("bad address or MAC: %s\n" % e)
        return 2

    mute_set = set()
    for x in a.mute_ip.split(","):
        x = x.strip()
        if x:
            mute_set.add(ip2b(x))
    if mute_set - set(macs):
        sys.stderr.write("--mute-ip names an address this host does not own\n")
        return 2

    echo_log = open(a.log_echo, "a", buffering=1) if a.log_echo else None

    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8 << 20)
    out = subprocess.check_output(
        ["tcpdump", "-dd", "-i", a.iface, "arp or icmp"]).decode()
    ins = [tuple(int(x, 0) for x in l.strip().strip("{},").split(","))
           for l in out.strip().splitlines()]

    class SF(ctypes.Structure):
        _fields_ = [("code", ctypes.c_uint16), ("jt", ctypes.c_uint8),
                    ("jf", ctypes.c_uint8), ("k", ctypes.c_uint32)]

    class FP(ctypes.Structure):
        _fields_ = [("len", ctypes.c_uint16), ("filter", ctypes.POINTER(SF))]

    arr = (SF * len(ins))(*[SF(*i) for i in ins])
    prog = FP(len(ins), arr)
    s.setsockopt(socket.SOL_SOCKET, SO_ATTACH_FILTER,
                 ctypes.string_at(ctypes.addressof(prog), ctypes.sizeof(prog)))
    s.bind((a.iface, 0))
    idx = socket.if_nametoindex(a.iface)
    s.setsockopt(SOL_PACKET, PACKET_ADD_MEMBERSHIP,
                 struct.pack("iHH8s", idx, PACKET_MR_PROMISC, 0, b""))
    s.settimeout(0.5)

    st = {"iface": a.iface, "addresses": ips,
          "macs": {b2ip(k): b2mac(v) for k, v in macs.items()},
          "arp_seen": 0, "arp_answered": 0, "arp_muted": 0,
          "icmp_seen": 0, "icmp_answered": 0, "icmp_muted": 0,
          "first_icmp": None, "last_icmp": None,
          "first_icmp_muted": None, "last_icmp_muted": None,
          "mute_windows": [], "mute_at": a.mute_at, "unmute_at": a.unmute_at,
          "mute_ip": sorted(b2ip(x) for x in mute_set) or ips,
          "started": time.time(), "stopped": None}
    run = [True]

    def stop(*_):
        run[0] = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    def dump():
        tmp = a.stats + ".tmp"
        with open(tmp, "w") as f:
            json.dump(st, f)
        os.replace(tmp, a.stats)

    last, muted_now, t0 = 0.0, False, time.time()
    while run[0]:
        if a.stopfile and os.path.exists(a.stopfile):
            break
        if a.duration and time.time() - t0 >= a.duration:
            break
        now = time.time()
        m = bool(a.mutefile) and os.path.exists(a.mutefile)
        if a.mute_at:
            el = now - t0
            m = m or (el >= a.mute_at and (not a.unmute_at or el < a.unmute_at))
        if m != muted_now:
            if m:
                st["mute_windows"].append([now, None])
            elif st["mute_windows"]:
                st["mute_windows"][-1][1] = now
            muted_now = m
            if not a.quiet:
                sys.stderr.write("hostsim: %s at %.3f\n"
                                 % ("MUTED" if m else "UNMUTED", now))
                sys.stderr.flush()
        if now - last >= 1.0:
            dump()
            last = now
        try:
            fr, addr = s.recvfrom(2048)
        except socket.timeout:
            continue
        if addr[2] == socket.PACKET_OUTGOING or len(fr) < 42:
            continue
        et = fr[12:14]

        if et == b"\x08\x06" and not a.no_arp:
            if struct.unpack("!H", fr[20:22])[0] != 1:        # not a request
                continue
            sha, spa, tpa = fr[22:28], fr[28:32], fr[38:42]
            if tpa not in macs:
                continue
            st["arp_seen"] += 1
            if m and a.mute_arp:
                st["arp_muted"] += 1
                continue
            our = macs[tpa]
            rep = (sha + our + b"\x08\x06"
                   + b"\x00\x01\x08\x00\x06\x04\x00\x02"
                   + our + tpa + sha + spa)
            s.send(rep + b"\0" * max(0, 60 - len(rep)))
            st["arp_answered"] += 1
            continue

        if et == b"\x08\x00" and not a.no_icmp:
            ihl = (fr[14] & 0x0F) * 4
            if ihl < 20 or fr[23] != 1:
                continue
            dst = fr[30:34]
            if dst not in macs:
                continue
            o = 14 + ihl
            if len(fr) < o + 8 or fr[o] != 8:                 # echo request only
                continue
            st["icmp_seen"] += 1
            st["first_icmp"] = st["first_icmp"] or now
            st["last_icmp"] = now
            src = fr[26:30]
            m_this = m and (not mute_set or dst in mute_set)
            if echo_log:
                echo_log.write("%.6f\t%s\t%s\t%d\t%d\t%s\n"
                               % (now, b2ip(dst), b2ip(src),
                                  struct.unpack("!H", fr[o + 4:o + 6])[0],
                                  struct.unpack("!H", fr[o + 6:o + 8])[0],
                                  "muted" if m_this else "answered"))
            if m_this:
                st["icmp_muted"] += 1
                st["first_icmp_muted"] = st["first_icmp_muted"] or now
                st["last_icmp_muted"] = now
                continue
            our = macs[dst]
            tot = struct.unpack("!H", fr[16:18])[0]
            icmp = bytearray(fr[o:14 + tot])
            icmp[0] = 0                                       # echo reply
            icmp[2:4] = b"\x00\x00"
            icmp[2:4] = struct.pack("!H", csum(bytes(icmp)))
            ip = bytearray(fr[14:o])
            ip[26 - 14:30 - 14] = dst
            ip[30 - 14:34 - 14] = src
            ip[8] = 64                                        # ttl
            ip[10:12] = b"\x00\x00"
            ip[10:12] = struct.pack("!H", csum(bytes(ip)))
            rep = fr[6:12] + our + b"\x08\x00" + bytes(ip) + bytes(icmp)
            s.send(rep + b"\0" * max(0, 60 - len(rep)))
            st["icmp_answered"] += 1

    if st["mute_windows"] and st["mute_windows"][-1][1] is None:
        st["mute_windows"][-1][1] = time.time()
    st["stopped"] = time.time()
    dump()
    if echo_log:
        echo_log.close()
    if not a.quiet:
        sys.stderr.write(
            "hostsim: arp %d/%d answered, icmp %d/%d answered, %d muted\n"
            % (st["arp_answered"], st["arp_seen"],
               st["icmp_answered"], st["icmp_seen"], st["icmp_muted"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
