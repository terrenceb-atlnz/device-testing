#!/usr/bin/env python3
"""Decode and COUNT the NTP packets in a `tcpdump -w` pcap -- IPv4 and IPv6.

Why it exists
-------------
NTP is UDP, and on this platform `show ntp status` and `show ntp counters` can print
COMPLETELY EMPTY output while `show ntp associations` lists a peer that no packet ever
reached. "The device is an NTP server" and "the device is an NTP client" are therefore
claims about the wire, and this is the instrument that reads it (STANDING-ORDERS §7).

It is the counting half of an NTP case's evidence: `ntpc.py` is one end of the exchange,
tcpdump plus this tool is the independent witness of what was actually on the link --
including packets neither end reported, such as a client's requests going out to a server
that never answers.

What it prints
--------------
one line per packet (direction, mode, stratum, LI, refid and the transmit timestamp), then
a summary: totals by mode, by source/destination pair, and a request/reply pairing that
matches each server reply to the client request whose transmit timestamp it echoes in its
origin field. An unpaired reply is reported as such rather than counted as an answer.
"""

import argparse
import struct
import sys
import time

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from snmpwire import packets                                     # noqa: E402  (classic pcap reader)

NTP_EPOCH = 2208988800
LI_TEXT = {0: "ok", 1: "+1s", 2: "-1s", 3: "UNSYNC"}
MODE_TEXT = {0: "reserved", 1: "sym-active", 2: "sym-passive", 3: "client",
             4: "server", 5: "broadcast", 6: "control", 7: "private"}


def ts(s, f):
    if s == 0 and f == 0:
        return None
    return (s - NTP_EPOCH) + f / float(1 << 32)


def stamp(t):
    if t is None:
        return "-"
    return time.strftime("%H:%M:%S", time.gmtime(t)) + ("%.6f" % (t % 1))[1:]


def v6str(b):
    parts = [("%x" % struct.unpack(">H", b[i:i + 2])[0]) for i in range(0, 16, 2)]
    s = ":".join(parts)
    # one round of :: compression, longest run of zero groups
    best_i = best_n = cur_i = cur_n = -1
    for i, p in enumerate(parts):
        if p == "0":
            if cur_n < 0:
                cur_i, cur_n = i, 1
            else:
                cur_n += 1
            if cur_n > best_n:
                best_i, best_n = cur_i, cur_n
        else:
            cur_n = -1
    if best_n > 1:
        s = ":".join(parts[:best_i]) + "::" + ":".join(parts[best_i + best_n:])
    return s


def udp(d, ports):
    """Return (src, sport, dst, dport, payload, family) for an IPv4 or IPv6 UDP frame."""
    if len(d) < 14:
        return None
    et = struct.unpack(">H", d[12:14])[0]
    off = 14
    while et in (0x8100, 0x88A8, 0x9100) and len(d) >= off + 4:
        et = struct.unpack(">H", d[off + 2:off + 4])[0]
        off += 4
    if et == 0x0800:
        if len(d) < off + 20:
            return None
        ihl = (d[off] & 0x0F) * 4
        if d[off + 9] != 17 or len(d) < off + ihl + 8:
            return None
        src = ".".join(str(b) for b in d[off + 12:off + 16])
        dst = ".".join(str(b) for b in d[off + 16:off + 20])
        u = off + ihl
        fam = "4"
    elif et == 0x86DD:
        if len(d) < off + 40:
            return None
        nh = d[off + 6]
        u = off + 40
        # walk the common extension headers to find UDP
        hops = 0
        while nh in (0, 43, 60) and len(d) >= u + 8 and hops < 8:
            nxt, hlen = d[u], d[u + 1]
            u += (hlen + 1) * 8
            nh = nxt
            hops += 1
        if nh != 17 or len(d) < u + 8:
            return None
        src = v6str(d[off + 8:off + 24])
        dst = v6str(d[off + 24:off + 40])
        fam = "6"
    else:
        return None
    sp, dp = struct.unpack(">HH", d[u:u + 4])
    if ports and sp not in ports and dp not in ports:
        return None
    return src, sp, dst, dp, d[u + 8:], fam


