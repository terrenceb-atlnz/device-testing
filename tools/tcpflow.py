#!/usr/bin/env python3
"""tcpflow.py -- summarise the TCP conversations in a `tcpdump -w` pcap, in pure Python.

The decoders beside this one (snmpwire, radwire, sflowwire, opt82dump) each know one
application protocol.  This one knows only TCP, which is what a case needs when the question
is "did a session to this port actually happen, or was it refused?":

  * one row per flow, with the TCP flags seen in each direction;
  * the handshake verdict per flow -- ESTABLISHED, REFUSED (SYN answered by RST),
    NO-ANSWER (SYN with nothing back), or RESET/CLOSED after data;
  * payload byte counts, and with --ascii the printable payload, which for a cleartext
    protocol such as telnet is the login banner itself.

A connection that was refused and a connection that was never attempted look identical in a
`show` command and completely different here, so this is the instrument for an
on/off/removed arc (STANDING-ORDERS §7: a control that must NOT produce the thing).

No scapy: it reads the pcap file format directly, so it runs anywhere Python does.

Usage:
  tcpflow.py <file.pcap> [--port N] [--ascii] [--max-bytes N] [--quiet]

Exit: 0 if at least one flow matched, 1 if none did, 2 on a usage or format error.
"""

import argparse
import struct
import sys

LINKTYPE_ETHERNET = 1
LINKTYPE_LINUX_SLL = 113
LINKTYPE_RAW = 101
LINKTYPE_LINUX_SLL2 = 276

FLAG_NAMES = [(0x01, "FIN"), (0x02, "SYN"), (0x04, "RST"),
              (0x08, "PSH"), (0x10, "ACK"), (0x20, "URG")]


def flags_str(flags):
    on = [n for bit, n in FLAG_NAMES if flags & bit]
    return ".".join(on) if on else "-"


def read_pcap(path):
    """Yield (ts_float, linktype, bytes) for each packet.  Handles pcap and pcapng."""
    with open(path, "rb") as fh:
        head = fh.read(4)
        fh.seek(0)
        if head == b"\x0a\x0d\x0d\x0a":
            for rec in _read_pcapng(fh):
                yield rec
        else:
            for rec in _read_pcap_classic(fh):
                yield rec


def _read_pcap_classic(fh):
    hdr = fh.read(24)
    if len(hdr) < 24:
        raise ValueError("short pcap header")
    magic = hdr[:4]
    if magic in (b"\xd4\xc3\xb2\xa1", b"\x4d\x3c\xb2\xa1"):
        endian = "<"
    elif magic in (b"\xa1\xb2\xc3\xd4", b"\xa1\xb2\x3c\x4d"):
        endian = ">"
    else:
        raise ValueError("not a pcap file (magic %r)" % magic)
    nano = magic in (b"\x4d\x3c\xb2\xa1", b"\xa1\xb2\x3c\x4d")
    linktype = struct.unpack(endian + "I", hdr[20:24])[0]
    while True:
        ph = fh.read(16)
        if len(ph) < 16:
            return
        ts_sec, ts_sub, caplen, _wirelen = struct.unpack(endian + "IIII", ph)
        data = fh.read(caplen)
        if len(data) < caplen:
            return
        ts = ts_sec + (ts_sub / 1e9 if nano else ts_sub / 1e6)
        yield ts, linktype, data


def _read_pcapng(fh):
    endian = "<"
    linktype = LINKTYPE_ETHERNET
    tsresol = 1e6
    while True:
        bh = fh.read(8)
        if len(bh) < 8:
            return
        btype = struct.unpack(endian + "I", bh[:4])[0]
        if btype == 0x0A0D0D0A:
            bom = fh.read(4)
            endian = "<" if bom == b"\x4d\x3c\x2b\x1a" else ">"
            blen = struct.unpack(endian + "I", bh[4:8])[0]
            fh.read(blen - 16)
            continue
        blen = struct.unpack(endian + "I", bh[4:8])[0]
        body = fh.read(blen - 12)
        fh.read(4)
        if btype == 1 and len(body) >= 4:            # Interface Description
            linktype = struct.unpack(endian + "H", body[:2])[0]
        elif btype == 6 and len(body) >= 20:         # Enhanced Packet
            _iface, th, tl, caplen, _wire = struct.unpack(endian + "IIIII", body[:20])
            ts = ((th << 32) | tl) / tsresol
            yield ts, linktype, body[20:20 + caplen]


def strip_link(linktype, data):
    """Return (ethertype, payload) or (None, None)."""
    if linktype == LINKTYPE_ETHERNET:
        if len(data) < 14:
            return None, None
        et = struct.unpack("!H", data[12:14])[0]
        off = 14
        while et in (0x8100, 0x88a8) and len(data) >= off + 4:
            et = struct.unpack("!H", data[off + 2:off + 4])[0]
            off += 4
        return et, data[off:]
    if linktype == LINKTYPE_LINUX_SLL:
        if len(data) < 16:
            return None, None
        return struct.unpack("!H", data[14:16])[0], data[16:]
    if linktype == LINKTYPE_LINUX_SLL2:
        if len(data) < 20:
            return None, None
        return struct.unpack("!H", data[0:2])[0], data[20:]
    if linktype == LINKTYPE_RAW:
        return (0x0800 if data and (data[0] >> 4) == 4 else 0x86dd), data
    return None, None


