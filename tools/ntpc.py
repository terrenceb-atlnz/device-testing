#!/usr/bin/env python3
"""Crafted NTP client: send mode-3 (or any mode) NTP packets and decode the replies.

Why it exists
-------------
An NTP case is a traffic case (STANDING-ORDERS §7). `show ntp associations` on the device
under test will happily list a peer that no packet ever reached, and on this platform
`show ntp status` / `show ntp counters` can print COMPLETELY EMPTY output, which looks
identical to a hung command. The verdict therefore has to come from the exchange itself:
the exact request this tool sent, and the exact reply that came back, field by field.

It is deliberately a plain UDP socket and not scapy:
  * it needs no root, so it runs anywhere a case runs;
  * on a box whose own ntpd owns UDP/123 a raw responder would race the kernel, while an
    ordinary client socket just talks to the device under test;
  * the request is still built byte by byte here, so it IS a crafted frame -- the version,
    mode, stratum, poll, precision and transmit timestamp are all arguments.

It proves a reply is a reply to US: the server echoes our transmit timestamp in the reply's
origin field, and `origin_echo=yes/no` is printed for every packet. A device (or a middlebox)
answering with something that does not echo it is reported, not counted as a match.

Exit codes
----------
  0  at least one reply decoded
  2  no reply at all -- a LEGITIMATE result for a control leg (server disabled, restricted,
     unreachable), not only an error
  3  usage / resolution error
"""

import argparse
import json
import os
import random
import socket
import struct
import sys
import time

NTP_EPOCH = 2208988800          # seconds between 1900-01-01 and 1970-01-01
PKT = 48                        # an NTP packet without extensions / MAC

LI_TEXT = {0: "no-warning", 1: "last-minute-61", 2: "last-minute-59", 3: "UNSYNCHRONIZED"}
MODE_TEXT = {0: "reserved", 1: "symmetric-active", 2: "symmetric-passive", 3: "client",
             4: "server", 5: "broadcast", 6: "control", 7: "private"}


def to_ntp(t):
    """UNIX float -> (seconds, fraction) in NTP era 0."""
    s = int(t) + NTP_EPOCH
    f = int((t - int(t)) * (1 << 32)) & 0xFFFFFFFF
    return s & 0xFFFFFFFF, f


def from_ntp(s, f):
    """(seconds, fraction) -> UNIX float; 0/0 means 'not set' and comes back as None."""
    if s == 0 and f == 0:
        return None
    return (s - NTP_EPOCH) + f / float(1 << 32)


def fixed16(v):
    """32-bit 16.16 fixed point -> float seconds."""
    return v / 65536.0


def refid_text(stratum, raw):
    """Stratum 0/1 use a 4-character ASCII code; stratum >= 2 use an IPv4 address (or, for
    IPv6 associations, the first 4 bytes of a hash -- which is why it is printed both ways."""
    ascii_ = "".join(chr(b) if 32 <= b < 127 else "." for b in raw)
    dotted = ".".join(str(b) for b in raw)
    if stratum in (0, 1):
        return "%s (%s)" % (ascii_.rstrip("\0. "), dotted)
    return "%s (ascii %r)" % (dotted, ascii_)


def build(version, mode, stratum, poll, precision, xmit_unix):
    b = bytearray(PKT)
    b[0] = ((0 & 0x3) << 6) | ((version & 0x7) << 3) | (mode & 0x7)
    b[1] = stratum & 0xFF
    b[2] = poll & 0xFF
    b[3] = precision & 0xFF
    s, f = to_ntp(xmit_unix)
    struct.pack_into(">II", b, 40, s, f)
    return bytes(b)