def decode(p):
    if len(p) < 48:
        return None
    li, vn, mode = (p[0] >> 6) & 3, (p[0] >> 3) & 7, p[0] & 7
    stratum = p[1]
    rid = p[12:16]
    ref_s, ref_f, org_s, org_f, rec_s, rec_f, xmt_s, xmt_f = struct.unpack(">8I", p[16:48])
    if stratum in (0, 1):
        refid = "".join(chr(b) if 32 <= b < 127 else "." for b in rid).rstrip("\0. ") or "----"
    else:
        refid = ".".join(str(b) for b in rid)
    return {"li": li, "vn": vn, "mode": mode, "stratum": stratum, "refid": refid,
            "poll": struct.unpack(">b", p[2:3])[0],
            "precision": struct.unpack(">b", p[3:4])[0],
            "reference": ts(ref_s, ref_f), "origin": ts(org_s, org_f),
            "receive": ts(rec_s, rec_f), "transmit": ts(xmt_s, xmt_f),
            "origin_words": (org_s, org_f), "transmit_words": (xmt_s, xmt_f),
            "len": len(p), "mac": len(p) > 48}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pcap")
    ap.add_argument("--port", type=int, action="append", default=[],
                    help="UDP port(s) to treat as NTP; any --port REPLACES the default [123]")
    ap.add_argument("--from", dest="src", action="append", default=[],
                    help="only packets with this source address (repeatable)")
    ap.add_argument("--to", dest="dst", action="append", default=[],
                    help="only packets with this destination address (repeatable)")
    ap.add_argument("--limit", type=int, default=0, help="print at most N packet lines")
    ap.add_argument("--quiet", action="store_true", help="summary only")
    args = ap.parse_args()

    ports = set(args.port) if args.port else {123}
    rows, shown = [], 0
    try:
        stream = packets(args.pcap)
    except (OSError, ValueError) as e:
        print("ntpwire: %s" % e)
        return 3
    total = 0
    for when, data in stream:
        total += 1
        u = udp(data, ports)
        if not u:
            continue
        src, sp, dst, dp, pay, fam = u
        if args.src and src not in args.src:
            continue
        if args.dst and dst not in args.dst:
            continue
        d = decode(pay)
        if d is None:
            continue
        d.update({"when": when, "src": src, "sport": sp, "dst": dst, "dport": dp, "family": fam})
        rows.append(d)
        if not args.quiet and (args.limit == 0 or shown < args.limit):
            shown += 1
            print("%s v%-3s %-39s:%-5d -> %-39s:%-5d  %-11s v%d LI=%-6s st=%-2d refid=%-16s"
                  " xmit=%s%s"
                  % (stamp(when), d["family"], src, sp, dst, dp, MODE_TEXT.get(d["mode"], "?"),
                     d["vn"], LI_TEXT.get(d["li"], "?"), d["stratum"], d["refid"],
                     stamp(d["transmit"]), "  +MAC(auth)" if d["mac"] else ""))

    print("")
    print("ntpwire: %s -- %d frames in the capture, %d NTP packets on port(s) %s"
          % (args.pcap, total, len(rows), ",".join(str(p) for p in sorted(ports))))
    if not rows:
        print("  NO NTP PACKETS. For a control leg that is the measurement, not an error.")
        return 2

    by_mode, by_pair, by_fam = {}, {}, {}
    for d in rows:
        by_mode[d["mode"]] = by_mode.get(d["mode"], 0) + 1
        k = "%s -> %s" % (d["src"], d["dst"])
        by_pair[k] = by_pair.get(k, 0) + 1
        by_fam[d["family"]] = by_fam.get(d["family"], 0) + 1
    print("  by family: " + "  ".join("IPv%s=%d" % (f, n) for f, n in sorted(by_fam.items())))
    print("  by mode:   " + "  ".join("%s(%d)=%d" % (MODE_TEXT.get(m, "?"), m, n)
                                      for m, n in sorted(by_mode.items())))
    for k in sorted(by_pair):
        print("  %-55s %d" % (k, by_pair[k]))

    # pair each server reply with the request whose transmit timestamp it echoes
    reqs = {}
    for d in rows:
        if d["mode"] in (1, 3):
            reqs.setdefault((d["src"], d["transmit_words"]), d)
    paired = unpaired = 0
    for d in rows:
        if d["mode"] not in (2, 4):
            continue
        if (d["dst"], d["origin_words"]) in reqs:
            paired += 1
        else:
            unpaired += 1
    nreq = sum(1 for d in rows if d["mode"] in (1, 3))
    nrep = sum(1 for d in rows if d["mode"] in (2, 4))
    print("  pairing:   requests=%d replies=%d  paired=%d unpaired=%d unanswered=%d"
          % (nreq, nrep, paired, unpaired, max(0, nreq - paired)))
    if unpaired:
        print("             an UNPAIRED reply does not echo any request in this capture --"
              " it is not evidence that a request was answered")
    kod = [d for d in rows if d["mode"] in (2, 4) and d["stratum"] == 0]
    if kod:
        print("  !! %d kiss-o'-death repl(ies), code(s): %s"
              % (len(kod), ",".join(sorted(set(d["refid"] for d in kod)))))
    unsync = [d for d in rows if d["mode"] in (2, 4) and d["li"] == 3]
    if unsync:
        print("  !! %d repl(ies) with LI=3 (server says it is NOT synchronised)" % len(unsync))
    return 0


if __name__ == "__main__":
    sys.exit(main())