def ip_str(b):
    return ".".join(str(x) for x in b)


def parse_tcp(linktype, data):
    et, payload = strip_link(linktype, data)
    if et != 0x0800 or payload is None or len(payload) < 20:
        return None
    ihl = (payload[0] & 0x0F) * 4
    if payload[9] != 6 or len(payload) < ihl + 20:
        return None
    total = struct.unpack("!H", payload[2:4])[0]
    src, dst = ip_str(payload[12:16]), ip_str(payload[16:20])
    tcp = payload[ihl:total] if total >= ihl + 20 and total <= len(payload) else payload[ihl:]
    if len(tcp) < 20:
        return None
    sport, dport = struct.unpack("!HH", tcp[0:4])
    doff = (tcp[12] >> 4) * 4
    flags = tcp[13]
    body = tcp[doff:] if len(tcp) > doff else b""
    return src, sport, dst, dport, flags, body


def printable(data, limit):
    out = []
    n = 0
    for b in data:
        if n >= limit:
            out.append("\n   ... truncated at %d bytes" % limit)
            break
        if b in (10, 13) or 32 <= b < 127:
            out.append(chr(b))
        elif b == 9:
            out.append("\t")
        else:
            out.append(".")
        n += 1
    return "".join(out)


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("pcap")
    ap.add_argument("--port", type=int, default=None,
                    help="only flows with this port on either end")
    ap.add_argument("--ascii", action="store_true",
                    help="print the printable payload per direction")
    ap.add_argument("--max-bytes", type=int, default=4000)
    ap.add_argument("--quiet", action="store_true", help="only the summary rows")
    args = ap.parse_args()

    flows = {}
    order = []
    total = 0
    try:
        for ts, linktype, data in read_pcap(args.pcap):
            total += 1
            got = parse_tcp(linktype, data)
            if not got:
                continue
            src, sport, dst, dport, flags, body = got
            if args.port is not None and args.port not in (sport, dport):
                continue
            a, b = (src, sport), (dst, dport)
            key = (a, b) if a <= b else (b, a)
            f = flows.get(key)
            if f is None:
                # the side that sent the first SYN (no ACK) is the client
                client = a if (flags & 0x02 and not flags & 0x10) else None
                f = flows[key] = {"first": ts, "last": ts, "client": client,
                                  "dirs": {}, "pkts": 0}
                order.append(key)
            if f["client"] is None and (flags & 0x02 and not flags & 0x10):
                f["client"] = a
            d = f["dirs"].setdefault((a, b), {"flags": set(), "pkts": 0,
                                              "bytes": 0, "data": bytearray()})
            d["flags"].add(flags)
            d["pkts"] += 1
            d["bytes"] += len(body)
            if args.ascii and len(d["data"]) < args.max_bytes:
                d["data"].extend(body)
            f["pkts"] += 1
            f["last"] = ts
    except (OSError, ValueError, struct.error) as exc:
        print("tcpflow: cannot read %s: %s" % (args.pcap, exc))
        return 2

    print("file %s: %d packet(s) total, %d TCP flow(s)%s"
          % (args.pcap, total, len(flows),
             "" if args.port is None else " on port %d" % args.port))
    if not flows:
        return 1

    for key in order:
        f = flows[key]
        client = f["client"]
        dirs = sorted(f["dirs"].items(),
                      key=lambda kv: 0 if (client and kv[0][0] == client) else 1)
        allf = set()
        for _, d in dirs:
            allf |= d["flags"]
        syn = any(fl & 0x02 and not fl & 0x10 for fl in
                  (f["dirs"].get((client, key[1] if key[0] == client else key[0]),
                                 {"flags": set()})["flags"] if client else set()))
        anyrst = any(fl & 0x04 for fl in allf)
        anysynack = any((fl & 0x02) and (fl & 0x10) for fl in allf)
        anydata = any(d["bytes"] for _, d in dirs)
        if anysynack and anydata:
            verdict = "ESTABLISHED+DATA"
        elif anysynack:
            verdict = "ESTABLISHED"
        elif anyrst:
            verdict = "REFUSED (SYN answered by RST)"
        elif syn or any(fl & 0x02 for fl in allf):
            verdict = "NO-ANSWER (SYN, nothing back)"
        else:
            verdict = "PARTIAL (no handshake in capture)"
        if anysynack and anyrst:
            verdict += " then RST"
        (a, b) = key
        print("")
        print("flow %s:%d <-> %s:%d  packets=%d  duration=%.3fs  => %s"
              % (a[0], a[1], b[0], b[1], f["pkts"], f["last"] - f["first"], verdict))
        for (s, d2), d in dirs:
            print("   %s:%d -> %s:%d  pkts=%d  payload=%d B  flags={%s}"
                  % (s[0], s[1], d2[0], d2[1], d["pkts"], d["bytes"],
                     ", ".join(sorted(flags_str(x) for x in d["flags"]))))
        if args.ascii and not args.quiet:
            for (s, d2), d in dirs:
                if d["data"]:
                    print("   --- payload %s:%d -> %s:%d (%d B shown) ---"
                          % (s[0], s[1], d2[0], d2[1], len(d["data"])))
                    print(printable(bytes(d["data"]), args.max_bytes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
