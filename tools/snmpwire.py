#!/usr/bin/env python3
"""Decode the SNMP messages in a libpcap file and say which ones are ENCRYPTED on the wire.

This answers the one question no `show` command on a device can: for SNMPv3, is the PDU
(the varbinds -- the OIDs and their values) actually encrypted in flight, or is it travelling
in the clear?  An SNMPv3 message carries `msgData` as either a plaintext `scopedPDU`
(ASN.1 tag 0x30, SEQUENCE) or an `encryptedPDU` (tag 0x04, OCTET STRING).  That tag, together
with the msgFlags auth/priv bits, is the proof.

No dependencies: it reads classic pcap itself (both byte orders), walks Ethernet (with
802.1Q/QinQ), IPv4 and UDP, and does its own BER parsing.

Usage:
  snmpwire.py <file.pcap> [--port 161] [--port 162] [--limit N] [--oids] [--values]

  --port N   UDP port(s) to treat as SNMP (default 161 and 162); repeatable
  --limit N  stop after N decoded SNMP messages
  --oids     also list the varbind OIDs of every PLAINTEXT message
  --values   list each varbind as OID = <type>: <value> (implies --oids).  A v2c/v3
             notification is identified by the VALUE of snmpTrapOID.0, not by its OID, so
             --oids alone cannot tell linkDown from linkUp or risingAlarm from fallingAlarm.
  --abs      print each message's absolute local time instead of the offset from the first
             one, so a trap can be correlated with the step that was meant to cause it (and
             with the silence of a control window).

Exit: 0 if at least one SNMP message was decoded, 1 if none, 2 on a file/usage error.
"""
import argparse
import struct
import sys
import time

PDU_TAGS = {0xa0: "GetRequest", 0xa1: "GetNextRequest", 0xa2: "Response", 0xa3: "SetRequest",
            0xa4: "Trap-v1", 0xa5: "GetBulkRequest", 0xa6: "InformRequest",
            0xa7: "SNMPv2-Trap", 0xa8: "Report"}

# snmpTrapOID.0 -- the varbind whose VALUE names a v2c/v3 notification (RFC 3418 / RFC 2819).
SNMP_TRAP_OID = "1.3.6.1.6.3.1.1.4.1.0"
# A few standard notification OIDs, so a trap decode reads without a MIB browser.  Annotation
# only: an unlisted OID is printed as-is and nothing is inferred from its absence.
NOTIFY_NAMES = {
    "1.3.6.1.6.3.1.1.5.1": "coldStart",
    "1.3.6.1.6.3.1.1.5.2": "warmStart",
    "1.3.6.1.6.3.1.1.5.3": "linkDown",
    "1.3.6.1.6.3.1.1.5.4": "linkUp",
    "1.3.6.1.6.3.1.1.5.5": "authenticationFailure",
    "1.3.6.1.2.1.16.0.1": "risingAlarm",
    "1.3.6.1.2.1.16.0.2": "fallingAlarm",
}


# ---------------------------------------------------------------- BER
def ber(buf, i):
    """Parse one TLV at offset i. Return (tag, value_start, value_len, next_offset)."""
    if i + 2 > len(buf):
        raise ValueError("truncated")
    tag = buf[i]
    ln = buf[i + 1]
    i += 2
    if ln & 0x80:
        n = ln & 0x7F
        if n == 0 or i + n > len(buf):
            raise ValueError("bad length")
        ln = int.from_bytes(buf[i:i + n], "big")
        i += n
    if i + ln > len(buf):
        raise ValueError("truncated value")
    return tag, i, ln, i + ln


def ber_int(buf, i, ln):
    return int.from_bytes(buf[i:i + ln], "big", signed=True) if ln else 0


