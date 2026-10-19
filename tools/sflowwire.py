#!/usr/bin/env python3
"""Decode the sFlow v5 datagrams in a libpcap file and print what each sample says.

This exists because `sflowtool` is not installed on every testbox and installing it is root
(STANDING-ORDERS §4), while a bench verdict on sFlow needs the one thing no `show` command on
the device can give: that a datagram really left the switch, that it names the configured
agent, and that the sampling rate and the sampled frame in it are the ones the test set up.
`show sflow` saying "Enabled" is not a measurement (platforms/x960.md §5).

No dependencies: it borrows `snmpwire.py`'s classic-pcap reader and its
Ethernet/802.1Q/IPv4/UDP walk (so it takes `tcpdump -w` output, NOT pcapng), and does its own
XDR parsing.

What it prints, per datagram: the agent address, sub-agent id, datagram sequence number, agent
uptime and sample count; then per sample, for a FLOW sample the sampling rate, sample pool,
drops, input and output ifIndex and the sampled frame's own header (MACs, EtherType, IPv4
addresses, protocol and ports), and for a COUNTERS sample the ifIndex and the generic interface
counters. A one-line SUMMARY ends the run.

Usage:
  sflowwire.py <file.pcap> [--port 6343] [--limit N] [--abs] [--quiet]

  --port N   UDP port(s) carrying sFlow (default 6343); repeatable
  --limit N  stop after N decoded datagrams
  --abs      absolute local time per datagram instead of the offset from the first one
  --quiet    the SUMMARY line only -- for counting datagrams and samples in a control window
  --find T   count the raw-header samples whose sampled bytes contain the ASCII text T, and
             mark each one. Use it to prove WHICH burst a sample belongs to: a frame marker
             such as vsend.py's --tag travels in the payload, and the sampled header is the
             only place a decoder can see it. Without this, two bursts of the same shape are
             indistinguishable in a decode.

Exit: 0 if at least one sFlow datagram was decoded, 1 if none, 2 on a file/usage error.
"""
import argparse
import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import snmpwire  # noqa: E402  (the pcap reader and the Ethernet/IPv4/UDP walk)

SAMPLE_TYPES = {1: "flow", 2: "counters", 3: "flow-expanded", 4: "counters-expanded"}
HEADER_PROTOCOLS = {1: "ethernet-iso88023", 2: "iso88024-tokenbus", 3: "iso88025-tokenring",
                    4: "fddi", 5: "frame-relay", 6: "x25", 7: "ppp", 8: "smds", 9: "aal5",
                    10: "aal5-ip", 11: "ipv4", 12: "ipv6", 13: "mpls", 14: "pos"}
IP_PROTOCOLS = {1: "ICMP", 2: "IGMP", 6: "TCP", 17: "UDP", 89: "OSPF"}


class XDR(object):
    """Just enough XDR to walk an sFlow datagram, with hard bounds on every read."""

    def __init__(self, buf, off=0, end=None):
        self.b = buf
        self.i = off
        self.end = len(buf) if end is None else end

    def left(self):
        return self.end - self.i

    def u32(self):
        if self.left() < 4:
            raise ValueError("truncated u32")
        v = struct.unpack_from(">I", self.b, self.i)[0]
        self.i += 4
        return v

    def u64(self):
        if self.left() < 8:
            raise ValueError("truncated u64")
        v = struct.unpack_from(">Q", self.b, self.i)[0]
        self.i += 8
        return v

    def raw(self, n):
        if n < 0 or self.left() < n:
            raise ValueError("truncated opaque(%d)" % n)
        v = self.b[self.i:self.i + n]
        self.i += n
        return v

    def opaque(self, n):
        """n bytes, then skip the XDR pad up to a 4-byte boundary."""
        v = self.raw(n)
        pad = (4 - (n % 4)) % 4
        if pad:
            self.i += min(pad, self.left())
        return v

    def ip(self, addr_type):
        if addr_type == 1:
            return ".".join(str(c) for c in self.raw(4))
        if addr_type == 2:
            h = self.raw(16).hex()
            return ":".join(h[k:k + 4] for k in range(0, 32, 4))
        raise ValueError("unknown address type %d" % addr_type)


def mac(b):
    return ":".join("%02x" % c for c in b)