def decode(buf):
    if len(buf) < PKT:
        return None
    li = (buf[0] >> 6) & 0x3
    vn = (buf[0] >> 3) & 0x7
    mode = buf[0] & 0x7
    stratum = buf[1]
    poll = struct.unpack(">b", buf[2:3])[0]
    prec = struct.unpack(">b", buf[3:4])[0]
    rdel, rdis = struct.unpack(">II", buf[4:12])
    rid = buf[12:16]
    ref_s, ref_f, org_s, org_f, rec_s, rec_f, xmt_s, xmt_f = struct.unpack(">8I", buf[16:48])
    return {
        "li": li, "li_text": LI_TEXT.get(li, str(li)),
        "version": vn, "mode": mode, "mode_text": MODE_TEXT.get(mode, str(mode)),
        "stratum": stratum, "poll": poll, "precision": prec,
        "root_delay": fixed16(rdel), "root_dispersion": fixed16(rdis),
        "refid_raw": list(rid), "refid": refid_text(stratum, rid),
        "reference": from_ntp(ref_s, ref_f), "origin": from_ntp(org_s, org_f),
        "receive": from_ntp(rec_s, rec_f), "transmit": from_ntp(xmt_s, xmt_f),
        "origin_words": (org_s, org_f), "extra_bytes": len(buf) - PKT,
    }


def stamp(t):
    if t is None:
        return "-"
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t)) + ("%.6f" % (t % 1))[1:] + "Z"