def ber_oid(buf, i, ln):
    if not ln:
        return ""
    out = [str(buf[i] // 40), str(buf[i] % 40)]
    v = 0
    for b in buf[i + 1:i + ln]:
        v = (v << 7) | (b & 0x7F)
        if not b & 0x80:
            out.append(str(v))
            v = 0
    return ".".join(out)


APP_TAGS = {0x40: "IpAddress", 0x41: "Counter32", 0x42: "Gauge32", 0x43: "TimeTicks",
            0x44: "Opaque", 0x46: "Counter64"}
EXCEPT_TAGS = {0x80: "noSuchObject", 0x81: "noSuchInstance", 0x82: "endOfMibView"}


def ber_value(buf, tag, i, ln):
    """Render one varbind value as (type_name, text).  Unknown tags print as hex."""
    if tag == 0x02:
        return "INTEGER", str(ber_int(buf, i, ln))
    if tag == 0x04:
        raw = buf[i:i + ln]
        txt = raw.decode("latin-1")
        if all(32 <= c < 127 or c in (9, 10, 13) for c in raw):
            return "STRING", txt
        return "Hex-STRING", raw.hex()
    if tag == 0x05:
        return "NULL", ""
    if tag == 0x06:
        return "OID", ber_oid(buf, i, ln)
    if tag == 0x40:
        return "IpAddress", ".".join(str(b) for b in buf[i:i + ln])
    if tag in (0x41, 0x42, 0x43, 0x46):
        return APP_TAGS[tag], str(int.from_bytes(buf[i:i + ln], "big"))
    if tag in EXCEPT_TAGS:
        return EXCEPT_TAGS[tag], ""
    return "0x%02x" % tag, buf[i:i + ln].hex()


def varbind_list(buf, i, end):
    """Collect (oid, type, value) from a VarBindList SEQUENCE spanning [i, end)."""
    out = []
    while i < end:
        try:
            t, vi, vl, nxt = ber(buf, i)
        except ValueError:
            break
        if t == 0x30:
            try:
                t2, vi2, vl2, after = ber(buf, vi)
                if t2 == 0x06:
                    oid = ber_oid(buf, vi2, vl2)
                    try:
                        t3, vi3, vl3, _ = ber(buf, after)
                        ty, val = ber_value(buf, t3, vi3, vl3)
                    except ValueError:
                        ty, val = "?", ""
                    out.append((oid, ty, val))
            except ValueError:
                pass
        i = nxt
    return out


def varbind_oids(buf, i, end):
    """Collect OIDs only, from a VarBindList SEQUENCE spanning [i, end)."""
    return [o for o, _, _ in varbind_list(buf, i, end)]


def decode_snmp(p, want_oids):
    """Decode an SNMP message. Return a dict, or None if it is not SNMP."""
    try:
        t, i, ln, end = ber(p, 0)
        if t != 0x30:
            return None
        t, vi, vl, nxt = ber(p, i)           # version
        if t != 0x02:
            return None
        ver = ber_int(p, vi, vl)
        if ver in (0, 1):                     # v1 / v2c
            t, vi, vl, nxt = ber(p, nxt)      # community
            if t != 0x04:
                return None
            comm = p[vi:vi + vl].decode("latin-1")
            t, vi, vl, nxt = ber(p, nxt)      # PDU
            r = {"ver": "v1" if ver == 0 else "v2c", "community": comm,
                 "pdu": PDU_TAGS.get(t, "0x%02x" % t), "enc": False, "oids": [], "vbs": []}
            if want_oids and t in PDU_TAGS and t != 0xa4:
                try:                           # request-id, error-status, error-index, varbinds
                    j = vi
                    for _ in range(3):
                        _, _, _, j = ber(p, j)
                    tv, vbi, vbl, _ = ber(p, j)
                    if tv == 0x30:
                        r["vbs"] = varbind_list(p, vbi, vbi + vbl)
                        r["oids"] = [o for o, _, _ in r["vbs"]]
                except ValueError:
                    pass
            return r
        if ver != 3:
            return None
        # v3: msgGlobalData
        t, gi, gl, nxt = ber(p, nxt)
        if t != 0x30:
            return None
        j = gi
        t, vi, vl, j = ber(p, j)              # msgID
        msgid = ber_int(p, vi, vl)
        t, vi, vl, j = ber(p, j)              # msgMaxSize
        t, vi, vl, j = ber(p, j)              # msgFlags
        flags = p[vi] if vl else 0
        t, vi, vl, j = ber(p, j)              # msgSecurityModel
        secmodel = ber_int(p, vi, vl)
        # msgSecurityParameters: OCTET STRING wrapping a USM SEQUENCE
        t, spi, spl, nxt = ber(p, nxt)
        eid, user = "", ""
        if t == 0x04:
            try:
                t2, ui, ul, _ = ber(p, spi)
                if t2 == 0x30:
                    k = ui
                    t3, a1, l1, k = ber(p, k)        # msgAuthoritativeEngineID
                    eid = p[a1:a1 + l1].hex()
                    _, _, _, k = ber(p, k)           # EngineBoots
                    _, _, _, k = ber(p, k)           # EngineTime
                    t3, a4, l4, k = ber(p, k)        # msgUserName
                    user = p[a4:a4 + l4].decode("latin-1")
            except ValueError:
                pass
        # msgData
        t, di, dl, _ = ber(p, nxt)
        r = {"ver": "v3", "msgid": msgid, "secmodel": secmodel,
             "auth": bool(flags & 1), "priv": bool(flags & 2), "reportable": bool(flags & 4),
             "engineid": eid, "user": user, "pdu": "", "oids": [], "vbs": [],
             "enc": (t == 0x04), "datalen": dl}
        if t == 0x30:                          # plaintext scopedPDU
            try:
                k = di
                _, _, _, k = ber(p, k)         # contextEngineID
                _, _, _, k = ber(p, k)         # contextName
                tp, pi, pl, _ = ber(p, k)      # the PDU
                r["pdu"] = PDU_TAGS.get(tp, "0x%02x" % tp)
                if want_oids:
                    m = pi
                    for _ in range(3):
                        _, _, _, m = ber(p, m)
                    tv, vbi, vbl, _ = ber(p, m)
                    if tv == 0x30:
                        r["vbs"] = varbind_list(p, vbi, vbi + vbl)
                        r["oids"] = [o for o, _, _ in r["vbs"]]
            except ValueError:
                pass
        return r
    except (ValueError, IndexError):
        return None


# ---------------------------------------------------------------- pcap
def packets(path):
    with open(path, "rb") as f:
        gh = f.read(24)
        if len(gh) < 24:
            raise ValueError("not a pcap file (short header)")
        magic = gh[:4]
        if magic in (b"\xa1\xb2\xc3\xd4", b"\xa1\xb2\x3c\x4d"):
            endian, nano = ">", magic.endswith(b"\x4d")
        elif magic in (b"\xd4\xc3\xb2\xa1", b"\x4d\x3c\xb2\xa1"):
            endian, nano = "<", magic.startswith(b"\x4d")
        elif magic == b"\x0a\x0d\x0d\x0a":
            raise ValueError("this is pcapng, not classic pcap -- capture with `tcpdump -w`")
        else:
            raise ValueError("not a pcap file (magic %s)" % magic.hex())
        link = struct.unpack(endian + "I", gh[20:24])[0]
        if link != 1:
            raise ValueError("link type %d is not Ethernet" % link)
        while True:
            ph = f.read(16)
            if len(ph) < 16:
                return
            ts, tus, caplen, _ = struct.unpack(endian + "IIII", ph)
            data = f.read(caplen)
            if len(data) < caplen:
                return
            yield ts + (tus / 1e9 if nano else tus / 1e6), data


def udp_payload(d, ports):
    if len(d) < 14:
        return None
    et = struct.unpack(">H", d[12:14])[0]
    off = 14
    while et in (0x8100, 0x88a8, 0x9100) and len(d) >= off + 4:
        et = struct.unpack(">H", d[off + 2:off + 4])[0]
        off += 4
    if et != 0x0800 or len(d) < off + 20:
        return None
    ihl = (d[off] & 0x0F) * 4
    if d[off + 9] != 17 or len(d) < off + ihl + 8:
        return None
    src = ".".join(str(b) for b in d[off + 12:off + 16])
    dst = ".".join(str(b) for b in d[off + 16:off + 20])
    u = off + ihl
    sp, dp = struct.unpack(">HH", d[u:u + 4])
    if sp not in ports and dp not in ports:
        return None
    return src, sp, dst, dp, d[u + 8:]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pcap")
    ap.add_argument("--port", type=int, action="append", default=[])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--oids", action="store_true")
    ap.add_argument("--values", action="store_true",
                    help="list each varbind as OID = <type>: <value> (implies --oids)")
    ap.add_argument("--abs", action="store_true",
                    help="print absolute local time per message instead of the offset")
    a = ap.parse_args()
    if a.values:
        a.oids = True
    ports = set(a.port) or {161, 162}

    n = enc = plain = 0
    t0 = None
    try:
        for ts, data in packets(a.pcap):
            u = udp_payload(data, ports)
            if not u:
                continue
            src, sp, dst, dp, pay = u
            m = decode_snmp(pay, a.oids)
            if not m:
                continue
            n += 1
            if t0 is None:
                t0 = ts
            when = (time.strftime("%H:%M:%S", time.localtime(ts)) + ".%03d" % int((ts % 1) * 1000)
                    if a.abs else "+%7.3fs" % (ts - t0))
            head = "#%-3d %s %s:%d -> %s:%d  SNMP%s" % (n, when, src, sp, dst, dp, m["ver"])
            if m["ver"] == "v3":
                body = "msgID=%d flags=%s%s%s user=%r engineID=%s" % (
                    m["msgid"],
                    "a" if m["auth"] else "-", "p" if m["priv"] else "-",
                    "r" if m["reportable"] else "-",
                    m["user"], m["engineid"] or "(none)")
                if m["enc"]:
                    enc += 1
                    body += "  msgData=ENCRYPTED(%d bytes, ASN.1 OCTET STRING)" % m["datalen"]
                else:
                    plain += 1
                    body += "  msgData=PLAINTEXT scopedPDU pdu=%s" % (m["pdu"] or "?")
            else:
                plain += 1
                body = "community=%r pdu=%s  msgData=PLAINTEXT" % (m["community"], m["pdu"])
            print(head + "  " + body)
            if a.oids and m["oids"]:
                if a.values:
                    for oid, ty, val in m["vbs"]:
                        extra = ""
                        if oid == SNMP_TRAP_OID and ty == "OID" and val in NOTIFY_NAMES:
                            extra = "   <- %s" % NOTIFY_NAMES[val]
                        print("      %s = %s: %s%s" % (oid, ty, val, extra))
                else:
                    print("      varbind OIDs in the clear: %s" % ", ".join(m["oids"]))
            if a.limit and n >= a.limit:
                break
    except (ValueError, OSError) as e:
        print("snmpwire: %s" % e, file=sys.stderr)
        return 2

    print("SUMMARY %d SNMP message(s): %d ENCRYPTED, %d PLAINTEXT" % (n, enc, plain))
    return 0 if n else 1


if __name__ == "__main__":
    sys.exit(main())