def decode_frame(hdr):
    """Describe a sampled Ethernet frame. Best effort: it never raises."""
    out = []
    try:
        if len(hdr) < 14:
            return "frame too short to decode (%d bytes)" % len(hdr)
        dst, src = mac(hdr[0:6]), mac(hdr[6:12])
        i, et = 12, struct.unpack_from(">H", hdr, 12)[0]
        tags = []
        while et in (0x8100, 0x88a8, 0x9100) and len(hdr) >= i + 8:
            tags.append(struct.unpack_from(">H", hdr, i + 2)[0] & 0x0FFF)
            i += 4
            et = struct.unpack_from(">H", hdr, i)[0]
        i += 2
        out.append("dst=%s src=%s" % (dst, src))
        if tags:
            out.append("vlan=%s" % ",".join(str(t) for t in tags))
        out.append("ethertype=0x%04x" % et)
        if et == 0x0800 and len(hdr) >= i + 20:
            ihl = (hdr[i] & 0x0F) * 4
            proto = hdr[i + 9]
            sip = ".".join(str(c) for c in hdr[i + 12:i + 16])
            dip = ".".join(str(c) for c in hdr[i + 16:i + 20])
            out.append("%s -> %s proto=%s" % (sip, dip, IP_PROTOCOLS.get(proto, proto)))
            if proto in (6, 17) and len(hdr) >= i + ihl + 4:
                sp, dp = struct.unpack_from(">HH", hdr, i + ihl)
                out.append("sport=%d dport=%d" % (sp, dp))
    except (struct.error, IndexError):
        out.append("(header truncated in the sample)")
    return "  ".join(out)


def flow_records(x, end, out, find=None, hits=None):
    """Walk the records of one flow sample."""
    n = x.u32()
    out.append("      %d flow record(s)" % n)
    for _ in range(n):
        if x.left() < 8:
            break
        fmt = x.u32()
        ln = x.u32()
        stop = min(x.i + ln, end)
        if fmt == 1:                                   # raw packet header
            try:
                proto = x.u32()
                frame_len = x.u32()
                stripped = x.u32()
                hdr_len = x.u32()
                hdr = x.opaque(min(hdr_len, max(0, stop - x.i)))
                out.append("      raw-header: protocol=%s frame_length=%d stripped=%d "
                           "header_length=%d" %
                           (HEADER_PROTOCOLS.get(proto, proto), frame_len, stripped, hdr_len))
                mark = ""
                if find:
                    if find.encode("latin-1") in hdr:
                        mark = "   <- contains %r" % find
                        if hits is not None:
                            hits[0] += 1
                    elif hits is not None:
                        hits[1] += 1
                out.append("        %s%s" % (decode_frame(hdr), mark))
            except ValueError as e:
                out.append("      raw-header: undecodable (%s)" % e)
        else:
            out.append("      record format %d, %d bytes (not decoded)" % (fmt, ln))
        x.i = stop


def counter_records(x, end, out):
    n = x.u32()
    out.append("      %d counter record(s)" % n)
    for _ in range(n):
        if x.left() < 8:
            break
        fmt = x.u32()
        ln = x.u32()
        stop = min(x.i + ln, end)
        if fmt == 1:                                   # generic interface counters
            try:
                out.append("      if-counters: ifIndex=%d ifType=%d ifSpeed=%d ifDirection=%d "
                           "ifStatus=0x%x" % (x.u32(), x.u32(), x.u64(), x.u32(), x.u32()))
                out.append("        in:  octets=%d ucast=%d multicast=%d broadcast=%d "
                           "discards=%d errors=%d unknownproto=%d" %
                           (x.u64(), x.u32(), x.u32(), x.u32(), x.u32(), x.u32(), x.u32()))
                out.append("        out: octets=%d ucast=%d multicast=%d broadcast=%d "
                           "discards=%d errors=%d" %
                           (x.u64(), x.u32(), x.u32(), x.u32(), x.u32(), x.u32()))
            except ValueError as e:
                out.append("      if-counters: undecodable (%s)" % e)
        else:
            out.append("      record format %d, %d bytes (not decoded)" % (fmt, ln))
        x.i = stop