def one(sock, dest, args, seq, out):
    xmit = time.time()
    pkt = build(args.version, args.mode, args.req_stratum, args.poll, args.precision, xmit)
    want = struct.unpack(">II", pkt[40:48])
    t1 = time.time()
    try:
        sock.sendto(pkt, dest)
    except OSError as e:
        print("  #%d SEND FAILED: %s" % (seq, e))
        return {"seq": seq, "sent": True, "error": str(e)}
    rec = {"seq": seq, "sent": True, "sent_at": t1, "sent_at_utc": stamp(t1), "reply": None}
    deadline = t1 + args.timeout
    while True:
        left = deadline - time.time()
        if left <= 0:
            print("  #%d sent %s -> NO REPLY within %.1f s" % (seq, stamp(t1), args.timeout))
            return rec
        sock.settimeout(left)
        try:
            buf, src = sock.recvfrom(2048)
        except socket.timeout:
            continue
        except OSError as e:
            print("  #%d recv failed: %s" % (seq, e))
            return rec
        t4 = time.time()
        d = decode(buf)
        if d is None:
            print("  #%d short packet (%d bytes) from %s" % (seq, len(buf), src[0]))
            continue
        d["origin_echo"] = (d["origin_words"] == want)
        d["from"] = src[0]
        d["from_port"] = src[1]
        d["bytes"] = len(buf)
        d["recv_at"] = t4
        t2, t3 = d["receive"], d["transmit"]
        if t2 is not None and t3 is not None:
            d["delay"] = (t4 - t1) - (t3 - t2)
            d["offset"] = ((t2 - t1) + (t3 - t4)) / 2.0
        else:
            d["delay"] = d["offset"] = None
        rec["reply"] = d
        print("  #%d sent %s  reply %d B from %s:%d" % (seq, stamp(t1), d["bytes"],
                                                        d["from"], d["from_port"]))
        print("      LI=%d(%s) VN=%d mode=%d(%s) stratum=%d poll=%d precision=%d"
              % (d["li"], d["li_text"], d["version"], d["mode"], d["mode_text"],
                 d["stratum"], d["poll"], d["precision"]))
        print("      refid=%s  root_delay=%.6fs root_dispersion=%.6fs"
              % (d["refid"], d["root_delay"], d["root_dispersion"]))
        print("      reference=%s" % stamp(d["reference"]))
        print("      origin   =%s  origin_echo=%s" % (stamp(d["origin"]),
                                                      "yes" if d["origin_echo"] else "NO"))
        print("      receive  =%s" % stamp(d["receive"]))
        print("      transmit =%s" % stamp(d["transmit"]))
        if d["offset"] is not None:
            print("      offset=%+.6f s  delay=%.6f s   (server clock minus ours)"
                  % (d["offset"], d["delay"]))
        if d["stratum"] == 0:
            print("      !! stratum 0 = KISS-O'-DEATH, code %s" % d["refid"])
        if d["li"] == 3:
            print("      !! LI=3: the server says it is NOT SYNCHRONISED")
        if not d["origin_echo"]:
            print("      !! the origin timestamp does NOT echo our transmit timestamp --"
                  " this reply is not an answer to this request")
        return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("server", help="the NTP server to query: IPv4 address, IPv6 address or name")
    ap.add_argument("--port", type=int, default=123)
    ap.add_argument("--count", type=int, default=1, help="packets to send (default 1)")
    ap.add_argument("--gap", type=float, default=1.0, help="seconds between packets")
    ap.add_argument("--timeout", type=float, default=3.0, help="seconds to wait per reply")
    ap.add_argument("--version", type=int, default=4, choices=[1, 2, 3, 4],
                    help="NTP version in the request (default 4)")
    ap.add_argument("--mode", type=int, default=3, choices=list(range(8)),
                    help="mode in the request: 3 client (default), 1 symmetric-active, ...")
    ap.add_argument("--req-stratum", type=int, default=0, help="stratum field of the request")
    ap.add_argument("--poll", type=int, default=4, help="poll field of the request")
    ap.add_argument("--precision", type=int, default=-6, help="precision field of the request")
    ap.add_argument("--bind", help="source address to bind (picks the NIC the request leaves by)")
    ap.add_argument("--bind-port", type=int, default=0, help="source port (default: ephemeral)")
    ap.add_argument("-6", "--ipv6", action="store_true", help="force IPv6")
    ap.add_argument("-4", "--ipv4", action="store_true", help="force IPv4")
    ap.add_argument("--json", help="write the whole result to this file as JSON")
    args = ap.parse_args()

    family = socket.AF_UNSPEC
    if args.ipv6:
        family = socket.AF_INET6
    if args.ipv4:
        family = socket.AF_INET
    try:
        info = socket.getaddrinfo(args.server, args.port, family, socket.SOCK_DGRAM)
    except socket.gaierror as e:
        print("cannot resolve %r: %s" % (args.server, e))
        return 3
    family, _, _, _, dest = info[0]

    sock = socket.socket(family, socket.SOCK_DGRAM)
    if args.bind or args.bind_port:
        try:
            bi = socket.getaddrinfo(args.bind or ("::" if family == socket.AF_INET6 else "0.0.0.0"),
                                    args.bind_port, family, socket.SOCK_DGRAM)[0][4]
            sock.bind(bi)
        except OSError as e:
            print("cannot bind to %s:%s -- %s" % (args.bind, args.bind_port, e))
            return 3
    local = sock.getsockname()

    fam = "IPv6" if family == socket.AF_INET6 else "IPv4"
    print("ntpc: %s  %s:%d -> %s:%d   version=%d mode=%d count=%d gap=%.1fs timeout=%.1fs"
          % (fam, local[0], local[1], dest[0], dest[1], args.version, args.mode,
             args.count, args.gap, args.timeout))
    print("      request transmit timestamps are this host's clock, UTC")

    results = []
    for i in range(1, args.count + 1):
        results.append(one(sock, dest, args, i, sys.stdout))
        if i < args.count:
            time.sleep(args.gap)
    sock.close()

    replies = [r for r in results if r.get("reply")]
    echoed = [r for r in replies if r["reply"].get("origin_echo")]
    print("")
    print("SUMMARY: sent=%d replies=%d origin_echo=%d no_reply=%d"
          % (len(results), len(replies), len(echoed), len(results) - len(replies)))
    if replies:
        strata = sorted(set(r["reply"]["stratum"] for r in replies))
        modes = sorted(set(r["reply"]["mode"] for r in replies))
        print("         reply stratum(s)=%s mode(s)=%s"
              % (",".join(str(s) for s in strata), ",".join(str(m) for m in modes)))
        offs = [r["reply"]["offset"] for r in replies if r["reply"]["offset"] is not None]
        if offs:
            print("         offset min=%+.6f max=%+.6f mean=%+.6f s"
                  % (min(offs), max(offs), sum(offs) / len(offs)))
    if args.json:
        with open(args.json, "w") as f:
            json.dump({"server": args.server, "port": args.port, "family": fam,
                       "local": list(local[:2]), "results": results}, f, indent=1, default=str)
        print("         JSON -> %s" % args.json)
    return 0 if replies else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(3)