def decode_datagram(pay, find=None, hits=None):
    """Decode one sFlow v5 datagram. Returns (header dict, [text lines]) or None."""
    try:
        x = XDR(pay)
        ver = x.u32()
        if ver != 5:
            return None
        addr_type = x.u32()
        agent = x.ip(addr_type)
        sub = x.u32()
        seq = x.u32()
        uptime = x.u32()
        nsamp = x.u32()
    except ValueError:
        return None
    hdr = {"agent": agent, "sub": sub, "seq": seq, "uptime": uptime, "nsamp": nsamp,
           "flow": 0, "counters": 0}
    lines = []
    for _ in range(nsamp):
        if x.left() < 8:
            lines.append("    (datagram ends early: %d sample(s) declared)" % nsamp)
            break
        try:
            stype = x.u32() & 0xFFF
            slen = x.u32()
        except ValueError:
            break
        end = min(x.i + slen, x.end)
        name = SAMPLE_TYPES.get(stype, "type-%d" % stype)
        try:
            if stype in (1, 3):
                hdr["flow"] += 1
                sseq = x.u32()
                if stype == 1:
                    sid = x.u32()
                    src = "%d:%d" % (sid >> 24, sid & 0x00FFFFFF)
                else:
                    src = "%d:%d" % (x.u32(), x.u32())
                rate, pool, drops = x.u32(), x.u32(), x.u32()
                if stype == 1:
                    inp, outp = str(x.u32()), str(x.u32())
                else:
                    inp = "%d:%d" % (x.u32(), x.u32())
                    outp = "%d:%d" % (x.u32(), x.u32())
                lines.append("    %s sample seq=%d source=%s sampling_rate=1-in-%d "
                             "sample_pool=%d drops=%d input=%s output=%s" %
                             (name, sseq, src, rate, pool, drops, inp, outp))
                flow_records(x, end, lines, find, hits)
            elif stype in (2, 4):
                hdr["counters"] += 1
                sseq = x.u32()
                if stype == 2:
                    sid = x.u32()
                    src = "%d:%d" % (sid >> 24, sid & 0x00FFFFFF)
                else:
                    src = "%d:%d" % (x.u32(), x.u32())
                lines.append("    %s sample seq=%d source=%s" % (name, sseq, src))
                counter_records(x, end, lines)
            else:
                lines.append("    %s sample, %d bytes (not decoded)" % (name, slen))
        except ValueError as e:
            lines.append("    %s sample: undecodable (%s)" % (name, e))
        x.i = end
    return hdr, lines


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pcap")
    ap.add_argument("--port", type=int, action="append", default=[])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--abs", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--find", default=None,
                    help="count raw-header samples whose sampled bytes contain this ASCII text")
    a = ap.parse_args()
    ports = set(a.port) or {6343}

    n = flow = counters = 0
    hits = [0, 0]
    agents, t0, first_seq, last_seq = set(), None, None, None
    try:
        for ts, data in snmpwire.packets(a.pcap):
            u = snmpwire.udp_payload(data, ports)
            if not u:
                continue
            src, sp, dst, dp, pay = u
            d = decode_datagram(pay, a.find, hits)
            if not d:
                continue
            h, lines = d
            n += 1
            flow += h["flow"]
            counters += h["counters"]
            agents.add(h["agent"])
            if t0 is None:
                t0 = ts
                first_seq = h["seq"]
            last_seq = h["seq"]
            if not a.quiet:
                when = (time.strftime("%H:%M:%S", time.localtime(ts)) +
                        ".%03d" % int((ts % 1) * 1000) if a.abs else "+%7.3fs" % (ts - t0))
                print("#%-3d %s %s:%d -> %s:%d  sFlow v5  agent=%s sub_agent=%d seq=%d "
                      "uptime=%dms samples=%d" %
                      (n, when, src, sp, dst, dp, h["agent"], h["sub"], h["seq"],
                       h["uptime"], h["nsamp"]))
                for ln in lines:
                    print(ln)
            if a.limit and n >= a.limit:
                break
    except (ValueError, OSError) as e:
        print("sflowwire: %s" % e, file=sys.stderr)
        return 2

    extra = ""
    if a.find:
        extra = "; %d sampled header(s) contain %r, %d do not" % (hits[0], a.find, hits[1])
    print("SUMMARY %d sFlow v5 datagram(s): %d flow sample(s), %d counters sample(s); "
          "agent(s) %s; seq %s..%s%s" %
          (n, flow, counters, ",".join(sorted(agents)) or "-",
           first_seq if first_seq is not None else "-",
           last_seq if last_seq is not None else "-", extra))
    return 0 if n else 1


if __name__ == "__main__":
    sys.exit(main())
